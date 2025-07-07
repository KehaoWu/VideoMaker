"""
TTS API客户端
用于文本转语音音频生成
"""

import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

import requests

from utils.logger import get_logger
from utils.config_manager import get_config
from utils.exceptions import VideoMakerError
from utils.file_utils import ensure_directory, safe_filename


class TTSAPIError(VideoMakerError):
    """TTS API相关异常"""
    pass


class TTSAPI:
    """TTS API客户端类"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        
        # API配置
        self.api_key = self.config.get('tts', {}).get('api_key')
        self.base_url = self.config.get('tts', {}).get('base_url', 'https://api.openai.com/v1')
        self.model = self.config.get('tts', {}).get('model', 'tts-1')
        self.voice = self.config.get('tts', {}).get('voice', 'alloy')
        self.speed = self.config.get('tts', {}).get('speed', 1.0)
        self.timeout = self.config.get('tts', {}).get('timeout', 60)
        self.max_retries = self.config.get('tts', {}).get('max_retries', 3)
        
        if not self.api_key:
            raise TTSAPIError("TTS API密钥未配置")
    
    def generate_speech(self, text: str, output_path: str, 
                       voice: Optional[str] = None, 
                       speed: Optional[float] = None) -> Dict[str, Any]:
        """
        生成语音音频文件
        
        Args:
            text: 要转换的文本
            output_path: 输出音频文件路径
            voice: 语音类型（可选）
            speed: 语音速度（可选）
            
        Returns:
            包含生成结果的字典
        """
        self.logger.info(f"开始生成语音: {text[:50]}...")
        
        # 参数验证
        if not text.strip():
            raise TTSAPIError("文本内容不能为空")
        
        if len(text) > 4096:
            raise TTSAPIError("文本长度超过限制（4096字符）")
        
        # 使用传入参数或默认配置
        voice = voice or self.voice
        speed = speed or self.speed
        
        # 确保输出目录存在
        ensure_directory(os.path.dirname(output_path))
        
        # 构建请求
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'input': text,
            'voice': voice,
            'speed': speed,
            'response_format': 'mp3'
        }
        
        # 执行请求
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/audio/speech",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    # 保存音频文件
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    # 获取音频时长
                    duration = self._get_audio_duration(output_path)
                    
                    result = {
                        'success': True,
                        'output_path': output_path,
                        'duration': duration,
                        'file_size': os.path.getsize(output_path),
                        'voice': voice,
                        'speed': speed,
                        'text_length': len(text)
                    }
                    
                    self.logger.info(f"语音生成成功: {output_path}, 时长: {duration:.2f}秒")
                    return result
                    
                elif response.status_code == 429:
                    # 请求限制，等待后重试
                    wait_time = 2 ** attempt
                    self.logger.warning(f"API请求限制，等待{wait_time}秒后重试")
                    time.sleep(wait_time)
                    continue
                else:
                    raise TTSAPIError(f"API请求失败: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"请求超时，重试第{attempt + 1}次")
                if attempt == self.max_retries - 1:
                    raise TTSAPIError("API请求超时")
            except requests.exceptions.RequestException as e:
                raise TTSAPIError(f"API请求异常: {e}")
        
        raise TTSAPIError("API请求达到最大重试次数")
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频文件时长"""
        try:
            # 尝试使用librosa获取精确时长
            try:
                import librosa
                duration = librosa.get_duration(filename=audio_path)
                return duration
            except ImportError:
                pass
            
            # 备用方案：使用mutagen
            try:
                from mutagen.mp3 import MP3
                audio = MP3(audio_path)
                return audio.info.length
            except ImportError:
                pass
            
            # 简单估算：基于文件大小（不准确）
            file_size = os.path.getsize(audio_path)
            # MP3大约 128kbps，估算时长
            estimated_duration = file_size / (128 * 1000 / 8)
            self.logger.warning("无法精确计算音频时长，使用估算值")
            return estimated_duration
            
        except Exception as e:
            self.logger.error(f"获取音频时长失败: {e}")
            return 0.0
    
    def validate_text(self, text: str) -> Dict[str, Any]:
        """
        验证文本是否适合TTS转换
        
        Returns:
            包含验证结果的字典
        """
        if not text or not text.strip():
            return {
                'valid': False,
                'reason': '文本内容为空'
            }
        
        text_length = len(text)
        if text_length > 4096:
            return {
                'valid': False,
                'reason': f'文本长度超过限制（{text_length}/4096字符）'
            }
        
        # 估算语音时长（中文约每分钟200字）
        estimated_duration = text_length / 200 * 60
        
        return {
            'valid': True,
            'text_length': text_length,
            'estimated_duration': estimated_duration,
            'character_count': len(text),
            'word_count': len(text.split())
        }
    
    def get_available_voices(self) -> List[str]:
        """获取可用的语音类型列表"""
        # OpenAI TTS支持的语音类型
        return ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    
    def batch_generate_speech(self, text_segments: List[Dict[str, Any]], 
                            output_dir: str) -> List[Dict[str, Any]]:
        """
        批量生成语音文件
        
        Args:
            text_segments: 文本段落列表，每个元素包含text和相关参数
            output_dir: 输出目录
            
        Returns:
            生成结果列表
        """
        self.logger.info(f"开始批量生成{len(text_segments)}个语音文件")
        
        ensure_directory(output_dir)
        results = []
        
        for i, segment in enumerate(text_segments):
            try:
                text = segment.get('text', '')
                segment_id = segment.get('segment_id', f'segment_{i+1}')
                voice = segment.get('voice', self.voice)
                speed = segment.get('speed', self.speed)
                
                # 生成文件名
                filename = safe_filename(f"{segment_id}.mp3")
                output_path = os.path.join(output_dir, filename)
                
                # 生成语音
                result = self.generate_speech(text, output_path, voice, speed)
                result['segment_id'] = segment_id
                results.append(result)
                
            except Exception as e:
                error_result = {
                    'success': False,
                    'segment_id': segment.get('segment_id', f'segment_{i+1}'),
                    'error': str(e)
                }
                results.append(error_result)
                self.logger.error(f"生成语音失败: {e}")
        
        success_count = sum(1 for r in results if r.get('success'))
        self.logger.info(f"批量语音生成完成: {success_count}/{len(text_segments)}个成功")
        
        return results 