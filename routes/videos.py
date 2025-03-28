from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import os
import json
import base64
from datetime import datetime, timedelta
import time
import requests
from config import API_KEY, API_BASE_URL, VIDEOS_DIR
from services.file_service import load_tasks, save_tasks, save_task, download_video
from services.video_service import check_task_status, create_text2video_task, create_image2video_task, create_extend_task
from services.video_service import handle_normal_task_videos, handle_extend_task_videos

# 创建蓝图
videos_bp = Blueprint('videos', __name__)

@videos_bp.route('/videos')
def videos():
    """视频生成页面"""
    return render_template('videos.html')

@videos_bp.route('/api/videos', methods=['GET'])
def get_videos():
    """获取所有视频任务"""
    tasks = load_tasks()
    # 修改返回格式，确保与前端期望的格式一致
    return jsonify({"success": True, "data": tasks})

@videos_bp.route('/api/videos/<task_id>', methods=['GET'])
def get_video(task_id):
    """获取单个视频任务"""
    tasks = load_tasks()
    for task in tasks:
        if task.get('task_id') == task_id:
            return jsonify({"success": True, "data": task})
    return jsonify({"success": False, "message": "任务不存在"}), 404

@videos_bp.route('/api/video_detail/<task_id>/<video_id>', methods=['GET'])
def api_video_detail(task_id, video_id):
    """获取视频详情"""
    print(f"[DEBUG] 获取视频详情: 任务ID={task_id}, 视频ID={video_id}")
    
    tasks = load_tasks()
    for task in tasks:
        if task.get('task_id') == task_id:
            # 查找匹配的视频
            for video in task.get('videos', []):
                if video.get('id') == video_id:
                    # 添加任务的提示词到视频信息中
                    video_data = video.copy()
                    video_data['prompt'] = task.get('prompt', '')
                    video_data['negative_prompt'] = task.get('negative_prompt', '')
                    video_data['model_name'] = task.get('model_name', '')
                    
                    print(f"[DEBUG] 找到视频: {video_data}")
                    return jsonify({"success": True, "data": video_data})
            
            print(f"[ERROR] 未找到视频: 任务ID={task_id}, 视频ID={video_id}")
            return jsonify({"success": False, "message": "视频不存在"})
    
    print(f"[ERROR] 未找到任务: 任务ID={task_id}")
    return jsonify({"success": False, "message": "任务不存在"})
@videos_bp.route('/api/videos/<task_id>/status', methods=['GET'])
def get_video_status(task_id):
    """获取视频任务状态"""
    print(f"\n[DEBUG] 获取视频任务状态: {task_id}")
    
    # 首先检查本地任务记录
    tasks = load_tasks()
    task = None
    
    for t in tasks:
        if t.get('task_id') == task_id:
            task = t
            break
    
    if not task:
        print(f"[ERROR] 任务不存在: {task_id}")
        return jsonify({"error": "任务不存在"}), 404
    
    # 如果任务已经完成或失败，直接返回状态
    if task.get('status') in ['completed', 'failed', 'deleted']:
        print(f"[DEBUG] 任务已经处于终态: {task.get('status')}")
        return jsonify({"status": task.get('status'), "task": task})
    
    # 检查任务状态
    status_data = check_task_status(task_id)
    
    # 检查API响应是否有错误
    if 'error' in status_data:
        print(f"[ERROR] 检查任务状态失败: {status_data.get('error')}")
        return jsonify({"error": status_data.get('error')}), 500
    
    # 检查API响应码
    if status_data.get('code') != 0:
        error_msg = status_data.get('message', '未知错误')
        print(f"[ERROR] API返回错误: {error_msg}")
        # 更新任务状态
        task['status'] = 'failed'
        task['error'] = error_msg
        save_tasks(tasks)
        return jsonify({"status": "failed", "error": error_msg, "task": task})
    
    # 获取任务数据
    task_data = status_data.get('data', {})
    task_status = task_data.get('task_status', 'unknown')
    task_msg = task_data.get('task_status_msg', '')
    
    # 更新任务状态
    if task_status == 'succeed':
        print(f"[DEBUG] 任务成功完成")
        task['status'] = 'completed'
        
        # 检查是否为延长视频任务
        if task.get('parameters', {}).get('operation') == 'extend' or 'parent_video_id' in task:
            print(f"[DEBUG] 处理延长视频任务")
            handle_extend_task_videos(task, task_data)
        else:
            print(f"[DEBUG] 处理普通视频任务")
            handle_normal_task_videos(task, task_data)
            
    elif task_status == 'failed':
        print(f"[DEBUG] 任务失败: {task_msg}")
        task['status'] = 'failed'
        task['error'] = task_msg
    else:
        print(f"[DEBUG] 任务进行中: {task_status} - {task_msg}")
        task['status'] = 'processing'
        task['progress'] = task_msg
    
    # 保存更新后的任务记录
    save_tasks(tasks)
    
    return jsonify({"status": task['status'], "task": task})

@videos_bp.route('/api/videos/<task_id>', methods=['DELETE'])
def delete_video(task_id):
    """删除视频任务"""
    tasks = load_tasks()
    for i, task in enumerate(tasks):
        if task.get('task_id') == task_id:
            # 标记为已删除
            tasks[i]['status'] = 'deleted'
            save_tasks(tasks)
            return jsonify({"status": "success"})
    return jsonify({"error": "任务不存在"}), 404

# 添加与原始路径一致的路由别名
# 确保 task_status 路由与前端调用一致

@videos_bp.route('/api/task_status/<task_id>', methods=['GET'])
def api_task_status(task_id):
    """任务状态检查（兼容原始路径）"""
    print(f"[DEBUG] 检查任务状态: {task_id}")
    return get_video_status(task_id)

@videos_bp.route('/generate', methods=['POST'])
def generate_video():
    """创建图生视频任务（兼容原始路径）"""
    data = request.json
    
    # 验证必要参数
    if not data.get('image'):
        return jsonify({"success": False, "message": "图片不能为空"}), 400
    
    # 获取参数
    image_base64 = data.get('image')
    image_tail_base64 = data.get('image_tail')
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    model_name = data.get('model_name', 'kling-v1')
    
    try:
        # 创建图生视频任务
        response_data = create_image2video_task(
            image_base64, image_tail_base64, prompt, negative_prompt, model_name
        )
        
        # 检查响应是否成功
        if response_data.get('code') != 0:
            error_msg = response_data.get('message', '未知错误')
            return jsonify({"success": False, "message": error_msg}), 500
        
        # 获取任务ID
        task_id = response_data.get('data', {}).get('task_id')
        if not task_id:
            return jsonify({"success": False, "message": "创建任务失败，未返回任务ID"}), 500
        
        # 保存任务记录
        task_data = {
            'task_id': task_id,
            'type': 'image2video',
            'status': 'submitted',
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'model_name': model_name,
            'videos': []
        }
        save_task(task_data)
        
        return jsonify({"success": True, "task_id": task_id})
        
    except Exception as e:
        print(f"[ERROR] 创建图生视频任务失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@videos_bp.route('/api/extend/<video_uuid>', methods=['POST'])
def api_extend_video(video_uuid):
    """延长视频（兼容原始路径）"""
    data = request.json
    prompt = data.get('prompt', '')
    
    try:
        # 创建延长视频任务
        response_data = create_extend_task(video_uuid, prompt)
        
        # 检查响应是否成功
        if response_data.get('code') != 0:
            error_msg = response_data.get('message', '未知错误')
            return jsonify({"success": False, "message": error_msg}), 500
        
        # 获取任务ID
        task_id = response_data.get('data', {}).get('task_id')
        if not task_id:
            return jsonify({"success": False, "message": "创建任务失败，未返回任务ID"}), 500
        
        # 保存任务记录
        task_data = {
            'task_id': task_id,
            'type': 'extend',
            'status': 'submitted',
            'prompt': prompt,
            'parent_video_id': video_uuid,
            'parameters': {
                'operation': 'extend',
                'video_id': video_uuid
            },
            'videos': []
        }
        save_task(task_data)
        
        return jsonify({"success": True, "task_id": task_id})
        
    except Exception as e:
        print(f"[ERROR] 延长视频任务失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@videos_bp.route('/api/download_video/<task_id>/<video_id>', methods=['GET'])
def api_download_video(task_id, video_id):
    """下载视频（兼容原始路径）"""
    # 查找视频URL
    tasks = load_tasks()
    for task in tasks:
        if task.get('task_id') == task_id:
            for video in task.get('videos', []):
                if video.get('id') == video_id:
                    url = video.get('url')
                    if url:
                        filename = f"{task_id}_{video_id}"
                        try:
                            local_url = download_video(url, filename)
                            if local_url:
                                # 更新视频信息
                                video['downloaded'] = True
                                video['local_url'] = local_url
                                save_tasks(tasks)
                                return jsonify({"success": True, "local_url": local_url})
                        except Exception as e:
                            return jsonify({"success": False, "message": str(e)}), 500
    return jsonify({"success": False, "message": "视频不存在"}), 404

@videos_bp.route('/api/videos/text2video', methods=['POST'])
def create_text2video():
    """创建文生视频任务"""
    data = request.json
    
    # 验证必要参数
    if not data.get('prompt'):
        return jsonify({"error": "提示词不能为空"}), 400
    
    # 处理摄像机控制参数
    camera_type = data.get('camera_type')
    if camera_type == 'simple':
        # 构建摄像机控制参数
        camera_control = {
            "horizontal": int(data.get('camera_horizontal', 0)),
            "vertical": int(data.get('camera_vertical', 0)),
            "pan": int(data.get('camera_pan', 0)),
            "tilt": int(data.get('camera_tilt', 0)),
            "roll": int(data.get('camera_roll', 0)),
            "zoom": int(data.get('camera_zoom', 0))
        }
        data['camera_control'] = camera_control
    elif camera_type:
        # 使用预设的摄像机运动
        data['camera_control'] = {"preset": camera_type}
    
    try:
        # 创建任务
        response_data = create_text2video_task(data)
        
        # 检查响应是否成功
        if response_data.get('code') != 0:
            error_msg = response_data.get('message', '未知错误')
            return jsonify({"error": error_msg}), 500
        
        # 获取任务ID
        task_id = response_data.get('data', {}).get('task_id')
        if not task_id:
            return jsonify({"error": "创建任务失败，未返回任务ID"}), 500
        
        # 保存任务记录
        task_data = {
            'task_id': task_id,
            'type': 'text2video',
            'status': 'submitted',
            'prompt': data.get('prompt', ''),
            'negative_prompt': data.get('negative_prompt', ''),
            'model_name': data.get('model_name', 'kling-v1'),
            'parameters': data,
            'videos': []
        }
        save_task(task_data)
        
        return jsonify({"success": True, "task_id": task_id})
        
    except Exception as e:
        print(f"[ERROR] 创建文生视频任务失败: {str(e)}")
        return jsonify({"error": str(e)}), 500