import json
import requests
from config import API_KEY, API_BASE_URL

def create_image_task(prompt, negative_prompt='', model_name='sd-turbo', width=1024, height=1024, steps=30, cfg_scale=7.0, seed=-1):
    """创建图像生成任务"""
    import time
    
    if not API_BASE_URL:
        raise Exception("API_BASE_URL未配置")
    if not API_KEY:
        raise Exception("API_KEY未配置")
        
    url = f"{API_BASE_URL}/v1/images/generations"
    print(f"[DEBUG] API URL: {url}")
    
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # 构建请求数据
    payload = {
        "model": model_name,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "seed": seed
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

def process_image_result(task_data, response_data):
    """处理图像生成结果"""
    from services.file_service import download_image, save_image_task
    import time
    import base64
    
    # 检查响应是否成功
    if response_data.get('code') != 0:
        error_msg = response_data.get('message', '未知错误')
        print(f"[ERROR] API返回错误: {error_msg}")
        task_data['status'] = 'failed'
        task_data['error'] = error_msg
        save_image_task(task_data)
        return None
    
    # 获取图像数据
    images = response_data.get('data', {}).get('images', [])
    if not images:
        print(f"[WARNING] 没有生成任何图像")
        task_data['status'] = 'failed'
        task_data['error'] = '没有生成任何图像'
        save_image_task(task_data)
        return None
    
    # 处理图像
    image_results = []
    for i, image_data in enumerate(images):
        image_url = image_data.get('url')
        if not image_url:
            # 检查是否有base64数据
            image_b64 = image_data.get('b64_json')
            if image_b64:
                # 保存base64图像到本地
                timestamp = int(time.time())
                filename = f"img_{task_data['task_id']}_{i}_{timestamp}"
                
                # 创建图像目录
                import os
                from config import IMAGES_DIR
                os.makedirs(IMAGES_DIR, exist_ok=True)
                
                # 保存图像
                image_path = os.path.join(IMAGES_DIR, f"{filename}.jpg")
                with open(image_path, 'wb') as f:
                    f.write(base64.b64decode(image_b64))
                
                local_url = f"/static/images/{filename}.jpg"
                image_results.append({
                    'url': None,
                    'local_url': local_url,
                    'downloaded': True
                })
                print(f"[DEBUG] 保存base64图像: {local_url}")
            continue
        
        # 下载图像
        timestamp = int(time.time())
        filename = f"img_{task_data['task_id']}_{i}_{timestamp}"
        local_url = download_image(image_url, filename)
        
        if local_url:
            image_results.append({
                'url': image_url,
                'local_url': local_url,
                'downloaded': True
            })
            print(f"[DEBUG] 图像下载成功: {local_url}")
        else:
            image_results.append({
                'url': image_url,
                'local_url': None,
                'downloaded': False
            })
            print(f"[WARNING] 图像下载失败: {image_url}")
    
    # 更新任务数据
    task_data['status'] = 'completed'
    task_data['images'] = image_results
    save_image_task(task_data)
    
    return image_results