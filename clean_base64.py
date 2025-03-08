#!/usr/bin/env python3
"""
清理 video_tasks_history.json 文件中的 base64 编码数据
"""

import json
import os
import re
from datetime import datetime

def is_base64(s):
    """
    判断字符串是否为base64编码
    """
    # base64编码通常是由字母、数字、+、/和=组成的
    if not isinstance(s, str):
        return False
    
    # 检查长度，base64编码的图片通常很长
    if len(s) < 500:  # 设置一个合理的最小长度
        return False
    
    # 检查是否包含base64常见的特征
    if re.match(r'^[A-Za-z0-9+/]+={0,2}$', s):
        return True
    
    # 检查是否包含data:image前缀
    if s.startswith('data:image'):
        return True
    
    return False

def clean_base64_from_json(json_file):
    """
    从JSON文件中清理base64编码数据
    """
    print(f"开始清理文件: {json_file}")
    
    # 备份原始文件
    backup_file = f"{json_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    os.system(f"cp {json_file} {backup_file}")
    print(f"创建备份文件: {backup_file}")
    
    with open(json_file, "r", encoding="utf-8") as f:
        try:
            tasks = json.load(f)
            original_size = os.path.getsize(json_file) / (1024 * 1024)  # 转换为MB
            print(f"原始文件大小: {original_size:.2f} MB")
            print(f"任务数量: {len(tasks)}")
            
            # 计数器
            base64_count = 0
            
            # 清理每个任务中的base64数据
            for task in tasks:
                # 遍历任务中的所有字段
                for key in list(task.keys()):
                    # 检查字段值是否为base64编码
                    if key in ["image", "image_tail"] and is_base64(task[key]):
                        # 记录该字段存在
                        task[f"has_{key}"] = True
                        # 删除base64数据
                        task.pop(key)
                        base64_count += 1
                    # 检查其他可能包含base64的字段
                    elif isinstance(task.get(key), str) and len(task[key]) > 1000 and is_base64(task[key]):
                        print(f"发现其他base64字段: {key}")
                        task[f"has_{key}_data"] = True
                        task.pop(key)
                        base64_count += 1
            
            print(f"清理了 {base64_count} 个base64数据项")
            
            # 保存清理后的数据
            with open(json_file, "w", encoding="utf-8") as f_out:
                json.dump(tasks, f_out, ensure_ascii=False, indent=2)
            
            # 计算清理后的文件大小
            new_size = os.path.getsize(json_file) / (1024 * 1024)  # 转换为MB
            print(f"清理后文件大小: {new_size:.2f} MB")
            print(f"减少了: {original_size - new_size:.2f} MB ({((original_size - new_size) / original_size * 100) if original_size > 0 else 0:.2f}%)")
            
            return True
        except json.JSONDecodeError as e:
            print(f"错误: JSON解析失败 - {e}")
            return False
        except Exception as e:
            print(f"错误: {e}")
            return False

if __name__ == "__main__":
    json_file = "video_tasks_history.json"
    
    # 检查文件是否存在
    if not os.path.exists(json_file):
        print(f"错误: 文件 {json_file} 不存在")
        exit(1)
    
    # 清理文件
    if clean_base64_from_json(json_file):
        print("清理完成!")
    else:
        print("清理失败，请检查备份文件")