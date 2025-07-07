"""
OpenAI API客户端
提供与OpenAI API的基础通信功能
"""

import base64
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from openai import OpenAI
from PIL import Image

from utils.logger import get_logger
from utils.config_manager import get_config
from utils.exceptions import VideoMakerError


class OpenAIAPIError(VideoMakerError):
    """OpenAI API相关异常"""
    pass


class OpenAIAPI:
    """OpenAI API客户端类"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        
        # API配置
        self.api_key = self.config.get('openai', {}).get('api_key')
        self.base_url = self.config.get('openai', {}).get('base_url', 'https://api.openai.com/v1')
        self.model = self.config.get('openai', {}).get('model', 'gpt-4-vision-preview')
        self.max_tokens = self.config.get('openai', {}).get('max_tokens', 4000)
        self.timeout = self.config.get('openai', {}).get('timeout', 30)
        
        if not self.api_key:
            self.logger.error("OpenAI API密钥未配置")
            raise OpenAIAPIError("OpenAI API密钥未配置")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    def _encode_image(self, image_path: str) -> str:
        """将图片编码为base64格式"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.exception(f"图片编码失败: {e}")
            raise OpenAIAPIError(f"图片编码失败: {e}")
    
    def send_message(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        发送消息到OpenAI API
        
        Args:
            messages: 消息列表，每个消息是一个字典，包含role和content
            
        Returns:
            API响应数据
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens
            )
            
            return {
                'content': response.choices[0].message.content,
                'role': response.choices[0].message.role,
                'model': response.model,
                'usage': response.usage.dict() if response.usage else None
            }
            
        except Exception as e:
            self.logger.exception(f"API请求异常: {e}")
            raise OpenAIAPIError(f"API请求异常: {e}")
    
    def send_message_with_image(self, prompt: str, image_path: str) -> Dict[str, Any]:
        """
        发送带图片的消息到OpenAI API
        
        Args:
            prompt: 提示词文本
            image_path: 图片文件路径
            
        Returns:
            API响应数据
        """
        # 验证图片文件
        if not Path(image_path).exists():
            self.logger.error(f"图片文件不存在: {image_path}")
            raise OpenAIAPIError(f"图片文件不存在: {image_path}")
        
        # 编码图片
        image_base64 = self._encode_image(image_path)
        
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        # 发送请求
        return self.send_message(messages)
    
    def validate_image(self, image_path: str) -> Dict[str, Any]:
        """
        验证图片是否有效且适合处理
        
        Returns:
            包含图片信息和适用性评估的字典
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode
                
            # 基本验证
            if width < 400 or height < 300:
                self.logger.warning(f"图片分辨率过低: {width}x{height}")
                return {
                    'valid': False,
                    'reason': '图片分辨率过低，建议至少400x300像素'
                }
            
            if width * height > 4000 * 4000:
                self.logger.warning(f"图片分辨率过高: {width}x{height}")
                return {
                    'valid': False, 
                    'reason': '图片分辨率过高，可能影响处理速度'
                }
            
            return {
                'valid': True,
                'width': width,
                'height': height,
                'format': format_name,
                'mode': mode
            }
            
        except Exception as e:
            self.logger.exception(f"图片文件无效: {e}")
            return {
                'valid': False,
                'reason': f'图片文件无效: {e}'
            } 