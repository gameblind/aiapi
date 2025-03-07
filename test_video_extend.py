import requests
import json
import os
from dotenv import load_dotenv

# 禁用不安全请求警告
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 加载环境变量
load_dotenv()

# 从环境变量获取配置
API_BASE_URL = os.getenv('API_BASE_URL')
API_KEY = os.getenv('API_KEY')

def test_video_extend():
    """测试视频延长API"""
    print("\n[DEBUG] ==================== 开始测试视频延长API ====================\n")
    
    try:
        # 1. 检查配置
        print("[DEBUG] 1. 检查API配置:")
        if not API_BASE_URL or not API_KEY:
            raise Exception("API配置不完整，请检查.env文件")
        print(f"[DEBUG] - API基础地址: {API_BASE_URL}")
        print(f"[DEBUG] - API密钥前10位: {API_KEY[:10]}...")
        
        # 2. 准备请求数据
        print("\n[DEBUG] 2. 准备请求数据:")
        video_id = "CmJ8DGePZioAAAAAAxsdCg"  # 使用一个示例视频ID
        prompt = "继续延长这个视频，保持相同的风格和主题"
        
        payload = {            "video_id": video_id,
            "prompt": prompt
        }
        print(f"[DEBUG] - 请求数据: {json.dumps(payload, ensure_ascii=False)}")
        
        # 3. 准备请求头
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        
        # 4. 发送请求
        print("\n[DEBUG] 3. 发送API请求:")
        url = f"{API_BASE_URL}/kling/v1/videos/video-extend"
        print(f"[DEBUG] - 请求URL: {url}")
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            verify=False,
            timeout=60
        )
        
        # 5. 处理响应
        print("\n[DEBUG] 4. 处理响应:")
        print(f"[DEBUG] - 状态码: {response.status_code}")
        print(f"[DEBUG] - 响应头: {dict(response.headers)}")
        
        response_data = response.json()
        print(f"[DEBUG] - 响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        # 6. 检查响应结果
        print("\n[DEBUG] 5. 检查响应结果:")
        if response_data.get('code') == 0:
            task_id = response_data['data']['task_id']
            print(f"[DEBUG] - 任务创建成功！")
            print(f"[DEBUG] - 任务ID: {task_id}")
        else:
            print(f"[DEBUG] - 任务创建失败")
            print(f"[DEBUG] - 错误信息: {response_data.get('message', '未知错误')}")
        
        print("\n[DEBUG] ==================== 测试完成 ====================\n")
        return response_data
        
    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生错误:")
        print(f"[ERROR] - 错误类型: {type(e).__name__}")
        print(f"[ERROR] - 错误信息: {str(e)}")
        print("\n[DEBUG] ==================== 测试异常终止 ====================\n")
        return {"error": str(e)}

if __name__ == "__main__":
    test_video_extend()