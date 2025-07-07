"""切图规划数据模型"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .base_model import BaseModel


@dataclass
class SourceImage:
    """源图片信息"""
    file_path: str
    width: int
    height: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceImage':
        return cls(
            file_path=data['file_path'],
            width=data['width'],
            height=data['height']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'width': self.width,
            'height': self.height
        }


@dataclass
class CuttingRegion:
    """切割区域"""
    region_id: str
    region_name: str
    description: str
    coordinates: Optional[Dict[str, int]] = None  # {x, y, width, height}
    output_path: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CuttingRegion':
        return cls(
            region_id=data['region_id'],
            region_name=data['region_name'],
            description=data['description'],
            coordinates=data.get('coordinates'),
            output_path=data.get('output_path')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'region_id': self.region_id,
            'region_name': self.region_name,
            'description': self.description
        }
        if self.coordinates:
            result['coordinates'] = self.coordinates
        if self.output_path:
            result['output_path'] = self.output_path
        return result
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证区域数据有效性"""
        errors = []
        
        if not self.region_id:
            errors.append("区域ID不能为空")
        
        if not self.region_name:
            errors.append("区域名称不能为空")
        
        if self.coordinates:
            required_keys = ['x', 'y', 'width', 'height']
            for key in required_keys:
                if key not in self.coordinates:
                    errors.append(f"坐标缺少{key}字段")
                elif self.coordinates[key] < 0:
                    errors.append(f"坐标{key}不能为负数")
            
            if 'width' in self.coordinates and self.coordinates['width'] <= 0:
                errors.append("宽度必须大于0")
            if 'height' in self.coordinates and self.coordinates['height'] <= 0:
                errors.append("高度必须大于0")
        
        return len(errors) == 0, errors


@dataclass
class CuttingPlan(BaseModel):
    """切图规划"""
    source_image: SourceImage
    total_slices: int
    regions: List[CuttingRegion]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CuttingPlan':
        return cls(
            source_image=SourceImage.from_dict(data['source_image']),
            total_slices=data['total_slices'],
            regions=[CuttingRegion.from_dict(region_data) for region_data in data['regions']]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_image': self.source_image.to_dict(),
            'total_slices': self.total_slices,
            'regions': [region.to_dict() for region in self.regions]
        }
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证切图规划有效性"""
        errors = []
        
        if self.total_slices != len(self.regions):
            errors.append(f"切片总数 {self.total_slices} 与实际区域数量 {len(self.regions)} 不匹配")
        
        if self.total_slices <= 0:
            errors.append("切片总数必须大于0")
        
        # 验证源图片
        if self.source_image.width <= 0 or self.source_image.height <= 0:
            errors.append("源图片尺寸必须大于0")
        
        # 验证每个区域
        region_ids = set()
        for i, region in enumerate(self.regions):
            is_valid, region_errors = region.validate()
            if not is_valid:
                errors.extend([f"区域{i+1}: {error}" for error in region_errors])
            
            # 检查ID重复
            if region.region_id in region_ids:
                errors.append(f"重复的区域ID: {region.region_id}")
            region_ids.add(region.region_id)
            
            # 检查坐标是否在源图片范围内
            if region.coordinates:
                x = region.coordinates.get('x', 0)
                y = region.coordinates.get('y', 0)
                width = region.coordinates.get('width', 0)
                height = region.coordinates.get('height', 0)
                
                if x + width > self.source_image.width:
                    errors.append(f"区域{region.region_name}超出图片宽度范围")
                if y + height > self.source_image.height:
                    errors.append(f"区域{region.region_name}超出图片高度范围")
        
        return len(errors) == 0, errors 