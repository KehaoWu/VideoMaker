"""
自定义异常类
"""

class VideoMakerError(Exception):
    """基础异常类"""
    pass


class ConfigError(VideoMakerError):
    """配置相关异常"""
    pass


class ValidationError(VideoMakerError):
    """验证相关异常"""
    pass


class FileError(VideoMakerError):
    """文件操作相关异常"""
    pass


class FileProcessingError(FileError):
    """文件处理相关异常"""
    def __init__(self, message: str, file_path: str = None):
        super().__init__(message)
        self.file_path = file_path


class APIError(VideoMakerError):
    """API相关异常基类"""
    pass


class OpenAIAPIError(APIError):
    """OpenAI API相关异常"""
    pass


class VideoAPIError(APIError):
    """视频生成API相关异常"""
    pass


class TTSAPIError(APIError):
    """TTS API相关异常"""
    pass


class WorkflowError(VideoMakerError):
    """工作流相关异常"""
    pass 