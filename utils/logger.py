import logging
import os
from typing import Optional
from datetime import datetime


class VideoMakerLogger:
    """统一的日志管理器"""
    
    def __init__(self, name: str = "VideoMaker", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_logger(log_file)
    
    def _setup_logger(self, log_file: Optional[str]):
        """设置日志配置"""
        self.logger.setLevel(logging.INFO)
        
        # 创建格式器 - 添加文件名、行号和函数名
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, exc_info=True, **kwargs):
        """错误日志，默认包含异常信息"""
        self.logger.error(message, *args, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """异常日志，自动包含堆栈信息"""
        self.logger.exception(message, *args, **kwargs)
    
    def success(self, message: str, *args, **kwargs):
        """成功日志（使用INFO级别，但添加✓标记）"""
        self.logger.info(f"✓ {message}", *args, **kwargs)
    
    def step(self, step_name: str, message: str = "", *args, **kwargs):
        """步骤日志"""
        separator = "=" * 60
        self.logger.info(f"\n{separator}", *args, **kwargs)
        self.logger.info(f"🎯 {step_name}", *args, **kwargs)
        if message:
            self.logger.info(f"   {message}", *args, **kwargs)
        self.logger.info(f"{separator}", *args, **kwargs)
    
    def progress(self, current: int, total: int, item_name: str = "项目", *args, **kwargs):
        """进度日志"""
        percentage = (current / total * 100) if total > 0 else 0
        self.logger.info(f"📊 进度: {current}/{total} ({percentage:.1f}%) - {item_name}", *args, **kwargs)


# 全局日志实例
logger = VideoMakerLogger(log_file="logs/video_maker.log")


def get_logger(name: str = None) -> VideoMakerLogger:
    """获取日志器实例"""
    if name:
        return VideoMakerLogger(name=name, log_file="logs/video_maker.log")
    return logger


# 便利函数
def log_info(message: str, *args, **kwargs):
    logger.info(message, *args, **kwargs)

def log_debug(message: str, *args, **kwargs):
    logger.debug(message, *args, **kwargs)

def log_warning(message: str, *args, **kwargs):
    logger.warning(message, *args, **kwargs)

def log_error(message: str, *args, exc_info=True, **kwargs):
    logger.error(message, *args, exc_info=exc_info, **kwargs)

def log_exception(message: str, *args, **kwargs):
    logger.exception(message, *args, **kwargs)

def log_success(message: str, *args, **kwargs):
    logger.success(message, *args, **kwargs)

def log_step(step_name: str, message: str = "", *args, **kwargs):
    logger.step(step_name, message, *args, **kwargs)

def log_progress(current: int, total: int, item_name: str = "项目", *args, **kwargs):
    logger.progress(current, total, item_name, *args, **kwargs) 