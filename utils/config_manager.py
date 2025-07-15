"""
配置管理工具
支持YAML配置文件和环境变量
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from .exceptions import ConfigError


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ConfigError(f"配置文件格式错误: {e}")
            except Exception as e:
                raise ConfigError(f"读取配置文件失败: {e}")
        else:
            # 如果配置文件不存在，创建默认配置
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'openai': {
                'api_key': os.getenv('OPENAI_API_KEY', ''),
                'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                'model': os.getenv('OPENAI_MODEL', 'gpt-4-vision-preview'),
                'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000')),
                'timeout': int(os.getenv('OPENAI_TIMEOUT', '30'))
            },
            'tts': {
                'api_base': os.getenv('TTS_API_BASE', 'http://jd-prpt-engn-t.jianda-test.dq.yingmi-inc.com'),
                'client_id': os.getenv('TTS_CLIENT_ID', '<client>'),
                'voice_type': os.getenv('TTS_VOICE_TYPE', 'zh_male_M392_conversation_wvae_bigtts'),
                'encoding': os.getenv('TTS_ENCODING', 'mp3'),
                'speed_ratio': float(os.getenv('TTS_SPEED_RATIO', '1.0'))
            },
            'video': {
                'api_key': os.getenv('VIDEO_API_KEY', ''),
                'base_url': os.getenv('VIDEO_BASE_URL', 'https://api.runway.com'),
                'model': os.getenv('VIDEO_MODEL', 'gen3'),
                'timeout': int(os.getenv('VIDEO_TIMEOUT', '300')),
                'max_retries': int(os.getenv('VIDEO_MAX_RETRIES', '2'))
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'file': os.getenv('LOG_FILE', 'logs/videomaker.log')
            },
            'output': {
                'base_dir': os.getenv('OUTPUT_DIR', 'output'),
                'video_dir': os.getenv('VIDEO_OUTPUT_DIR', 'output/videos'),
                'audio_dir': os.getenv('AUDIO_OUTPUT_DIR', 'output/audio')
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的键路径
        
        Args:
            key: 配置键，支持 'section.key' 格式
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持 'section.key' 格式
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 创建嵌套字典路径
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, file_path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            file_path: 保存路径，默认使用初始化时的配置文件
        """
        save_path = file_path or self.config_file
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        except Exception as e:
            raise ConfigError(f"保存配置文件失败: {e}")
    
    def reload(self):
        """重新加载配置文件"""
        self._load_config()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()


# 全局配置实例
_config_manager = None


def get_config(config_file: str = "config.yaml") -> ConfigManager:
    """
    获取全局配置管理器实例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        ConfigManager实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager


def reload_config():
    """重新加载全局配置"""
    global _config_manager
    if _config_manager:
        _config_manager.reload() 