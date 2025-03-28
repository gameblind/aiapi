import json
import requests
from config import API_KEY, API_BASE_URL

def check_task_status(task_id):
    """检查任务状态"""
    from services.file_service import load_tasks
    
    print(f"\n[DEBUG] ========== 开始检查任务状态 ==========")
    print(f"[DEBUG] 任务ID: {task_id}")
    print(f"[DEBUG] API基础地址: {API_BASE_URL}")
    
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json'
    }
    print(f"[DEBUG] 认证信息: {headers['Authorization'][:10]}...{headers['Authorization'][-10:]}")
    
    try:
        if not API_BASE_URL:
            raise Exception("API_BASE_URL not configured")
        
        # 首先检查本地任务记录，确定任务类型
        tasks = load_tasks()
        task_type = "image2video"  # 默认任务类型
        
        for task in tasks:
            if task.get('task_id') == task_id:
                # 检查是否为延长视频任务
                if task.get('parameters', {}).get('operation') == 'extend' or 'parent_video_id' in task:
                    task_type = "extend"
                    print(f"[DEBUG] 检测到延长视频任务")
                break
        
        # 根据任务类型构建不同的API URL
        if task_type == "extend":
            url = f"{API_BASE_URL}/kling/v1/videos/extendVideo/{task_id}"
            print(f"[DEBUG] 使用延长视频API URL: {url}")
        else:
            url = f"{API_BASE_URL}/kling/v1/videos/image2video/{task_id}"
            print(f"[DEBUG] 使用图生视频API URL: {url}")
            
        print(f"[DEBUG] 发送请求...")
        
        response = requests.get(
            url,
            headers=headers,
            verify=False
        )
        
        print(f"[DEBUG] 收到响应:")
        print(f"[DEBUG] - 状态码: {response.status_code}")
        print(f"[DEBUG] - 响应头: {dict(response.headers)}")
        
        status_data = response.json()
        print(f"[DEBUG] 响应内容: {json.dumps(status_data, ensure_ascii=False, indent=2)}")

        # 检查响应码
        if status_data.get('code') != 0:
            print(f"[ERROR] API返回错误: {status_data.get('message', '未知错误')}")
            return status_data

        # 获取任务数据
        task_data = status_data.get('data', {})
        task_status = task_data.get('task_status', 'unknown')
        task_msg = task_data.get('task_status_msg', '')
        print(f"[DEBUG] 解析结果:")
        print(f"[DEBUG] - 任务状态: {task_status}")
        print(f"[DEBUG] - 状态信息: {task_msg}")
        
        # 检查视频信息
        if task_status == 'succeed':
            videos = task_data.get('task_result', {}).get('videos', [])
            print(f"[DEBUG] 视频信息:")
            print(f"[DEBUG] - 视频数量: {len(videos)}")
            for i, video in enumerate(videos):
                print(f"[DEBUG] - 视频 {i+1}:")
                print(f"[DEBUG]   - ID: {video.get('id', 'N/A')}")
                print(f"[DEBUG]   - URL: {video.get('url', 'N/A')}")
                print(f"[DEBUG]   - 时长: {video.get('duration', 'N/A')}")
                
            # 如果是延长视频任务，记录父视频信息
            if task_type == "extend":
                parent_info = task_data.get('task_info', {}).get('parent_video', {})
                if parent_info:
                    print(f"[DEBUG] 父视频信息:")
                    print(f"[DEBUG] - ID: {parent_info.get('id', 'N/A')}")
                    print(f"[DEBUG] - URL: {parent_info.get('url', 'N/A')}")
                    print(f"[DEBUG] - 时长: {parent_info.get('duration', 'N/A')}")
        
        print(f"[DEBUG] ========== 完成检查任务状态 ==========\n")
        return status_data
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 网络请求失败:")
        print(f"[ERROR] - 错误类型: {type(e).__name__}")
        print(f"[ERROR] - 错误信息: {str(e)}")
        return {"error": f"请求失败: {str(e)}"}
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON解析失败:")
        print(f"[ERROR] - 错误位置: {e.pos}")
        print(f"[ERROR] - 错误信息: {str(e)}")
        return {"error": f"JSON解析失败: {str(e)}"}
    except Exception as e:
        print(f"[ERROR] 未预期的错误:")
        print(f"[ERROR] - 错误类型: {type(e).__name__}")
        print(f"[ERROR] - 错误信息: {str(e)}")
        return {"error": str(e)}

def create_text2video_task(data):
    """创建文生视频任务"""
    import time
    
    if not API_BASE_URL:
        raise Exception("API_BASE_URL未配置")
    if not API_KEY:
        raise Exception("API_KEY未配置")
        
    url = f"{API_BASE_URL}/kling/v1/videos/text2video"
    print(f"[DEBUG] API URL: {url}")
    
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # 构建请求数据
    external_task_id = f"text2video_{int(time.time())}"
    payload = {
        "model_name": data.get('model_name', 'kling-v1'),
        "prompt": data.get('prompt', ''),
        "negative_prompt": data.get('negative_prompt', ''),
        "mode": data.get('mode', 'std'),
        "duration": data.get('duration', '5'),
        "cfg_scale": float(data.get('cfg_scale', '0.5')),
        "aspect_ratio": data.get('aspect_ratio', '16:9'),
        "external_task_id": external_task_id
    }
    
    # 添加摄像机控制参数（如果有）
    if data.get('camera_control'):
        payload["camera_control"] = data.get('camera_control')
    
    # 发送请求
    print("\n[DEBUG] 发送API请求...")
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        verify=False
    )
    
    # 处理响应
    print(f"[DEBUG] 收到响应:")
    print(f"[DEBUG] - 状态码: {response.status_code}")
    
    response_data = response.json()
    print(f"[DEBUG] - 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
    
    return response_data

# 修改 create_image2video_task 函数，使其接受更多参数
def create_image2video_task(image_base64, image_tail_base64=None, prompt='', negative_prompt='', model_name='kling-v1', mode='std', duration='5', cfg_scale=0.5):
    """创建图生视频任务"""
    import time
    
    if not API_BASE_URL:
        raise Exception("API_BASE_URL未配置")
    if not API_KEY:
        raise Exception("API_KEY未配置")
        
    url = f"{API_BASE_URL}/kling/v1/videos/image2video"
    print(f"[DEBUG] API URL: {url}")
    
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # 构建请求数据
    external_task_id = f"image2video_{int(time.time())}"
    payload = {
        "model_name": model_name,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "image": image_base64,
        "mode": mode,
        "duration": duration,
        "cfg_scale": float(cfg_scale),
        "external_task_id": external_task_id
    }
    
    # 添加尾帧图片（如果有）
    if image_tail_base64:
        payload["image_tail"] = image_tail_base64
    
    # 发送请求
    print("\n[DEBUG] 发送API请求...")
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        verify=False
    )
    
    # 处理响应
    print(f"[DEBUG] 收到响应:")
    print(f"[DEBUG] - 状态码: {response.status_code}")
    
    response_data = response.json()
    print(f"[DEBUG] - 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
    
    return response_data

def create_extend_task(video_uuid, prompt=''):
    """创建视频延长任务"""
    import time
    
    if not API_BASE_URL:
        raise Exception("API_BASE_URL未配置")
    if not API_KEY:
        raise Exception("API_KEY未配置")
        
    url = f"{API_BASE_URL}/kling/v1/videos/extendVideo"
    print(f"[DEBUG] API URL: {url}")
    
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # 构建请求数据
    external_task_id = f"extend_{int(time.time())}"
    payload = {
        "video_id": video_uuid,
        "prompt": prompt,
        "external_task_id": external_task_id
    }
    
    # 发送请求
    print("\n[DEBUG] 发送API请求...")
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        verify=False
    )
    
    # 处理响应
    print(f"[DEBUG] 收到响应:")
    print(f"[DEBUG] - 状态码: {response.status_code}")
    
    response_data = response.json()
    print(f"[DEBUG] - 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
    
    return response_data

def handle_normal_task_videos(task, task_data):
    """处理普通视频任务的视频信息"""
    from services.file_service import download_video
    
    videos = task_data.get('task_result', {}).get('videos', [])
    if not videos:
        print(f"[WARNING] 任务成功但没有视频信息")
        return
        
    print(f"[DEBUG] 发现 {len(videos)} 个视频:")
    existing_videos = {v.get('id'): v for v in task.get('videos', [])}
    
    # 创建新的视频列表
    new_videos = []
    
    for i, video in enumerate(videos):
        video_id = video.get('id')
        if not video_id:
            continue
            
        print(f"\n[DEBUG] 处理视频 {i+1}/{len(videos)}")
        
        # 创建视频信息对象
        video_info = {
            'id': video_id,
            'url': video.get('url', ''),
            'duration': video.get('duration', '0'),
            'local_url': None,
            'downloaded': False
        }
        
        # 检查是否已存在且已下载
        if video_id in existing_videos and existing_videos[video_id].get('downloaded'):
            # 保留已下载的信息
            video_info['downloaded'] = True
            video_info['local_url'] = existing_videos[video_id].get('local_url')
            print(f"[DEBUG] 视频已下载过，保留下载信息")
        # 检查任务是否已删除
        elif task.get('status') == 'deleted':
            print(f"[DEBUG] 任务已被标记为删除，跳过下载")
        # 下载视频
        elif video_info['url']:
            local_url = download_video(video_info['url'], f"{task['task_id']}_{video_id}", force_download=False)
            if local_url:
                video_info['local_url'] = local_url
                video_info['downloaded'] = True
                print(f"[DEBUG] 视频下载成功: {local_url}")
            else:
                print(f"[WARNING] 视频下载失败")
        
        # 添加到新的视频列表
        new_videos.append(video_info)
    
    # 更新任务的视频列表
    task['videos'] = new_videos

def handle_extend_task_videos(task, task_data):
    """处理延长视频任务的视频信息"""
    from services.file_service import download_video
    
    print(f"[DEBUG] 处理延长视频任务的视频信息")
    
    # 获取任务结果中的视频信息
    task_result = task_data.get('task_result', {})
    videos = task_result.get('videos', [])
    
    if not videos:
        print(f"[WARNING] 延长任务成功但没有视频信息")
        return
    
    print(f"[DEBUG] 发现 {len(videos)} 个延长后的视频")
    
    # 获取父视频信息
    parent_info = task_data.get('task_info', {}).get('parent_video', {})
    parent_id = parent_info.get('id')
    
    if parent_id:
        print(f"[DEBUG] 父视频ID: {parent_id}")
        # 记录父视频ID，用于后续处理
        task['parent_video_id'] = parent_id
    
    # 处理视频信息
    existing_videos = {v.get('id'): v for v in task.get('videos', [])}
    new_videos = []
    
    for i, video in enumerate(videos):
        video_id = video.get('id')
        if not video_id:
            continue
            
        print(f"[DEBUG] 处理延长后的视频 {i+1}/{len(videos)}, ID: {video_id}")
        
        # 创建视频信息对象
        video_info = {
            'id': video_id,
            'url': video.get('url', ''),
            'duration': video.get('duration', '0'),
            'local_url': None,
            'downloaded': False
        }
        
        # 检查是否已存在且已下载
        if video_id in existing_videos and existing_videos[video_id].get('downloaded'):
            # 保留已下载的信息
            video_info['downloaded'] = True
            video_info['local_url'] = existing_videos[video_id].get('local_url')
            print(f"[DEBUG] 视频已下载过，保留下载信息")
        # 检查任务是否已删除
        elif task.get('status') == 'deleted':
            print(f"[DEBUG] 任务已被标记为删除，跳过下载")
        # 下载视频
        elif video_info['url']:
            # 为延长视频使用特殊的文件名前缀
            local_url = download_video(video_info['url'], f"extend_{task['task_id']}_{video_id}", force_download=False)
            if local_url:
                video_info['local_url'] = local_url
                video_info['downloaded'] = True
                print(f"[DEBUG] 延长视频下载成功: {local_url}")
            else:
                print(f"[WARNING] 延长视频下载失败")
        
        # 添加到新的视频列表
        new_videos.append(video_info)
    
    # 更新任务的视频列表
    task['videos'] = new_videos
    # 标记为延长视频任务
    if 'parameters' not in task:
        task['parameters'] = {}
    task['parameters']['operation'] = 'extend'