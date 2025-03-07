import os
import json
import shutil
from datetime import datetime
from video_extend import get_extend_task

# 文件路径配置
TASKS_FILE = 'tasks_history.json'
BACKUP_DIR = 'backups'
VIDEOS_DIR = 'static/videos'

# 确保备份目录存在
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def backup_tasks():
    """备份任务记录"""
    try:
        # 检查任务文件是否存在
        if not os.path.exists(TASKS_FILE):
            print(f"[WARNING] 任务文件不存在: {TASKS_FILE}")
            return False
            
        # 创建备份文件名（包含时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'tasks_backup_{timestamp}.json'
        backup_path = os.path.join(BACKUP_DIR, backup_file)
        
        # 复制文件
        shutil.copy2(TASKS_FILE, backup_path)
        print(f"[INFO] 任务记录已备份到: {backup_path}")
        
        # 清理旧备份（保留最近10个备份）
        cleanup_old_backups()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 备份任务记录失败: {str(e)}")
        return False

def cleanup_old_backups(max_backups=10):
    """清理旧的备份文件，只保留最近的几个"""
    try:
        # 获取所有备份文件
        backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith('tasks_backup_')]
        backup_files.sort(reverse=True)  # 按文件名排序（最新的在前）
        
        # 删除多余的备份
        for old_file in backup_files[max_backups:]:
            os.remove(os.path.join(BACKUP_DIR, old_file))
            print(f"[INFO] 删除旧备份文件: {old_file}")
            
    except Exception as e:
        print(f"[ERROR] 清理旧备份失败: {str(e)}")

def delete_task(task_id):
    """删除指定的任务记录和相关视频文件"""
    try:
        # 加载任务记录
        if not os.path.exists(TASKS_FILE):
            raise Exception(f"任务文件不存在: {TASKS_FILE}")
            
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
            
        # 查找要删除的任务
        task_index = None
        for i, task in enumerate(tasks):
            if task['task_id'] == task_id:
                task_index = i
                break
                
        if task_index is None:
            raise Exception(f"未找到任务: {task_id}")
            
        # 删除相关文件
        task = tasks[task_index]
        base_dir = os.path.dirname(os.path.dirname(TASKS_FILE))
        
        # 删除视频文件
        for video in task.get('videos', []):
            if video.get('local_url'):
                video_path = os.path.join(base_dir, video['local_url'].lstrip('/'))
                if os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                        print(f"[INFO] 删除视频文件: {video_path}")
                    except Exception as e:
                        print(f"[WARNING] 删除视频文件失败: {video_path}, 错误: {str(e)}")
        
        # 删除图片文件
        if task.get('image_url'):
            image_path = os.path.join(base_dir, task['image_url'].lstrip('/'))
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"[INFO] 删除图片文件: {image_path}")
                except Exception as e:
                    print(f"[WARNING] 删除图片文件失败: {image_path}, 错误: {str(e)}")
                    
        # 删除任务记录
        deleted_task = tasks.pop(task_index)
        
        # 保存更新后的任务记录
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
            
        print(f"[INFO] 成功删除任务: {task_id}")
        return {
            'success': True,
            'message': f'成功删除任务: {task_id}',
            'deleted_task': deleted_task
        }
        
    except Exception as e:
        error_msg = f"删除任务失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            'success': False,
            'message': error_msg
        }

def update_task_status(task_id):
    """更新单个任务的状态"""
    try:
        # 查询任务状态
        status_data = get_extend_task(task_id)
        if status_data.get('error'):
            raise Exception(status_data['error'])
            
        # 加载当前任务记录
        if not os.path.exists(TASKS_FILE):
            raise Exception(f"任务文件不存在: {TASKS_FILE}")
            
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
            
        # 查找并更新任务
        task_updated = False
        for task in tasks:
            if task['task_id'] == task_id:
                # 更新任务状态
                task['status'] = status_data.get('data', {}).get('task_status', 'unknown')
                task['status_msg'] = status_data.get('data', {}).get('task_status_msg', '')
                
                # 更新视频信息
                if task['status'] == 'succeed':
                    videos = status_data.get('data', {}).get('task_result', {}).get('videos', [])
                    for video in videos:
                        video_info = {
                            'id': video.get('id'),
                            'url': video.get('url'),
                            'duration': video.get('duration'),
                            'local_url': None,
                            'downloaded': False
                        }
                        task['videos'].append(video_info)
                        
                task_updated = True
                break
                
        if not task_updated:
            raise Exception(f"未找到任务: {task_id}")
            
        # 保存更新后的任务记录
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
            
        print(f"[INFO] 成功更新任务状态: {task_id}")
        return {
            'success': True,
            'message': f'成功更新任务状态: {task_id}',
            'task_status': status_data
        }
        
    except Exception as e:
        error_msg = f"更新任务状态失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            'success': False,
            'message': error_msg
        }