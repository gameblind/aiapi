# AI图像和视频生成系统部署指南

## 群晖NAS部署说明

本文档提供了将AI图像和视频生成系统部署到群晖NAS的详细步骤。

### 前提条件

1. 群晖NAS已安装Docker套件
2. 已获取API密钥和基础URL
3. 具有NAS的管理员权限

### 部署步骤

#### 1. 准备项目文件

1. 将项目文件上传到群晖NAS的共享文件夹中，例如：`/volume1/docker/aiapi/`
2. 确保上传了以下文件和目录：
   - 所有Python源代码文件（.py）
   - templates目录（包含HTML模板）
   - static目录（用于存储生成的图片和视频）
   - requirements.txt（依赖列表）
   - Dockerfile（Docker镜像构建文件）
   - docker-compose.yml（Docker Compose配置文件）
   - config.ini（配置文件，需要修改）

#### 2. 配置应用

1. 编辑`config.ini`文件，填入正确的API密钥和其他配置信息：

```ini
[API]
# 替换为您的API密钥
API_KEY = your_actual_api_key_here
API_BASE_URL = your_actual_api_base_url_here

[DATABASE]
# 数据库连接信息（如果需要）
DB_HOST = localhost
DB_USER = username
DB_PASSWORD = password
DB_NAME = database_name

[SERVICES]
# 其他服务配置
SERVICE_URL = https://example.com/api
```

#### 3. 使用Docker Compose部署

1. 通过SSH连接到群晖NAS
2. 导航到项目目录：
   ```bash
   cd /volume1/docker/aiapi/
   ```
3. 构建并启动Docker容器：
   ```bash
   docker-compose up -d
   ```

#### 4. 验证部署

1. 打开浏览器，访问：`http://[NAS_IP]:5001`
2. 确认应用程序已成功启动并可以访问

### 持久化存储

docker-compose.yml文件已配置以下卷挂载，确保数据持久化：

```yaml
volumes:
  - ./config.ini:/app/config.ini
  - ./static:/app/static
  - ./tasks_history.json:/app/tasks_history.json
  - ./video_tasks_history.json:/app/video_tasks_history.json
```

### 自动启动设置

在docker-compose.yml中已设置`restart: always`，确保NAS重启后容器自动启动。

### 日志查看

查看应用日志：
```bash
docker logs aiapi
```

或者实时查看日志：
```bash
docker logs -f aiapi
```

### 更新应用

当需要更新应用时，执行以下步骤：

1. 上传新版本的代码文件到NAS
2. 重新构建并启动容器：
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

### 故障排除

1. 如果应用无法启动，检查日志：
   ```bash
   docker logs aiapi
   ```

2. 确认config.ini中的API密钥和URL配置正确

3. 检查端口映射是否正确，确保5001端口没有被其他应用占用

4. 如果遇到权限问题，确保挂载的目录具有正确的读写权限

### 安全注意事项

1. 不要将包含API密钥的config.ini文件提交到公共代码仓库
2. 考虑为应用设置反向代理和HTTPS，特别是如果需要从外部网络访问
3. 定期更新Docker镜像和依赖包，以修复潜在的安全漏洞

### 备份策略

定期备份以下文件和目录：

1. config.ini（配置文件）
2. static目录（生成的图片和视频）
3. tasks_history.json和video_tasks_history.json（任务历史记录）

可以使用群晖的备份工具或设置定时任务来自动备份这些文件。