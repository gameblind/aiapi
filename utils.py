import os
import json
import time
import shutil
from datetime import datetime, timedelta
import requests
from config import TASKS_FILE, IMAGE_TASKS_FILE, VIDEOS_DIR, IMAGES_DIR, STATIC_DIR

# 初始化应用所需的目录和文件
def ensure_app_files():
    """确保应用所需的目录和文件都存在"""
    # 确保目录存在
    for directory in [STATIC_DIR, VIDEOS_DIR, IMAGES_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"[INFO] 创建目录: {directory}")
    
    # 确保任务文件存在
    for file_path, default_content in [
        (TASKS_FILE, []),
        (IMAGE_TASKS_FILE, [])
    ]:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 创建文件: {file_path}")

# 备份任务文件
def backup_tasks():
    """备份任务文件"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(STATIC_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # 备份视频任务文件
        if os.path.exists(TASKS_FILE):
            backup_file = os.path.join(backup_dir, f"video_tasks_{timestamp}.json")
            shutil.copy2(TASKS_FILE, backup_file)
            print(f"[INFO] 视频任务文件已备份: {backup_file}")
        
        # 备份图片任务文件
        if os.path.exists(IMAGE_TASKS_FILE):
            backup_file = os.path.join(backup_dir, f"image_tasks_{timestamp}.json")
            shutil.copy2(IMAGE_TASKS_FILE, backup_file)
            print(f"[INFO] 图片任务文件已备份: {backup_file}")
            
        return True
    except Exception as e:
        print(f"[ERROR] 备份任务文件失败: {str(e)}")
        return False