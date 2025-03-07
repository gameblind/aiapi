import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# 从环境变量获取配置
API_BASE_URL = os.getenv('API_BASE_URL')
API_KEY = os.getenv('API_KEY')

def query_all_tasks(page_size=100):
    """查询所有历史任务
    
    Args:
        page_size: 每页数量，默认100条
        
    Returns:
        所有任务列表
    """
    print(f"\n[DEBUG] ========== 开始查询所有历史任务 ==========")
    print(f"[DEBUG] 每页数量: {page_size}")
    
    all_tasks = []
    page_num = 1
    total_pages = 1  # 初始值，会在第一次请求后更新
    
    try:
        if not API_BASE_URL:
            raise Exception("API_BASE_URL not configured")
            
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        print(f"[DEBUG] 请求头: {headers}")
        
        # 循环获取所有页面的数据
        while page_num <= total_pages:
            print(f"\n[DEBUG] 正在获取第 {page_num} 页数据...")
            
            url = f"{API_BASE_URL}/kling/v1/videos/image2video"
            params = {
                'pageNum': page_num,
                'pageSize': page_size
            }
            print(f"[DEBUG] 请求URL: {url}")
            print(f"[DEBUG] 请求参数: {params}")
            
            # 设置请求超时和重试参数
            max_retries = 3
            retry_delay = 2
            timeout = 60
            
            # 发送请求（带重试机制）
            for attempt in range(max_retries):
                try:
                    print(f"[DEBUG] 第 {attempt + 1} 次尝试发送请求")
                    response = requests.get(
                        url,
                        params=params,
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
            
            if response_data.get('code') != 0:
                print(f"[ERROR] API返回错误: {response_data.get('message', '未知错误')}")
                break
                
            # 获取数据
            data = response_data.get('data', {})
            tasks = data.get('tasks', [])
            all_tasks.extend(tasks)
            
            # 更新总页数
            total = data.get('total', 0)
            total_pages = (total + page_size - 1) // page_size
            
            print(f"[DEBUG] 当前页任务数: {len(tasks)}")
            print(f"[DEBUG] 累计获取任务数: {len(all_tasks)}")
            print(f"[DEBUG] 总任务数: {total}")
            print(f"[DEBUG] 总页数: {total_pages}")
            
            # 继续下一页
            page_num += 1
        
        print(f"\n[DEBUG] ========== 完成查询所有历史任务 ==========")
        print(f"[DEBUG] 总共获取 {len(all_tasks)} 条任务记录")
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "total": len(all_tasks),
                "tasks": all_tasks
            }
        }
        
    except Exception as e:
        print(f"[ERROR] 查询所有任务失败: {str(e)}")
        # 返回错误信息
        error_response = {
            "code": -1,
            "message": str(e),
            "data": None
        }
        return error_response

def query_task_by_id(task_id):
    """根据任务ID查询单个任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务详情
    """
    print(f"\n[DEBUG] ========== 开始查询任务详情 ==========")
    print(f"[DEBUG] 任务ID: {task_id}")
    
    try:
        if not API_BASE_URL:
            raise Exception("API_BASE_URL not configured")
            
        url = f"{API_BASE_URL}/kling/v1/videos/image2video/{task_id}"
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
        
        print(f"[DEBUG] ========== 完成查询任务详情 ==========\n")
        return response_data
        
    except Exception as e:
        print(f"[ERROR] 查询任务详情失败: {str(e)}")
        return {"code": -1, "message": str(e), "data": None}