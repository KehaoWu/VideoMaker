"""元信息数据模型"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .base_model import BaseModel


@dataclass
class VideoResolution:
    """视频分辨率"""
    width: int
    height: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoResolution':
        return cls(
            width=data['width'],
            height=data['height']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'width': self.width,
            'height': self.height
        }


@dataclass
class MetaInfo(BaseModel):
    """视频元信息"""
    plan_version: str
    source_image: str
    video_title: str
    total_duration: float
    video_resolution: VideoResolution
    source_image_size: Optional[VideoResolution] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetaInfo':
        return cls(
            plan_version=data['plan_version'],
            source_image=data['source_image'],
            video_title=data['video_title'],
            total_duration=data['total_duration'],
            video_resolution=VideoResolution.from_dict(data['video_resolution']),
            source_image_size=VideoResolution.from_dict(data['source_image_size']) 
                             if 'source_image_size' in data else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'plan_version': self.plan_version,
            'source_image': self.source_image,
            'video_title': self.video_title,
            'total_duration': self.total_duration,
            'video_resolution': self.video_resolution.to_dict()
        }
        if self.source_image_size:
            result['source_image_size'] = self.source_image_size.to_dict()
        return result
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证元信息有效性"""
        errors = []
        
        if not self.video_title:
            errors.append("视频标题不能为空")
        
        if self.total_duration <= 0:
            errors.append("视频总时长必须大于0")
        
        if self.video_resolution.width <= 0 or self.video_resolution.height <= 0:
            errors.append("视频分辨率必须为正数")
        
        if not self.source_image:
            errors.append("源图片路径不能为空")
        
        return len(errors) == 0, errors 