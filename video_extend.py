import requests
import json
from datetime import datetime
import os
import time
from dotenv import load_dotenv

# 禁用不安全请求警告
from urllib3.exceptions import InsecureRequestWarning
import urllib3  # 直接导入urllib3
urllib3.disable_warnings(InsecureRequestWarning)  # 使用直接导入的urllib3

load_dotenv()

# 从环境变量获取配置
API_BASE_URL = os.getenv('API_BASE_URL')
API_KEY = os.getenv('API_KEY')

def create_extend_task(video_id, prompt=None, callback_url=None):
    """创建视频延长任务"""
    print(f"\n[DEBUG] ========== 开始创建视频延长任务 ==========")
    print(f"[DEBUG] 视频ID: {video_id}")
    print(f"[DEBUG] 提示词: {prompt}")
    print(f"[DEBUG] 回调URL: {callback_url}")
    
    try:
        if not API_BASE_URL:
            raise Exception("API_BASE_URL未配置")
            
        if not API_KEY:
            raise Exception("API_KEY未配置")
        
        url = f"{API_BASE_URL}/kling/v1/videos/video-extend"
        print(f"[DEBUG] 请求URL: {url}")
        
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        print(f"[DEBUG] 请求头: {headers}")
        
        # 注意：不需要处理video_id格式
        # API需要完整的UUID格式，而不是task_id
        # 例如："cfb10889-cf09-41c7-ae58-acf2e67556ee"
        
        # 构建请求数据
        payload = {
            "video_id": video_id,  # 使用完整的UUID
            "prompt": prompt if prompt else ""
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
            
        print(f"[DEBUG] 请求数据: {json.dumps(payload, ensure_ascii=False)}")
        
        # 设置请求超时和重试参数
        max_retries = 3
        retry_delay = 2
        timeout = 60
        
        # 发送请求（带重试机制）
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
        
        print(f"[DEBUG] 响应状态码: {response.status_code}")
        response_data = response.json()
        print(f"[DEBUG] 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
        
        if response_data.get('code') == 0:
            print(f"[DEBUG] 任务创建成功: {response_data['data']['task_id']}")
        else:
            print(f"[ERROR] 任务创建失败: {response_data.get('message', '未知错误')}")
            
        print(f"[DEBUG] ========== 完成创建视频延长任务 ==========\n")
        return response_data
        
    except Exception as e:
        print(f"[ERROR] 创建任务失败: {str(e)}")
        return {"error": str(e)}

def get_extend_task(task_id):
    """查询单个视频延长任务状态"""
    print(f"\n[DEBUG] ========== 开始查询视频延长任务 ==========")
    print(f"[DEBUG] 任务ID: {task_id}")
    
    try:
        if not API_BASE_URL:
            raise Exception("API_BASE_URL not configured")
            
        url = f"{API_BASE_URL}/kling/v1/videos/video-extend/{task_id}"
        print(f"[DEBUG] 请求URL: {url}")
        
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        print(f"[DEBUG] 请求头: {headers}")
        
        # 发送请求
        response = requests.get(
            url,
            headers=headers,
            verify=False
        )
        
        print(f"[DEBUG] 响应状态码: {response.status_code}")
        response_data = response.json()
        print(f"[DEBUG] 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
        
        print(f"[DEBUG] ========== 完成查询视频延长任务 ==========\n")
        return response_data
        
    except Exception as e:
        print(f"[ERROR] 查询任务失败: {str(e)}")
        return {"error": str(e)}

def list_extend_tasks(page_num=1, page_size=30):
    """查询视频延长任务列表"""
    print(f"\n[DEBUG] ========== 开始查询视频延长任务列表 ==========")
    print(f"[DEBUG] 页码: {page_num}")
    print(f"[DEBUG] 每页数量: {page_size}")
    
    try:
        if not API_BASE_URL:
            raise Exception("API_BASE_URL未配置")
            
        if not API_KEY:
            raise Exception("API_KEY未配置")
            
        url = f"{API_BASE_URL}/kling/v1/videos/video-extend"
        
        # 构建请求数据 - 尝试使用不同的参数名称
        payload = {
            'page': page_num,  # 尝试使用更简单的参数名
            'size': page_size  # 尝试使用更简单的参数名
        }
        
        print(f"[DEBUG] 请求URL: {url}")
        print(f"[DEBUG] 请求参数: {payload}")
        
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        print(f"[DEBUG] 请求头: {headers}")
        
        # 发送请求 - 尝试使用GET方法
        response = requests.get(
            url,
            params=payload,  # 使用params而不是json
            headers=headers,
            verify=False
        )
        
        print(f"[DEBUG] 响应状态码: {response.status_code}")
        response_data = response.json()
        print(f"[DEBUG] 响应数据: {json.dumps(response_data, ensure_ascii=False)}")
        
        print(f"[DEBUG] ========== 完成查询视频延长任务列表 ==========\n")
        return response_data
        
    except Exception as e:
        print(f"[ERROR] 查询任务列表失败: {str(e)}")
        # 返回错误信息
        error_response = {
            "code": -1,
            "message": str(e),
            "data": None
        }
        return error_response


def get_video_uuid_from_task(task_id, video_tasks_file='/Users/wangchong/DEV/AIAPI_2025-3-5/static/video_tasks_history.json'):
    """从任务ID获取视频UUID"""
    try:
        with open(video_tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
            
        for task in tasks:
            if task.get('task_id') == task_id and task.get('videos'):
                # 返回第一个视频的UUID
                return task['videos'][0]['id']
                
        return None
    except Exception as e:
        print(f"[ERROR] 获取视频UUID失败: {str(e)}")
        return None
