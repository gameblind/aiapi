import os
import json
import requests
import uuid
import mimetypes
from datetime import datetime
from config import TASKS_FILE, IMAGE_TASKS_FILE, VIDEOS_DIR, IMAGES_DIR, STATIC_DIR, AUDIO_DIR, VOICE_DIR, FILES_DIR, API_KEY, API_BASE_URL

def load_tasks():
    """加载视频任务历史记录"""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
            
        # 首先检查状态为submitted和processing的任务
        for task in tasks:
            if task.get('status') in ['submitted', 'processing']:
                for video in task.get('videos', []):
                    if not video.get('downloaded'):
                        # 检查本地文件是否存在
                        task_id = task['task_id']
                        video_id = video.get('id', '')
                        base_task_id = f"{task_id}_{video_id}".split('_')[0]
                        video_filename = f"{base_task_id}.mp4"
                        video_path = os.path.join(VIDEOS_DIR, video_filename)
                        
                        if os.path.exists(video_path):
                            video['downloaded'] = True
                            video['local_url'] = f"/static/videos/{video_filename}"
                            print(f"[DEBUG] 发现本地视频文件: {video_filename}")
        
        # 然后检查其他状态的任务
        for task in tasks:
            if task.get('status') not in ['submitted', 'processing']:
                for video in task.get('videos', []):
                    if not video.get('downloaded'):
                        # 检查本地文件是否存在
                        task_id = task['task_id']
                        video_id = video.get('id', '')
                        base_task_id = f"{task_id}_{video_id}".split('_')[0]
                        video_filename = f"{base_task_id}.mp4"
                        video_path = os.path.join(VIDEOS_DIR, video_filename)
                        
                        if os.path.exists(video_path):
                            video['downloaded'] = True
                            video['local_url'] = f"/static/videos/{video_filename}"
                            print(f"[DEBUG] 发现本地视频文件: {video_filename}")
        
        # 保存更新后的任务记录
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
            
        return tasks
    return []

def save_tasks(tasks):
    """保存视频任务记录"""
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def save_task(task_data):
    """保存单个视频任务记录"""
    from datetime import datetime, timedelta
    import time
    
    tasks = load_tasks()
    # 添加更多任务信息
    task_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_data['external_task_id'] = f"custom_{int(time.time())}"  # 自定义任务ID
    task_data['expiration_date'] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")  # 视频过期时间
    tasks.append(task_data)
    save_tasks(tasks)

def load_image_tasks():
    """加载图片任务历史记录"""
    if os.path.exists(IMAGE_TASKS_FILE):
        with open(IMAGE_TASKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_image_tasks(tasks):
    """保存图片任务记录"""
    with open(IMAGE_TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def save_image_task(task_data):
    """保存单个图片任务记录"""
    from datetime import datetime
    import time
    
    tasks = load_image_tasks()
    # 添加更多任务信息
    task_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_data['task_id'] = f"img_{int(time.time())}"  # 自定义任务ID
    tasks.append(task_data)
    save_image_tasks(tasks)

def download_video(url, filename_prefix, force_download=False):
    """下载视频并保存到本地"""
    try:
        print(f"[DEBUG] 开始下载视频: {url}")
        print(f"[DEBUG] 文件名前缀: {filename_prefix}")
        
        # 创建视频目录
        video_dir = os.path.join(STATIC_DIR, 'videos')
        os.makedirs(video_dir, exist_ok=True)
        
        # 构建本地文件路径
        local_filename = f"{filename_prefix}.mp4"
        local_path = os.path.join(video_dir, local_filename)
        local_url = f"/static/videos/{local_filename}"
        
        # 检查文件是否已存在
        if os.path.exists(local_path) and not force_download:
            print(f"[DEBUG] 视频文件已存在，跳过下载: {local_path}")
            return local_url
        
        print(f"[DEBUG] 下载视频到: {local_path}")
        
        # 下载视频
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()
        
        # 保存视频文件
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"[DEBUG] 视频下载完成: {local_path}")
        return local_url
        
    except Exception as e:
        print(f"[ERROR] 下载视频失败: {str(e)}")
        import traceback
        print(f"[ERROR] 堆栈跟踪: {traceback.format_exc()}")
        return None

def download_image(url, filename_prefix, force_download=False):
    """下载图片并保存到本地"""
    try:
        print(f"[DEBUG] 开始下载图片: {url}")
        
        # 创建图片目录
        image_dir = os.path.join(STATIC_DIR, 'images')
        os.makedirs(image_dir, exist_ok=True)
        
        # 构建本地文件路径
        local_filename = f"{filename_prefix}.jpg"
        local_path = os.path.join(image_dir, local_filename)
        local_url = f"/static/images/{local_filename}"
        
        # 检查文件是否已存在
        if os.path.exists(local_path) and not force_download:
            print(f"[DEBUG] 图片文件已存在，跳过下载: {local_path}")
            return local_url
        
        print(f"[DEBUG] 下载图片到: {local_path}")
        
        # 下载图片
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()
        
        # 保存图片文件
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"[DEBUG] 图片下载完成: {local_path}")
        return local_url
        
    except Exception as e:
        print(f"[ERROR] 下载图片失败: {str(e)}")
        return None

def upload_file(file_obj, purpose="assistants", upload_to_cloud=True):
    """
    上传文件并返回访问URL
    
    Args:
        file_obj: 文件对象
        purpose: 文件用途，默认为assistants
        upload_to_cloud: 是否同时上传到云端
        
    Returns:
        dict: 包含文件信息的字典
    """
    try:
        # 获取文件名和扩展名
        original_filename = file_obj.filename
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        # 生成唯一文件名
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(datetime.now().timestamp())
        new_filename = f"{unique_id}_{timestamp}{file_ext}"
        
        # 根据文件类型确定存储目录
        mime_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"
        file_type = mime_type.split('/')[0]
        
        if file_type == "image":
            target_dir = os.path.join(STATIC_DIR, 'images')
            url_prefix = "/static/images"
        elif file_type == "video":
            target_dir = os.path.join(STATIC_DIR, 'videos')
            url_prefix = "/static/videos"
        elif file_type == "audio":
            target_dir = os.path.join(STATIC_DIR, 'audio')
            url_prefix = "/static/audio"
        else:
            target_dir = os.path.join(STATIC_DIR, 'files')
            url_prefix = "/static/files"
        
        # 确保目录存在
        os.makedirs(target_dir, exist_ok=True)
        
        # 保存文件到本地
        file_path = os.path.join(target_dir, new_filename)
        file_obj.save(file_path)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 构建本地文件信息
        file_info = {
            "id": f"file-{unique_id}",
            "object": "file",
            "bytes": file_size,
            "created_at": timestamp,
            "filename": original_filename,
            "url": f"{url_prefix}/{new_filename}",
            "purpose": purpose,
            "cloud_file_id": None  # 初始化云端文件ID为None
        }
        
        # 如果需要上传到云端
        if upload_to_cloud:
            cloud_file_info = upload_to_cloud_api(file_path, original_filename, purpose)
            if cloud_file_info:
                file_info["cloud_file_id"] = cloud_file_info.get("id")
                file_info["cloud_url"] = cloud_file_info.get("url")
        
        # 记录文件信息到文件记录中
        save_file_record(file_info)
        
        return file_info
        
    except Exception as e:
        print(f"[ERROR] 上传文件失败: {str(e)}")
        import traceback
        print(f"[ERROR] 堆栈跟踪: {traceback.format_exc()}")
        return None

def upload_to_cloud_api(file_path, filename, purpose="assistants"):
    """
    将文件上传到云端API
    
    Args:
        file_path: 本地文件路径
        filename: 原始文件名
        purpose: 文件用途
        
    Returns:
        dict: 云端文件信息
    """
    try:
        # 构建API URL
        url = f"{API_BASE_URL}/v1/files?purpose={purpose}"
        
        # 准备请求头
        headers = {
            'Authorization': f'Bearer {API_KEY}'
        }
        
        # 准备文件
        with open(file_path, 'rb') as f:
            files = {
                'file': (filename, f, 'application/octet-stream')
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, files=files)
            
            # 检查响应
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] 云端上传失败: {response.text}")
                return None
                
    except Exception as e:
        print(f"[ERROR] 云端上传异常: {str(e)}")
        return None

def save_file_record(file_info):
    """
    保存文件记录到files.json
    
    Args:
        file_info: 文件信息字典
    """
    files_record_path = os.path.join(STATIC_DIR, 'files.json')
    
    # 读取现有记录
    if os.path.exists(files_record_path):
        with open(files_record_path, 'r', encoding='utf-8') as f:
            try:
                files_record = json.load(f)
            except json.JSONDecodeError:
                files_record = []
    else:
        files_record = []
    
    # 添加新记录
    files_record.append(file_info)
    
    # 保存记录
    with open(files_record_path, 'w', encoding='utf-8') as f:
        json.dump(files_record, f, ensure_ascii=False, indent=2)

def get_file_info(file_id):
    """
    获取文件信息
    
    Args:
        file_id: 文件ID
        
    Returns:
        dict: 文件信息字典，如果未找到则返回None
    """
    files_record_path = os.path.join(STATIC_DIR, 'files.json')
    
    if not os.path.exists(files_record_path):
        return None
    
    with open(files_record_path, 'r', encoding='utf-8') as f:
        try:
            files_record = json.load(f)
            for file_info in files_record:
                if file_info.get('id') == file_id:
                    return file_info
        except json.JSONDecodeError:
            pass
    
    return None

def delete_file(file_id):
    """
    删除文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        bool: 删除成功返回True，否则返回False
    """
    file_info = get_file_info(file_id)
    if not file_info:
        return False
    
    # 获取文件路径
    file_url = file_info.get('url')
    if not file_url:
        return False
    
    # 转换URL为本地路径
    local_path = os.path.join(STATIC_DIR, file_url.replace('/static/', ''))
    
    # 删除本地文件
    try:
        if os.path.exists(local_path):
            os.remove(local_path)
        
        # 如果有云端文件ID，也删除云端文件
        cloud_file_id = file_info.get('cloud_file_id')
        if cloud_file_id:
            delete_from_cloud_api(cloud_file_id)
        
        # 更新文件记录
        files_record_path = os.path.join(STATIC_DIR, 'files.json')
        with open(files_record_path, 'r', encoding='utf-8') as f:
            files_record = json.load(f)
        
        files_record = [f for f in files_record if f.get('id') != file_id]
        
        with open(files_record_path, 'w', encoding='utf-8') as f:
            json.dump(files_record, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"[ERROR] 删除文件失败: {str(e)}")
        return False

def delete_from_cloud_api(file_id):
    """
    从云端API删除文件
    
    Args:
        file_id: 云端文件ID
    """
    try:
        # 构建API URL
        url = f"{API_BASE_URL}/v1/files/{file_id}"
        
        # 准备请求头
        headers = {
            'Authorization': f'Bearer {API_KEY}'
        }
        
        # 发送请求
        response = requests.delete(url, headers=headers)
        
        # 检查响应
        if response.status_code == 200:
            print(f"[INFO] 云端文件删除成功: {file_id}")
        else:
            print(f"[ERROR] 云端文件删除失败: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] 云端删除异常: {str(e)}")

def list_files(purpose=None):
    """
    列出所有文件
    
    Args:
        purpose: 可选，按用途筛选
        
    Returns:
        list: 文件信息列表
    """
    files_record_path = os.path.join(STATIC_DIR, 'files.json')
    
    if not os.path.exists(files_record_path):
        return []
    
    with open(files_record_path, 'r', encoding='utf-8') as f:
        try:
            files_record = json.load(f)
            if purpose:
                return [f for f in files_record if f.get('purpose') == purpose]
            return files_record
        except json.JSONDecodeError:
            return []


def load_voice_tasks():
    """加载语音任务历史记录"""
    from config import VOICE_TASKS_FILE
    
    if os.path.exists(VOICE_TASKS_FILE):
        with open(VOICE_TASKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_voice_tasks(tasks):
    """保存语音任务记录"""
    from config import VOICE_TASKS_FILE
    
    with open(VOICE_TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def save_voice_task(task_data):
    """保存单个语音任务记录"""
    from datetime import datetime
    import time
    
    tasks = load_voice_tasks()
    # 添加更多任务信息
    task_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_data['task_id'] = f"voice_{int(time.time())}"  # 自定义任务ID
    tasks.append(task_data)
    save_voice_tasks(tasks)
    return task_data

def download_audio(url, filename_prefix, force_download=False):
    """下载音频并保存到本地"""
    try:
        print(f"[DEBUG] 开始下载音频: {url}")
        
        # 创建音频目录
        audio_dir = os.path.join(STATIC_DIR, 'voice')
        os.makedirs(audio_dir, exist_ok=True)
        
        # 构建本地文件路径
        local_filename = f"{filename_prefix}.mp3"
        local_path = os.path.join(audio_dir, local_filename)
        local_url = f"/static/voice/{local_filename}"
        
        # 检查文件是否已存在
        if os.path.exists(local_path) and not force_download:
            print(f"[DEBUG] 音频文件已存在，跳过下载: {local_path}")
            return local_url
        
        print(f"[DEBUG] 下载音频到: {local_path}")
        
        # 下载音频
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()
        
        # 保存音频文件
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"[DEBUG] 音频下载完成: {local_path}")
        return local_url
        
    except Exception as e:
        print(f"[ERROR] 下载音频失败: {str(e)}")
        return None