from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import requests
import json
import os
import base64
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image as PILImage
from task_query import query_all_tasks
from task_backup import backup_tasks, delete_task
from task_backup import backup_tasks, delete_task
from image_generate import image_bp

# 禁用不安全请求警告
#from urllib3.exceptions import InsecureRequestWarning
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)
load_dotenv()

# 从环境变量获取配置
API_BASE_URL = os.getenv('API_BASE_URL')
API_KEY = os.getenv('API_KEY')

# 注册Blueprint并添加调试日志
print("[DEBUG] 开始注册Blueprint...")
# 修改为与前端匹配的URL前缀
app.register_blueprint(image_bp, url_prefix='/generate_image')
print("[DEBUG] Blueprint注册完成，url_prefix='/generate_image'")
# 文件存储路径
TASKS_FILE = 'video_tasks_history.json'
VIDEOS_DIR = 'static/videos'
if not os.path.exists(VIDEOS_DIR):
    os.makedirs(VIDEOS_DIR)

def load_tasks():
    """加载任务历史记录"""
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

def save_task(task_data):
    """保存任务记录"""
    tasks = load_tasks()
    # 添加更多任务信息
    task_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_data['external_task_id'] = f"custom_{int(time.time())}"  # 自定义任务ID
    task_data['expiration_date'] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")  # 视频过期时间
    tasks.append(task_data)
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def check_task_status(task_id):
    """检查任务状态"""
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
            
        url = f"{API_BASE_URL}/kling/v1/videos/image2video/{task_id}"
        print(f"[DEBUG] 完整请求URL: {url}")
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
def upload_to_github_base64(base64_string):
    """直接返回Base64字符串，不再上传到GitHub"""
    try:
        print(f"[DEBUG] 处理Base64编码图片")
        return base64_string
    except Exception as e:
        print(f"[ERROR] 处理Base64图片失败: {str(e)}")
        raise Exception(f"Failed to process Base64 image: {str(e)}")
def download_video(video_url, task_id, max_retries=3, force_download=False):
    """下载视频到本地"""
    print(f"\n[DEBUG] ========== 开始下载视频 ==========")
    print(f"[DEBUG] 视频URL: {video_url}")
    print(f"[DEBUG] 任务ID: {task_id}")
    print(f"[DEBUG] 强制下载: {force_download}")
    
    # 1. 生成文件名和路径
    base_task_id = task_id.split('_')[0]  # 获取基础任务ID
    video_filename = f"{base_task_id}.mp4"
    video_path = os.path.join(VIDEOS_DIR, video_filename)
    local_url = f"/static/videos/{video_filename}"
    
    # 2. 检查本地文件
    if os.path.exists(video_path):
        if not force_download:
            print(f"[DEBUG] 检测到本地已存在视频文件，直接使用")
            print(f"[DEBUG] ========== 视频下载完成 ==========\n")
            return local_url
        else:
            print(f"[DEBUG] 检测到本地文件，但由于强制下载标志，将重新下载")
    
    # 3. 开始下载
    print(f"[DEBUG] 开始下载文件...")
    for attempt in range(max_retries):
        try:
            print(f"\n[DEBUG] 第 {attempt + 1} 次尝试下载")
            
            # 设置请求头
            headers = {
                'Authorization': API_KEY,
                'User-Agent': 'Mozilla/5.0'
            }
            
            # 发送请求
            response = requests.get(video_url, headers=headers, stream=True, verify=False)
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            print(f"[DEBUG] 视频文件大小: {total_size / 1024 / 1024:.2f} MB")
            
            # 写入文件
            downloaded_size = 0
            with open(video_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"[DEBUG] 下载进度: {progress:.1f}%")
            
            print(f"[DEBUG] 下载完成，本地路径: {local_url}")
            print(f"[DEBUG] ========== 视频下载完成 ==========\n")
            return local_url
            
        except Exception as e:
            print(f"[ERROR] 下载失败 (尝试 {attempt + 1}/{max_retries}):")
            print(f"[ERROR] - 错误类型: {type(e).__name__}")
            print(f"[ERROR] - 错误信息: {str(e)}")
            if attempt == max_retries - 1:
                return None
            print(f"[DEBUG] 等待2秒后重试...")
            time.sleep(2)
    
    print(f"[ERROR] 视频下载失败，已达到最大重试次数")
    print(f"[DEBUG] ========== 视频下载结束 ==========\n")
    return None
@app.route('/index.html')
def index_html():
    return render_template('index.html')  # 或者 redirect('/')
@app.route('/')
def index():
    """首页重定向到图片生成页面"""
    return redirect(url_for('images'))

@app.route('/tasks')
def tasks():
    """显示任务历史记录"""
    task_list = load_tasks()
    return render_template('tasks.html', tasks=task_list)

@app.route('/all_tasks', methods=['GET'])
def all_tasks():
    """查询所有历史任务"""
    try:
        print("\n[DEBUG] ==================== 开始查询所有历史任务 ====================")
        
        # 调用查询函数
        result = query_all_tasks()
        
        if 'error' in result:
            print(f"[ERROR] 查询失败: {result['error']}")
            return jsonify({"error": result['error']}), 500
            
        if result.get('code') != 0:
            print(f"[ERROR] API返回错误: {result.get('message', '未知错误')}")
            return jsonify(result), 400
        
        # 获取任务数据
        tasks_data = result.get('data', {})
        tasks = tasks_data.get('tasks', [])
        total = tasks_data.get('total', 0)
        
        print(f"[DEBUG] 获取到 {len(tasks)} 条任务记录")
        print(f"[DEBUG] ==================== 完成查询所有历史任务 ====================")
        
        # 渲染模板
        return render_template('all_tasks.html', tasks=tasks, total=total)
        
    except Exception as e:
        error_msg = f"查询所有任务出错: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/images')
def images():
    """图片墙页面"""
    return render_template('images.html')  # 确保 images.html 在 templates 目录

@app.route('/generate', methods=['POST'])
def generate_video():
    try:
        print("\n[DEBUG] ==================== 开始处理视频生成请求 ====================")
        
        # 1. 检查请求数据
        print("\n[DEBUG] 1. 检查请求数据:")
        data = request.get_json()
        if not data or 'image' not in data:
            raise Exception("未找到图片数据")
        
        # 2. 获取并验证表单数据
        print("\n[DEBUG] 2. 获取表单数据:")
        image_base64 = process_image_base64(data['image'])
        image_tail_base64 = process_image_base64(data.get('image_tail', '')) if data.get('image_tail') else None
        prompt = data.get('prompt', '')[:2500]  # 限制提示词长度
        negative_prompt = data.get('negative_prompt', '')[:2500]  # 限制负向提示词长度
        duration = data.get('duration', '5')
        mode = data.get('mode', 'std')
        model_name = data.get('model_name', 'kling-v1')
        cfg_scale = float(data.get('cfg_scale', '0.5'))
        
        # 验证参数
        if len(prompt) > 2500:
            raise Exception("提示词长度不能超过2500个字符")
        if len(negative_prompt) > 2500:
            raise Exception("负向提示词长度不能超过2500个字符")
        if cfg_scale < 0 or cfg_scale > 1:
            raise Exception("生成视频的自由度必须在0到1之间")
        if model_name not in ['kling-v1', 'kling-v1-5', 'kling-v1-6']:
            raise Exception("不支持的模型版本")
        if mode not in ['std', 'pro']:
            raise Exception("不支持的生成模式")
        if duration not in ['5', '10']:
            raise Exception("不支持的视频时长")
        
        # 如果使用尾帧控制，强制使用5秒时长
        if image_tail_base64 and duration != '5':
            duration = '5'
            print("[DEBUG] 检测到尾帧图片，已强制设置时长为5秒")
        
        print(f"[DEBUG] 请求参数详情:")
        print(f"[DEBUG] - 首帧图片: Base64编码数据")
        print(f"[DEBUG] - 尾帧图片: {'包含Base64编码数据' if image_tail_base64 else 'None'}")
        print(f"[DEBUG] - 提示词: {prompt}")
        print(f"[DEBUG] - 负向提示词: {negative_prompt}")
        print(f"[DEBUG] - 时长: {duration}")
        print(f"[DEBUG] - 模式: {mode}")
        print(f"[DEBUG] - 模型: {model_name}")
        print(f"[DEBUG] - 自由度: {cfg_scale}")
        
        # 3. 准备API调用
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
        
        # 4. 构建请求数据
        external_task_id = f"custom_{int(time.time())}"
        payload = {
            "model_name": model_name,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "image": image_base64,
            "image_tail": image_tail_base64,
            "mode": mode,
            "duration": duration,
            "cfg_scale": cfg_scale,
            "external_task_id": external_task_id
        }
        
        # 5. 发送请求
        print("\n[DEBUG] 5. 发送API请求...")
        max_retries = 3
        retry_delay = 2
        timeout = 60  # 增加超时时间
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] 第 {attempt + 1} 次尝试发送请求")
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    verify=False,
                    timeout=timeout
                )
                break
            except requests.exceptions.SSLError as ssl_err:
                print(f"[ERROR] SSL错误 (尝试 {attempt + 1}/{max_retries}):")
                print(f"[ERROR] - 错误类型: {type(ssl_err).__name__}")
                print(f"[ERROR] - 错误信息: {str(ssl_err)}")
                if attempt == max_retries - 1:
                    raise
                print(f"[DEBUG] 等待{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            except requests.exceptions.Timeout as timeout_err:
                print(f"[ERROR] 请求超时 (尝试 {attempt + 1}/{max_retries}):")
                print(f"[ERROR] - 错误类型: {type(timeout_err).__name__}")
                print(f"[ERROR] - 错误信息: {str(timeout_err)}")
                if attempt == max_retries - 1:
                    raise
                print(f"[DEBUG] 等待{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            except requests.exceptions.RequestException as req_err:
                print(f"[ERROR] 请求错误 (尝试 {attempt + 1}/{max_retries}):")
                print(f"[ERROR] - 错误类型: {type(req_err).__name__}")
                print(f"[ERROR] - 错误信息: {str(req_err)}")
                if attempt == max_retries - 1:
                    raise
                print(f"[DEBUG] 等待{retry_delay}秒后重试...")
                time.sleep(retry_delay)
        
        response_data = response.json()
        
        # 6. 处理响应
        if response_data.get('code') == 0 and response_data.get('data', {}).get('task_id'):
            task_id = response_data['data']['task_id']
            
            # 7. 保存任务记录
            task_record = {
                'task_id': task_id,
                'external_task_id': external_task_id,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'status': 'submitted',
                'status_msg': '',
                'parameters': {
                    'model_name': model_name,
                    'duration': duration,
                    'mode': mode,
                    'cfg_scale': cfg_scale
                },
                'image_url': f"data:image/jpeg;base64,{image_base64}",
                'videos': []
            }
            
            save_task(task_record)
            
            return jsonify({
                'success': True,
                'message': '任务已提交',
                'data': {'task_id': task_id, 'external_task_id': external_task_id}
            })
        else:
            error_msg = response_data.get('message', '未知错误')
            return jsonify({
                'success': False,
                'message': f'提交任务失败: {error_msg}',
                'data': response_data
            })
            
    except Exception as e:
        print(f"[ERROR] 处理失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"处理失败: {str(e)}"
        }), 500
def validate_image_dimensions(img):
    """验证图片尺寸和宽高比"""
    width = img.width
    height = img.height
    
    # 检查最小分辨率
    if width < 300 or height < 300:
        raise Exception("图片分辨率不能小于300*300px")
    
    # 检查宽高比
    ratio = width / height
    if ratio < 0.4 or ratio > 2.5:  # 1:2.5 ~ 2.5:1
        raise Exception("图片宽高比必须在1:2.5到2.5:1之间")
    
    return True
def process_image_base64(base64_str):
    """处理Base64图片数据"""
    # 如果包含前缀，去除前缀
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    
    # 检查文件大小（Base64字符串长度 * 0.75 ≈ 实际文件大小）
    file_size = len(base64_str) * 0.75 / (1024 * 1024)  # 转换为MB
    if file_size > 10:
        raise Exception("图片文件大小不能超过10MB")
    
    return base64_str
@app.route('/extend_video', methods=['POST'])
def extend_video():
    """处理视频延长请求 - 简化版"""
    try:
        print("\n[DEBUG] ==================== 开始处理视频延长请求 ====================")
        
        # 1. 获取请求数据
        data = request.json
        print(f"[DEBUG] 请求数据: {json.dumps(data, ensure_ascii=False)}")
        
        if not data:
            raise Exception("请求数据不完整")
            
        if 'video_id' not in data:
            raise Exception("请求数据缺少视频ID")
            
        video_id = data['video_id']
        prompt = data.get('prompt', '')
        external_task_id = data.get('external_task_id')  # 可选参数，仅用于日志记录
        
        print(f"[DEBUG] 视频ID: {video_id}")
        print(f"[DEBUG] 提示词: {prompt}")
        if external_task_id:
            print(f"[DEBUG] 原始任务ID: {external_task_id}")

        # 2. 处理提示词长度
        if len(prompt) > 2500:
            print(f"[WARNING] 提示词超长，已截断: {len(prompt)} -> 2500")
            prompt = prompt[:2500]
            
        # 3. 处理video_id格式
        if "-" in video_id:
            print(f"[DEBUG] 原始video_id: {video_id}")
            video_id = video_id.split("-")[0] if "-" in video_id else video_id
            print(f"[DEBUG] 处理后video_id: {video_id}")

        # 4. 发送API请求
        print("\n[DEBUG] 发送API请求...")
        from video_extend import create_extend_task
        response_data = create_extend_task(video_id, prompt)
        
        # 5. 检查响应
        if "error" in response_data:
            raise Exception(f"API错误: {response_data['error']}")
            
        if not response_data or response_data.get('code') != 0 or not response_data.get('data') or not response_data.get('data', {}).get('task_id'):
            error_msg = response_data.get('message', '未知错误') if response_data else '无响应数据'
            print(f"[ERROR] API返回无效数据: {error_msg}")
            raise Exception(f"API返回无效数据: {error_msg}")
            
        # 6. 获取任务ID并返回
        task_id = response_data['data']['task_id']
        print(f"[DEBUG] 任务创建成功，任务ID: {task_id}")
        
        print("\n[DEBUG] ==================== 视频延长请求处理完成 ====================")
        return jsonify({
            'success': True,
            'message': '延长任务已提交',
            'task_id': task_id
        })

    except Exception as e:
        print(f"[ERROR] 处理视频延长请求失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
def handle_extend_task_status(task, task_data, parent_task):
    """处理延长任务的状态"""
    if 'extend' in task.get('parameters', {}).get('operation', ''):
        task_result = task_data.get('task_result', {})
        videos = task_result.get('videos', [])
        # 继承原始视频的下载路径
        if videos and parent_task:
            parent_video = next(
                (v for v in parent_task.get('videos', []) 
                 if v['id'] == task.get('parent_video_id')),
                None
            )
            if parent_video:
                for video in videos:
                    video['local_url'] = parent_video.get('local_url')
                    video['downloaded'] = True
    
@app.route('/check_status/<task_id>', methods=['GET'])
def check_status(task_id):
    """检查特定任务的状态"""
    try:
        downloaded_count = 0  # 初始化下载计数器
        print(f"\n[DEBUG] ====== 开始检查任务状态 {task_id} ======")
        status_data = check_task_status(task_id)
        
        if 'error' in status_data:
            print(f"[ERROR] 获取任务状态失败: {status_data['error']}")
            return jsonify(status_data), 500
            
        if status_data.get('code') != 0:
            print(f"[ERROR] API返回错误: {status_data.get('message', '未知错误')}")
            return jsonify(status_data), 400
        
        # 更新任务状态
        tasks = load_tasks()
        updated = False
        
        for task in tasks:
            if task['task_id'] == task_id:
                # 获取任务数据
                task_data = status_data.get('data', {})
                task_status = task_data.get('task_status', 'unknown')
                task_status_msg = task_data.get('task_status_msg', '')
                print(f"[DEBUG] 更新任务状态: {task_status} ({task_status_msg})")
                
                task['status'] = task_status
                task['status_msg'] = task_msg
                
                # 如果任务成功且有视频信息
                if task_status == 'succeed':
                    task_result = task_data.get('task_result', {})
                    videos = task_result.get('videos', [])
                    
                    if videos:
                        print(f"[DEBUG] 发现 {len(videos)} 个视频")
                        task['videos'] = []
                        
                        for video in videos:
                            video_info = {
                                'id': video.get('id', ''),
                                'url': video.get('url', ''),
                                'duration': video.get('duration', '0'),
                                'local_url': None,
                                'downloaded': False
                            }
                            
                            print(f"[DEBUG] 视频信息:")
                            print(f"[DEBUG] - ID: {video_info['id']}")
                            print(f"[DEBUG] - URL: {video_info['url']}")
                            print(f"[DEBUG] - 时长: {video_info['duration']}")
                            
                            if video_info['url']:
                                # 检查是否已下载过
                                for old_video in task.get('videos', []):
                                    if old_video.get('id') == video_info['id'] and old_video.get('downloaded'):
                                        video_info['downloaded'] = True
                                        video_info['local_url'] = old_video.get('local_url')
                                        print(f"[DEBUG] 视频已下载过，跳过下载")
                                        break
                                else:
                                    local_url = download_video(video_info['url'], f"{task_id}_{video_info['id']}", force_download=False)
                                    if local_url:
                                        video_info['local_url'] = local_url
                                        video_info['downloaded'] = True
                                        downloaded_count += 1
                                        print(f"[DEBUG] 视频下载成功: {local_url}")
                                    else:
                                        print(f"[WARNING] 视频下载失败")
                            else:
                                print(f"[WARNING] 视频URL为空")
                                    
                            task['videos'].append(video_info)
                    else:
                        print("[WARNING] 任务成功但没有视频信息")
                
                updated = True
                break
        
        if updated:
            print("[DEBUG] 保存更新后的任务记录")
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        
        print(f"[DEBUG] ====== 完成检查任务状态 {task_id} ======\n")
        return jsonify(status_data)
    except Exception as e:
        print(f"[ERROR] 检查状态出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/static/videos/<filename>')
def serve_video(filename):
    """提供视频文件访问"""
    return send_from_directory(VIDEOS_DIR, filename)
@app.route('/static/images/<filename>')
def serve_image(filename):
    """提供图片文件访问"""
    return send_from_directory('static/images', filename)
@app.route('/batch_update', methods=['POST'])
def batch_update():
    """批量更新任务状态"""
    try:
        print("\n[DEBUG] ==================== 开始批量更新任务 ====================")
        
        # 1. 备份当前任务记录
        backup_result = backup_tasks()
        if backup_result:
            print(f"[DEBUG] 任务记录已备份")
        
        # 2. 加载本地任务
        local_tasks = load_tasks()
        local_tasks_dict = {task['task_id']: task for task in local_tasks}
        print(f"[DEBUG] 本地任务数: {len(local_tasks)}")
        
        # 3. 过滤需要更新的任务
        pending_tasks = [
            task for task in local_tasks 
            if (
                task['status'] != 'deleted' and  # 排除已删除的任务
                (task['status'] not in ['succeed', 'failed'] or  # 未完成的任务
                (task['status'] == 'succeed' and  # 已完成但视频未下载完成的任务
                 task.get('videos') and 
                 not all(video.get('downloaded', False) for video in task['videos'])))
            )
        ]
        
        if not pending_tasks:
            print("[DEBUG] 没有找到需要更新的任务")
            return jsonify({
                'success': True,
                'message': '没有需要更新的任务'
            })
        
        print(f"[DEBUG] 需要更新的任务数: {len(pending_tasks)}")
        
        # 4. 逐个更新任务状态
        updated_count = 0
        downloaded_count = 0
        
        for task in pending_tasks:
            task_id = task['task_id']
            print(f"\n[DEBUG] ---------- 处理任务 {task_id} ----------")
            
            # 获取任务详细信息
            status_data = check_task_status(task_id)
            if status_data.get('code') != 0 or not status_data.get('data'):
                print(f"[WARNING] 获取任务状态失败: {status_data.get('message', '未知错误')}")
                continue
                
            task_data = status_data['data']
            task_status = task_data.get('task_status')
            task_msg = task_data.get('task_status_msg', '')
            
            # 更新任务状态
            print(f"[DEBUG] 任务状态:")
            print(f"[DEBUG] - 原状态: {task.get('status', 'unknown')}")
            print(f"[DEBUG] - 新状态: {task_status}")
            print(f"[DEBUG] - 状态信息: {task_msg}")
            
            task['status'] = task_status
            task['status_msg'] = task_msg
            updated_count += 1
            
            # 处理视频下载
            if task_status == 'succeed':
                videos = task_data.get('task_result', {}).get('videos', [])
                if not videos:
                    print(f"[WARNING] 任务成功但没有视频信息")
                    continue
                    
                print(f"[DEBUG] 发现 {len(videos)} 个视频:")
                existing_videos = {v.get('id'): v for v in task.get('videos', [])}
                
                for i, video in enumerate(videos):
                    video_id = video.get('id')
                    if not video_id:
                        continue
                        
                    print(f"\n[DEBUG] 处理视频 {i+1}/{len(videos)}")
                    
                    # 检查是否已存在且已下载
                    if video_id in existing_videos and existing_videos[video_id].get('downloaded'):
                        print(f"[DEBUG] 视频已下载过，跳过下载")
                        continue
                    
                    # 检查任务是否已删除
                    if task.get('status') == 'deleted':
                        print(f"[DEBUG] 任务已被标记为删除，跳过下载")
                        continue
                    
                    # 创建或更新视频信息
                    video_info = {
                        'id': video_id,
                        'url': video.get('url', ''),
                        'duration': video.get('duration', '0'),
                        'local_url': None,
                        'downloaded': False
                    }
                    
                    # 下载视频
                    if video_info['url']:
                        local_url = download_video(video_info['url'], f"{task_id}_{video_id}", force_download=False)
                        if local_url:
                            video_info['local_url'] = local_url
                            video_info['downloaded'] = True
                            downloaded_count += 1
                            print(f"[DEBUG] 视频下载成功: {local_url}")
                        else:
                            print(f"[WARNING] 视频下载失败")
                    
                    # 更新任务的视频列表
                    if video_id in existing_videos:
                        for i, v in enumerate(task['videos']):
                            if v['id'] == video_id:
                                task['videos'][i] = video_info
                                break
                    else:
                        task['videos'].append(video_info)
        
        # 保存更新后的任务记录
        print("\n[DEBUG] 保存更新后的任务记录...")
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(local_tasks, f, ensure_ascii=False, indent=2)
        
        message = f'成功更新 {updated_count} 个任务，下载 {downloaded_count} 个视频'
        print(f"\n[DEBUG] 处理结果:")
        print(f"[DEBUG] - 更新任务数: {updated_count}")
        print(f"[DEBUG] - 下载视频数: {downloaded_count}")
        print(f"[DEBUG] ==================== 完成批量更新任务 ====================\n")
        
        return jsonify({
            'success': True,
            'message': message
        })
            
    except Exception as e:
        error_msg = f"批量更新出错: {str(e)}"
        print(f"[ERROR] 发生异常:")
        print(f"[ERROR] - 类型: {type(e).__name__}")
        print(f"[ERROR] - 信息: {str(e)}")
        print(f"[DEBUG] ==================== 批量更新任务异常结束 ====================\n")
        return jsonify({"error": error_msg}), 500
@app.route('/test_task_status', methods=['GET'])
def test_task_status():
    """测试特定任务状态"""
    try:
        print("\n[DEBUG] ==================== 开始测试特定任务状态 ====================")
        task_id = "CmJ8DGePZioAAAAAAxsdCg"
        print(f"[DEBUG] 测试任务ID: {task_id}")
        
        # 1. 检查API配置
        print("\n[DEBUG] 1. 检查API配置:")
        print(f"[DEBUG] - API基础地址: {API_BASE_URL}")
        print(f"[DEBUG] - API基础地址类型: {type(API_BASE_URL)}")
        print(f"[DEBUG] - API基础地址长度: {len(API_BASE_URL) if API_BASE_URL else 0}")
        print(f"[DEBUG] - API密钥前10位: {API_KEY[:10] if API_KEY else 'None'}")
        
        if not API_BASE_URL:
            raise Exception("API基础地址未配置")
        
        if not API_BASE_URL.startswith(('http://', 'https://')):
            raise Exception(f"API基础地址格式不正确: {API_BASE_URL}")
            
        # 2. 构建请求
        url = f"{API_BASE_URL}/kling/v1/videos/image2video/{task_id}"
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        
        print("\n[DEBUG] 2. 请求详情:")
        print(f"[DEBUG] - API基础地址: {API_BASE_URL}")
        print(f"[DEBUG] - 完整URL: {url}")
        print(f"[DEBUG] - 请求头: {headers}")
        
        # 3. 发送请求
        print("\n[DEBUG] 3. 发送请求...")
        response = requests.get(url, headers=headers, verify=False)
        
        print("\n[DEBUG] 4. 响应详情:")
        print(f"[DEBUG] - 状态码: {response.status_code}")
        print(f"[DEBUG] - 响应头: {dict(response.headers)}")
        
        # 5. 解析响应
        status_data = response.json()
        print("\n[DEBUG] 5. 响应内容:")
        print(f"[DEBUG] {json.dumps(status_data, ensure_ascii=False, indent=2)}")
        
        # 5. 如果任务成功，尝试下载视频
        task_status = status_data.get('data', {}).get('task_status', 'unknown')
        print(f"\n[DEBUG] 6. 任务状态: {task_status}")
        
        if task_status == 'succeed':
            print("\n[DEBUG] 7. 处理视频信息:")
            videos = status_data.get('data', {}).get('task_result', {}).get('videos', [])
            print(f"[DEBUG] - 发现 {len(videos)} 个视频")
            
            for i, video in enumerate(videos):
                print(f"\n[DEBUG] 处理第 {i+1} 个视频:")
                video_url = video.get('url')
                if video_url:
                    print(f"[DEBUG] - 视频URL: {video_url}")
                    print(f"[DEBUG] - 开始下载...")
                    local_url = download_video(video_url, f"{task_id}_{video.get('id', '')}")
                    if local_url:
                        print(f"[DEBUG] - 下载成功，本地路径: {local_url}")
                    else:
                        print(f"[DEBUG] - 下载失败")
                else:
                    print(f"[DEBUG] - 无效的视频URL")
        
        print(f"\n[DEBUG] ==================== 测试任务状态完成 ====================\n")
        return jsonify(status_data)
        
    except Exception as e:
        error_msg = f"测试任务状态失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] - 错误类型: {type(e).__name__}")
        print(f"[ERROR] - 错误信息: {str(e)}")
        return jsonify({"error": error_msg}), 500

@app.route('/delete_task/<task_id>', methods=['POST'])
def delete_task_route(task_id):
    """删除指定的任务记录和相关视频文件"""
    try:
        print(f"\n[DEBUG] ==================== 开始删除任务 ====================")
        print(f"[DEBUG] 任务ID: {task_id}")
        
        # 先备份当前任务记录
        backup_result = backup_tasks()
        if backup_result:
            print(f"[DEBUG] 任务记录已备份")
        
        # 执行删除操作
        result = delete_task(task_id)
        
        print(f"[DEBUG] 删除结果: {result['message']}")
        print(f"[DEBUG] ==================== 完成删除任务 ====================\n")
        
        # 返回结果
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        error_msg = f"删除任务失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    print("\n[INFO] ==================== 启动服务器 ====================")
    print("[INFO] 服务器配置:")
    print("[INFO] - 监听地址: 0.0.0.0")
    print("[INFO] - 监听端口: 5001")
    print("[INFO] - 调试模式: 开启")
    print("[INFO] 您可以通过以下地址访问服务:")
    print("[INFO] - 本机访问: http://127.0.0.1:5001")
    print("[INFO] - 局域网访问: http://<本机IP>:5001")
    print("[INFO] =================================================\n")
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
    