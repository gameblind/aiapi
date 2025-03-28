from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import requests
import json
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from task_query import query_all_tasks
from task_backup import backup_tasks, delete_task
from image_generate import image_bp
from routes.file_routes import file_bp
from routes.web_routes import web_bp


# 禁用不安全请求警告
#from urllib3.exceptions import InsecureRequestWarning
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)
load_dotenv()

# 从环境变量获取配置
API_BASE_URL = os.getenv('API_BASE_URL')
API_KEY = os.getenv('API_KEY')

# 文件存储路径
TASKS_FILE = 'static/video_tasks_history.json'
IMAGE_TASKS_FILE = 'static/image_tasks.json'
VIDEOS_DIR = 'static/videos'
IMAGES_DIR = 'static/images'
STATIC_DIR = 'static'

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

# 应用启动时初始化文件
ensure_app_files()

# 注册Blueprint并添加调试日志
print("[DEBUG] 开始注册Blueprint...")
# 注册蓝图
#app.register_blueprint(api_bp)
app.register_blueprint(web_bp)
app.register_blueprint(file_bp)  # 添加文件路由
# 修改为与前端匹配的URL前缀
app.register_blueprint(image_bp, url_prefix='/generate_image')
print("[DEBUG] Blueprint注册完成，url_prefix='/generate_image'")

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
        return None

# 添加语音墙路由
@app.route('/voice')
def voice_wall():
    return render_template('voice.html')

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
    return render_template('images.html')

@app.route('/videos')
def videos():
    """视频墙页面"""
    return render_template('videos.html')
@app.route('/api/videos')
def api_videos():
    """获取视频列表API"""
    tasks = load_tasks()
    videos_list = []
    
    # 创建一个集合来存储已经处理过的视频文件名
    processed_videos = set()
    
    # 从任务记录中获取所有任务，包括处理中的任务
    for task in tasks:
        # 对于已完成的任务，添加其视频
        if task.get('status') == 'succeed' and task.get('videos'):
            for video in task.get('videos', []):
                if video.get('local_url'):
                    local_url = video.get('local_url')
                    video_filename = os.path.basename(local_url)
                    processed_videos.add(video_filename)
                    
                    videos_list.append({
                        'task_id': task.get('task_id'),
                        'video_id': video.get('id'),
                        'url': local_url,
                        'created_at': task.get('created_at'),
                        'prompt': task.get('prompt'),
                        'status': 'succeed',
                        'parameters': task.get('parameters', {})
                    })
        # 对于处理中的任务，也添加到列表中
        elif task.get('status') in ['submitted', 'processing']:
            videos_list.append({
                'task_id': task.get('task_id'),
                'video_id': None,  # 处理中的任务还没有视频ID
                'url': None,       # 处理中的任务还没有视频URL
                'created_at': task.get('created_at'),
                'prompt': task.get('prompt'),
                'status': task.get('status'),
                'parameters': task.get('parameters', {})
            })
    
    # 检查本地视频文件夹中是否有未在JSON中记录的视频
    if os.path.exists(VIDEOS_DIR):
        for filename in os.listdir(VIDEOS_DIR):
            if filename.endswith('.mp4') and filename not in processed_videos:
                # 提取任务ID作为视频ID的一部分
                task_id = filename.split('.')[0].split('_')[0]
                
                # 添加到视频列表中
                videos_list.append({
                    'task_id': task_id,
                    'video_id': 'local_' + task_id,
                    'url': f"/static/videos/{filename}",
                    'created_at': None,  # 没有创建时间信息
                    'prompt': f"本地视频: {filename}",  # 使用文件名作为提示
                    'status': 'succeed',  # 本地视频默认为成功状态
                    'parameters': {}      # 本地视频没有参数信息
                })
    
    # 反转列表顺序，使最新的视频排在前面
    videos_list.reverse()
    
    return jsonify({
        'success': True,
        'data': videos_list
    })

@app.route('/api/text2video', methods=['POST'])
def text2video():
    """处理文生视频请求"""
    try:
        print("\n[DEBUG] ==================== 开始处理文生视频请求 ====================\n")
        
        # 1. 检查请求数据
        print("\n[DEBUG] 1. 检查请求数据:")
        data = request.json
        if not data or 'prompt' not in data:
            raise Exception("未找到提示词数据")
        
        # 2. 获取并验证表单数据
        print("\n[DEBUG] 2. 获取表单数据:")
        prompt = data.get('prompt', '')[:2500]  # 限制提示词长度
        negative_prompt = data.get('negative_prompt', '')[:2500]  # 限制负向提示词长度
        duration = data.get('duration', '5')
        mode = data.get('mode', 'std')
        model_name = data.get('model_name', 'kling-v1')
        cfg_scale = float(data.get('cfg_scale', '0.5'))
        camera_control = data.get('camera_control', None)
        aspect_ratio = data.get('aspect_ratio', '16:9')
        
        # 验证参数
        if len(prompt) > 2500:
            raise Exception("提示词长度不能超过2500个字符")
        if len(negative_prompt) > 2500:
            raise Exception("负向提示词长度不能超过2500个字符")
        if cfg_scale < 0 or cfg_scale > 1:
            raise Exception("生成视频的自由度必须在0到1之间")
        if model_name not in ['kling-v1', 'kling-v1-6']:
            raise Exception("不支持的模型版本")
        if mode not in ['std', 'pro']:
            raise Exception("不支持的生成模式")
        if duration not in ['5', '10']:
            raise Exception("不支持的视频时长")
        if aspect_ratio not in ['16:9', '9:16', '1:1']:
            raise Exception("不支持的画面纵横比")
        
        print(f"[DEBUG] 请求参数详情:")
        print(f"[DEBUG] - 提示词: {prompt}")
        print(f"[DEBUG] - 负向提示词: {negative_prompt}")
        print(f"[DEBUG] - 时长: {duration}")
        print(f"[DEBUG] - 模式: {mode}")
        print(f"[DEBUG] - 模型: {model_name}")
        print(f"[DEBUG] - 自由度: {cfg_scale}")
        print(f"[DEBUG] - 画面纵横比: {aspect_ratio}")
        print(f"[DEBUG] - 摄像机控制: {camera_control}")
        
        # 3. 准备API调用
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
        
        # 4. 构建请求数据
        external_task_id = f"text2video_{int(time.time())}"
        payload = {
            "model_name": model_name,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "mode": mode,
            "duration": duration,
            "cfg_scale": cfg_scale,
            "aspect_ratio": aspect_ratio,
            "external_task_id": external_task_id
        }
        
        # 添加摄像机控制参数（如果有）
        if camera_control:
            payload["camera_control"] = camera_control
        
        # 5. 发送请求
        print("\n[DEBUG] 5. 发送API请求...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False
        )
        
        # 6. 处理响应
        print(f"[DEBUG] 收到响应:")
        print(f"[DEBUG] - 状态码: {response.status_code}")
        
        response_data = response.json()
        print(f"[DEBUG] - 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
        
        # 检查响应结果
        if response_data.get('code') != 0:
            error_msg = response_data.get('message', '未知错误')
            print(f"[ERROR] API返回错误: {error_msg}")
            raise Exception(f"API返回错误: {error_msg}")
            
        # 7. 获取任务ID
        task_id = response_data['data']['task_id']
        print(f"[DEBUG] 任务创建成功，任务ID: {task_id}")
        
        # 8. 保存任务信息
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
                'cfg_scale': cfg_scale,
                'aspect_ratio': aspect_ratio,
                'camera_control': camera_control
            },
            'videos': [],  # 确保包含空的视频数组
            'created_at': int(time.time() * 1000)  # 添加创建时间
        }
        
        # 使用原来的 save_task 函数保存任务
        save_task(task_record)
        print(f"[DEBUG] 任务信息已保存")
        
        print("\n[DEBUG] ==================== 文生视频请求处理完成 ====================\n")
        return jsonify({
            'success': True,
            'message': '任务已提交',
            'task_id': task_id
        })
        
    except Exception as e:
        print(f"[ERROR] 处理文生视频请求失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/video_detail/<task_id>/<video_id>')
def api_video_detail(task_id, video_id):
    """获取视频详情API"""
    tasks = load_tasks()
    
    # 检查是否为本地视频（视频ID以'local_'开头）
    if video_id.startswith('local_'):
        # 构建本地视频的详情信息
        video_filename = f"{task_id}.mp4"
        video_path = os.path.join(VIDEOS_DIR, video_filename)
        
        if os.path.exists(video_path):
            return jsonify({
                'success': True,
                'data': {
                    'task_id': task_id,
                    'video_id': video_id,
                    'url': f"/static/videos/{video_filename}",
                    'created_at': None,  # 本地视频没有创建时间
                    'prompt': f"本地视频: {video_filename}",
                    'status': 'succeed',
                    'model_name': '未知',
                    'duration': '未知',
                    'expiration_date': None
                }
            })
    
    # 常规视频处理逻辑
    for task in tasks:
        if task.get('task_id') == task_id:
            for video in task.get('videos', []):
                if video.get('id') == video_id:
                    return jsonify({
                        'success': True,
                        'data': {
                            'task_id': task.get('task_id'),
                            'video_id': video.get('id'),
                            'url': video.get('local_url'),
                            'created_at': task.get('created_at'),
                            'prompt': task.get('prompt'),
                            'status': task.get('status'),
                            'model_name': task.get('parameters', {}).get('model_name'),
                            'duration': video.get('duration'),
                            'expiration_date': task.get('expiration_date')
                        }
                    })
    
    return jsonify({
        'success': False,
        'message': '未找到视频'
    })

@app.route('/api/text2video_status/<task_id>')
def text2video_status(task_id):
    """获取文生视频任务状态API"""
    print(f"\n[DEBUG] ==================== 开始查询文生视频任务状态 ====================\n")
    print(f"[DEBUG] 任务ID: {task_id}")
    
    try:
        # 1. 首先检查本地任务记录
        tasks = load_tasks()
        print(f"[DEBUG] 加载了 {len(tasks)} 条本地任务记录")
        
        for task in tasks:
            if task.get('task_id') == task_id:
                print(f"[DEBUG] 在本地找到任务记录")
                print(f"[DEBUG] 任务状态: {task.get('status')}")
                
                # 如果任务已完成且有视频，检查是否已下载
                if task.get('status') == 'succeed' and task.get('videos'):
                    for video in task.get('videos', []):
                        if not video.get('downloaded'):
                            # 尝试下载视频
                            video_url = video.get('url')
                            if video_url:
                                print(f"[DEBUG] 尝试下载视频: {video_url}")
                                local_url = download_video(video_url, task_id)
                                if local_url:
                                    video['downloaded'] = True
                                    video['local_url'] = local_url
                    
                    # 保存更新后的任务记录
                    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(tasks, f, ensure_ascii=False, indent=2)
                
                print(f"[DEBUG] ==================== 完成查询文生视频任务状态 ====================\n")
                return jsonify({
                    'success': True,
                    'data': task
                })
        
        # 2. 如果本地没有找到，从API查询
        print(f"[DEBUG] 本地未找到任务记录，尝试从API查询")
        
        if not API_BASE_URL:
            raise Exception("API_BASE_URL未配置")
        if not API_KEY:
            raise Exception("API_KEY未配置")
            
        url = f"{API_BASE_URL}/kling/v1/videos/text2video/{task_id}"
        print(f"[DEBUG] API URL: {url}")
        
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        
        # 发送请求
        response = requests.get(
            url,
            headers=headers,
            verify=False
        )
        
        print(f"[DEBUG] 收到响应:")
        print(f"[DEBUG] - 状态码: {response.status_code}")
        
        response_data = response.json()
        print(f"[DEBUG] - 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
        
        # 检查响应结果
        if response_data.get('code') != 0:
            error_msg = response_data.get('message', '未知错误')
            print(f"[ERROR] API返回错误: {error_msg}")
            raise Exception(f"API返回错误: {error_msg}")
        
        # 3. 解析API返回的任务数据
        api_task_data = response_data.get('data', {})
        task_status = api_task_data.get('task_status', 'unknown')
        task_msg = api_task_data.get('task_status_msg', '')
        
        # 4. 构建任务记录
        task_record = {
            'task_id': task_id,
            'status': task_status,
            'status_msg': task_msg,
            'videos': []
        }
        
        # 5. 如果任务成功，处理视频信息
        if task_status == 'succeed':
            videos = api_task_data.get('task_result', {}).get('videos', [])
            for video_data in videos:
                video_id = video_data.get('id', '')
                video_url = video_data.get('url', '')
                
                # 尝试下载视频
                local_url = None
                if video_url:
                    local_url = download_video(video_url, f"{task_id}_{video_id}")
                
                # 添加视频信息
                task_record['videos'].append({
                    'id': video_id,
                    'url': video_url,
                    'downloaded': bool(local_url),
                    'local_url': local_url
                })
        
        # 6. 保存任务记录
        save_task(task_record)
        print(f"[DEBUG] 已保存新的任务记录")
        
        print(f"[DEBUG] ==================== 完成查询文生视频任务状态 ====================\n")
        return jsonify({
            'success': True,
            'data': task_record
        })
        
    except Exception as e:
        print(f"[ERROR] 查询文生视频任务状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/task_status/<task_id>')
def api_task_status(task_id):
    """获取任务状态API"""
    print(f"\n[DEBUG] 开始查询任务状态: {task_id}")
    tasks = load_tasks()
    
    # 查找本地任务记录
    local_task = None
    for task in tasks:
        if task.get('task_id') == task_id:
            local_task = task
            print(f"[DEBUG] 在本地找到任务记录，状态: {task.get('status')}")
            break
    
    # 如果找到本地任务记录
    if local_task:
        # 如果任务状态是已完成或失败，直接返回本地记录
        if local_task.get('status') in ['succeed', 'failed']:
            print(f"[DEBUG] 任务已完成，直接返回本地记录")
            return jsonify({
                'success': True,
                'data': local_task
            })
        
        # 如果任务状态是提交或处理中，从API查询最新状态
        print(f"[DEBUG] 任务状态为 {local_task.get('status')}，从API查询最新状态")
        status_data = check_task_status(task_id)
        
        # 如果API查询成功
        if status_data.get('code') == 0:
            # 获取API返回的任务数据
            api_task_data = status_data.get('data', {})
            api_task_status = api_task_data.get('task_status', 'unknown')
            
            print(f"[DEBUG] API返回任务状态: {api_task_status}")
            
            # 更新本地任务状态
            local_task['status'] = api_task_status
            local_task['status_msg'] = api_task_data.get('task_status_msg', '')
            
            # 如果任务成功，处理视频信息
            if api_task_status == 'succeed':
                task_result = api_task_data.get('task_result', {})
                videos = task_result.get('videos', [])
                
                # 更新视频信息
                if videos:
                    print(f"[DEBUG] 发现 {len(videos)} 个视频")
                    
                    # 创建新的视频列表
                    new_videos = []
                    
                    for video in videos:
                        video_id = video.get('id', '')
                        video_url = video.get('url', '')
                        
                        # 尝试下载视频
                        local_url = None
                        if video_url:
                            local_url = download_video(video_url, f"{task_id}_{video_id}")
                        
                        # 添加视频信息
                        new_videos.append({
                            'id': video_id,
                            'url': video_url,
                            'duration': video.get('duration', '0'),
                            'downloaded': bool(local_url),
                            'local_url': local_url
                        })
                    
                    # 更新任务的视频列表
                    local_task['videos'] = new_videos
            
            # 保存更新后的任务记录
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
            
            print(f"[DEBUG] 返回更新后的任务记录")
            return jsonify({
                'success': True,
                'data': local_task
            })
        else:
            # API查询失败，返回本地记录
            print(f"[WARNING] API查询失败，返回本地记录")
            return jsonify({
                'success': True,
                'data': local_task
            })
    
    # 如果在本地找不到任务，尝试从API查询
    print(f"[DEBUG] 本地未找到任务记录，尝试从API查询")
    status_data = check_task_status(task_id)
    if status_data.get('code') == 0:
        print(f"[DEBUG] API查询成功，返回API数据")
        return jsonify({
            'success': True,
            'data': status_data.get('data', {})
        })
    
    print(f"[DEBUG] 未找到任务")
    return jsonify({
        'success': False,
        'message': '未找到任务'
    })

# 添加图生视频的API调用路由
@app.route('/generate', methods=['POST'])
def generate_video():
    """处理图生视频请求"""
    try:
        print("\n[DEBUG] ==================== 开始处理图生视频请求 ====================")
        
        # 1. 检查请求数据
        print("\n[DEBUG] 1. 检查请求数据:")
        data = request.json
        if not data or 'image' not in data:
            raise Exception("未找到图片数据")
        
        # 2. 获取并验证表单数据
        print("\n[DEBUG] 2. 获取表单数据:")
        image_base64 = data['image']
        image_tail_base64 = data.get('image_tail', '')
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
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False
        )
        
        # 6. 处理响应
        print(f"[DEBUG] 收到响应:")
        print(f"[DEBUG] - 状态码: {response.status_code}")
        
        response_data = response.json()
        print(f"[DEBUG] - 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
        
        # 检查响应结果
        if response_data.get('code') != 0:
            error_msg = response_data.get('message', '未知错误')
            print(f"[ERROR] API返回错误: {error_msg}")
            raise Exception(f"API返回错误: {error_msg}")
            
        # 7. 获取任务ID
        task_id = response_data['data']['task_id']
        print(f"[DEBUG] 任务创建成功，任务ID: {task_id}")
        
        # 8. 保存任务信息
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
            'videos': [],  # 确保包含空的视频数组
            'has_image_url_data': bool(image_base64) or bool(image_tail_base64)
        }
        
        # 使用原来的 save_task 函数保存任务
        save_task(task_record)
        print(f"[DEBUG] 任务信息已保存")
        
        print("\n[DEBUG] ==================== 图生视频请求处理完成 ====================")
        return jsonify({
            'success': True,
            'message': '任务已提交',
            'task_id': task_id
        })
        
    except Exception as e:
        print(f"[ERROR] 处理图生视频请求失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 修改保存任务信息的代码，避免保存 base64 数据：
def save_task_info(task_id, data):
    # 创建任务记录，但不保存base64图片数据
    task_info = {
        "task_id": task_id,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
        "prompt": data.get("prompt", ""),
        "negative_prompt": data.get("negative_prompt", ""),
        "model_name": data.get("model_name", ""),
        "mode": data.get("mode", ""),
        "duration": data.get("duration", ""),
        "cfg_scale": data.get("cfg_scale", ""),
        # 只记录是否有图片，不保存base64数据
        "has_image": bool(data.get("image", "")),
        "has_image_tail": bool(data.get("image_tail", ""))
    }
    
    # 读取现有任务
    tasks = []
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            try:
                tasks = json.load(f)
            except json.JSONDecodeError:
                tasks = []
    
    # 添加新任务并保存
    tasks.append(task_info)
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    return task_info
@app.route('/api/extend/<video_uuid>', methods=['POST'])
def api_extend_video(video_uuid):
    """处理视频延长请求 - 直接使用视频UUID"""
    try:
        print(f"\n[DEBUG] ==================== 开始处理视频延长请求 (UUID直接调用) ====================")
        
        # 1. 获取请求数据
        print(f"\n[DEBUG] 1. 获取请求数据:")
        print(f"[DEBUG] 视频UUID: {video_uuid}")
        
        if request.is_json:
            data = request.get_json() or {}
            print(f"[DEBUG] 收到JSON数据: {json.dumps(data, ensure_ascii=False)}")
        else:
            # 尝试从表单数据或查询参数获取
            data = request.form.to_dict() or request.args.to_dict() or {}
            print(f"[DEBUG] 收到非JSON数据: {data}")
        
        # 2. 获取并验证参数
        print(f"\n[DEBUG] 2. 获取并验证参数:")
        prompt = data.get('prompt', '')
        external_task_id = data.get('external_task_id')  # 可选参数，仅用于日志记录
        
        print(f"[DEBUG] 提示词: {prompt}")
        if external_task_id:
            print(f"[DEBUG] 外部任务ID: {external_task_id}")
        
        # 处理提示词长度
        if len(prompt) > 2500:
            print(f"[WARNING] 提示词超长，已截断: {len(prompt)} -> 2500")
            prompt = prompt[:2500]
        
        # 3. 准备API调用
        print(f"\n[DEBUG] 3. 准备API调用:")
        if not API_BASE_URL:
            raise Exception("API_BASE_URL未配置")
        if not API_KEY:
            raise Exception("API_KEY未配置")
        
        # 4. 发送API请求
        print(f"\n[DEBUG] 4. 发送API请求:")
        from video_extend import create_extend_task
        response_data = create_extend_task(video_uuid, prompt)
        
        # 5. 处理响应
        print(f"\n[DEBUG] 5. 处理响应:")
        print(f"[DEBUG] 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
        
        # 检查响应
        if "error" in response_data:
            raise Exception(f"API错误: {response_data['error']}")
            
        if not response_data or response_data.get('code') != 0:
            error_msg = response_data.get('message', '未知错误') if response_data else '无响应数据'
            raise Exception(f"API返回错误: {error_msg}")
        
        # 6. 获取任务ID
        task_id = response_data['data']['task_id']
        print(f"[DEBUG] 任务创建成功，任务ID: {task_id}")
        
        # 7. 查找原始视频所属的任务信息
        print(f"\n[DEBUG] 7. 查找原始视频任务信息:")
        tasks = load_tasks()
        original_task = None
        original_video = None
        
        for task in tasks:
            for video in task.get('videos', []):
                if video.get('id') == video_uuid:
                    original_task = task
                    original_video = video
                    break
            if original_task:
                break
        
        if original_task:
            print(f"[DEBUG] 找到原始任务: {original_task.get('task_id')}")
        else:
            print(f"[WARNING] 未找到原始任务信息")
        
        # 8. 创建并保存任务记录
        print(f"\n[DEBUG] 8. 创建并保存任务记录:")
        if not external_task_id:
            external_task_id = f"extend_{int(time.time())}"
            
        task_record = {
            'task_id': task_id,
            'external_task_id': external_task_id,
            'prompt': prompt,
            'negative_prompt': original_task.get('negative_prompt', '') if original_task else '',
            'status': 'submitted',
            'status_msg': '',
            'parameters': {
                'model_name': original_task.get('parameters', {}).get('model_name', 'kling-v1') if original_task else 'kling-v1',
                'duration': '5',
                'mode': 'std',
                'cfg_scale': 0.5,
                'operation': 'extend',  # 添加标记，表明这是延长任务
                'original_video_id': video_uuid,  # 记录原始视频ID
                'original_task_id': original_task.get('task_id') if original_task else None  # 记录原始任务ID
            },
            'videos': [],  # 初始化为空视频列表
            'has_image_url_data': original_task.get('has_image_url_data', True) if original_task else True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'expiration_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        }
        
        # 保存任务记录
        save_task(task_record)
        print(f"[DEBUG] 延长任务记录已保存到 video_tasks_history.json")
        
        print(f"\n[DEBUG] ==================== 视频延长请求处理完成 ====================")
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

# 简化版的视频延长路由
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
        #if "-" in video_id:
        print(f"[DEBUG] 原始video_id: {video_id}")
         #   video_id = video_id.split("-")[0] if "-" in video_id else video_id
        #    print(f"[DEBUG] 处理后video_id: {video_id}")

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
        
         # 查找原始视频所属的任务信息
        tasks = load_tasks()
        original_task = None
        original_video = None
        
        for task in tasks:
            for video in task.get('videos', []):
                if video.get('id') == video_id:
                    original_task = task
                    original_video = video
                    break
            if original_task:
                break
        
        # 创建延长任务记录
        if not external_task_id:
            external_task_id = f"custom_{int(time.time())}"
            
        task_record = {
            'task_id': task_id,
            'external_task_id': external_task_id,
            'prompt': prompt,
            'negative_prompt': original_task.get('negative_prompt', '') if original_task else '',
            'status': 'submitted',
            'status_msg': '',
            'parameters': {
                'model_name': original_task.get('parameters', {}).get('model_name', 'kling-v1') if original_task else 'kling-v1',
                'duration': '5',
                'mode': 'std',
                'cfg_scale': 0.5,
                'operation': 'extend',  # 添加标记，表明这是延长任务
                'original_video_id': video_id,  # 记录原始视频ID
                'original_task_id': original_task.get('task_id') if original_task else None  # 记录原始任务ID
            },
            'videos': [],  # 初始化为空视频列表
            'has_image_url_data': original_task.get('has_image_url_data', True) if original_task else True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'expiration_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        }
        
        # 保存任务记录
        save_task(task_record)
        print(f"[DEBUG] 延长任务记录已保存到 video_tasks_history.json")
        
        print("\n[DEBUG] ==================== 视频延长请求处理完成 ====================")
        return jsonify({
            'success': True,
            'message': '延长任务已提交',
            'task_id': task_id
        })
    
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
                task['status_msg'] = task_status_msg
                
                # 如果任务成功且有视频信息
                if task_status == 'succeed':
                    task_result = task_data.get('task_result', {})
                    videos = task_result.get('videos', [])
                    
                    if videos:
                        print(f"[DEBUG] 发现 {len(videos)} 个视频")
                        
                        # 创建现有视频的映射
                        existing_videos = {v.get('id'): v for v in task.get('videos', [])}
                        
                        # 创建新的视频列表
                        new_videos = []
                        
                        for video in videos:
                            video_id = video.get('id', '')
                            video_info = {
                                'id': video_id,
                                'url': video.get('url', ''),
                                'duration': video.get('duration', '0'),
                                'local_url': None,
                                'downloaded': False
                            }
                            
                            print(f"[DEBUG] 视频信息:")
                            print(f"[DEBUG] - ID: {video_info['id']}")
                            print(f"[DEBUG] - URL: {video_info['url']}")
                            print(f"[DEBUG] - 时长: {video_info['duration']}")
                            
                            # 检查是否已存在且已下载
                            if video_id in existing_videos and existing_videos[video_id].get('downloaded'):
                                # 保留已下载的信息
                                video_info['downloaded'] = True
                                video_info['local_url'] = existing_videos[video_id].get('local_url')
                                print(f"[DEBUG] 视频已下载过，保留下载信息")
                            # 下载视频
                            elif video_info['url']:
                                local_url = download_video(video_info['url'], f"{task_id}_{video_id}", force_download=False)
                                if local_url:
                                    video_info['local_url'] = local_url
                                    video_info['downloaded'] = True
                                    downloaded_count += 1
                                    print(f"[DEBUG] 视频下载成功: {local_url}")
                                else:
                                    print(f"[WARNING] 视频下载失败")
                            else:
                                print(f"[WARNING] 视频URL为空")
                                    
                            new_videos.append(video_info)
                            
                        # 更新任务的视频列表
                        task['videos'] = new_videos
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
            
            # 判断任务类型
            is_extend_task = False
            if task.get('parameters', {}).get('operation') == 'extend' or 'parent_video_id' in task:
                is_extend_task = True
                print(f"[DEBUG] 检测到延长视频任务")
            
            try:
                # 获取任务详细信息
                status_data = check_task_status(task_id)
                
                # 检查API响应是否有效
                if not isinstance(status_data, dict):
                    print(f"[WARNING] 获取任务状态返回无效数据类型: {type(status_data)}")
                    continue
                    
                if 'error' in status_data:
                    print(f"[WARNING] 获取任务状态失败: {status_data.get('error')}")
                    continue
                    
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
                    # 根据任务类型处理视频信息
                    if is_extend_task:
                        # 处理延长视频任务
                        handle_extend_task_videos(task, task_data)
                    else:
                        # 处理普通视频任务
                        handle_normal_task_videos(task, task_data)
                        
                    # 计算下载的视频数量
                    for video in task.get('videos', []):
                        if video.get('downloaded') and not video.get('counted', False):
                            downloaded_count += 1
                            video['counted'] = True
            
            except Exception as e:
                print(f"[WARNING] 处理任务 {task_id} 时出错: {str(e)}")
                continue
        
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
        import traceback
        print(f"[ERROR] - 堆栈: {traceback.format_exc()}")
        print(f"[DEBUG] ==================== 批量更新任务异常结束 ====================\n")
        return jsonify({"error": error_msg}), 500

def handle_normal_task_videos(task, task_data):
    """处理普通视频任务的视频信息"""
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

@app.route('/api/pull_video/<task_id>/<video_id>', methods=['POST'])
def pull_video(task_id, video_id):
    """从云端重新拉取视频"""
    try:
        print(f"\n[DEBUG] ==================== 开始拉取视频 ====================")
        print(f"[DEBUG] 任务ID: {task_id}")
        print(f"[DEBUG] 视频ID: {video_id}")
        
        tasks = load_tasks()
        
        # 查找对应的任务和视频
        for task in tasks:
            if task.get('task_id') == task_id:
                for video in task.get('videos', []):
                    if video.get('id') == video_id:
                        # 获取视频URL
                        video_url = video.get('url')
                        if not video_url:
                            print(f"[ERROR] 未找到视频URL")
                            return jsonify({
                                'success': False,
                                'message': '未找到视频URL'
                            })
                        
                        print(f"[DEBUG] 视频URL: {video_url}")
                        print(f"[DEBUG] 开始强制重新下载视频...")
                        
                        # 强制重新下载视频
                        local_url = download_video(video_url, f"{task_id}_{video_id}", force_download=True)
                        if local_url:
                            # 更新视频状态
                            video['downloaded'] = True
                            video['local_url'] = local_url
                            
                            # 保存更新后的任务记录
                            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                                json.dump(tasks, f, ensure_ascii=False, indent=2)
                            
                            print(f"[DEBUG] 视频拉取成功: {local_url}")
                            print(f"[DEBUG] ==================== 完成拉取视频 ====================\n")
                            
                            return jsonify({
                                'success': True,
                                'message': '视频拉取成功',
                                'local_url': local_url
                            })
                        else:
                            print(f"[ERROR] 视频下载失败")
                            print(f"[DEBUG] ==================== 拉取视频失败 ====================\n")
                            
                            return jsonify({
                                'success': False,
                                'message': '视频下载失败'
                            })
        
        print(f"[ERROR] 未找到对应的任务或视频")
        print(f"[DEBUG] ==================== 拉取视频失败 ====================\n")
        
        return jsonify({
            'success': False,
            'message': '未找到对应的任务或视频'
        })
    
    except Exception as e:
        error_msg = f"拉取视频失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[DEBUG] ==================== 拉取视频异常 ====================\n")
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
    