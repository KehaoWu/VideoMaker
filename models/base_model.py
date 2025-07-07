"""基础模型类 - 定义所有数据模型的通用接口"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from dataclasses import dataclass


class BaseModel(ABC):
    """所有数据模型的基类"""
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """从字典创建对象"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @abstractmethod
    def validate(self) -> tuple[bool, List[str]]:
        """验证数据有效性，返回(是否有效, 错误信息列表)"""
        pass


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    
    def __bool__(self) -> bool:
        return self.is_valid 