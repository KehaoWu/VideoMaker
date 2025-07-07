import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Claude API 配置
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', 'your-claude-api-key-here')
CLAUDE_BASE_URL = os.getenv('CLAUDE_BASE_URL', 'https://api.anthropic.com')

# 视频生成API 配置
VIDEO_API_KEY = os.getenv('VIDEO_API_KEY', '<client>|VOLCENGINE')
VIDEO_BASE_URL = os.getenv('VIDEO_BASE_URL', 'http://jd-prpt-engn.jianda-test.dq.yingmi-inc.com/prompt_engine/prompt/video')

# 默认设置
DEFAULT_IMAGE_PATH = os.getenv('DEFAULT_IMAGE_PATH', "assets/sample_infographic.png")
OUTPUT_DIR = os.getenv('OUTPUT_DIR', "assets")
VIDEO_OUTPUT_DIR = os.getenv('VIDEO_OUTPUT_DIR', "assets/generated_videos")

# 视频生成设置
VIDEO_GENERATION_SETTINGS = {
    'model': 'wan2.1-14_i2v-250225',
    'max_wait_time': 30000,  # 最大等待时间（秒）
    'check_interval': 10,  # 检查间隔（秒）
    'max_scenes': 5,       # 最大生成场景数
    'max_cuts': 3          # 最大处理切片数
}

# 图片处理设置
IMAGE_SETTINGS = {
    'supported_formats': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'max_size': 10 * 1024 * 1024,  # 10MB
    'output_quality': 95
} 