from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import os
import json
import base64
from datetime import datetime
import time
from config import API_KEY, API_BASE_URL, IMAGES_DIR
from services.file_service import load_image_tasks, save_image_tasks, save_image_task, download_image
from services.image_service import create_image_task, process_image_result

# 创建蓝图
images_bp = Blueprint('images', __name__)

@images_bp.route('/images')
def images():
    """图像生成页面"""
    return render_template('images.html')

@images_bp.route('/api/images', methods=['GET'])
def get_images():
    """获取所有图像任务"""
    tasks = load_image_tasks()
    return jsonify(tasks)

# 这里您可以添加更多图像相关路由
@images_bp.route('/api/images/<task_id>', methods=['GET'])
def get_image(task_id):
    """获取单个图像任务"""
    tasks = load_image_tasks()
    for task in tasks:
        if task.get('task_id') == task_id:
            return jsonify(task)
    return jsonify({"error": "任务不存在"}), 404

@images_bp.route('/api/images/<task_id>', methods=['DELETE'])
def delete_image(task_id):
    """删除图像任务"""
    tasks = load_image_tasks()
    for i, task in enumerate(tasks):
        if task.get('task_id') == task_id:
            # 标记为已删除
            tasks[i]['status'] = 'deleted'
            save_image_tasks(tasks)
            return jsonify({"status": "success"})
    return jsonify({"error": "任务不存在"}), 404

@images_bp.route('/api/images/generate', methods=['POST'])
def generate_image():
    """生成图像"""
    data = request.json
    
    # 验证必要参数
    if not data.get('prompt'):
        return jsonify({"error": "提示词不能为空"}), 400
    
    # 获取参数
    prompt = data.get('prompt')
    negative_prompt = data.get('negative_prompt', '')
    model_name = data.get('model', 'sd-turbo')
    width = int(data.get('width', 1024))
    height = int(data.get('height', 1024))
    steps = int(data.get('steps', 30))
    cfg_scale = float(data.get('cfg_scale', 7.0))
    seed = int(data.get('seed', -1))
    
    try:
        # 创建任务数据
        task_data = {
            'type': 'image_generation',
            'status': 'submitted',
            'parameters': {
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'model': model_name,
                'width': width,
                'height': height,
                'steps': steps,
                'cfg_scale': cfg_scale,
                'seed': seed
            },
            'images': []
        }
        
        # 创建图像生成任务
        response_data = create_image_task(
            prompt, negative_prompt, model_name, 
            width, height, steps, cfg_scale, seed
        )
        
        # 处理结果
        image_results = process_image_result(task_data, response_data)
        
        if image_results:
            return jsonify({"status": "success", "task_id": task_data.get('task_id'), "images": image_results})
        else:
            return jsonify({"error": task_data.get('error', '生成图像失败')}), 500
        
    except Exception as e:
        print(f"[ERROR] 生成图像失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@images_bp.route('/api/images/download', methods=['POST'])
def download_image_api():
    """下载图像"""
    data = request.json
    url = data.get('url')
    filename = data.get('filename')
    
    if not url or not filename:
        return jsonify({"error": "URL和文件名不能为空"}), 400
    
    try:
        local_url = download_image(url, filename, force_download=True)
        if local_url:
            return jsonify({"local_url": local_url})
        else:
            return jsonify({"error": "下载失败"}), 500
    except Exception as e:
        print(f"[ERROR] 下载图像失败: {str(e)}")
        return jsonify({"error": str(e)}), 500