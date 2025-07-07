"""
步骤1：图片切割
使用Claude API分析图片并切割出指定区域
"""

import os
from typing import Dict, List, Any
from PIL import Image
from pathlib import Path

from .base_step import BaseStep, StepResult
from models.video_plan import VideoPlan
from models.cutting_plan import CuttingRegion
from apis.claude_api import OpenAIAPI, OpenAIAPIError
from utils.logger import get_logger
from utils.file_utils import ensure_directory, safe_filename
from utils.config_manager import get_config


class Step1ImageCutting(BaseStep):
    """图片切割处理步骤"""
    
    def __init__(self):
        super().__init__()
        self.step_name = "图片切割"
        self.step_id = "step1"
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # 初始化Claude API客户端
        try:
            self.claude_api = OpenAIAPI()
        except OpenAIAPIError as e:
            self.logger.warning(f"Claude API初始化失败: {e}")
            self.claude_api = None
    
    def execute(self, video_plan: VideoPlan, output_dir: str) -> StepResult:
        """
        执行图片切割步骤
        
        Args:
            video_plan: 视频规划对象
            output_dir: 输出目录
            
        Returns:
            StepResult: 步骤执行结果
        """
        self.logger.info("开始执行图片切割步骤")
        
        try:
            # 验证输入
            if not self.validate_inputs(video_plan):
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message="输入验证失败"
                )
            
            # 创建输出目录
            cutting_dir = os.path.join(output_dir, "step1_cutting")
            ensure_directory(cutting_dir)
            
            # 获取源图片信息
            source_image = video_plan.cutting_plan.source_image
            image_path = source_image.file_path
            
            # 验证源图片文件
            if not os.path.exists(image_path):
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message=f"源图片文件不存在: {image_path}"
                )
            
            # 获取需要切割的区域
            regions = video_plan.cutting_plan.regions
            if not regions:
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message="没有定义切割区域"
                )
            
            output_files = []
            
            # 如果有Claude API，使用AI分析图片和生成旁白
            if self.claude_api:
                # 分析图片区域
                analyzed_regions = self._analyze_regions_with_ai(image_path, regions)
                if analyzed_regions:
                    regions = analyzed_regions
                
                # 生成旁白文本
                self._generate_narration_with_ai(image_path, video_plan)
            
            # 执行图片切割
            for region in regions:
                try:
                    output_path = self._cut_region(image_path, region, cutting_dir)
                    if output_path:
                        output_files.append(output_path)
                        # 更新region的输出路径
                        region.output_path = output_path
                        self.logger.info(f"成功切割区域: {region.region_name} -> {output_path}")
                        
                except Exception as e:
                    self.logger.error(f"切割区域 {region.region_name} 失败: {e}")
                    continue
            
            if output_files:
                return StepResult(
                    step_name=self.step_name,
                    status="completed",
                    output_files=output_files,
                    metadata={
                        "total_regions": len(regions),
                        "successful_cuts": len(output_files),
                        "source_image": image_path
                    }
                )
            else:
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message="没有成功切割任何区域"
                )
                
        except Exception as e:
            self.logger.error(f"图片切割步骤执行失败: {e}")
            return StepResult(
                step_name=self.step_name,
                status="failed", 
                error_message=str(e)
            )
    
    def _analyze_regions_with_ai(self, image_path: str, regions: List[CuttingRegion]) -> List[CuttingRegion]:
        """使用AI分析图片区域"""
        try:
            self.logger.info("使用Claude API分析图片区域")
            
            # 构建区域描述列表
            descriptions = []
            for region in regions:
                desc = f"{region.region_name}: {region.description}"
                descriptions.append(desc)
            
            # 调用Claude API分析
            analyzed_regions = self.claude_api.analyze_image_regions(image_path, descriptions)
            
            # 更新区域坐标
            for i, ai_region in enumerate(analyzed_regions):
                if i < len(regions):
                    coordinates = ai_region.get('coordinates', {})
                    if coordinates:
                        regions[i].coordinates = coordinates
                        self.logger.info(f"AI分析区域 {regions[i].region_name}: {coordinates}")
            
            return regions
            
        except Exception as e:
            self.logger.warning(f"AI分析失败，使用默认坐标: {e}")
            return regions
    
    def _generate_narration_with_ai(self, image_path: str, video_plan: VideoPlan) -> None:
        """使用AI生成旁白文本"""
        try:
            self.logger.info("使用Claude API生成旁白文本")
            
            # 获取视频信息
            title = video_plan.meta_info.video_title
            duration = video_plan.meta_info.total_duration
            
            # 调用Claude API生成旁白
            narration_text = self.claude_api.generate_narration_from_image(image_path, title, duration)
            
            # 更新旁白脚本
            if video_plan.narration_script and video_plan.narration_script.segments:
                video_plan.narration_script.segments[0].text = narration_text
                self.logger.info(f"✓ AI生成旁白文本: {narration_text[:50]}...")
            else:
                self.logger.warning("旁白脚本结构不存在，无法更新")
            
        except Exception as e:
            self.logger.warning(f"AI旁白生成失败: {e}")
            # 使用默认旁白文本
            if video_plan.narration_script and video_plan.narration_script.segments:
                video_plan.narration_script.segments[0].text = "这是一个由VideoMaker自动生成的视频，展示了图片中的内容。"
    
    def _cut_region(self, image_path: str, region: CuttingRegion, output_dir: str) -> str:
        """切割单个区域"""
        try:
            # 打开源图片
            with Image.open(image_path) as img:
                # 获取坐标
                coords = region.coordinates
                if not coords:
                    # 如果没有坐标，使用默认区域（整张图片）
                    coords = {
                        'x': 0,
                        'y': 0, 
                        'width': img.width,
                        'height': img.height
                    }
                
                # 验证坐标
                x = max(0, coords.get('x', 0))
                y = max(0, coords.get('y', 0))
                width = min(coords.get('width', img.width), img.width - x)
                height = min(coords.get('height', img.height), img.height - y)
                
                if width <= 0 or height <= 0:
                    raise ValueError(f"无效的切割尺寸: {width}x{height}")
                
                # 切割图片
                box = (x, y, x + width, y + height)
                cropped_img = img.crop(box)
                
                # 生成输出文件名
                safe_name = safe_filename(region.region_name)
                output_filename = f"slice_{region.region_id}_{safe_name}.png"
                output_path = os.path.join(output_dir, output_filename)
                
                # 保存切割结果
                cropped_img.save(output_path, 'PNG')
                
                return output_path
                
        except Exception as e:
            self.logger.error(f"切割区域失败: {e}")
            raise
    
    def validate_inputs(self, video_plan: VideoPlan) -> bool:
        """验证输入参数"""
        try:
            # 检查cutting_plan
            if not video_plan.cutting_plan:
                self.logger.error("缺少cutting_plan")
                return False
            
            # 检查源图片
            source_image = video_plan.cutting_plan.source_image
            if not source_image or not source_image.file_path:
                self.logger.error("缺少源图片文件路径")
                return False
            
            # 检查文件是否存在
            if not os.path.exists(source_image.file_path):
                self.logger.error(f"源图片文件不存在: {source_image.file_path}")
                return False
            
            # 检查切割区域
            regions = video_plan.cutting_plan.regions
            if not regions:
                self.logger.error("没有定义切割区域")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"输入验证失败: {e}")
            return False
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的步骤列表"""
        return []  # 图片切割是第一步，没有依赖
    
    def get_output_info(self, video_plan: VideoPlan) -> Dict[str, Any]:
        """获取输出信息"""
        regions = video_plan.cutting_plan.regions
        return {
            "expected_outputs": len(regions),
            "output_format": "PNG",
            "output_prefix": "slice_"
        } 