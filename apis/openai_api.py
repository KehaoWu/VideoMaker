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
    
    def analyze_image_regions(self, image_path: str, region_descriptions: List[str], stream: bool = True) -> List[Dict[str, Any]]:
        """
        分析图片中的指定区域
        
        Args:
            image_path: 图片文件路径
            region_descriptions: 区域描述列表
            stream: 是否使用流式模式
            
        Returns:
            区域分析结果列表，每个结果包含坐标信息
        """
        prompt = "请分析图片中的以下区域，并提供每个区域的坐标信息（x, y, width, height）：\n"
        for desc in region_descriptions:
            prompt += f"- {desc}\n"
        prompt += "\n请以JSON格式返回结果，格式如下：\n"
        prompt += """[
            {
                "description": "区域描述",
                "coordinates": {
                    "x": 0,
                    "y": 0,
                    "width": 100,
                    "height": 100
                }
            }
        ]"""
        
        response = self.send_message_with_image(prompt, image_path, stream=stream)
        
        try:
            # 尝试解析JSON响应
            content = response['content'].strip()
            # 找到第一个 [ 和最后一个 ] 之间的内容
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                self.logger.error("无法从响应中提取JSON数据")
                return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"处理响应数据失败: {e}")
            return []
    
    def generate_narration_from_image(self, image_path: str, title: str, duration: float, stream: bool = True) -> str:
        """
        根据图片生成旁白文本
        
        Args:
            image_path: 图片文件路径
            title: 视频标题
            duration: 视频时长（秒）
            stream: 是否使用流式模式
            
        Returns:
            生成的旁白文本
        """
        prompt = f"""请根据这张图片生成一段旁白文本，用于{duration}秒的视频。
视频标题是：{title}
要求：
1. 文本长度要适合{duration}秒的语音
2. 描述要生动有趣
3. 语言要自然流畅
4. 重点描述图片中的主要内容和特点"""
        
        response = self.send_message_with_image(prompt, image_path, stream=stream)
        return response['content']
    
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