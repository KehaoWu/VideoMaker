"""数据验证工具模块"""
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from PIL import Image
from .exceptions import ValidationError, FileProcessingError


@dataclass
class ValidationResult:
    """验证结果类"""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0


class FileValidator:
    """文件验证器"""
    
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.aac', '.m4a'}
    
    @staticmethod
    def validate_image_file(file_path: str, max_size_mb: int = 10) -> bool:
        """验证图片文件"""
        if not os.path.exists(file_path):
            raise FileProcessingError(f"图片文件不存在: {file_path}", file_path)
        
        # 检查文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in FileValidator.SUPPORTED_IMAGE_FORMATS:
            raise ValidationError(f"不支持的图片格式: {ext}")
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValidationError(f"图片文件过大: {file_size / 1024 / 1024:.2f}MB > {max_size_mb}MB")
        
        # 尝试打开图片验证格式
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            raise ValidationError(f"图片文件损坏或格式无效: {e}")
        
        return True
    
    @staticmethod
    def validate_directory(dir_path: str, create_if_not_exists: bool = True) -> bool:
        """验证目录"""
        if not os.path.exists(dir_path):
            if create_if_not_exists:
                os.makedirs(dir_path, exist_ok=True)
                return True
            else:
                raise FileProcessingError(f"目录不存在: {dir_path}")
        
        if not os.path.isdir(dir_path):
            raise ValidationError(f"路径不是有效目录: {dir_path}")
        
        if not os.access(dir_path, os.W_OK):
            raise ValidationError(f"目录没有写入权限: {dir_path}")
        
        return True


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_api_key(api_key: str, service_name: str = "API") -> bool:
        """验证API密钥"""
        if not api_key or api_key.strip() == "":
            raise ValidationError(f"{service_name} 密钥不能为空")
        
        if api_key in ["your-api-key-here", "your-claude-api-key-here"]:
            raise ValidationError(f"{service_name} 密钥未配置")
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式"""
        url_pattern = re.compile(
            r'^https?://'  # http:// 或 https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
            r'(?::\d+)?'  # 可选端口
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise ValidationError(f"无效的URL格式: {url}")
        
        return True
    
    @staticmethod
    def validate_video_plan(plan_data: Dict[str, Any]) -> bool:
        """验证视频规划数据"""
        required_fields = ['content_overview', 'video_structure']
        
        for field in required_fields:
            if field not in plan_data:
                raise ValidationError(f"视频规划缺少必需字段: {field}")
        
        # 验证视频结构
        video_structure = plan_data.get('video_structure', {})
        if 'total_duration' not in video_structure:
            raise ValidationError("视频结构缺少总时长信息")
        
        return True
    
    @staticmethod
    def validate_tts_plan(tts_plan: Dict[str, Any]) -> bool:
        """验证TTS规划数据"""
        required_fields = ['narration_timeline', 'tts_config', 'total_duration']
        
        for field in required_fields:
            if field not in tts_plan:
                raise ValidationError(f"TTS规划缺少必需字段: {field}")
        
        # 验证时间轴
        timeline = tts_plan.get('narration_timeline', [])
        if not timeline:
            raise ValidationError("TTS规划时间轴为空")
        
        for item in timeline:
            if 'start_time' not in item or 'duration' not in item:
                raise ValidationError("时间轴项目缺少时间信息")
        
        return True


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """验证完整配置"""
        # 验证基础配置
        if 'claude' not in config:
            raise ValidationError("配置缺少Claude API设置")
        
        claude_config = config['claude']
        DataValidator.validate_api_key(claude_config.get('api_key', ''), "Claude API")
        DataValidator.validate_url(claude_config.get('base_url', ''))
        
        # 验证视频API配置
        if 'video' not in config:
            raise ValidationError("配置缺少视频API设置")
        
        video_config = config['video']
        DataValidator.validate_api_key(video_config.get('api_key', ''), "视频API")
        DataValidator.validate_url(video_config.get('base_url', ''))
        
        return True 