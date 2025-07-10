"""日志工具模块"""

import logging
import os
import sys
import traceback
from typing import Optional
from datetime import datetime


def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """配置并返回日志器"""
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
        
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(filename)s:%(lineno)d\n%(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 创建默认日志器
default_logger = setup_logger('VideoMaker', 'logs/video_maker.log')


def get_logger(name: str = None) -> logging.Logger:
    """获取日志器实例"""
    if name:
        return setup_logger(name, 'logs/video_maker.log')
    return default_logger


def format_exception(e: Exception) -> str:
    """格式化异常信息，包含完整的堆栈跟踪"""
    # 获取当前异常的完整堆栈
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_type is None:  # 如果没有活动的异常，使用传入的异常
        return ''.join(traceback.format_exception(type(e), e, e.__traceback__))
    return ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))


# 便利函数
def info(message: str, *args, **kwargs):
    default_logger.info(message, *args, **kwargs)

def debug(message: str, *args, **kwargs):
    default_logger.debug(message, *args, **kwargs)

def warning(message: str, *args, **kwargs):
    default_logger.warning(message, *args, **kwargs)

def error(message: str, e: Optional[Exception] = None, *args, **kwargs):
    """错误日志，自动包含完整的异常堆栈
    
    Args:
        message: 错误消息
        e: 可选的异常对象
    """
    if e:
        error_msg = f"{message}\n{format_exception(e)}"
    else:
        exc_info = sys.exc_info()
        if exc_info[0] is not None:  # 如果有活动的异常
            error_msg = f"{message}\n{''.join(traceback.format_exception(*exc_info))}"
        else:
            error_msg = message
    
    default_logger.error(error_msg, *args, **kwargs)

def exception(message: str, *args, **kwargs):
    """异常日志，自动包含当前异常的完整堆栈"""
    exc_info = sys.exc_info()
    if exc_info[0] is not None:
        error_msg = f"{message}\n{''.join(traceback.format_exception(*exc_info))}"
        default_logger.error(error_msg, *args, **kwargs)
    else:
        default_logger.error(f"{message} (no active exception)", *args, **kwargs)

def success(message: str, *args, **kwargs):
    default_logger.info(f"✓ {message}", *args, **kwargs)

def step(step_name: str, message: str = "", *args, **kwargs):
    """记录步骤信息"""
    separator = "=" * 60
    default_logger.info(f"\n{separator}")
    default_logger.info(f"🎯 {step_name}")
    if message:
        default_logger.info(f"   {message}")
    default_logger.info(separator)

def progress(current: int, total: int, item_name: str = "项目", *args, **kwargs):
    """记录进度信息"""
    percentage = (current / total * 100) if total > 0 else 0
    default_logger.info(f"📊 进度: {current}/{total} ({percentage:.1f}%) - {item_name}") 