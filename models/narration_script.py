"""旁白脚本数据模型"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .base_model import BaseModel


@dataclass
class NarrationSegment:
    """旁白片段"""
    segment_id: str
    text: str
    estimated_duration: float
    speaking_rate: float = 1.0  # 语速，范围0.5-2.0
    voice: str = "alloy"  # OpenAI TTS声音: alloy, echo, fable, onyx, nova, shimmer
    actual_duration: Optional[float] = None  # 实际生成的音频时长
    audio_file_path: Optional[str] = None  # 生成的音频文件路径
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NarrationSegment':
        return cls(
            segment_id=data['segment_id'],
            text=data['text'],
            estimated_duration=data['estimated_duration'],
            speaking_rate=float(data.get('speaking_rate', 1.0)),
            voice=data.get('voice', 'alloy'),
            actual_duration=data.get('actual_duration'),
            audio_file_path=data.get('audio_file_path')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'segment_id': self.segment_id,
            'text': self.text,
            'estimated_duration': self.estimated_duration,
            'speaking_rate': self.speaking_rate,
            'voice': self.voice
        }
        if self.actual_duration is not None:
            result['actual_duration'] = self.actual_duration
        if self.audio_file_path:
            result['audio_file_path'] = self.audio_file_path
        return result
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证旁白片段有效性"""
        errors = []
        
        if not self.segment_id:
            errors.append("片段ID不能为空")
        
        if not self.text.strip():
            errors.append("旁白文本不能为空")
        
        if self.estimated_duration <= 0:
            errors.append("预估时长必须大于0")
        
        # 验证语速范围
        if not (0.5 <= self.speaking_rate <= 2.0):
            errors.append("语速必须在0.5-2.0范围内")
        
        # 验证voice选项
        valid_voices = {'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'}
        if self.voice not in valid_voices:
            errors.append(f"voice必须是以下之一: {', '.join(valid_voices)}")
        
        return len(errors) == 0, errors


@dataclass
class NarrationScript(BaseModel):
    """旁白脚本"""
    total_segments: int
    segments: List[NarrationSegment]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NarrationScript':
        return cls(
            total_segments=data['total_segments'],
            segments=[NarrationSegment.from_dict(seg_data) for seg_data in data['segments']]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_segments': self.total_segments,
            'segments': [seg.to_dict() for seg in self.segments]
        }
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证旁白脚本有效性"""
        errors = []
        
        if self.total_segments != len(self.segments):
            errors.append(f"片段总数 {self.total_segments} 与实际片段数量 {len(self.segments)} 不匹配")
        
        if self.total_segments <= 0:
            errors.append("片段总数必须大于0")
        
        # 验证每个片段
        segment_ids = set()
        for i, segment in enumerate(self.segments):
            is_valid, seg_errors = segment.validate()
            if not is_valid:
                errors.extend([f"片段{i+1}: {error}" for error in seg_errors])
            
            # 检查ID重复
            if segment.segment_id in segment_ids:
                errors.append(f"重复的片段ID: {segment.segment_id}")
            segment_ids.add(segment.segment_id)
        
        return len(errors) == 0, errors
    
    def get_total_estimated_duration(self) -> float:
        """获取总的预估时长"""
        return sum(seg.estimated_duration for seg in self.segments)
    
    def get_total_actual_duration(self) -> Optional[float]:
        """获取总的实际时长（如果所有片段都已生成音频）"""
        if all(seg.actual_duration is not None for seg in self.segments):
            return sum(seg.actual_duration for seg in self.segments)
        return None 