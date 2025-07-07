"""数据模型层 - 定义核心数据结构"""

from .video_plan import VideoPlan
from .meta_info import MetaInfo
from .cutting_plan import CuttingPlan, CuttingRegion, SourceImage
from .narration_script import NarrationScript, NarrationSegment
from .video_composition import VideoComposition, Timeline, TimelineSegment, VisualEffect, BackgroundTrack, AudioTrack
from .constants import *

__all__ = [
    'VideoPlan',
    'MetaInfo', 
    'CuttingPlan',
    'CuttingRegion',
    'SourceImage',
    'NarrationScript',
    'NarrationSegment',
    'VideoComposition',
    'Timeline',
    'TimelineSegment',
    'VisualEffect', 
    'BackgroundTrack',
    'AudioTrack'
] 