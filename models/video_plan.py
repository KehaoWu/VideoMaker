"""VideoPlan - 视频规划核心类，负责管理视频内容规划"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from .cutting_plan import CuttingPlan, SourceImage, CuttingRegion
from PIL import Image

@dataclass
class TextToVideoConfig:
    """文生视频配置"""
    video_id: str
    description: str
    prompt: str
    duration: float
    style: str = "realistic"
    resolution: List[int] = field(default_factory=lambda: [1920, 1080])
    output_path: Optional[str] = None
    status: str = "pending"

@dataclass
class MetaInfo:
    """视频元信息"""
    video_id: str  # 视频唯一标识符
    source_image: str  # 源图片路径
    output_dir: str  # 输出目录
    total_duration: float = 60.0  # 目标视频时长(秒)
    title: str = ""  # 视频标题
    description: str = ""  # 视频描述
    creation_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    plan_version: str = "1.0"
    status: str = "pending"  # pending, planning, completed, failed

@dataclass
class VideoPlan:
    """视频规划核心类 - 负责管理视频制作的完整规划"""
    
    meta_info: MetaInfo
    regions: List[Dict[str, Any]] = field(default_factory=list)  # 区域列表
    text_to_video_segments: List[TextToVideoConfig] = field(default_factory=list)  # 文生视频片段
    background_track: Optional[str] = None  # 背景音乐
    timestamp_dir: str = ""  # 添加时间戳目录属性
    cutting_plan: Optional[CuttingPlan] = None  # 切图规划
    narration_script: Optional[Dict[str, Any]] = None  # 旁白脚本

    @classmethod
    def create_empty_plan(cls, image_path: str, output_dir: str, duration: float = 60.0) -> 'VideoPlan':
        """创建空的视频规划实例
        
        Args:
            image_path: 源图片路径
            output_dir: 输出目录
            duration: 目标视频时长(秒)
            
        Returns:
            VideoPlan: 基础视频规划实例
        """
        # 生成视频ID（使用时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_id = f'video_{timestamp}'
        
        # 创建完整输出路径
        full_output_dir = os.path.join(output_dir, video_id)
        os.makedirs(full_output_dir, exist_ok=True)
        
        # 创建基础的切图规划
        with Image.open(image_path) as img:
            width, height = img.size
            source_image = SourceImage(
                file_path=image_path,
                width=width,
                height=height
            )
        
        cutting_plan = CuttingPlan(
            source_image=source_image,
            total_slices=0,
            regions=[]
        )
        
        return cls(
            meta_info=MetaInfo(
                video_id=video_id,
                title="",
                description="",
                total_duration=duration,
                creation_time=datetime.now().isoformat(),
                source_image=image_path,
                output_dir=full_output_dir
            ),
            regions=[], # Placeholder for regions, will be populated later
            text_to_video_segments=[], # Placeholder for text_to_video_segments, will be populated later
            background_track=None,
            timestamp_dir=video_id,
            cutting_plan=cutting_plan
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoPlan':
        """从字典创建视频规划实例"""
        # 判断是否为旧格式数据（字段在根级别）
        is_legacy = 'meta_info' not in data and 'source_image' in data
        
        # 获取meta_info数据
        meta_data = data.get('meta_info', {}) if not is_legacy else {
            'video_id': os.path.basename(data.get('output_dir', '')),
            'source_image': data.get('source_image', ''),
            'output_dir': data.get('output_dir', ''),
            'total_duration': data.get('total_duration', 60.0),
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'creation_time': data.get('creation_time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            'plan_version': data.get('plan_version', '1.0'),
            'status': data.get('status', 'pending')
        }
        
        meta_info = MetaInfo(
            video_id=meta_data.get('video_id', ''),
            source_image=meta_data.get('source_image', ''),
            output_dir=meta_data.get('output_dir', ''),
            total_duration=meta_data.get('total_duration', 60.0),
            title=meta_data.get('title', ''),
            description=meta_data.get('description', ''),
            creation_time=meta_data.get('creation_time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            plan_version=meta_data.get('plan_version', '1.0'),
            status=meta_data.get('status', 'pending')
        )
        
        # 处理文生视频配置
        text_to_video_segments = []
        for segment_data in data.get('text_to_video_segments', []):
            segment = TextToVideoConfig(
                video_id=segment_data['video_id'],
                description=segment_data['description'],
                prompt=segment_data['prompt'],
                duration=segment_data['duration'],
                style=segment_data.get('style', 'realistic'),
                resolution=segment_data.get('resolution', [1920, 1080]),
                output_path=segment_data.get('output_path'),
                status=segment_data.get('status', 'pending')
            )
            text_to_video_segments.append(segment)
        
        # 处理切图规划
        cutting_plan_data = data.get('cutting_plan')
        if cutting_plan_data:
            cutting_plan = CuttingPlan.from_dict(cutting_plan_data)
        else:
            # 从regions构建cutting_plan
            regions = data.get('regions', [])
            if regions and meta_info.source_image:
                # 获取源图片尺寸
                try:
                    with Image.open(meta_info.source_image) as img:
                        width, height = img.size
                        source_image = SourceImage(
                            file_path=meta_info.source_image,
                            width=width,
                            height=height
                        )
                        
                        # 从regions数据构建切图规划
                        cutting_regions = []
                        for region in regions:
                            cutting_region = CuttingRegion.from_dict({
                                'region_id': region['region_id'],
                                'region_name': region['region_name'],
                                'description': region['description'],
                                'coordinates': region['coordinates'],
                                'output_path': os.path.join(meta_info.output_dir, 'cuts', f"{region['region_id']}.png")
                            })
                            cutting_regions.append(cutting_region)
                        
                        cutting_plan = CuttingPlan(
                            source_image=source_image,
                            total_slices=len(regions),
                            regions=cutting_regions
                        )
                except Exception as e:
                    print(f"构建切图规划失败: {e}")
                    cutting_plan = None
            else:
                cutting_plan = None
        
        # 构建旁白脚本
        narration_script = {
            'segments': [
                {
                    'segment_id': region['region_id'],
                    'text': region['narration']['text'],
                    'estimated_duration': region['narration']['estimated_duration'],
                    'output_path': os.path.join(meta_info.output_dir, 'audio', f"{region['region_id']}.mp3"),
                    'status': 'pending'
                }
                for region in data.get('regions', [])
                if 'narration' in region
            ],
            'total_duration': sum(
                region['narration']['estimated_duration']
                for region in data.get('regions', [])
                if 'narration' in region
            )
        }
        
        # 获取timestamp_dir
        timestamp_dir = data.get('timestamp_dir', '') or os.path.basename(meta_info.output_dir)
        
        return cls(
            meta_info=meta_info,
            regions=data.get('regions', []),
            text_to_video_segments=text_to_video_segments,
            background_track=data.get('background_track'),
            timestamp_dir=timestamp_dir,
            cutting_plan=cutting_plan,
            narration_script=narration_script
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'meta_info': {
                'source_image': self.meta_info.source_image,
                'output_dir': self.meta_info.output_dir,
                'total_duration': self.meta_info.total_duration,
                'title': self.meta_info.title,
                'description': self.meta_info.description,
                'creation_time': self.meta_info.creation_time,
                'plan_version': self.meta_info.plan_version,
                'status': self.meta_info.status
            },
            'regions': self.regions,
            'text_to_video_segments': [
                {
                    'video_id': segment.video_id,
                    'description': segment.description,
                    'prompt': segment.prompt,
                    'duration': segment.duration,
                    'style': segment.style,
                    'resolution': segment.resolution,
                    'output_path': segment.output_path,
                    'status': segment.status
                }
                for segment in self.text_to_video_segments
            ],
            'background_track': self.background_track,
            'timestamp_dir': self.timestamp_dir,
            'cutting_plan': self.cutting_plan.to_dict() if self.cutting_plan else None
        }
    
    @classmethod
    def from_json_file(cls, file_path: str) -> 'VideoPlan':
        """从JSON文件加载视频规划"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"视频规划文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def save_to_json_file(self, file_path: Optional[str] = None) -> str:
        """保存到JSON文件
        
        Args:
            file_path: 可选的文件路径。如果不提供，将在output_dir中自动生成
            
        Returns:
            str: 保存的文件路径
        """
        if file_path is None:
            # 生成基于时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(self.meta_info.output_dir, f"video_plan_{timestamp}.json")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 保存到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            
        return file_path
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证视频规划的有效性"""
        errors = []

        print(self.meta_info)
        
        # 检查必需的文件和目录
        if not os.path.exists(self.meta_info.source_image):
            errors.append(f"源图片不存在: {self.meta_info.source_image}")
        
        if not os.path.exists(self.meta_info.output_dir):
            errors.append(f"输出目录不存在: {self.meta_info.output_dir}")
        
        # 检查基本参数
        if self.meta_info.total_duration <= 0:
            errors.append(f"无效的视频时长: {self.meta_info.total_duration}")
        
        # 规划完成后的验证
        if self.meta_info.status == "completed":
            if not self.meta_info.title:
                errors.append("视频标题不能为空")
            
            if not self.meta_info.description:
                errors.append("视频描述不能为空")
            
            if not self.regions:
                errors.append("必须至少包含一个区域")
            
            # 验证区域数据
            region_ids = set()
            total_duration = 0
            
            for region in self.regions:
                # 检查必需字段
                required_fields = ['region_id', 'region_name', 'description', 'coordinates', 'narration']
                missing_fields = [f for f in required_fields if f not in region]
                if missing_fields:
                    errors.append(f"区域缺少必需字段: {', '.join(missing_fields)}")
                    continue
                
                # 检查ID唯一性
                if region['region_id'] in region_ids:
                    errors.append(f"重复的区域ID: {region['region_id']}")
                region_ids.add(region['region_id'])
                
                # 累计时长
                if 'narration' in region and 'estimated_duration' in region['narration']:
                    total_duration += region['narration']['estimated_duration']
            
            # 检查总时长
            if total_duration > self.meta_info.total_duration:
                errors.append(f"旁白总时长 {total_duration}秒 超过视频总时长 {self.meta_info.total_duration}秒")
        
        return len(errors) == 0, errors
    
    def get_region_by_id(self, region_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取区域信息"""
        for region in self.regions:
            if region['region_id'] == region_id:
                return region
        return None
    
    def update_region(self, region_id: str, updates: Dict[str, Any]) -> bool:
        """更新区域信息
        
        Args:
            region_id: 区域ID
            updates: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        for i, region in enumerate(self.regions):
            if region['region_id'] == region_id:
                self.regions[i].update(updates)
                return True
        return False 