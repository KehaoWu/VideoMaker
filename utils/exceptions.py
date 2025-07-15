"""
自定义异常类
用于VideoMaker项目的错误处理
"""


class VideoMakerError(Exception):
    """VideoMaker基础异常类"""
    pass


class ConfigError(VideoMakerError):
    """配置相关异常"""
    pass


class APIError(VideoMakerError):
    """API相关异常"""
    pass


class TTSAPIError(APIError):
    """TTS API异常"""
    pass


class VideoAPIError(APIError):
    """Video API异常"""
    pass


class FileError(VideoMakerError):
    """文件操作异常"""
    pass


class ValidationError(VideoMakerError):
    """验证异常"""
    pass 