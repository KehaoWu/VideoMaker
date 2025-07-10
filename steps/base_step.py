"""处理步骤基类 - 定义所有处理步骤的统一接口"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class StepResult:
    """步骤执行结果"""
    step_name: str
    status: str = "pending"  # pending, completed, failed
    error_message: Optional[str] = None
    output_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'step_name': self.step_name,
            'status': self.status,
            'error_message': self.error_message,
            'output_files': self.output_files,
            'metadata': self.metadata,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration
        }
    
    @property
    def is_successful(self) -> bool:
        """是否执行成功"""
        return self.status == "completed"


class BaseStep(ABC):
    """所有处理步骤的基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化步骤
        
        Args:
            config: 步骤配置字典
        """
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, video_plan: Any, output_dir: Optional[str] = None) -> Any:
        """执行处理步骤
        
        Args:
            video_plan: 视频规划实例
            output_dir: 可选的输出目录
            
        Returns:
            更新后的视频规划实例
        """
        pass
    
    @abstractmethod
    def validate_inputs(self, video_plan: Any) -> bool:
        """验证输入参数
        
        Args:
            video_plan: 视频规划实例
            
        Returns:
            bool: 验证是否通过
        """
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """获取依赖的步骤列表
        
        Returns:
            List[str]: 依赖步骤的名称列表
        """
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def _create_result(self, status: str, start_time: datetime, 
                      end_time: datetime = None, output_files: List[str] = None,
                      error_message: str = None, metadata: Dict[str, Any] = None) -> StepResult:
        """创建步骤结果对象"""
        return StepResult(
            step_name=self.name,
            status=status,
            start_time=start_time.isoformat() if start_time else datetime.now().isoformat(),
            end_time=end_time.isoformat() if end_time else None,
            output_files=output_files or [],
            error_message=error_message,
            metadata=metadata or {}
        )
    
    def _handle_error(self, start_time: datetime, error: Exception) -> StepResult:
        """处理执行错误"""
        return self._create_result(
            status="failed",
            start_time=start_time,
            error_message=str(error),
            metadata={'exception_type': type(error).__name__}
        ) 