"""
文件操作工具
提供文件和目录管理功能
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
import mimetypes

from .exceptions import FileError


def ensure_directory(directory_path: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path: 目录路径
        
    Returns:
        目录的绝对路径
    """
    try:
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())
    except Exception as e:
        raise FileError(f"创建目录失败: {directory_path} - {e}")


def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    生成安全的文件名，移除或替换危险字符
    
    Args:
        filename: 原始文件名
        max_length: 最大文件名长度
        
    Returns:
        安全的文件名
    """
    # 移除或替换危险字符
    unsafe_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    
    # 移除前后空格和点
    safe_name = safe_name.strip(' .')
    
    # 限制长度
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        max_name_length = max_length - len(ext)
        safe_name = name[:max_name_length] + ext
    
    # 确保文件名不为空
    if not safe_name:
        safe_name = "unnamed_file"
    
    return safe_name


def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    计算文件的哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 ('md5', 'sha1', 'sha256')
        
    Returns:
        文件的哈希值
    """
    if not Path(file_path).exists():
        raise FileError(f"文件不存在: {file_path}")
    
    try:
        hash_func = getattr(hashlib, algorithm.lower())()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    except Exception as e:
        raise FileError(f"计算文件哈希失败: {e}")


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        包含文件信息的字典
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileError(f"文件不存在: {file_path}")
    
    stat = path.stat()
    mime_type, _ = mimetypes.guess_type(str(path))
    
    return {
        'path': str(path.absolute()),
        'name': path.name,
        'stem': path.stem,
        'suffix': path.suffix,
        'size': stat.st_size,
        'size_mb': round(stat.st_size / 1024 / 1024, 2),
        'created_time': stat.st_ctime,
        'modified_time': stat.st_mtime,
        'mime_type': mime_type,
        'is_file': path.is_file(),
        'is_dir': path.is_dir()
    }


def copy_file(src: str, dst: str, overwrite: bool = False) -> str:
    """
    复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        目标文件的绝对路径
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    if not src_path.exists():
        raise FileError(f"源文件不存在: {src}")
    
    if dst_path.exists() and not overwrite:
        raise FileError(f"目标文件已存在: {dst}")
    
    try:
        # 确保目标目录存在
        ensure_directory(str(dst_path.parent))
        
        # 复制文件
        shutil.copy2(src, dst)
        return str(dst_path.absolute())
    except Exception as e:
        raise FileError(f"复制文件失败: {e}")


def move_file(src: str, dst: str, overwrite: bool = False) -> str:
    """
    移动文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        目标文件的绝对路径
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    if not src_path.exists():
        raise FileError(f"源文件不存在: {src}")
    
    if dst_path.exists() and not overwrite:
        raise FileError(f"目标文件已存在: {dst}")
    
    try:
        # 确保目标目录存在
        ensure_directory(str(dst_path.parent))
        
        # 移动文件
        shutil.move(src, dst)
        return str(dst_path.absolute())
    except Exception as e:
        raise FileError(f"移动文件失败: {e}")


def delete_file(file_path: str) -> bool:
    """
    删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否删除成功
    """
    try:
        path = Path(file_path)
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            return True
        return False
    except Exception as e:
        raise FileError(f"删除文件失败: {e}")


def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> List[str]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        pattern: 文件匹配模式
        recursive: 是否递归搜索子目录
        
    Returns:
        文件路径列表
    """
    try:
        path = Path(directory)
        if not path.exists():
            raise FileError(f"目录不存在: {directory}")
        
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        # 只返回文件，排除目录
        return [str(f) for f in files if f.is_file()]
    except Exception as e:
        raise FileError(f"列出文件失败: {e}")


def get_directory_size(directory: str) -> int:
    """
    计算目录大小（字节）
    
    Args:
        directory: 目录路径
        
    Returns:
        目录大小（字节）
    """
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size
    except Exception as e:
        raise FileError(f"计算目录大小失败: {e}")


def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24):
    """
    清理临时文件
    
    Args:
        temp_dir: 临时目录路径
        max_age_hours: 文件最大保留时间（小时）
    """
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in list_files(temp_dir, recursive=True):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                delete_file(file_path)
    except Exception as e:
        raise FileError(f"清理临时文件失败: {e}") 