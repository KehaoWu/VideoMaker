"""视频合成数据模型 - 完整实现"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from .base_model import BaseModel


@dataclass
class TimelineSegment:
    """时间轴片段"""
    segment_id: str
    start_time: float  # 开始时间（秒）
    end_time: float    # 结束时间（秒）
    duration: float    # 持续时间（秒）
    layer: int         # 图层
    content_type: str  # 内容类型：'image', 'audio', 'video', 'text'
    content_path: str  # 内容文件路径
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimelineSegment':
        return cls(
            segment_id=data['segment_id'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration=data['duration'],
            layer=data['layer'],
            content_type=data['content_type'],
            content_path=data['content_path'],
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'segment_id': self.segment_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'layer': self.layer,
            'content_type': self.content_type,
            'content_path': self.content_path,
            'metadata': self.metadata
        }


@dataclass
class Timeline(BaseModel):
    """时间轴"""
    total_duration: float
    segments: List[TimelineSegment]
    layer_count: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Timeline':
        return cls(
            total_duration=data['total_duration'],
            segments=[TimelineSegment.from_dict(seg_data) for seg_data in data['segments']],
            layer_count=data['layer_count']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_duration': self.total_duration,
            'segments': [seg.to_dict() for seg in self.segments],
            'layer_count': self.layer_count
        }
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证时间轴有效性"""
        errors = []
        
        if self.total_duration <= 0:
            errors.append("时间轴总时长必须大于0")
        
        if self.layer_count <= 0:
            errors.append("图层数量必须大于0")
        
        # 验证每个片段
        for i, segment in enumerate(self.segments):
            if segment.start_time < 0:
                errors.append(f"片段{i+1}开始时间不能为负数")
            
            if segment.end_time <= segment.start_time:
                errors.append(f"片段{i+1}结束时间必须大于开始时间")
            
            if segment.duration != segment.end_time - segment.start_time:
                errors.append(f"片段{i+1}持续时间计算错误")
            
            if segment.layer < 0 or segment.layer >= self.layer_count:
                errors.append(f"片段{i+1}图层超出范围")
        
        return len(errors) == 0, errors


@dataclass
class VisualEffect:
    """视觉特效"""
    effect_id: str
    effect_type: str  # 'fade_in', 'fade_out', 'zoom', 'pan', 'transition'
    target_layer: int
    start_time: float
    duration: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisualEffect':
        return cls(
            effect_id=data['effect_id'],
            effect_type=data['effect_type'],
            target_layer=data['target_layer'],
            start_time=data['start_time'],
            duration=data['duration'],
            parameters=data.get('parameters', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'effect_id': self.effect_id,
            'effect_type': self.effect_type,
            'target_layer': self.target_layer,
            'start_time': self.start_time,
            'duration': self.duration,
            'parameters': self.parameters
        }


@dataclass
class AudioTrack:
    """音轨"""
    track_id: str
    track_type: str  # 'narration', 'background', 'effects'
    audio_file_path: str
    start_time: float
    duration: float
    volume: float = 1.0  # 音量 0.0-1.0
    fade_in: float = 0.0  # 淡入时间
    fade_out: float = 0.0  # 淡出时间
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioTrack':
        return cls(
            track_id=data['track_id'],
            track_type=data['track_type'],
            audio_file_path=data['audio_file_path'],
            start_time=data['start_time'],
            duration=data['duration'],
            volume=data.get('volume', 1.0),
            fade_in=data.get('fade_in', 0.0),
            fade_out=data.get('fade_out', 0.0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'track_id': self.track_id,
            'track_type': self.track_type,
            'audio_file_path': self.audio_file_path,
            'start_time': self.start_time,
            'duration': self.duration,
            'volume': self.volume,
            'fade_in': self.fade_in,
            'fade_out': self.fade_out
        }


@dataclass
class BackgroundTrack(BaseModel):
    """背景音轨"""
    audio_tracks: List[AudioTrack]
    master_volume: float = 1.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackgroundTrack':
        return cls(
            audio_tracks=[AudioTrack.from_dict(track_data) for track_data in data['audio_tracks']],
            master_volume=data.get('master_volume', 1.0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'audio_tracks': [track.to_dict() for track in self.audio_tracks],
            'master_volume': self.master_volume
        }
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证背景音轨有效性"""
        errors = []
        
        if self.master_volume < 0 or self.master_volume > 1:
            errors.append("主音量必须在0-1之间")
        
        # 验证每个音轨
        for i, track in enumerate(self.audio_tracks):
            if track.volume < 0 or track.volume > 1:
                errors.append(f"音轨{i+1}音量必须在0-1之间")
            
            if track.start_time < 0:
                errors.append(f"音轨{i+1}开始时间不能为负数")
            
            if track.duration <= 0:
                errors.append(f"音轨{i+1}持续时间必须大于0")
        
        return len(errors) == 0, errors


@dataclass
class VideoComposition(BaseModel):
    """视频合成配置 - 完整版本"""
    timeline: Timeline
    visual_effects: List[VisualEffect]
    background_track: BackgroundTrack
    output_settings: Dict[str, Any] = field(default_factory=dict)
    composition_strategy: str = "layered_timeline"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoComposition':
        return cls(
            timeline=Timeline.from_dict(data['timeline']),
            visual_effects=[VisualEffect.from_dict(effect_data) 
                           for effect_data in data.get('visual_effects', [])],
            background_track=BackgroundTrack.from_dict(data['background_track']),
            output_settings=data.get('output_settings', {}),
            composition_strategy=data.get('composition_strategy', 'layered_timeline')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timeline': self.timeline.to_dict(),
            'visual_effects': [effect.to_dict() for effect in self.visual_effects],
            'background_track': self.background_track.to_dict(),
            'output_settings': self.output_settings,
            'composition_strategy': self.composition_strategy
        }
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证视频合成配置有效性"""
        errors = []
        
        # 验证时间轴
        timeline_valid, timeline_errors = self.timeline.validate()
        if not timeline_valid:
            errors.extend([f"时间轴: {error}" for error in timeline_errors])
        
        # 验证背景音轨
        background_valid, background_errors = self.background_track.validate()
        if not background_valid:
            errors.extend([f"背景音轨: {error}" for error in background_errors])
        
        # 验证视觉特效
        for i, effect in enumerate(self.visual_effects):
            if effect.start_time < 0:
                errors.append(f"特效{i+1}开始时间不能为负数")
            
            if effect.duration <= 0:
                errors.append(f"特效{i+1}持续时间必须大于0")
            
            if effect.target_layer < 0 or effect.target_layer >= self.timeline.layer_count:
                errors.append(f"特效{i+1}目标图层超出范围")
        
        return len(errors) == 0, errors
    
    def get_total_duration(self) -> float:
        """获取总时长"""
        return self.timeline.total_duration
    
    def add_visual_effect(self, effect: VisualEffect):
        """添加视觉特效"""
        self.visual_effects.append(effect)
    
    def remove_visual_effect(self, effect_id: str) -> bool:
        """移除视觉特效"""
        for i, effect in enumerate(self.visual_effects):
            if effect.effect_id == effect_id:
                del self.visual_effects[i]
                return True
        return False 