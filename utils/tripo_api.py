import requests
import time
import os
import json
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TripoAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.tripo3d.ai/v2/openapi"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def upload_file(self, file_obj, file_name):
        """上传文件到 Tripo"""
        url = f"{self.base_url}/upload"
        
        # 简单的 MIME 类型判断
        mime_type = 'image/jpeg'
        if file_name.lower().endswith('.png'):
            mime_type = 'image/png'
        elif file_name.lower().endswith('.webp'):
            mime_type = 'image/webp'
            
        # 增加重试机制
        max_retries = 3
        last_exception = None
        
        for i in range(max_retries):
            try:
                # 每次重试前都要把文件指针重置到开头
                file_obj.seek(0)
                
                files = {
                    'file': (file_name, file_obj, mime_type)
                }
                
                # 上传不需要 Content-Type header，requests 会自动处理
                headers_copy = self.headers.copy()
                if 'Content-Type' in headers_copy:
                    del headers_copy['Content-Type']
                    
                # verify=False 解决 SSL 问题
                response = requests.post(url, headers=headers_copy, files=files, verify=False, timeout=60)
                
                # 打印详细错误信息
                if response.status_code != 200:
                    print(f"Upload API Error (Attempt {i+1}): {response.status_code} - {response.text}")
                    
                response.raise_for_status()
                data = response.json()
                if data['code'] == 0:
                    return data['data']['image_token']
                else:
                    raise Exception(f"Upload failed: {data['message']}")
            
            except Exception as e:
                print(f"Upload attempt {i+1} failed: {e}")
                last_exception = e
                time.sleep(2) # 失败等待2秒
        
        # 如果重试都失败了
        print(f"Upload finally failed after {max_retries} attempts.")
        raise last_exception

    def create_task(self, image_token, file_type="jpg"):
        """创建 image_to_model 任务"""
        url = f"{self.base_url}/task"
        
        # 确保 file_type 是 Tripo 支持的格式 (jpg, png, webp)
        if file_type.lower() in ['jpeg', 'jpg']:
            file_type = 'jpg'
        elif file_type.lower() == 'png':
            file_type = 'png'
        elif file_type.lower() == 'webp':
            file_type = 'webp'
        else:
            file_type = 'jpg' # 默认回退到 jpg
            
        payload = {
            "type": "image_to_model",
            "file": {
                "type": file_type,
                "file_token": image_token
            }
        }
        
        try:
            # verify=False 解决 SSL 问题
            response = requests.post(url, headers=self.headers, json=payload, verify=False, timeout=60)
            
            # 详细错误信息
            print(f"Create Task Response Status: {response.status_code}")
            print(f"Create Task Response Body: {response.text}")
            
            if response.status_code == 403:
                try:
                    error_data = response.json()
                    error_code = error_data.get('code', 0)
                    error_msg = error_data.get('message', '')
                    
                    if error_code == 2010:
                        raise Exception(
                            "❌ Tripo3D 账户积分不足！\n\n"
                            "解决方案：\n"
                            "1. 登录 https://platform.tripo3d.ai 充值积分\n"
                            "2. Tripo 提供免费积分额度，可查看是否有免费额度\n"
                            "3. 或暂时使用离线演示模式"
                        )
                    else:
                        raise Exception(f"API 错误 ({error_code}): {error_msg}")
                except Exception as e:
                    if "积分不足" in str(e):
                        raise e
                    raise Exception(f"403 Forbidden - {response.text}")
            
            if response.status_code != 200:
                print(f"Create Task API Error: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            data = response.json()
            if data['code'] == 0:
                return data['data']['task_id']
            else:
                raise Exception(f"Create task failed: {data['message']}")
        except Exception as e:
            print(f"Create task exception: {e}")
            raise e

    def get_task_result(self, task_id):
        """查询任务状态"""
        url = f"{self.base_url}/task/{task_id}"
        try:
            # verify=False 解决 SSL 问题
            response = requests.get(url, headers=self.headers, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data['code'] == 0:
                return data['data']
            else:
                raise Exception(f"Get task failed: {data['message']}")
        except Exception as e:
            print(f"Get task error: {e}")
            return None

    def poll_task(self, task_id, interval=2, max_retries=60, progress_callback=None):
        """轮询任务直到完成"""
        retries = 0
        while retries < max_retries:
            result = self.get_task_result(task_id)
            if not result:
                break
            
            status = result['status']
            progress = result.get('progress', 0)
            
            if progress_callback:
                progress_callback(status, progress)
            
            if status == 'success':
                return result['output']
            elif status == 'failed':
                raise Exception("Task generation failed.")
            elif status == 'cancelled':
                raise Exception("Task was cancelled.")
            
            time.sleep(interval)
            retries += 1
        
        raise Exception("Task polling timed out.")
