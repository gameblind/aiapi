#!/usr/bin/env python3
"""
清理缓存文件脚本

在构建Docker镜像前运行此脚本，清理不必要的缓存文件和临时文件，
以减小Docker镜像的大小并提高构建效率。
"""

import os
import shutil
import glob
import fnmatch
from datetime import datetime

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 需要清理的目录和文件模式
CLEANUP_PATTERNS = [
    # Python缓存文件
    '**/__pycache__',
    '**/*.pyc',
    '**/*.pyo',
    '**/*.pyd',
    
    # 临时文件
    '**/*.log',
    '**/*.tmp',
    '**/*.temp',
    '**/.DS_Store',
    '**/Thumbs.db',
    
    # 备份文件
    '**/static/backups/*',
    '**/*copy*.json',
    '**/*bak*',
    
    # 压缩文件
    '**/*.tar',
    '**/*.gz',
    '**/*.zip',
]

# 需要保留的文件
KEEP_FILES = [
    'static/image_tasks.json',
    'static/video_tasks_history.json',
]

def should_keep(path):
    """检查文件是否应该保留"""
    rel_path = os.path.relpath(path, ROOT_DIR)
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in KEEP_FILES)

def clean_cache_files():
    """清理缓存文件"""
    print(f"\n开始清理缓存文件 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_cleaned = 0
    total_size = 0
    
    for pattern in CLEANUP_PATTERNS:
        # 使用glob查找匹配的文件和目录
        for path in glob.glob(os.path.join(ROOT_DIR, pattern), recursive=True):
            # 跳过需要保留的文件
            if should_keep(path):
                continue
                
            try:
                if os.path.isfile(path):
                    # 获取文件大小
                    size = os.path.getsize(path)
                    # 删除文件
                    os.remove(path)
                    print(f"已删除文件: {os.path.relpath(path, ROOT_DIR)} ({size/1024:.2f} KB)")
                    total_cleaned += 1
                    total_size += size
                elif os.path.isdir(path):
                    # 获取目录大小
                    dir_size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                                  for dirpath, _, filenames in os.walk(path) 
                                  for filename in filenames)
                    # 删除目录
                    shutil.rmtree(path)
                    print(f"已删除目录: {os.path.relpath(path, ROOT_DIR)} ({dir_size/1024:.2f} KB)")
                    total_cleaned += 1
                    total_size += dir_size
            except Exception as e:
                print(f"清理失败: {path} - {str(e)}")
    
    print(f"\n清理完成! 共清理 {total_cleaned} 个文件/目录，释放空间 {total_size/(1024*1024):.2f} MB")
    print(f"现在可以构建Docker镜像了。\n")

def clean_docker_build_cache():
    """清理Docker构建缓存"""
    print("\n提示: 如果需要清理Docker构建缓存，可以运行以下命令:")
    print("docker builder prune -f  # 清理未使用的构建缓存")
    print("docker image prune -f    # 清理未使用的镜像")
    print("docker system prune -f    # 清理整个系统缓存\n")

if __name__ == "__main__":
    clean_cache_files()
    clean_docker_build_cache()