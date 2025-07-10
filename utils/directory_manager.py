"""目录管理工具模块"""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from .logger import get_logger
from .config_manager import get_config
from .exceptions import FileError, FileProcessingError
from .file_utils import get_directory_size, format_file_size


class DirectoryManager:
    """目录管理器 - 负责管理项目的目录结构"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger(__name__)
        self.config = config if config else get_config()
    
    def create_video_directories(self, video_id: str) -> Dict[str, str]:
        """
        为视频项目创建目录结构
        
        Args:
            video_id: 视频ID
            
        Returns:
            包含所有创建的目录路径的字典
        """
        try:
            # 获取基础配置
            output_dir = self.config.get('paths.output_dir', 'output')
            
            # 创建目录结构
            paths = {}
            
            # 创建视频项目根目录
            video_root = os.path.join(output_dir, video_id)
            paths['root'] = video_root
            os.makedirs(video_root, exist_ok=True)
            
            # 创建主要子目录
            subdirs = {
                'cuts': 'cuts',          # 切图输出
                'audio': 'audio',         # 音频文件
                'background': 'background',    # 背景视频
                'composition': 'composition',   # 合成中间文件
                'final': 'final'          # 最终输出
            }
            
            for key, subdir in subdirs.items():
                path = os.path.join(video_root, subdir)
                paths[key] = path
                os.makedirs(path, exist_ok=True)
            
            self.logger.info(f"已创建视频项目目录结构: {video_id}")
            return paths
            
        except Exception as e:
            raise FileProcessingError(f"创建视频目录结构失败: {e}", video_id)
    
    def get_video_paths(self, video_id: str) -> Dict[str, str]:
        """
        获取视频项目的所有目录路径
        
        Args:
            video_id: 视频ID
            
        Returns:
            包含所有目录路径的字典
        """
        output_dir = self.config.get('paths.output_dir', 'output')
        
        paths = {}
        video_root = os.path.join(output_dir, video_id)
        paths['root'] = video_root
        
        subdirs = {
            'cuts': 'cuts',
            'audio': 'audio',
            'background': 'background',
            'composition': 'composition',
            'final': 'final'
        }
        
        for key, subdir in subdirs.items():
            paths[key] = os.path.join(video_root, subdir)
        
        return paths

    def cleanup_cache(self, max_age_hours: int = None) -> Dict[str, int]:
        """
        清理缓存目录中的旧文件
        
        Args:
            max_age_hours: 文件最大保留时间（小时），None表示使用配置值
            
        Returns:
            清理统计信息
        """
        stats = {
            'files_cleaned': 0,
            'total_size_freed_mb': 0.0
        }
        
        try:
            # 获取配置的最大保留时间
            if max_age_hours is None:
                max_age_hours = self.config.get('cache.max_age_hours', 24)
            
            # 计算截止时间
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # 清理各个缓存目录
            cache_dirs = [
                Path('data/cache/api_responses'),
                Path('data/cache/processed_images'),
                Path('data/cache/temp_files')
            ]
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    cleaned = self._cleanup_directory(cache_dir, cutoff_time, stats)
                    stats['files_cleaned'] += cleaned
            
            if stats['files_cleaned'] > 0:
                self.logger.info(
                    f"缓存清理完成: 删除{stats['files_cleaned']}个文件, "
                    f"释放{stats['total_size_freed_mb']:.1f}MB空间"
                )
            
            return stats
            
        except Exception as e:
            raise FileProcessingError(f"清理缓存失败: {e}")
    
    def _cleanup_directory(self, directory: Path, cutoff_time: datetime, 
                          stats: Dict[str, int]) -> int:
        """清理指定目录中的过期文件"""
        cleaned_count = 0
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                try:
                    # 检查文件修改时间
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_time:
                        # 计算文件大小
                        file_size = file_path.stat().st_size
                        stats['total_size_freed_mb'] += file_size / (1024 * 1024)
                        
                        # 删除文件
                        file_path.unlink()
                        cleaned_count += 1
                        
                        self.logger.debug(f"删除过期文件: {file_path}")
                        
                except Exception as e:
                    self.logger.warning(f"删除文件失败 {file_path}: {e}")
        
        return cleaned_count
    
    def get_cache_size(self) -> Dict[str, float]:
        """获取各类缓存的大小（MB）"""
        try:
            cache_sizes = {}
            
            cache_dirs = {
                'api_responses': 'data/cache/api_responses',
                'processed_images': 'data/cache/processed_images',
                'temp_files': 'data/cache/temp_files',
                'total': 'data/cache'
            }
            
            for cache_type, cache_path in cache_dirs.items():
                size_mb = get_directory_size(Path(cache_path)) / (1024 * 1024)
                cache_sizes[cache_type] = size_mb
            
            return cache_sizes
            
        except Exception as e:
            raise FileProcessingError(f"获取缓存大小失败: {e}")
    
    def check_storage_quota(self) -> Dict[str, Any]:
        """检查存储配额使用情况"""
        try:
            quota_info = {
                'quota_exceeded': False,
                'warnings': [],
                'cache_sizes': self.get_cache_size()
            }
            
            # 检查配置的限制
            max_cache_size = self.config.get('cache.max_size_mb', 1024)  # 默认1GB
            max_output_size = self.config.get('output.max_size_mb', 5120)  # 默认5GB
            
            # 检查输出目录大小
            output_size = get_directory_size('output') / (1024 * 1024)
            quota_info['output_size'] = output_size
            
            if output_size > max_output_size:
                quota_info['quota_exceeded'] = True
                quota_info['warnings'].append(
                    f"输出目录超出配额: {output_size:.1f}MB/{max_output_size}MB"
                )
            
            if quota_info['cache_sizes']['total'] > max_cache_size:
                quota_info['quota_exceeded'] = True
                quota_info['warnings'].append(
                    f"缓存超出配额: {quota_info['cache_sizes']['total']:.1f}MB/{max_cache_size}MB"
                )
            
            return quota_info
            
        except Exception as e:
            raise FileProcessingError(f"检查存储配额失败: {e}")
    
    def auto_cleanup_if_needed(self) -> bool:
        """如果需要，自动清理缓存"""
        try:
            quota_info = self.check_storage_quota()
            
            if quota_info.get('quota_exceeded'):
                self.logger.warning("存储配额超出，开始自动清理")
                
                # 首先清理临时文件和缓存
                self.cleanup_cache(max_age_hours=1)  # 清理1小时前的缓存
                
                # 再次检查配额
                quota_info = self.check_storage_quota()
                if quota_info.get('quota_exceeded'):
                    self.logger.warning("清理后仍超出配额，需要手动处理")
                    return False
                
                return True
            
            return True
            
        except Exception as e:
            raise FileProcessingError(f"自动清理失败: {e}")
    
    def backup_user_data(self, backup_dir: str = "backups") -> bool:
        """备份用户数据"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
            
            # 创建备份目录
            os.makedirs(backup_path, exist_ok=True)
            
            # 需要备份的目录
            dirs_to_backup = [
                "data/datasets/user_data",
                "assets/templates",
                self.config.get('paths.output_dir', 'output')
            ]
            
            for src_dir in dirs_to_backup:
                if os.path.exists(src_dir):
                    dst_dir = os.path.join(backup_path, os.path.basename(src_dir))
                    shutil.copytree(src_dir, dst_dir)
                    self.logger.info(f"已备份: {src_dir} -> {dst_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"备份失败: {e}")
            return False


# 单例模式
_directory_manager = None

def get_directory_manager() -> DirectoryManager:
    """获取目录管理器实例"""
    global _directory_manager
    if _directory_manager is None:
        _directory_manager = DirectoryManager()
    return _directory_manager

def initialize_directories() -> bool:
    """初始化目录结构"""
    return get_directory_manager().initialize_directories()

def cleanup_cache(max_age_hours: int = None) -> Dict[str, int]:
    """清理缓存"""
    return get_directory_manager().cleanup_cache(max_age_hours)

def auto_cleanup_if_needed() -> bool:
    """如果需要，自动清理缓存"""
    return get_directory_manager().auto_cleanup_if_needed() 