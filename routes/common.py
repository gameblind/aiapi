from flask import Blueprint, render_template, jsonify, request
from utils import backup_tasks
from services.file_service import load_tasks, load_image_tasks

# 创建蓝图
common_bp = Blueprint('common', __name__)

@common_bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@common_bp.route('/tasks')
def tasks():
    """任务历史页面"""
    return render_template('tasks.html')

@common_bp.route('/api/tasks')
def get_tasks():
    """获取所有任务"""
    tasks = load_tasks()
    return jsonify(tasks)

@common_bp.route('/api/image_tasks')
def get_image_tasks():
    """获取所有图片任务"""
    tasks = load_image_tasks()
    return jsonify(tasks)

@common_bp.route('/api/backup', methods=['POST'])
def backup():
    """备份任务数据"""
    success = backup_tasks()
    if success:
        return jsonify({"status": "success", "message": "备份成功"})
    else:
        return jsonify({"status": "error", "message": "备份失败"}), 500