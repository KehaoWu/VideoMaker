"""VideoPlan - 视频规划核心类，负责管理视频内容规划"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

@dataclass
class MetaInfo:
    """视频元信息"""
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
    background_track: Optional[str] = None  # 背景音乐
    
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
        meta_info = MetaInfo(
            source_image=image_path,
            output_dir=output_dir,
            total_duration=duration
        )
        return cls(meta_info=meta_info)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoPlan':
        """从字典创建视频规划实例"""
        meta_info = MetaInfo(
            source_image=data['source_image'],
            output_dir=data['output_dir'],
            total_duration=data.get('total_duration', 60.0),
            title=data.get('title', ''),
            description=data.get('description', ''),
            creation_time=data.get('creation_time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            plan_version=data.get('plan_version', '1.0'),
            status=data.get('status', 'pending')
        )
        
        return cls(
            meta_info=meta_info,
            regions=data.get('regions', []),
            background_track=data.get('background_track')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'source_image': self.meta_info.source_image,
            'output_dir': self.meta_info.output_dir,
            'total_duration': self.meta_info.total_duration,
            'title': self.meta_info.title,
            'description': self.meta_info.description,
            'regions': self.regions,
            'background_track': self.background_track,
            'creation_time': self.meta_info.creation_time,
            'plan_version': self.meta_info.plan_version,
            'status': self.meta_info.status
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