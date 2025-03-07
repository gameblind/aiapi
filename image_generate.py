from flask import Blueprint, request, jsonify
import requests
import json
import os
import base64
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re # 新增导入

# 加载环境变量
load_dotenv()

# 创建Blueprint
image_bp = Blueprint('image', __name__)

# 从环境变量获取配置
API_BASE_URL = os.getenv('API_BASE_URL')
API_KEY = os.getenv('API_KEY')

# 任务记录文件
IMAGE_TASKS_FILE = 'static/image_tasks.json'
IMAGE_SAVE_DIR = 'static/images'


def sync_local_images():
    """同步本地图片与任务记录
    扫描本地图片目录，确保所有图片都有对应的任务记录
    """
    try:
        print("[DEBUG] ==================== 开始同步本地图片与任务记录 ====================")
        
        # 确保目录存在
        if not os.path.exists(IMAGE_SAVE_DIR):
            os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)
            print(f"[DEBUG] 创建图片目录: {IMAGE_SAVE_DIR}")
            return []
        
        # 加载现有任务记录
        tasks = []
        if os.path.exists(IMAGE_TASKS_FILE):
            with open(IMAGE_TASKS_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
        tasks_dict = {task['task_id']: task for task in tasks}
        
        # 记录所有已知的本地图片路径
        known_local_images = set()
        for task in tasks:
            if task.get('images'):
                for img in task['images']:
                    if img.get('local_url'):
                        # 从URL中提取文件名
                        filename = os.path.basename(img['local_url'])
                        known_local_images.add(filename)
        
        # 扫描本地图片目录
        local_images = [f for f in os.listdir(IMAGE_SAVE_DIR) if os.path.isfile(os.path.join(IMAGE_SAVE_DIR, f))]
        print(f"[DEBUG] 发现本地图片: {len(local_images)}个")
        
        # 查找未记录的本地图片
        new_images = []
        for img_file in local_images:
            if img_file not in known_local_images:
                print(f"[DEBUG] 发现未记录的本地图片: {img_file}")
                new_images.append(img_file)
                
                # 尝试从文件名解析任务ID和索引
                # 文件名格式通常为: {task_id}_{index}.{ext}
                name_parts = os.path.splitext(img_file)[0].split('_')
                if len(name_parts) >= 2:
                    task_id = name_parts[0]
                    try:
                        index = int(name_parts[1])
                    except ValueError:
                        index = 0
                    
                    # 检查是否有对应的任务记录
                    if task_id in tasks_dict:
                        # 检查任务是否已被删除
                        task = tasks_dict[task_id]
                        if task.get('status') == 'deleted':
                            # 如果任务已被删除，删除本地图片
                            try:
                                os.remove(os.path.join(IMAGE_SAVE_DIR, img_file))
                                print(f"[DEBUG] 删除已删除任务的本地图片: {img_file}")
                                continue
                            except Exception as e:
                                print(f"[ERROR] 删除本地图片失败: {img_file} | 错误: {str(e)}")
                        
                        # 更新现有任务记录
                        if not task.get('images'):
                            task['images'] = []
                            
                        # 检查是否已有相同索引的图片
                        for img in task['images']:
                            if img.get('index') == index:
                                # 更新现有图片记录
                                img['local_url'] = f"/static/images/{img_file}"
                                img['downloaded'] = True
                                print(f"[DEBUG] 更新图片记录: {img_file}")
                                break
                        else:
                            # 添加新的图片记录
                            task['images'].append({
                                'index': index,
                                'url': "",  # 无法确定原始URL
                                'local_url': f"/static/images/{img_file}",
                                'downloaded': True
                            })
                            print(f"[DEBUG] 添加图片记录: {img_file}")
                    else:
                        # 创建新的任务记录
                        new_task = {
                            'task_id': task_id,
                            'external_task_id': f"local_{int(time.time())}",
                            'prompt': "本地导入图片",
                            'negative_prompt': "",
                            'status': "succeed",
                            'status_msg': "",
                            'parameters': {
                                'model_name': "unknown",
                                'n': 1,
                                'aspect_ratio': "unknown"
                            },
                            'images': [{
                                'index': index,
                                'url': "",
                                'local_url': f"/static/images/{img_file}",
                                'downloaded': True
                            }]
                        }
                        tasks.append(new_task)
                        tasks_dict[task_id] = new_task
                        print(f"[DEBUG] 创建新任务记录: {task_id}")
        
        # 保存更新后的任务记录
        if new_images:
            print(f"[DEBUG] 发现 {len(new_images)} 个新图片，更新任务记录")
            with open(IMAGE_TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        else:
            print("[DEBUG] 未发现新图片，无需更新任务记录")
            
        print("[DEBUG] ==================== 完成同步本地图片与任务记录 ====================\n")
        return tasks
        
    except Exception as e:
        print(f"[ERROR] 同步本地图片失败: {str(e)}")
        return []

def load_image_tasks():
    """加载图片任务记录并同步本地图片"""
    # 同步本地图片并获取更新后的任务记录
    return sync_local_images()

def save_image_task(task_record):
    """保存图片任务记录"""
    tasks = []
    
    # 检查目录是否存在
    if not os.path.exists(os.path.dirname(IMAGE_TASKS_FILE)):
        os.makedirs(os.path.dirname(IMAGE_TASKS_FILE))
    
    # 检查文件是否存在，如果存在则读取内容
    if os.path.exists(IMAGE_TASKS_FILE):
        try:
            with open(IMAGE_TASKS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # 确保文件不为空
                    tasks = json.loads(content)
                    if not isinstance(tasks, list):
                        tasks = []
        except (json.JSONDecodeError, Exception) as e:
            print(f"[WARNING] 读取任务记录文件失败: {str(e)}，将创建新文件")
            tasks = []
    
    tasks.append(task_record)
    with open(IMAGE_TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def check_image_task_status(task_id):
    """检查图片任务状态"""
    try:
        if not API_BASE_URL:
            raise Exception("API_BASE_URL未配置")
            
        url = f"{API_BASE_URL}/kling/v1/images/generations/{task_id}"
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            url,
            headers=headers,
            verify=False
        )
        
        return response.json()
        
    except Exception as e:
        print(f"[ERROR] 检查图片任务状态失败: {str(e)}")
        return {"error": str(e)}
import re  # 新增导入

def download_image(url, task_id):
    """下载图片到本地"""
    try:
        if not os.path.exists(IMAGE_SAVE_DIR):
            os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)

        # 清理特殊字符防止路径问题
        safe_task_id = re.sub(r'[^a-zA-Z0-9_-]', '_', task_id)
        
        # 获取文件扩展名
        response = requests.head(url, verify=False, timeout=5)
        content_type = response.headers.get('Content-Type', '')
        
        if 'jpeg' in content_type or 'jpg' in content_type:
            file_ext = '.jpg'
        elif 'png' in content_type:
            file_ext = '.png'
        else:
            file_ext = os.path.splitext(url)[1] or '.png'

        local_path = os.path.join(IMAGE_SAVE_DIR, f"{safe_task_id}{file_ext}")

        # 下载图片
        response = requests.get(url, stream=True, verify=False, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return f"/static/images/{safe_task_id}{file_ext}"

    except Exception as e:
        print(f"[ERROR] 下载失败 | URL: {url} | 错误: {str(e)}")
        return None

@image_bp.route('/text2img', methods=['POST'])
def generate_text2img():
    """文本生成图像接口"""
    try:
        print("\n[DEBUG] ========== 开始处理文本生成图像请求 ==========\n")
        
        # 获取请求参数
        data = request.form
        prompt = data.get('prompt', '')
        if not prompt:
            raise Exception("提示词不能为空")
        if len(prompt) > 500:
            raise Exception("提示词不能超过500个字符")
            
        negative_prompt = data.get('negative_prompt', '')
        if len(negative_prompt) > 200:
            raise Exception("负向提示词不能超过200个字符")
            
        # 获取其他参数
        n = int(data.get('n', '1'))
        if not 1 <= n <= 9:
            raise Exception("生成数量必须在1-9之间")
            
        aspect_ratio = data.get('aspect_ratio', '16:9')
        if aspect_ratio not in ['16:9', '9:16', '1:1', '4:3', '3:4', '3:2', '2:3']:
            raise Exception("不支持的图像纵横比")
        
        # 获取模型名称
        model_name = data.get('model', 'kling-v1')
        
        # 准备API调用
        if not API_BASE_URL:
            raise Exception("API_BASE_URL未配置")
            
        url = f"{API_BASE_URL}/kling/v1/images/generations"
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        
        # 构建请求数据
        external_task_id = f"custom_{int(time.time())}"
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "model_name": model_name,
            "n": n,
            "aspect_ratio": aspect_ratio
        }
        
        # 发送请求
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            verify=False
        )
        
        response_data = response.json()
        print(f"[DEBUG] API响应: {json.dumps(response_data, ensure_ascii=False)}")
        
        if response_data.get('code') == 0:
            task_id = response_data['data']['task_id']
            
            # 保存任务记录
            task_record = {
                'task_id': task_id,
                'external_task_id': external_task_id,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'status': 'submitted',
                'status_msg': '',
                'parameters': {
                    'model_name': model_name,
                    'n': n,
                    'aspect_ratio': aspect_ratio
                },
                'images': []
            }
            
            try:
                save_image_task(task_record)
                print("[DEBUG] 任务记录保存成功")
            except Exception as e:
                print(f"[ERROR] 保存任务记录失败: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': '任务已提交',
                'data': {'task_id': task_id, 'external_task_id': external_task_id}
            })
        else:
            return jsonify({
                'success': False,
                'message': response_data.get('message', '未知错误')
            })
            
    except Exception as e:
        print(f"[ERROR] 处理失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@image_bp.route('/img2img', methods=['POST'])
def generate_img2img():
    """图像生成图像接口"""
    try:
        print("\n[DEBUG] ========== 开始处理图像生成图像请求 ==========\n")
        
        # 获取请求参数
        if 'image' not in request.files:
            raise Exception("未找到图片文件")
            
        image_file = request.files['image']
        if not image_file.filename:
            raise Exception("图片文件名为空")
            
        # 获取其他参数
        prompt = request.form.get('prompt', '')
        if len(prompt) > 5000:
            raise Exception("提示词不能超过5000个字符")
            
        # 图生图模式下不支持负向提示词
        image_fidelity = float(request.form.get('image_fidelity', '0.5'))
        if not 0 <= image_fidelity <= 1:
            raise Exception("图像参考强度必须在0-1之间")
            
        # 获取生成数量
        n = int(request.form.get('n', '1'))
        if not 1 <= n <= 9:
            raise Exception("生成数量必须在1-9之间")
            
        # 获取图像纵横比
        aspect_ratio = request.form.get('aspect_ratio', '16:9')
        if aspect_ratio not in ['16:9', '9:16', '1:1', '4:3', '3:4', '3:2', '2:3']:
            raise Exception("不支持的图像纵横比")
        
        print(f"[DEBUG] 请求参数:\n")
        print(f"[DEBUG] - 图片: {image_file.filename}")
        print(f"[DEBUG] - 提示词: {prompt}")
        print(f"[DEBUG] - 参考强度: {image_fidelity}")
        print(f"[DEBUG] - 生成数量: {n}")
        print(f"[DEBUG] - 纵横比: {aspect_ratio}")
        
        # 转换图片为base64
        image_base64 = encode_image_to_base64(image_file)
        
        # 准备API调用
        if not API_BASE_URL:
            raise Exception("API_BASE_URL未配置")
            
        url = f"{API_BASE_URL}/kling/v1/images/generations"
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        
        # 获取模型名称
        model_name = request.form.get('model', 'kling-v1')
        
        # 构建请求数据
        external_task_id = f"custom_{int(time.time())}"
        payload = {
            "image": image_base64,
            "prompt": prompt,
            "model_name": model_name,
            "image_fidelity": image_fidelity,
            "n": n,
            "aspect_ratio": aspect_ratio
        }
        
        # 发送请求
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            verify=False
        )
        
        response_data = response.json()
        print(f"[DEBUG] API响应: {json.dumps(response_data, ensure_ascii=False)}")
        
        if response_data.get('code') == 0:
            task_id = response_data['data']['task_id']
            
            # 保存任务记录
            task_record = {
                'task_id': task_id,
                'external_task_id': external_task_id,
                'prompt': prompt,
                'negative_prompt': "",  # 图生图模式不支持负向提示词
                'status': 'submitted',
                'status_msg': '',
                'parameters': {
                    'model_name': model_name,
                    'image_fidelity': image_fidelity,
                    'n': n
                },
                'images': []
            }
            
            try:
                save_image_task(task_record)
                print("[DEBUG] 任务记录保存成功")
            except Exception as e:
                print(f"[ERROR] 保存任务记录失败: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': '任务已提交',
                'data': {'task_id': task_id, 'external_task_id': external_task_id}
            })
        else:
            return jsonify({
                'success': False,
                'message': response_data.get('message', '未知错误')
            })
            
    except Exception as e:
        print(f"[ERROR] 处理失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@image_bp.route('/batch_update', methods=['POST'])
def batch_update():
    """批量更新任务状态"""
    try:
        print("[DEBUG] ==================== 开始批量更新任务 ====================")
        
        # 获取所有任务
        tasks = load_image_tasks()
        
        # 过滤出需要更新的任务
        pending_tasks = [
            task for task in tasks 
            if (
                task['status'] != 'deleted' and  # 排除已删除的任务
                (task['status'] not in ['succeed', 'failed'] or  # 未完成的任务
                (task['status'] == 'succeed' and  # 已完成但图片未下载完成的任务
                 task.get('images') and 
                 not all(img.get('downloaded', False) for img in task['images'])))
            )
        ]
        
        if not pending_tasks:
            print("[DEBUG] 没有找到需要更新的任务")
            return jsonify({
                'success': True,
                'message': '没有需要更新的任务'
            })
            
        updated_count = 0
        downloaded_count = 0
        tasks_dict = {task['task_id']: task for task in tasks}
        
        # 处理每个任务的状态
        for task in pending_tasks:
            task_id = task['task_id']
            status_data = check_image_task_status(task_id)
            
            if status_data.get('code') == 0 and status_data.get('data'):
                task_data = status_data['data']
                task_status = task_data.get('task_status', 'unknown')
                task_msg = task_data.get('task_status_msg', '')
                
                print(f"[DEBUG] 任务状态 ({task_id}):")
                print(f"[DEBUG] - 原状态: {task.get('status', 'unknown')}")
                print(f"[DEBUG] - 新状态: {task_status}")
                
                task['status'] = task_status
                task['status_msg'] = task_msg
                tasks_dict[task_id] = task
                
                if task_status == 'succeed':
                    task_result = task_data.get('task_result', {})
                    images = task_result.get('images', [])
                    
                    if images:
                        print(f"[DEBUG] 发现 {len(images)} 个图片:")
                        task['images'] = []
                        
                        for i, image in enumerate(images):
                            print(f"\n[DEBUG] 处理图片 {i+1}/{len(images)}")
                            image_info = {
                                'index': image.get('index', 0),
                                'url': image.get('url', ''),
                                'local_url': None,
                                'downloaded': False
                            }
                            
                            print(f"[DEBUG] 图片信息:")
                            print(f"[DEBUG] - URL: {image_info['url']}")
                            
                            if image_info['url']:
                                # 检查是否已删除
                                if task.get('status') == 'deleted':
                                    print(f"[DEBUG] 任务已被标记为删除，跳过下载")
                                    continue
                                    
                                # 检查是否已下载过
                                for old_image in task.get('images', []):
                                    if old_image.get('url') == image_info['url'] and old_image.get('downloaded'):
                                        image_info['downloaded'] = True
                                        image_info['local_url'] = old_image.get('local_url')
                                        print(f"[DEBUG] 图片已下载过，跳过下载")
                                        break
                                else:
                                    local_url = download_image(image_info['url'], f"{task_id}_{image_info['index']}")
                                    if local_url:
                                        image_info['local_url'] = local_url
                                        image_info['downloaded'] = True
                                        downloaded_count += 1
                                        print(f"[DEBUG] 图片下载成功: {local_url}")
                                    else:
                                        print(f"[WARNING] 图片下载失败")
                            else:
                                print(f"[WARNING] 图片URL为空")
                                    
                            task['images'].append(image_info)
                    else:
                        print(f"[WARNING] 任务成功但没有图片信息")
                updated_count += 1
            else:
                print(f"[WARNING] 获取任务状态失败: {status_data.get('message', '未知错误')}")
        
        # 保存更新后的任务记录
        print("\n[DEBUG] 保存更新后的任务记录...")
        with open(IMAGE_TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(tasks_dict.values()), f, ensure_ascii=False, indent=2)
        
        message = f"成功更新 {updated_count} 个任务，下载 {downloaded_count} 个图片"
        print("\n[DEBUG] 处理结果:")
        print(f"[DEBUG] - 更新任务数: {updated_count}")
        print(f"[DEBUG] - 下载图片数: {downloaded_count}")
        print("[DEBUG] ==================== 完成批量更新任务 ====================\n")
        
        return jsonify({
            'success': True,
            'message': message,
            'data': list(tasks_dict.values())  # 返回所有任务数据
        })
            
    except Exception as e:
        error_msg = f"批量更新出错: {str(e)}"
        print("[ERROR] 发生异常:")
        print(f"[ERROR] - 类型: {type(e).__name__}")
        print(f"[ERROR] - 信息: {str(e)}")
        print("[DEBUG] ==================== 批量更新任务异常结束 ====================\n")
        return jsonify({"error": error_msg}), 500

@image_bp.route('/list', methods=['GET'])
def list_images():
    """获取图片列表"""
    try:
        tasks = load_image_tasks()
        return jsonify({
            'success': True,
            'data': tasks
        })
    except Exception as e:
        print(f"[ERROR] 获取图片列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@image_bp.route('/delete', methods=['POST'])
def delete_image():
    """删除图片接口"""
    try:
        print("\n[DEBUG] ========== 开始处理删除图片请求 ==========\n")
        
        # 获取请求参数
        data = request.get_json()
        if not data or 'image_url' not in data:
            raise Exception("未提供图片URL")
            
        image_url = data['image_url']
        if not image_url:
            raise Exception("图片URL为空")
            
        # 从URL中提取文件名
        filename = image_url.split('/')[-1]
        if not filename:
            raise Exception("无法从URL中提取文件名")
            
        # 构建图片文件路径
        image_path = os.path.join(IMAGE_SAVE_DIR, filename)
        
        # 更新任务记录
        tasks = load_image_tasks()
        updated = False
        
        # 检查文件是否存在
        if os.path.exists(image_path):
            # 删除图片文件
            os.remove(image_path)
            print(f"[DEBUG] 已删除图片文件: {filename}")
        else:
            print(f"[DEBUG] 图片文件不存在: {filename}，仅更新任务记录")

        
        for task in tasks:
            if task.get('images'):
                # 过滤掉已删除的图片
                task['images'] = [img for img in task['images'] 
                                if img.get('local_url') != f"/static/images/{filename}"]
                if len(task['images']) == 0:
                    task['status'] = 'deleted'
                    task['status_msg'] = '图片已删除'
                updated = True
                
        if updated:
            # 保存更新后的任务记录
            save_image_tasks(tasks)
            print("[DEBUG] 已更新任务记录")
        
        print("[DEBUG] ========== 完成删除图片请求 ==========\n")
        
        return jsonify({
            'success': True,
            'message': f'成功删除图片: {filename}'
        })
        
    except Exception as e:
        error_msg = f"删除图片失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

def encode_image_to_base64(image_file):
    """将图片文件转换为Base64编码"""
    try:
        # 读取图片文件内容
        image_content = image_file.read()
        
        # 检查文件大小（字节数转换为MB）
        file_size = len(image_content) / (1024 * 1024)
        if file_size > 10:
            raise Exception("图片文件大小不能超过10MB")
            
        # 转换为Base64编码
        base64_bytes = base64.b64encode(image_content)
        base64_string = base64_bytes.decode('utf-8')
        
        return base64_string
        
    except Exception as e:
        print(f"[ERROR] 图片转Base64失败: {str(e)}")
        raise Exception(f"图片转Base64失败: {str(e)}")

def save_image_tasks(tasks):
    """保存图片任务记录到文件"""
    with open(IMAGE_TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)