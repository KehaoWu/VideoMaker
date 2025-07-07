"""
Step 0: 视频规划
使用 LLM (Claude) 生成完整的视频规划方案
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path
from PIL import Image

from apis.claude_api import OpenAIAPI
from models.video_plan import VideoPlan
from models.meta_info import MetaInfo, VideoResolution
from models.cutting_plan import CuttingPlan, SourceImage, CuttingRegion
from models.narration_script import NarrationScript, NarrationSegment
from models.video_composition import VideoComposition, Timeline, TimelineSegment, BackgroundTrack
from utils.logger import get_logger
from .base_step import BaseStep, StepResult


class Step0VideoPlanning(BaseStep):
    """视频规划步骤，使用LLM生成完整的视频规划"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.claude_api = OpenAIAPI()
    
    def execute(self, video_plan: VideoPlan) -> VideoPlan:
        """
        执行视频规划步骤
        
        Args:
            video_plan: 初始的视频计划对象
            
        Returns:
            更新后的视频计划对象
        """
        self.logger.info("开始执行视频规划步骤")
        start_time = datetime.now()
        
        try:
            # 获取基本信息
            image_path = video_plan.meta_info.source_image
            duration = video_plan.meta_info.total_duration
            
            # 生成完整的视频规划
            plan_data = self._generate_video_plan(image_path, duration)
            
            # 更新视频计划对象
            self._update_video_plan(video_plan, plan_data)
            
            # 设置状态为完成
            video_plan.status = "completed"
            
            return video_plan
            
        except Exception as e:
            self.logger.error(f"视频规划步骤失败: {e}")
            video_plan.status = "failed"
            raise
    
    def save_to_json_file(self, video_plan: VideoPlan) -> str:
        """
        将视频规划保存为JSON文件
        
        Args:
            video_plan: 视频规划对象
            
        Returns:
            保存的文件路径
        """
        try:
            # 确保输出目录存在
            output_dir = video_plan.meta_info.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'video_plan_{timestamp}.json'
            output_path = os.path.join(output_dir, filename)
            
            # 准备要保存的数据
            plan_data = {
                'meta_info': {
                    'title': video_plan.meta_info.title,
                    'description': video_plan.meta_info.description,
                    'source_image': video_plan.meta_info.source_image,
                    'total_duration': video_plan.meta_info.total_duration,
                    'output_dir': video_plan.meta_info.output_dir,
                    'status': video_plan.status
                },
                'regions': video_plan.regions
            }
            
            # 保存为JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"视频规划已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"保存视频规划失败: {e}")
            raise
    
    def _generate_video_plan(self, image_path: str, duration: float) -> Dict[str, Any]:
        """
        使用Claude生成完整的视频规划
        
        Args:
            image_path: 图片文件路径
            duration: 视频时长（秒）
            
        Returns:
            完整的视频规划数据
        """
        self.logger.info(f"开始生成视频规划: {image_path}")
        
        # 获取图片尺寸
        with Image.open(image_path) as img:
            width, height = img.size
        
        # 构建提示词
        prompt = self._build_planning_prompt(image_path, width, height, duration)
        
        # 调用Claude API
        response = self.claude_api.send_message_with_image(prompt, image_path)
        
        # 解析响应
        try:
            print(response)
            content = response['content']
            
            # 提取JSON部分
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            plan_data = json.loads(json_str)
            self.logger.info("成功生成视频规划")
            return plan_data
            
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            self.logger.error(f"解析API响应失败: {e}")
            self.logger.error(f"响应内容: {response}")
            raise ValueError(f"解析API响应失败: {e}")
    
    def _build_planning_prompt(self, image_path: str, width: int, height: int, duration: float) -> str:
        """构建视频规划提示词"""
        return f"""请分析这张图片，生成一个完整的视频规划方案。视频时长为 {duration} 秒。

请从以下几个方面进行规划：

1. 内容分析：
- 分析图片的主要内容和布局
- 识别关键区域和重要元素
- 确定内容的逻辑顺序

2. 切图规划：
- 将图片划分为合适的区域
- 每个区域需要包含完整的内容单元
- 提供每个区域的精确坐标（x, y, width, height）

3. 旁白脚本：
- 为每个区域生成对应的旁白文本
- 语言要自然、专业
- 内容要与图片区域紧密相关
- 控制每段旁白的时长，总时长不超过{duration}秒

请以JSON格式返回完整的规划方案，格式如下：
{{
  "meta_info": {{
    "title": "视频标题",
    "description": "整体内容概述"
  }},
  "regions": [
    {{
      "region_id": "region_1",
      "region_name": "区域名称",
      "description": "区域内容描述",
      "coordinates": {{
        "x": 100,
        "y": 50,
        "width": 400,
        "height": 200
      }},
      "narration": {{
        "text": "该区域的旁白文本",
        "estimated_duration": 10.5
      }}
    }}
  ],
  "total_duration": {duration}
}}

注意：
1. 坐标以图片左上角为原点(0,0)
2. 图片实际尺寸为 {width}x{height} 像素
3. 所有区域的旁白总时长不要超过视频总时长
4. 只返回JSON格式，不要其他解释文字"""
    
    def _update_video_plan(self, video_plan: VideoPlan, plan_data: Dict[str, Any]) -> None:
        """
        使用生成的规划数据更新视频计划对象
        
        Args:
            video_plan: 要更新的视频计划对象
            plan_data: 生成的规划数据
        """
        # 更新元信息
        meta_info = plan_data.get('meta_info', {})
        video_plan.meta_info.title = meta_info.get('title', '')
        video_plan.meta_info.description = meta_info.get('description', '')
        video_plan.meta_info.status = "completed"
        
        # 更新区域信息
        video_plan.regions = plan_data.get('regions', [])
    
    def validate_inputs(self, video_plan: VideoPlan) -> bool:
        """验证输入参数"""
        if not video_plan or not video_plan.meta_info:
            return False
        if not video_plan.meta_info.source_image or not video_plan.meta_info.output_dir:
            return False
        if video_plan.meta_info.total_duration <= 0:
            return False
        return True
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的步骤列表"""
        return []  # 这是第一个步骤，没有依赖 