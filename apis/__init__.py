"""
API模块
包含各种外部API的客户端实现
"""

from .openai_api import OpenAIAPI
from .video_api import VideoAPI
from .tts_api import TTSAPI

__all__ = [
    'OpenAIAPI',
    'VideoAPI',
    'TTSAPI'
] 