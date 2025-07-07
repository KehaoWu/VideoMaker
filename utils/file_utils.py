"""
文件操作工具函数
提供通用的文件和目录操作功能
"""

import os
import shutil
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


def ensure_directory(directory_path: str) -> None:
    """确保目录存在，如果不存在则创建"""
    os.makedirs(directory_path, exist_ok=True)


def safe_filename(filename: str) -> str:
    """生成安全的文件名，移除或替换不安全字符"""
    # 移除或替换危险字符
    unsafe_chars = '<>:"/\\|?*'
    safe_name = filename
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    
    # 移除首尾空格和点
    safe_name = safe_name.strip('. ')
    
    # 限制长度
    if len(safe_name) > 200:
        safe_name = safe_name[:200]
    
    return safe_name


def get_unique_filename(base_path: str, extension: str = "") -> str:
    """生成唯一文件名，如果文件已存在则添加序号"""
    if not extension.startswith('.') and extension:
        extension = '.' + extension
    
    filename = base_path + extension
    counter = 1
    
    while os.path.exists(filename):
        name_part = base_path
        filename = f"{name_part}_{counter}{extension}"
        counter += 1
    
    return filename


def copy_file(source_path: str, dest_path: str, create_dirs: bool = True) -> bool:
    """复制文件"""
    try:
        if create_dirs:
            ensure_directory(os.path.dirname(dest_path))
        shutil.copy2(source_path, dest_path)
        return True
    except Exception as e:
        print(f"复制文件失败: {source_path} -> {dest_path}, 错误: {e}")
        return False


def move_file(source_path: str, dest_path: str, create_dirs: bool = True) -> bool:
    """移动文件"""
    try:
        if create_dirs:
            ensure_directory(os.path.dirname(dest_path))
        shutil.move(source_path, dest_path)
        return True
    except Exception as e:
        print(f"移动文件失败: {source_path} -> {dest_path}, 错误: {e}")
        return False


def delete_file(file_path: str) -> bool:
    """删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"删除文件失败: {file_path}, 错误: {e}")
        return False


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def get_file_modified_time(file_path: str) -> Optional[datetime]:
    """获取文件修改时间"""
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception:
        return None


def list_files_with_extension(directory: str, extension: str) -> List[str]:
    """列出目录中指定扩展名的所有文件"""
    if not extension.startswith('.'):
        extension = '.' + extension
    
    files = []
    try:
        for filename in os.listdir(directory):
            if filename.lower().endswith(extension.lower()):
                files.append(os.path.join(directory, filename))
    except Exception as e:
        print(f"列出文件失败: {directory}, 错误: {e}")
    
    return files


def read_json_file(file_path: str) -> Optional[Dict[Any, Any]]:
    """读取JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {file_path}, 错误: {e}")
        return None


def write_json_file(file_path: str, data: Dict[Any, Any], create_dirs: bool = True) -> bool:
    """写入JSON文件"""
    try:
        if create_dirs:
            ensure_directory(os.path.dirname(file_path))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"写入JSON文件失败: {file_path}, 错误: {e}")
        return False


def read_text_file(file_path: str) -> Optional[str]:
    """读取文本文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文本文件失败: {file_path}, 错误: {e}")
        return None


def write_text_file(file_path: str, content: str, create_dirs: bool = True) -> bool:
    """写入文本文件"""
    try:
        if create_dirs:
            ensure_directory(os.path.dirname(file_path))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"写入文本文件失败: {file_path}, 错误: {e}")
        return False


def cleanup_directory(directory: str, keep_days: int = 7) -> int:
    """清理目录中的旧文件"""
    if not os.path.exists(directory):
        return 0
    
    cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    deleted_count = 0
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
    except Exception as e:
        print(f"清理目录失败: {directory}, 错误: {e}")
    
    return deleted_count


def get_directory_size(directory: str) -> int:
    """获取目录总大小（字节）"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
    except Exception as e:
        print(f"计算目录大小失败: {directory}, 错误: {e}")
    
    return total_size


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f}{size_names[i]}" 