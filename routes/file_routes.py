from flask import Blueprint, request, jsonify
from services.file_service import upload_file, get_file_info, delete_file, list_files
from functools import wraps
from config import API_KEY

file_bp = Blueprint('file', __name__)

# 验证API密钥的装饰器 - 仅用于云端API调用
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头中获取 Authorization
        auth_header = request.headers.get('Authorization')
        
        # 检查 Authorization 头是否存在且格式正确
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "error": {
                    "message": "Missing or invalid API key",
                    "type": "authentication_error",
                    "code": "invalid_api_key"
                }
            }), 401
        
        # 提取 API 密钥
        provided_key = auth_header.split('Bearer ')[1].strip()
        
        # 验证 API 密钥
        if provided_key != API_KEY:
            return jsonify({
                "error": {
                    "message": "Invalid API key",
                    "type": "authentication_error",
                    "code": "invalid_api_key"
                }
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

# 修改文件上传路由，移除API密钥验证
@file_bp.route('/v1/files', methods=['POST'])
def upload_file_route():
    """上传文件API - 本地存储，无需验证"""
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({
            "error": {
                "message": "No file provided",
                "type": "invalid_request_error",
                "code": "no_file"
            }
        }), 400
    
    file = request.files['file']
    
    # 检查文件是否为空
    if file.filename == '':
        return jsonify({
            "error": {
                "message": "Empty filename",
                "type": "invalid_request_error",
                "code": "empty_filename"
            }
        }), 400
    
    # 获取purpose参数
    purpose = request.args.get('purpose', 'assistants')
    
    # 获取是否上传到云端的参数
    upload_to_cloud = request.args.get('upload_to_cloud', 'true').lower() == 'true'
    
    # 上传文件
    file_info = upload_file(file, purpose, upload_to_cloud)
    
    if file_info:
        return jsonify(file_info), 200
    else:
        return jsonify({
            "error": {
                "message": "File upload failed",
                "type": "server_error",
                "code": "upload_failed"
            }
        }), 500

# 添加一个需要API密钥验证的云端上传路由
@file_bp.route('/v1/cloud/files', methods=['POST'])
@require_api_key
def upload_to_cloud_route():
    """上传文件到云端API - 需要验证"""
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({
            "error": {
                "message": "No file provided",
                "type": "invalid_request_error",
                "code": "no_file"
            }
        }), 400
    
    file = request.files['file']
    
    # 检查文件是否为空
    if file.filename == '':
        return jsonify({
            "error": {
                "message": "Empty filename",
                "type": "invalid_request_error",
                "code": "empty_filename"
            }
        }), 400
    
    # 获取purpose参数
    purpose = request.args.get('purpose', 'assistants')
    
    # 强制上传到云端
    file_info = upload_file(file, purpose, True)
    
    if file_info:
        return jsonify(file_info), 200
    else:
        return jsonify({
            "error": {
                "message": "File upload failed",
                "type": "server_error",
                "code": "upload_failed"
            }
        }), 500

# 其他路由也移除API密钥验证
@file_bp.route('/v1/files/<file_id>', methods=['GET'])
def get_file_route(file_id):
    """获取文件信息API - 本地存储，无需验证"""
    file_info = get_file_info(file_id)
    
    if file_info:
        return jsonify(file_info), 200
    else:
        return jsonify({
            "error": {
                "message": f"File {file_id} not found",
                "type": "invalid_request_error",
                "code": "file_not_found"
            }
        }), 404

@file_bp.route('/v1/files/<file_id>', methods=['DELETE'])
def delete_file_route(file_id):
    """删除文件API - 本地存储，无需验证"""
    success = delete_file(file_id)
    
    if success:
        return jsonify({
            "id": file_id,
            "object": "file",
            "deleted": True
        }), 200
    else:
        return jsonify({
            "error": {
                "message": f"File {file_id} not found or could not be deleted",
                "type": "invalid_request_error",
                "code": "file_not_found"
            }
        }), 404

@file_bp.route('/v1/files', methods=['GET'])
def list_files_route():
    """列出文件API - 本地存储，无需验证"""
    purpose = request.args.get('purpose')
    files = list_files(purpose)
    
    return jsonify({
        "object": "list",
        "data": files
    }), 200

# 添加云端文件操作路由，这些路由需要API密钥验证
@file_bp.route('/v1/cloud/files/<file_id>', methods=['GET'])
@require_api_key
def get_cloud_file_route(file_id):
    """获取云端文件信息API - 需要验证"""
    # 这里应该调用云端API获取文件信息
    # 暂时返回错误，表示功能未实现
    return jsonify({
        "error": {
            "message": "Cloud file operations not implemented yet",
            "type": "not_implemented",
            "code": "not_implemented"
        }
    }), 501

@file_bp.route('/v1/cloud/files/<file_id>', methods=['DELETE'])
@require_api_key
def delete_cloud_file_route(file_id):
    """删除云端文件API - 需要验证"""
    # 这里应该调用云端API删除文件
    # 暂时返回错误，表示功能未实现
    return jsonify({
        "error": {
            "message": "Cloud file operations not implemented yet",
            "type": "not_implemented",
            "code": "not_implemented"
        }
    }), 501

@file_bp.route('/v1/cloud/files', methods=['GET'])
@require_api_key
def list_cloud_files_route():
    """列出云端文件API - 需要验证"""
    # 这里应该调用云端API列出文件
    # 暂时返回错误，表示功能未实现
    return jsonify({
        "error": {
            "message": "Cloud file operations not implemented yet",
            "type": "not_implemented",
            "code": "not_implemented"
        }
    }), 501