"""
配置管理器
支持多层配置：命令行 > 环境变量 > config.yaml > 默认值
"""

import os
import yaml
from typing import Any, Dict, Optional, Union
from pathlib import Path
import re
from dotenv import load_dotenv


class ConfigManager:
    """配置管理器，支持多层配置和环境变量替换"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_file: YAML配置文件路径
        """
        # 加载环境变量
        load_dotenv()
        
        self.config_file = config_file
        self._config = {}
        self._loaded = False
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self._loaded:
            return
            
        # 加载YAML配置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        self._config = config_data
            except Exception as e:
                print(f"警告：加载配置文件失败 {self.config_file}: {e}")
                self._config = {}
        else:
            print(f"警告：配置文件不存在 {self.config_file}，使用默认配置")
            self._config = self._get_default_config()
        
        # 替换环境变量
        self._config = self._replace_env_vars(self._config)
        self._loaded = True
    
    def _replace_env_vars(self, obj: Any) -> Any:
        """递归替换配置中的环境变量引用"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # 查找 ${VAR_NAME} 格式的环境变量引用
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, obj)
            
            for match in matches:
                env_value = os.getenv(match, f"${{{match}}}")  # 如果环境变量不存在，保持原样
                obj = obj.replace(f"${{{match}}}", env_value)
            
            return obj
        else:
            return obj
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "claude": {
                "api_key": os.getenv('CLAUDE_API_KEY', 'your-claude-api-key-here'),
                "base_url": "https://api.anthropic.com",
                "model": "claude-3-sonnet-20240229",
                "timeout": 60,
                "max_retries": 3
            },
            "video": {
                "api_key": os.getenv('VIDEO_API_KEY', 'your-video-api-key-here'),
                "base_url": "https://api.video-service.com",
                "timeout": 300,
                "max_retries": 2
            },
            "paths": {
                "default_image_path": "assets/sample_infographic.png",
                "output_dir": "output",
                "temp_dir": "temp",
                "logs_dir": "logs"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": {
                    "enabled": True,
                    "filename": "logs/videomaker.log"
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键，支持点号分隔 (如 "claude.api_key")
            default: 默认值
            
        Returns:
            配置值
        """
        self._load_config()
        
        # 首先检查环境变量 (键转换为大写，点号替换为下划线)
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        # 然后查找配置文件中的值
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔
            value: 配置值
        """
        self._load_config()
        
        keys = key.split('.')
        config = self._config
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置节
        
        Args:
            section: 节名称
            
        Returns:
            配置节字典
        """
        return self.get(section, {})
    
    def save(self, file_path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            file_path: 保存路径，默认为原配置文件
        """
        if file_path is None:
            file_path = self.config_file
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, 
                     allow_unicode=True, indent=2)
    
    def update(self, config_dict: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config_dict: 要更新的配置字典
        """
        self._load_config()
        self._deep_update(self._config, config_dict)
    
    def _deep_update(self, base: Dict, update: Dict) -> Dict:
        """深度更新字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
        return base
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置的有效性
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 验证必需的配置项
        required_keys = [
            "claude.api_key",
            "video.api_key",
            "paths.output_dir"
        ]
        
        for key in required_keys:
            value = self.get(key)
            if not value or value == f"your-{key.split('.')[0]}-api-key-here":
                errors.append(f"缺少必需的配置项: {key}")
        
        # 验证路径配置
        paths_to_check = [
            "paths.output_dir",
            "paths.temp_dir",
            "paths.logs_dir"
        ]
        
        for path_key in paths_to_check:
            path_value = self.get(path_key)
            if path_value:
                try:
                    Path(path_value).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"无法创建目录 {path_key}: {path_value} - {e}")
        
        return len(errors) == 0, errors
    
    def print_config(self):
        """打印当前配置（隐藏敏感信息）"""
        self._load_config()
        
        def hide_sensitive(obj, path=""):
            """隐藏敏感信息"""
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if any(sensitive in k.lower() for sensitive in ['key', 'password', 'secret', 'token']):
                        result[k] = "***HIDDEN***"
                    else:
                        result[k] = hide_sensitive(v, current_path)
                return result
            elif isinstance(obj, list):
                return [hide_sensitive(item, path) for item in obj]
            else:
                return obj
        
        safe_config = hide_sensitive(self._config)
        print("当前配置:")
        print(yaml.dump(safe_config, default_flow_style=False, 
                       allow_unicode=True, indent=2))


# 全局配置实例
config = ConfigManager()


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    return config


# 便捷函数
def get(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return config.get(key, default)


def get_section(section: str) -> Dict[str, Any]:
    """获取配置节的便捷函数"""
    return config.get_section(section)


# 常用配置的便捷访问
def get_claude_config() -> Dict[str, Any]:
    """获取Claude API配置"""
    return get_section("claude")


def get_video_config() -> Dict[str, Any]:
    """获取视频API配置"""
    return get_section("video")


def get_paths_config() -> Dict[str, Any]:
    """获取路径配置"""
    return get_section("paths")


def get_logging_config() -> Dict[str, Any]:
    """获取日志配置"""
    return get_section("logging")


if __name__ == "__main__":
    # 测试配置管理器
    cfg = ConfigManager()
    
    # 验证配置
    is_valid, errors = cfg.validate()
    if not is_valid:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("配置验证通过")
    
    # 打印配置
    cfg.print_config() 