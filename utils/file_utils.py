"""文件操作工具模块"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .exceptions import FileError, FileProcessingError


def ensure_directory(directory: str) -> bool:
    """确保目录存在，如果不存在则创建"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        raise FileProcessingError(f"创建目录失败: {e}", directory)


def safe_filename(filename: str) -> str:
    """生成安全的文件名"""
    # 移除不安全字符
    safe_chars = [c if c.isalnum() or c in '._- ' else '_' for c in filename]
    return ''.join(safe_chars).strip()


def get_unique_filename(directory: str, filename: str) -> str:
    """生成唯一的文件名"""
    name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    
    return new_filename


def copy_file(source_path: str, dest_path: str, create_dirs: bool = True) -> bool:
    """复制文件"""
    try:
        if create_dirs:
            ensure_directory(os.path.dirname(dest_path))
        shutil.copy2(source_path, dest_path)
        return True
    except Exception as e:
        raise FileProcessingError(f"复制文件失败: {e}", source_path)


def move_file(source_path: str, dest_path: str, create_dirs: bool = True) -> bool:
    """移动文件"""
    try:
        if create_dirs:
            ensure_directory(os.path.dirname(dest_path))
        shutil.move(source_path, dest_path)
        return True
    except Exception as e:
        raise FileProcessingError(f"移动文件失败: {e}", source_path)


def delete_file(file_path: str) -> bool:
    """删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        raise FileProcessingError(f"删除文件失败: {e}", file_path)


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        raise FileProcessingError(f"获取文件大小失败: {e}", file_path)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def list_files_with_extension(directory: str, extension: str) -> List[str]:
    """列出目录中指定扩展名的所有文件"""
    if not extension.startswith('.'):
        extension = '.' + extension
    
    try:
        files = []
        for filename in os.listdir(directory):
            if filename.lower().endswith(extension.lower()):
                files.append(os.path.join(directory, filename))
        return files
    except Exception as e:
        raise FileProcessingError(f"列出文件失败: {e}", directory)


def read_json_file(file_path: str) -> Dict[Any, Any]:
    """读取JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise FileError(f"JSON解析失败: {e}")
    except Exception as e:
        raise FileProcessingError(f"读取JSON文件失败: {e}", file_path)


def write_json_file(file_path: str, data: Dict[Any, Any], indent: int = 2) -> bool:
    """写入JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        raise FileProcessingError(f"写入JSON文件失败: {e}", file_path)


def read_text_file(file_path: str) -> str:
    """读取文本文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise FileProcessingError(f"读取文本文件失败: {e}", file_path)


def write_text_file(file_path: str, content: str) -> bool:
    """写入文本文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        raise FileProcessingError(f"写入文本文件失败: {e}", file_path)


def get_file_modification_time(file_path: str) -> datetime:
    """获取文件修改时间"""
    try:
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    except Exception as e:
        raise FileProcessingError(f"获取文件修改时间失败: {e}", file_path)


def get_directory_size(directory: str) -> int:
    """获取目录总大小（字节）"""
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
        return total_size
    except Exception as e:
        raise FileProcessingError(f"计算目录大小失败: {e}", directory) 