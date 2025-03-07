from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from test_video_extend import test_video_extend

# 加载环境变量
load_dotenv()

app = Flask(__name__)

@app.route('/test_video_extend', methods=['GET'])
def api_test_video_extend():
    """通过Web接口测试视频延长API"""
    print("\n[INFO] 通过Web接口触发视频延长API测试")
    
    # 调用测试函数
    result = test_video_extend()
    
    # 返回测试结果
    return jsonify(result)

@app.route('/')
def index():
    """简单的首页，提供测试链接"""
    return '''
    <html>
        <head>
            <title>视频延长API测试</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #333; }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                .note { color: #666; font-style: italic; }
            </style>
        </head>
        <body>
            <h1>视频延长API测试工具</h1>
            <p>点击下面的按钮测试视频延长API格式：</p>
            <a href="/test_video_extend" class="button">运行API测试</a>
            <p class="note">测试结果将以JSON格式显示，同时在服务器控制台输出详细日志</p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    # 设置主机和端口
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))  # 使用不同于主应用的端口
    
    print(f"\n[INFO] 启动测试服务器在 http://{host}:{port}/")
    print(f"[INFO] 访问 http://localhost:{port}/ 开始测试")
    
    # 启动Flask应用
    app.run(host=host, port=port, debug=True)