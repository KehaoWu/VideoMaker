"""
系统常量定义
包含VideoMaker系统中使用的各种常量
"""

# 版本信息
VERSION = "1.0.0"
APP_NAME = "VideoMaker"

# 支持的文件格式
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.aac', '.ogg']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv']

# 文件大小限制（字节）
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

# 处理限制
MAX_CUTTING_REGIONS = 20  # 最大切割区域数
MAX_AUDIO_SEGMENTS = 50   # 最大音频段数
MAX_VIDEO_SEGMENTS = 30   # 最大视频段数
MAX_TEXT_LENGTH = 4096    # 最大文本长度

# 时间限制
MIN_VIDEO_DURATION = 1.0    # 最小视频时长（秒）
MAX_VIDEO_DURATION = 600.0  # 最大视频时长（秒）
MIN_AUDIO_DURATION = 0.5    # 最小音频时长（秒）
MAX_AUDIO_DURATION = 300.0  # 最大音频时长（秒）

# 分辨率预设
RESOLUTION_PRESETS = {
    '480p': (854, 480),
    '720p': (1280, 720),
    '1080p': (1920, 1080),
    '1440p': (2560, 1440),
    '4k': (3840, 2160)
}

# 帧率选项
FRAME_RATES = [24, 25, 30, 60]

# 视频编码选项
VIDEO_CODECS = ['h264', 'h265', 'vp9']
AUDIO_CODECS = ['aac', 'mp3', 'opus']

# 质量预设
QUALITY_PRESETS = {
    'low': 70,
    'medium': 85,
    'high': 95,
    'ultra': 100
}

# 比特率预设（视频）
BITRATE_PRESETS = {
    '480p': '2M',
    '720p': '5M',
    '1080p': '8M',
    '1440p': '16M',
    '4k': '35M'
}

# API配置
DEFAULT_API_TIMEOUT = 30
DEFAULT_API_RETRIES = 3
API_RATE_LIMIT_DELAY = 1.0

# Claude API相关
CLAUDE_MAX_TOKENS = 4000
CLAUDE_MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB

# TTS API相关
TTS_MAX_TEXT_LENGTH = 4096
TTS_AVAILABLE_VOICES = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
TTS_SPEED_RANGE = (0.25, 4.0)

# Video API相关
VIDEO_MAX_PROMPT_LENGTH = 1000
VIDEO_DURATION_RANGE = (1.0, 30.0)
VIDEO_STYLES = ['realistic', 'artistic', 'animated', 'cinematic']

# 处理步骤相关
STEP_NAMES = {
    'step1': '图片切割',
    'step2': '音频生成', 
    'step3': '时间轴重计算',
    'step4': '文生视频生成',
    'step5': '视频合成'
}

STEP_DEPENDENCIES = {
    'step1': [],
    'step2': [],
    'step3': ['step2'],
    'step4': ['step3'],
    'step5': ['step1', 'step2', 'step4']
}

# 缓存相关
DEFAULT_CACHE_SIZE_GB = 10
DEFAULT_CACHE_EXPIRY_HOURS = 24
DEFAULT_IMAGE_CACHE_DAYS = 7
DEFAULT_TEMP_FILE_HOURS = 1

# 日志相关
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = "INFO"
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 3

# 错误码
ERROR_CODES = {
    'CONFIG_ERROR': 1001,
    'FILE_NOT_FOUND': 1002,
    'INVALID_FORMAT': 1003,
    'SIZE_LIMIT_EXCEEDED': 1004,
    'API_ERROR': 2001,
    'API_TIMEOUT': 2002,
    'API_RATE_LIMIT': 2003,
    'PROCESSING_ERROR': 3001,
    'VALIDATION_ERROR': 3002,
    'WORKFLOW_ERROR': 3003
}

# 状态码
STATUS_CODES = {
    'PENDING': 'pending',
    'RUNNING': 'running',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'CANCELLED': 'cancelled'
}

# 正则表达式模式
PATTERNS = {
    'EMAIL': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'URL': r'^https?://[^\s/$.?#].[^\s]*$',
    'FILENAME': r'^[^<>:"/\\|?*]+$',
    'TIMESTAMP': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'
}

# 环境变量名
ENV_VARS = {
    'CLAUDE_API_KEY': 'CLAUDE_API_KEY',
    'TTS_API_KEY': 'TTS_API_KEY',
    'VIDEO_API_KEY': 'VIDEO_API_KEY',
    'LOG_LEVEL': 'VIDEOMAKER_LOG_LEVEL',
    'CONFIG_PATH': 'VIDEOMAKER_CONFIG_PATH'
}

# 默认配置路径
DEFAULT_PATHS = {
    'CONFIG_FILE': 'config.yaml',
    'LOG_DIR': 'logs',
    'CACHE_DIR': 'data/cache',
    'TEMP_DIR': 'temp',
    'OUTPUT_DIR': 'output',
    'ASSETS_DIR': 'assets',
    'MODELS_DIR': 'data/models'
}

# 文件命名模板
FILENAME_TEMPLATES = {
    'SLICE': 'slice_{region_id}_{region_name}',
    'AUDIO': 'audio_segment_{index}_{duration}s',
    'VIDEO': 'background_video_{segment_id}',
    'FINAL': '{project_name}_final_{timestamp}'
}

# 性能配置
PERFORMANCE_SETTINGS = {
    'MAX_CONCURRENT_APIS': 3,
    'CHUNK_SIZE': 8192,
    'BUFFER_SIZE': 65536,
    'MEMORY_LIMIT_MB': 2048
} 