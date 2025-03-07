# 使用本地Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制应用程序文件
COPY . /app/

# 安装依赖包
RUN pip install -r requirements.txt

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 5001

# 启动应用
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]