import os
import json
import time
from video_extend import create_extend_task, get_extend_task, list_extend_tasks

def test_video_extend_api():
    """测试视频延长API的各项功能"""
    print("\n========== 开始测试视频延长API ==========")
    
    # 1. 首先测试列表功能，查看是否有现有任务
    print("\n1. 测试获取任务列表")
    list_result = list_extend_tasks(page_num=1, page_size=5)
    
    if "error" in list_result:
        print(f"获取任务列表失败: {list_result['error']}")
    else:
        print(f"获取任务列表成功，状态码: {list_result.get('code')}")
        
        # 如果有任务，尝试获取第一个任务的详情
        if list_result.get('code') == 0 and list_result.get('data', {}).get('list'):
            task_list = list_result['data']['list']
            print(f"找到 {len(task_list)} 个任务")
            
            if task_list:
                first_task_id = task_list[0].get('task_id')
                print(f"\n2. 测试获取单个任务详情: {first_task_id}")
                task_result = get_extend_task(first_task_id)
                
                if "error" in task_result:
                    print(f"获取任务详情失败: {task_result['error']}")
                else:
                    print(f"获取任务详情成功，状态码: {task_result.get('code')}")
    
    # 3. 测试创建新任务
    # 注意：这里需要一个有效的视频ID，您可以根据实际情况修改
    test_video_id = input("\n请输入要测试的视频ID: ")
    if test_video_id:
        print(f"\n3. 测试创建新任务，视频ID: {test_video_id}")
        test_prompt = "测试视频延长功能"
        create_result = create_extend_task(test_video_id, test_prompt)
        
        if "error" in create_result:
            print(f"创建任务失败: {create_result['error']}")
        else:
            print(f"创建任务结果，状态码: {create_result.get('code')}")
            
            # 如果创建成功，等待并查询任务状态
            if create_result.get('code') == 0 and create_result.get('data', {}).get('task_id'):
                new_task_id = create_result['data']['task_id']
                print(f"新任务ID: {new_task_id}")
                
                print("\n4. 等待5秒后查询新任务状态...")
                time.sleep(5)
                
                check_result = get_extend_task(new_task_id)
                if "error" in check_result:
                    print(f"查询新任务状态失败: {check_result['error']}")
                else:
                    print(f"新任务状态: {check_result.get('data', {}).get('task_status', '未知')}")
    
    print("\n========== 视频延长API测试完成 ==========")

if __name__ == "__main__":
    test_video_extend_api()