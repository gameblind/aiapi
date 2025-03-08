# AI图像和视频生成系统群晖NAS部署指南

本文档提供了将AI图像和视频生成系统部署到群晖NAS的详细步骤。

## 前提条件

1. 群晖NAS已安装Docker套件
2. 已获取API密钥和基础URL
3. 具有NAS的管理员权限

## 部署步骤

### 1. 准备项目文件

1. 将项目文件上传到群晖NAS的共享文件夹中，例如：`/volume1/docker/aiapi/`
2. 确保上传了以下文件和目录：
   - 所有Python源代码文件（.py）
   - templates目录（包含HTML模板）
   - static目录（用于存储生成的图片和视频）
   - requirements.txt（依赖列表）
   - Dockerfile（Docker镜像构建文件）
   - docker-compose.yml（Docker Compose配置文件）
   - .env（环境变量配置文件）

### 2. 配置环境变量

1. 在项目目录中创建`.env`文件，填入正确的API密钥和其他配置信息：

```
# API配置
API_KEY=your_actual_api_key_here
API_BASE_URL=your_actual_api_base_url_here

# 数据库配置
DB_HOST=localhost
DB_USER=username
DB_PASSWORD=password
DB_NAME=database_name

# 服务配置
SERVICE_URL=https://example.com/api
```

### 3. 使用Docker Compose部署

1. 通过SSH连接到群晖NAS
2. 导航到项目目录：
   ```bash
   cd /volume1/docker/aiapi/
   ```
3. 构建并启动Docker容器：
   ```bash
   docker-compose up -d
   ```

### 4. 验证部署

1. 打开浏览器，访问：`http://[NAS_IP]:5001`
2. 确认应用程序已成功启动并可以访问

## 持久化存储

docker-compose.yml文件已配置以下卷挂载，确保数据持久化：

```yaml
volumes:
  - ./static:/app/static
  - ./tasks_history.json:/app/tasks_history.json
  - ./video_tasks_history.json:/app/video_tasks_history.json
```

## 自动启动设置

在docker-compose.yml中已设置`restart: always`，确保NAS重启后容器自动启动。

## 日志查看

查看应用日志：
```bash
docker logs aiapi
```

或者实时查看日志：
```bash
docker logs -f aiapi
```

## 更新应用

当需要更新应用时，执行以下步骤：

1. 上传新版本的代码文件到NAS
2. 重新构建并启动容器：
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## 注意事项

1. 确保`.env`文件中的API密钥和其他敏感信息安全存储
2. 定期备份`tasks_history.json`和`video_tasks_history.json`文件
3. 如果需要更改端口，请修改docker-compose.yml文件中的端口映射

## 故障排除

1. 如果容器无法启动，检查日志：
   ```bash
   docker logs aiapi
   ```

2. 确保NAS上的Docker套件已正确安装和配置

3. 检查`.env`文件中的配置是否正确

4. 如果遇到权限问题，可能需要调整目录权限：
   ```bash
   chmod -R 755 /volume1/docker/aiapi/
   ```

## 系统架构

本应用使用Docker容器化部署，主要组件包括：

- Flask Web应用：处理用户请求和API调用
- 环境变量配置：通过.env文件和docker-compose.yml管理
- 持久化存储：使用卷挂载保存生成的图像、视频和任务历史

通过这种架构，系统可以在群晖NAS上稳定运行，并且易于维护和更新。