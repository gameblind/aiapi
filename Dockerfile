# 强制指定目标架构（关键！）
FROM --platform=linux/amd64 python:3.9-slim

# 设置代理环境变量（构建时使用）
ARG HTTP_PROXY=http://host.docker.internal:7897
ARG HTTPS_PROXY=http://host.docker.internal:7897

# 配置APT国内源（加速构建）
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list

# 安装基础编译工具
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 首先只复制必要的文件
COPY requirements.txt .dockerignore /app/

# 设置pip源为国内镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖（确保二进制兼容性）
RUN pip install --no-cache-dir -r requirements.txt \
    && find /usr/local/lib -name '*.c' -delete \
    && find /usr/local/lib -name '*.pyx' -delete

# 设置环境变量
ENV FLASK_APP=app.py FLASK_ENV=production TZ=Asia/Shanghai

# 复制应用程序文件（在安装依赖后）
COPY . /app/

# 创建必要的目录并设置权限
RUN mkdir -p /app/static/videos /app/static/images \
    && chmod -R 755 /app/static

# 清理构建残留减小镜像体积
RUN apt-get purge -y gcc g++ \
    && apt-get autoremove -y

# 取消代理设置（运行时不使用代理）
ENV HTTP_PROXY= HTTPS_PROXY=

# 暴露端口
EXPOSE 5001

# 启动应用
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5001"]