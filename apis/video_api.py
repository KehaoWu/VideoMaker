"""
Video API客户端
用于文生视频和图生视频功能
"""

import os
import time
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

import requests

from utils.logger import get_logger
from utils.config_manager import get_config
from utils.exceptions import VideoMakerError
from utils.file_utils import ensure_directory, safe_filename


class VideoAPIError(VideoMakerError):
    """Video API相关异常"""
    pass


class VideoAPI:
    """Video API客户端类"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        
        # API配置
        self.api_key = self.config.get('video', {}).get('api_key')
        self.base_url = self.config.get('video', {}).get('base_url', 'https://api.runway.com')
        self.model = self.config.get('video', {}).get('model', 'gen3')
        self.timeout = self.config.get('video', {}).get('timeout', 300)
        self.max_retries = self.config.get('video', {}).get('max_retries', 2)
        
        if not self.api_key:
            raise VideoAPIError("Video API密钥未配置")
    
    def text_to_video(self, prompt: str, output_path: str,
                     duration: float = 5.0,
                     style: str = "realistic",
                     resolution: str = "1280x720") -> Dict[str, Any]:
        """
        文本转视频生成
        
        Args:
            prompt: 文本提示词
            output_path: 输出视频文件路径
            duration: 视频时长（秒）
            style: 视频风格
            resolution: 视频分辨率
            
        Returns:
            包含生成结果的字典
        """
        self.logger.info(f"开始文生视频: {prompt[:100]}...")
        
        # 参数验证
        if not prompt.strip():
            raise VideoAPIError("提示词不能为空")
        
        if duration < 1.0 or duration > 30.0:
            raise VideoAPIError("视频时长必须在1-30秒之间")
        
        # 确保输出目录存在
        ensure_directory(os.path.dirname(output_path))
        
        # 构建请求
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'prompt': prompt,
            'duration': duration,
            'style': style,
            'resolution': resolution,
            'output_format': 'mp4'
        }
        
        # 提交生成任务
        task_id = self._submit_generation_task(headers, payload)
        
        # 等待任务完成
        result = self._wait_for_completion(task_id, headers)
        
        if result.get('status') == 'completed':
            # 下载生成的视频
            video_url = result.get('output_url')
            if video_url:
                self._download_video(video_url, output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'duration': duration,
                    'file_size': os.path.getsize(output_path),
                    'prompt': prompt,
                    'style': style,
                    'resolution': resolution,
                    'task_id': task_id
                }
            else:
                raise VideoAPIError("生成结果中没有视频URL")
        else:
            error_msg = result.get('error', '未知错误')
            raise VideoAPIError(f"视频生成失败: {error_msg}")
    
    def image_to_video(self, image_path: str, output_path: str,
                      motion_prompt: str = "",
                      duration: float = 5.0) -> Dict[str, Any]:
        """
        图片转视频生成
        
        Args:
            image_path: 输入图片路径
            output_path: 输出视频文件路径
            motion_prompt: 运动描述提示词
            duration: 视频时长（秒）
            
        Returns:
            包含生成结果的字典
        """
        self.logger.info(f"开始图生视频: {image_path}")
        
        # 验证图片文件
        if not Path(image_path).exists():
            raise VideoAPIError(f"图片文件不存在: {image_path}")
        
        # 确保输出目录存在
        ensure_directory(os.path.dirname(output_path))
        
        # 构建请求
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # 上传图片
        image_url = self._upload_image(image_path, headers)
        
        # 构建生成请求
        payload = {
            'model': self.model,
            'image_url': image_url,
            'motion_prompt': motion_prompt,
            'duration': duration,
            'output_format': 'mp4'
        }
        
        headers['Content-Type'] = 'application/json'
        
        # 提交生成任务
        task_id = self._submit_generation_task(headers, payload, endpoint='image-to-video')
        
        # 等待任务完成
        result = self._wait_for_completion(task_id, headers)
        
        if result.get('status') == 'completed':
            # 下载生成的视频
            video_url = result.get('output_url')
            if video_url:
                self._download_video(video_url, output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'duration': duration,
                    'file_size': os.path.getsize(output_path),
                    'image_path': image_path,
                    'motion_prompt': motion_prompt,
                    'task_id': task_id
                }
            else:
                raise VideoAPIError("生成结果中没有视频URL")
        else:
            error_msg = result.get('error', '未知错误')
            raise VideoAPIError(f"视频生成失败: {error_msg}")
    
    def _submit_generation_task(self, headers: Dict, payload: Dict, 
                               endpoint: str = 'text-to-video') -> str:
        """提交视频生成任务"""
        try:
            response = requests.post(
                f"{self.base_url}/v1/{endpoint}",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                if task_id:
                    self.logger.info(f"任务提交成功: {task_id}")
                    return task_id
                else:
                    raise VideoAPIError("响应中没有任务ID")
            else:
                raise VideoAPIError(f"任务提交失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise VideoAPIError(f"任务提交异常: {e}")
    
    def _wait_for_completion(self, task_id: str, headers: Dict, 
                           max_wait_time: int = 600) -> Dict[str, Any]:
        """等待任务完成"""
        self.logger.info(f"等待任务完成: {task_id}")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(
                    f"{self.base_url}/v1/tasks/{task_id}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'completed':
                        self.logger.info("任务完成")
                        return result
                    elif status == 'failed':
                        error_msg = result.get('error', '未知错误')
                        raise VideoAPIError(f"任务失败: {error_msg}")
                    elif status in ['pending', 'processing']:
                        progress = result.get('progress', 0)
                        self.logger.info(f"任务进行中: {progress}%")
                        time.sleep(10)  # 等待10秒后再次检查
                    else:
                        self.logger.warning(f"未知状态: {status}")
                        time.sleep(5)
                else:
                    raise VideoAPIError(f"查询任务状态失败: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"查询任务状态异常: {e}")
                time.sleep(5)
        
        raise VideoAPIError("任务等待超时")
    
    def _upload_image(self, image_path: str, headers: Dict) -> str:
        """上传图片文件"""
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(
                    f"{self.base_url}/v1/upload/image",
                    headers={'Authorization': headers['Authorization']},
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                image_url = result.get('url')
                if image_url:
                    self.logger.info(f"图片上传成功: {image_url}")
                    return image_url
                else:
                    raise VideoAPIError("上传响应中没有图片URL")
            else:
                raise VideoAPIError(f"图片上传失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise VideoAPIError(f"图片上传异常: {e}")
    
    def _download_video(self, video_url: str, output_path: str):
        """下载生成的视频文件"""
        try:
            response = requests.get(video_url, timeout=120, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"视频下载完成: {output_path}")
            
        except requests.exceptions.RequestException as e:
            raise VideoAPIError(f"视频下载异常: {e}")
    
    def validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        验证提示词是否适合视频生成
        
        Returns:
            包含验证结果的字典
        """
        if not prompt or not prompt.strip():
            return {
                'valid': False,
                'reason': '提示词不能为空'
            }
        
        prompt_length = len(prompt)
        if prompt_length > 1000:
            return {
                'valid': False,
                'reason': f'提示词长度超过限制（{prompt_length}/1000字符）'
            }
        
        # 检查敏感内容（简单关键词过滤）
        sensitive_words = ['暴力', '血腥', '成人', '裸体']
        for word in sensitive_words:
            if word in prompt:
                return {
                    'valid': False,
                    'reason': f'提示词包含敏感内容: {word}'
                }
        
        return {
            'valid': True,
            'prompt_length': prompt_length,
            'estimated_complexity': 'medium'  # 可以根据提示词复杂度评估
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/v1/tasks/{task_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise VideoAPIError(f"查询任务状态失败: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise VideoAPIError(f"查询任务状态异常: {e}") 