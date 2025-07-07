"""
目录管理工具
负责初始化目录结构、管理缓存和清理临时文件
"""

import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

from .logger import get_logger
from .config_manager import get_config


class DirectoryManager:
    """目录管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        
    def initialize_directories(self) -> bool:
        """初始化所有必需的目录结构"""
        try:
            directories = [
                # 输入目录
                "assets/input/images",
                "assets/input/audio", 
                "assets/input/videos",
                
                # 输出目录
                self.config.get('paths.output_dir', 'output'),
                self.config.get('paths.temp_dir', 'temp'),
                self.config.get('paths.logs_dir', 'logs'),
                
                # 缓存目录
                "data/cache/api_responses/claude",
                "data/cache/api_responses/video_api",
                "data/cache/api_responses/tts_api",
                "data/cache/processed_images/cut_regions",
                "data/cache/processed_images/resized",
                "data/cache/processed_images/optimized",
                "data/cache/temp_files/uploads",
                "data/cache/temp_files/downloads",
                "data/cache/temp_files/processing",
                
                # 模型目录
                "data/models/weights/image_analysis",
                "data/models/weights/text_processing",
                "data/models/weights/video_generation",
                "data/models/configs",
                "data/models/metadata",
                
                # 数据集目录
                "data/datasets/training/image_datasets",
                "data/datasets/training/text_datasets",
                "data/datasets/training/video_datasets",
                "data/datasets/validation/test_cases",
                "data/datasets/validation/benchmarks",
                "data/datasets/validation/ground_truth",
                "data/datasets/user_data/projects",
                "data/datasets/user_data/preferences",
                "data/datasets/user_data/history",
                
                # 模板目录细分
                "assets/templates/plans",
                "assets/templates/scripts",
                "assets/templates/configs"
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                self.logger.debug(f"确保目录存在: {directory}")
            
            self.logger.info(f"已初始化 {len(directories)} 个目录")
            return True
            
        except Exception as e:
            self.logger.error(f"目录初始化失败: {e}")
            return False
    
    def cleanup_cache(self, max_age_hours: int = None) -> Dict[str, int]:
        """
        清理过期的缓存文件
        
        Args:
            max_age_hours: 最大保留时间（小时），None则使用配置值
            
        Returns:
            清理统计信息
        """
        if max_age_hours is None:
            max_age_hours = self.config.get('cache.api_cache_hours', 24)
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        stats = {
            'api_responses_cleaned': 0,
            'processed_images_cleaned': 0,
            'temp_files_cleaned': 0,
            'total_size_freed_mb': 0
        }
        
        try:
            # 清理API响应缓存
            api_cache_dir = Path("data/cache/api_responses")
            if api_cache_dir.exists():
                stats['api_responses_cleaned'] = self._cleanup_directory(
                    api_cache_dir, cutoff_time, stats
                )
            
            # 清理处理后的图片缓存（使用更长的保留期）
            image_cutoff = datetime.now() - timedelta(
                days=self.config.get('cache.image_cache_days', 7)
            )
            image_cache_dir = Path("data/cache/processed_images")
            if image_cache_dir.exists():
                stats['processed_images_cleaned'] = self._cleanup_directory(
                    image_cache_dir, image_cutoff, stats
                )
            
            # 清理临时文件（使用较短的保留期）
            temp_cutoff = datetime.now() - timedelta(
                hours=self.config.get('cache.temp_file_hours', 1)
            )
            temp_cache_dir = Path("data/cache/temp_files")
            if temp_cache_dir.exists():
                stats['temp_files_cleaned'] = self._cleanup_directory(
                    temp_cache_dir, temp_cutoff, stats
                )
            
            self.logger.info(f"缓存清理完成: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"缓存清理失败: {e}")
            return stats
    
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
        cache_sizes = {}
        
        cache_dirs = {
            'api_responses': 'data/cache/api_responses',
            'processed_images': 'data/cache/processed_images',
            'temp_files': 'data/cache/temp_files',
            'total': 'data/cache'
        }
        
        for cache_type, cache_path in cache_dirs.items():
            size_mb = self._get_directory_size(Path(cache_path))
            cache_sizes[cache_type] = size_mb
        
        return cache_sizes
    
    def _get_directory_size(self, directory: Path) -> float:
        """计算目录大小（MB）"""
        if not directory.exists():
            return 0.0
        
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            self.logger.warning(f"计算目录大小失败 {directory}: {e}")
        
        return total_size / (1024 * 1024)  # 转换为MB
    
    def check_storage_quota(self) -> Dict[str, Any]:
        """检查存储配额使用情况"""
        max_cache_size_gb = self.config.get('cache.max_size_gb', 10)
        cache_sizes = self.get_cache_size()
        
        total_cache_gb = cache_sizes.get('total', 0) / 1024
        
        quota_info = {
            'max_size_gb': max_cache_size_gb,
            'current_size_gb': total_cache_gb,
            'usage_percentage': (total_cache_gb / max_cache_size_gb) * 100,
            'exceeds_quota': total_cache_gb > max_cache_size_gb,
            'cache_breakdown_mb': cache_sizes
        }
        
        if quota_info['exceeds_quota']:
            self.logger.warning(f"缓存大小超出配额: {total_cache_gb:.2f}GB > {max_cache_size_gb}GB")
        
        return quota_info
    
    def auto_cleanup_if_needed(self) -> bool:
        """根据配额自动清理缓存"""
        if not self.config.get('storage.auto_cleanup', True):
            return False
        
        quota_info = self.check_storage_quota()
        
        if quota_info['exceeds_quota'] or quota_info['usage_percentage'] > 80:
            self.logger.info("触发自动缓存清理")
            
            # 先清理临时文件
            self.cleanup_cache(max_age_hours=0.5)  # 30分钟
            
            # 如果还超配额，清理API缓存
            if self.check_storage_quota()['exceeds_quota']:
                self.cleanup_cache(max_age_hours=12)  # 12小时
            
            # 如果还超配额，清理图片缓存
            if self.check_storage_quota()['exceeds_quota']:
                image_cutoff = datetime.now() - timedelta(days=3)
                image_cache_dir = Path("data/cache/processed_images")
                if image_cache_dir.exists():
                    stats = {'total_size_freed_mb': 0}
                    self._cleanup_directory(image_cache_dir, image_cutoff, stats)
            
            return True
        
        return False
    
    def backup_user_data(self, backup_dir: str = "backups") -> bool:
        """备份用户数据"""
        if not self.config.get('storage.backup_user_data', True):
            return False
        
        try:
            # 创建备份目录
            backup_path = Path(backup_dir) / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 备份用户数据
            user_data_dir = Path("data/datasets/user_data")
            if user_data_dir.exists():
                shutil.copytree(user_data_dir, backup_path / "user_data")
            
            # 备份重要配置
            config_files = ['config.yaml', 'config.py']
            for config_file in config_files:
                if Path(config_file).exists():
                    shutil.copy2(config_file, backup_path)
            
            self.logger.info(f"用户数据备份完成: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"用户数据备份失败: {e}")
            return False


# 全局实例
_directory_manager = None

def get_directory_manager() -> DirectoryManager:
    """获取目录管理器单例"""
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
    """自动清理缓存"""
    return get_directory_manager().auto_cleanup_if_needed() 