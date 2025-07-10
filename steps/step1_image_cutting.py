"""
步骤1：图片切割
根据计划信息切割图片到指定区域
"""

import os
from typing import Dict, List, Any
from PIL import Image
from pathlib import Path
from datetime import datetime

from .base_step import BaseStep, StepResult
from models.video_plan import VideoPlan
from models.cutting_plan import CuttingRegion
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
    
    def execute(self, video_plan: VideoPlan, output_dir: str) -> StepResult:
        """
        执行图片切割步骤
        
        Args:
            video_plan: 视频规划对象
            output_dir: 输出目录
            
        Returns:
            StepResult: 步骤执行结果
        """
        start_time = datetime.now()
        self.logger.info("开始执行图片切割步骤")
        
        try:
            # 验证输入
            if not self.validate_inputs(video_plan):
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    start_time=start_time.isoformat(),
                    error_message="输入验证失败"
                )
            
            # 创建输出目录
            cutting_dir = os.path.join(output_dir, "cuts")  # 使用cuts目录
            ensure_directory(cutting_dir)
            
            # 获取源图片信息
            source_image = video_plan.cutting_plan.source_image
            image_path = source_image.file_path
            
            # 验证源图片文件
            if not os.path.exists(image_path):
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    start_time=start_time.isoformat(),
                    error_message=f"源图片文件不存在: {image_path}"
                )
            
            # 获取需要切割的区域
            regions = video_plan.cutting_plan.regions
            if not regions:
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    start_time=start_time.isoformat(),
                    error_message="没有定义切割区域"
                )
            
            output_files = []
            
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
                    start_time=start_time.isoformat(),
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
                    start_time=start_time.isoformat(),
                    error_message="没有成功切割任何区域"
                )
                
        except Exception as e:
            self.logger.error(f"图片切割步骤执行失败: {e}")
            return StepResult(
                step_name=self.step_name,
                status="failed",
                start_time=start_time.isoformat(),
                error_message=str(e)
            )
    
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
        if not video_plan:
            return False
            
        if not video_plan.meta_info.source_image:
            self.logger.error("缺少源图片路径")
            return False
            
        if not os.path.exists(video_plan.meta_info.source_image):
            self.logger.error(f"源图片不存在: {video_plan.meta_info.source_image}")
            return False
            
        if not video_plan.cutting_plan:
            self.logger.error("缺少cutting_plan")
            return False
            
        if not video_plan.cutting_plan.regions:
            self.logger.error("cutting_plan中没有区域定义")
            return False
            
        return True
    
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