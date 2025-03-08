# 使用官方Python基础镜像
FROM python:3.9-slim

# 设置代理环境变量（构建时使用）
ARG HTTP_PROXY=http://host.docker.internal:7897
ARG HTTPS_PROXY=http://host.docker.internal:7897
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}

# 设置工作目录
WORKDIR /app

# 复制应用程序文件
COPY . /app/

# 设置pip源为国内镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖包
RUN pip install -r requirements.txt

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV TZ=Asia/Shanghai

# 创建必要的目录
RUN mkdir -p /app/static/videos
RUN mkdir -p /app/static/images

# 设置权限
RUN chmod -R 755 /app/static

# 取消代理设置（运行时不使用代理）
ENV HTTP_PROXY=
ENV HTTPS_PROXY=

# 暴露端口
EXPOSE 5001

# 启动应用
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5001"]