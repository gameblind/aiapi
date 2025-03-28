from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
import os
from config import API_KEY

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@web_bp.route('/videos')
def videos():
    """视频生成页面"""
    return render_template('videos.html')

@web_bp.route('/images')
def images():
    """图片生成页面"""
    return render_template('images.html')

@web_bp.route('/voice')
def voice():
    """语音处理页面"""
    return render_template('voice.html')

@web_bp.route('/chat')
def chat():
    """聊天页面"""
    return render_template('chat.html')

@web_bp.route('/file-upload-test')
def file_upload_test():
    """文件上传测试页面"""
    return render_template('file_upload_test.html')

@web_bp.route('/settings')
def settings():
    """设置页面"""
    return render_template('settings.html')

@web_bp.route('/api-key', methods=['POST'])
def set_api_key():
    """设置API密钥"""
    api_key = request.form.get('api_key')
    if api_key:
        session['api_key'] = api_key
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '无效的API密钥'})

@web_bp.route('/api-key', methods=['GET'])
def get_api_key():
    """获取API密钥"""
    api_key = session.get('api_key', API_KEY)
    return jsonify({'api_key': api_key})