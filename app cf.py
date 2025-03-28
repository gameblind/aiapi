from flask import Flask, send_from_directory
import os
import urllib3
from dotenv import load_dotenv
from routes.common import common_bp
from routes.videos import videos_bp
from routes.images import images_bp
from utils import ensure_app_files

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建Flask应用
app = Flask(__name__)
load_dotenv()

# 初始化应用所需的目录和文件
ensure_app_files()

# 注册蓝图
app.register_blueprint(common_bp)
app.register_blueprint(videos_bp)
app.register_blueprint(images_bp)

# 静态文件路由
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)