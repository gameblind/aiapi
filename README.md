# AI图像和视频生成系统

## 项目概述
本项目是一个基于Web的AI图像和视频生成系统，提供图片生成、视频生成以及任务管理等功能。系统支持多种模型版本，可以根据用户的需求生成高质量的图片和视频内容。

## 技术架构
- 前端：HTML5, Bootstrap 5, jQuery
- 后端：Python Flask
- 依赖管理：requirements.txt
- 文件存储：本地文件系统

## 主要功能模块

### 1. 图片生成（/images）
- 支持多种图片生成模式
- 可调整图像纵横比（16:9, 9:16, 1:1等）
- 支持变化程度调节
- 支持批量生成（1-9张）
- 实时图片预览功能

### 2. 视频生成（/）
- 支持首帧图片上传
- 支持可选的尾帧图片控制
- 多种模型版本选择（Kling V1/V1.5/V1.6）
- 支持标准模式和专家模式
- 可调整视频时长（5秒/10秒）
- 生成自由度可调节（0-1）

### 3. 任务管理（/tasks）
- 任务历史记录
- 任务状态跟踪
- 任务结果预览
- 定期任务备份

## 文件结构
```
├── app.py                 # 主应用入口
├── image_generate.py      # 图片生成模块
├── video_extend.py        # 视频生成模块
├── task_backup.py         # 任务备份模块
├── task_query.py          # 任务查询模块
├── static/               # 静态资源目录
│   ├── images/          # 生成的图片存储
│   └── videos/          # 生成的视频存储
├── templates/            # 页面模板
│   ├── images.html      # 图片生成页面
│   ├── index.html       # 视频生成页面
│   └── tasks.html       # 任务管理页面
└── requirements.txt      # 项目依赖
```

## API接口

### 图片生成
- 接口：`/generate_image`
- 方法：POST
- 参数：
  - image：原始图片（Base64）
  - prompt：提示词
  - model：模型版本
  - aspect_ratio：图像比例
  - n：生成数量

### 视频生成
- 接口：`/generate`
- 方法：POST
- 参数：
  - image：首帧图片（Base64）
  - image_tail：尾帧图片（可选，Base64）
  - prompt：提示词
  - negative_prompt：负向提示词
  - model_name：模型版本
  - mode：生成模式
  - duration：视频时长
  - cfg_scale：生成自由度

## 部署说明

### 环境要求
- Python 3.x
- Flask
- 其他依赖见requirements.txt

### 安装步骤
1. 克隆项目代码
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量（.env文件）
4. 运行应用：`python app.py`

### Docker部署
项目提供Dockerfile，可以通过以下命令构建和运行：
```bash
docker build -t aiapi .
docker run -p 5000:5000 aiapi
```

## 注意事项
1. 图片上传限制：
   - 支持格式：JPG/JPEG/PNG
   - 大小限制：10MB
   - 分辨率要求：不小于300*300px
   - 宽高比限制：1:2.5到2.5:1之间

2. 视频生成限制：
   - 使用尾帧控制时仅支持5秒视频
   - 生成时长根据选择的模式有所不同

## 备份机制
系统自动定期备份任务数据到backups目录，确保数据安全性。备份文件采用时间戳命名，方便追溯和恢复。

## 最近更新 (2025-03-06)

### 核心功能改进
1. **路由配置优化**  
   - 修复首页访问 404 问题  
   - 新增 Flask 路由处理：  
     ```python:app.py
     @app.route('/')  # 根路径重定向
     @app.route('/index.html')  # 显式处理 index.html
     ```
   - 相关文件：<mcfile name="app.py" path="/Users/wangchong/DEV/AIAPI_2025-3-5/app.py"></mcfile>

2. **视频生成流程增强**  
   - 优化图片跳转视频生成逻辑  
   - 添加参数校验和错误处理：  
     ```javascript:templates%2Fimages.html
     if (!imageUrl) {
         console.error('图片 URL 为空');
         alert('无法获取图片地址');
         return;
     }
     ```
   - 更新跳转 URL 格式：`/index.html?image=...`

3. **下载功能改进**  
   - 新增视频下载重试机制（最多 3 次）  
   - 添加下载进度日志追踪：  
     <mcsymbol name="download_video" filename="app.py" path="/Users/wangchong/DEV/AIAPI_2025-3-5/app.py" startline="245" type="function"></mcsymbol>

### 问题修复
- 修复图片生成卡片 prepend 顺序问题
- 解决模态框初始化多次绑定事件的问题
- 修正文件上传时的 MIME 类型验证逻辑