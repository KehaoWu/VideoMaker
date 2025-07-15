"""
OpenAI API客户端
提供与OpenAI API的基础通信功能
"""

import base64
import json
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path

from openai import OpenAI
from openai.types.chat import ChatCompletion
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
    
    def send_message(self, messages: List[Dict], stream: bool = True) -> Dict[str, Any]:
        """
        发送消息到OpenAI API
        
        Args:
            messages: 消息列表，每个消息是一个字典，包含role和content
            stream: 是否使用流式模式
            
        Returns:
            API响应数据
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                stream=stream
            )
            
            if stream:
                # 处理流式响应
                collected_content = []
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        collected_content.append(chunk.choices[0].delta.content)
                        # 可以在这里添加回调函数来实时处理内容
                
                return {
                    'content': ''.join(collected_content),
                    'role': 'assistant',
                    'model': self.model,
                    'usage': None  # 流式模式下无法获取usage信息
                }
            else:
                # 处理普通响应
                return {
                    'content': response.choices[0].message.content,
                    'role': response.choices[0].message.role,
                    'model': response.model,
                    'usage': response.usage.dict() if response.usage else None
                }
            
        except Exception as e:
            self.logger.exception(f"API请求异常: {e}")
            raise OpenAIAPIError(f"API请求异常: {e}")
    
    def send_message_with_image(self, prompt: str, image_path: str, stream: bool = True) -> Dict[str, Any]:
        """
        发送带图片的消息到OpenAI API
        
        Args:
            prompt: 提示词文本
            image_path: 图片文件路径
            stream: 是否使用流式模式
            
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
        return self.send_message(messages, stream=stream)
    
