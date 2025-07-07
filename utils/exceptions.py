"""自定义异常类模块"""

class VideoMakerError(Exception):
    """VideoMaker基础异常类"""
    pass


class ConfigurationError(VideoMakerError):
    """配置相关错误"""
    pass


class APIError(VideoMakerError):
    """API调用相关错误"""
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class OpenAIAPIError(APIError):
    """OpenAI API相关异常"""
    pass


class VideoAPIError(APIError):
    """视频生成API错误"""
    pass


class TTSAPIError(APIError):
    """TTS API错误"""
    pass


class FileProcessingError(VideoMakerError):
    """文件处理错误"""
    def __init__(self, message: str, file_path: str = None):
        super().__init__(message)
        self.file_path = file_path


class ImageProcessingError(FileProcessingError):
    """图片处理错误"""
    pass


class VideoProcessingError(FileProcessingError):
    """视频处理错误"""
    pass


class AudioProcessingError(FileProcessingError):
    """音频处理错误"""
    pass


class ValidationError(VideoMakerError):
    """数据验证错误"""
    pass


class TimeoutError(VideoMakerError):
    """超时错误"""
    def __init__(self, message: str, timeout_seconds: int = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class FFmpegError(VideoProcessingError):
    """FFmpeg相关错误"""
    def __init__(self, message: str, command: str = None, stderr: str = None):
        super().__init__(message)
        self.command = command
        self.stderr = stderr 