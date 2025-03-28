#!/bin/bash
# 跨平台Docker镜像构建脚本
# 用于在M4芯片的macOS上构建AMD64架构的Docker镜像

# 显示彩色输出
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${BLUE}===== 开始跨平台Docker镜像构建 =====${NC}"

# 步骤1: 启用Docker实验性功能
echo -e "${YELLOW}步骤1: 启用Docker实验性功能${NC}"
export DOCKER_CLI_EXPERIMENTAL=enabled
echo "已设置 DOCKER_CLI_EXPERIMENTAL=enabled"

# 步骤2: 创建多架构构建器
echo -e "${YELLOW}步骤2: 创建多架构构建器${NC}"
docker buildx create --use --name cross-builder || {
    echo "构建器已存在，切换到该构建器"
    docker buildx use cross-builder
}
docker buildx inspect --bootstrap

# 步骤3: 清理缓存文件（可选）
echo -e "${YELLOW}步骤3: 清理缓存文件（可选）${NC}"
if [ -f "./clean_cache.py" ]; then
    echo "运行缓存清理脚本..."
    python3 ./clean_cache.py
fi

# 步骤4: 使用buildx构建并推送镜像
echo -e "${YELLOW}步骤4: 构建跨平台Docker镜像${NC}"
echo "注意: 此命令将构建linux/amd64架构的镜像"

# 询问是否需要推送到Docker Hub
read -p "是否需要推送到Docker Hub? (y/n): " PUSH_IMAGE

if [ "$PUSH_IMAGE" = "y" ] || [ "$PUSH_IMAGE" = "Y" ]; then
    # 询问Docker Hub用户名和镜像名称
    read -p "请输入Docker Hub用户名: " DOCKER_USERNAME
    read -p "请输入镜像名称 (默认: aiapi): " IMAGE_NAME
    IMAGE_NAME=${IMAGE_NAME:-aiapi}
    
    # 构建并推送
    echo "构建并推送镜像到 ${DOCKER_USERNAME}/${IMAGE_NAME}..."
    docker buildx build --platform linux/amd64 \
        --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:latest \
        --push .
    
    echo -e "${GREEN}镜像已成功构建并推送到 ${DOCKER_USERNAME}/${IMAGE_NAME}:latest${NC}"
    echo "在群晖Docker中，可以直接拉取此镜像: ${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
else
    # 仅构建本地镜像
    echo "仅构建本地镜像 aiapi:latest..."
    docker buildx build --platform linux/amd64 \
        --tag aiapi:latest \
        --load .
    
    echo -e "${GREEN}本地镜像已成功构建: aiapi:latest${NC}"
    echo "您可以使用 'docker save aiapi:latest -o aiapi.tar' 导出镜像，然后在群晖中导入"
fi

echo -e "${BLUE}===== 跨平台Docker镜像构建完成 =====${NC}"

# 显示后续步骤
echo -e "${YELLOW}后续步骤:${NC}"
echo "1. 如果构建了本地镜像，可以使用以下命令导出:"
echo "   docker save aiapi:latest -o aiapi.tar"
echo "2. 将导出的镜像文件上传到群晖NAS"
echo "3. 在群晖Docker中导入镜像或直接拉取已推送的镜像"
echo "4. 使用docker-compose.yml启动容器"