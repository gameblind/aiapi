import os
import json
import requests
from dotenv import load_dotenv

# 禁用不安全请求警告
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)

load_dotenv()

# 从环境变量获取配置
API_BASE_URL = os.getenv('API_BASE_URL')
API_KEY = os.getenv('API_KEY')

def test_simple_extend():
    """简单测试视频延长API"""
    # 尝试不同格式的视频ID
    video_id = "Cjil7mfhdHgAAAAAAKt0Bw"  # 原始格式
    
    # 尝试从videos数组中获取id
    video_uuid = "cfb10889-cf09-41c7-ae58-acf2e67556ee"  # 从JSON中找到的视频UUID
    
    url = f"{API_BASE_URL}/kling/v1/videos/video-extend"
    
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # 尝试使用不同的payload格式
    payloads = [
        # 原始payload
        {
            "video_id": video_id,
            "prompt": "测试视频延长功能"
        },
        # 尝试使用UUID
        {
            "video_id": video_uuid,
            "prompt": "测试视频延长功能"
        },
        # 尝试添加model_name字段
        {
            "video_id": video_id,
            "prompt": "测试视频延长功能",
            "model_name": "kling-v1"
        },
        # 尝试添加空model字段
        {
            "video_id": video_id,
            "prompt": "测试视频延长功能",
            "model": ""
        },
        # 尝试添加model字段与原视频相同
        {
            "video_id": video_id,
            "prompt": "测试视频延长功能",
            "model": "kling-v1"
        }
    ]
    
    for i, payload in enumerate(payloads):
        print(f"\n测试 #{i+1}:")
        print(f"请求URL: {url}")
        print(f"请求头: {headers}")
        print(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=30
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应数据: {json.dumps(response.json(), ensure_ascii=False)}")
        except Exception as e:
            print(f"请求发生错误: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_simple_extend()