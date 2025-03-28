import os
from dotenv import load_dotenv

# 定义项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

# 从环境变量获取配置
API_BASE_URL = os.getenv('API_BASE_URL')
API_KEY = os.getenv('API_KEY')

# 文件存储路径
TASKS_FILE = 'static/video_tasks_history.json'
IMAGE_TASKS_FILE = 'static/image_tasks.json'
VOICE_TASKS_FILE = 'static/voice_tasks.json'  # 添加语音任务文件

# 文件存储目录
STATIC_DIR = os.path.join(BASE_DIR, 'static')
VIDEOS_DIR = os.path.join(STATIC_DIR, 'videos')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
AUDIO_DIR = os.path.join(STATIC_DIR, 'audio')  # 添加音频目录
VOICE_DIR = os.path.join(STATIC_DIR, 'voice')  # 添加语音目录
FILES_DIR = os.path.join(STATIC_DIR, 'files')

# 其他配置
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'