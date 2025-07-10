"""
语音合成API封装
支持多个TTS服务商:
- Azure TTS
- 火山引擎TTS
"""

import os
import json
import uuid
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from utils.logger import get_logger
from utils.config_manager import get_config
from utils.exceptions import TTSAPIError

class TTSAPI:
    """语音合成API封装"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # 初始化配置
        self.api_base = self.config.get('tts.api_base', 'http://jd-prpt-engn-t.jianda-test.dq.yingmi-inc.com')
        self.client_id = self.config.get('tts.client_id', '<client>')
        self.voice_type = self.config.get('tts.voice_type', 'zh_male_M392_conversation_wvae_bigtts')
        self.encoding = self.config.get('tts.encoding', 'mp3')
        self.speed_ratio = float(self.config.get('tts.speed_ratio', 1.0))
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """验证配置"""
        if not self.api_base:
            raise TTSAPIError("缺少TTS API基础URL配置")
        if not self.client_id:
            raise TTSAPIError("缺少TTS客户端ID配置")
    
    def generate_audio(self, text: str, output_path: str, voice_type: Optional[str] = None) -> Dict[str, Any]:
        """
        生成语音文件
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
            voice_type: 可选的语音类型，如果不指定则使用默认值
            
        Returns:
            Dict: 包含生成结果的字典
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 准备请求数据
            request_data = {
                "user": {
                    "uid": f"videomaker_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                },
                "audio": {
                    "voice_type": voice_type or self.voice_type,
                    "encoding": self.encoding,
                    "speed_ratio": self.speed_ratio
                },
                "request": {
                    "reqid": str(uuid.uuid4()),
                    "text": text,
                    "operation": "query"
                }
            }
            
            # 设置请求头
            headers = {
                'Authorization': f'Bear {self.client_id}|VOLCENGINE',
                'Content-Type': 'application/json'
            }
            
            # 发送请求
            response = requests.post(
                f"{self.api_base}/prompt_engine/prompt/audio/generation",
                headers=headers,
                json=request_data
            )
            
            # 检查响应状态
            if response.status_code != 200:
                raise TTSAPIError(f"TTS API请求失败: {response.status_code} - {response.text}")
            
            # 解析响应
            result = response.json()
            
            # 检查响应内容
            if not result.get('success'):
                raise TTSAPIError(f"TTS生成失败: {result.get('message', '未知错误')}")
            
            # 获取音频数据
            audio_data = result.get('data', {}).get('audio_content')
            if not audio_data:
                raise TTSAPIError("响应中没有音频数据")
            
            # 保存音频文件
            with open(output_path, 'wb') as f:
                f.write(audio_data.encode('utf-8'))
            
            self.logger.info(f"✓ 语音生成成功: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'duration': result.get('data', {}).get('duration', 0),
                'text_length': len(text),
                'voice_type': voice_type or self.voice_type
            }
            
        except Exception as e:
            error_msg = f"语音生成失败: {str(e)}"
            self.logger.error(error_msg)
            raise TTSAPIError(error_msg)
    
    def validate_text(self, text: str) -> bool:
        """
        验证文本是否适合语音合成
        
        Args:
            text: 要验证的文本
            
        Returns:
            bool: 文本是否有效
        """
        if not text or not isinstance(text, str):
            return False
            
        # 检查文本长度
        if len(text) > 5000:  # 假设最大支持5000字符
            return False
            
        # 检查是否包含特殊字符
        invalid_chars = set('~!@#$%^&*()_+=[]{}|\\;:"<>?')
        if any(char in invalid_chars for char in text):
            return False
            
        return True
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        获取可用的语音列表
        
        Returns:
            Dict: 包含可用语音的字典
        """
        return {
            'zh_male_M392_conversation_wvae_bigtts': '中文男声-M392',
            # 可以添加更多语音类型
        }
    
    def get_voice_info(self, voice_type: str) -> Optional[Dict[str, Any]]:
        """
        获取指定语音类型的详细信息
        
        Args:
            voice_type: 语音类型ID
            
        Returns:
            Optional[Dict]: 语音类型信息，如果不存在则返回None
        """
        voices = self.get_available_voices()
        if voice_type in voices:
            return {
                'id': voice_type,
                'name': voices[voice_type],
                'language': 'zh-CN',
                'gender': 'Male' if 'male' in voice_type.lower() else 'Female'
            }
        return None 