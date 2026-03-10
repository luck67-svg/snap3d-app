"""
Meshy.ai API 适配器
支持 Image to 3D 功能，输出格式包括 GLB、STL 等
"""

import requests
import time
import base64
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MeshyAPI:
    """
    Meshy.ai API 客户端
    
    API 文档: https://docs.meshy.ai/en/api/image-to-3d
    """
    
    BASE_URL = "https://api.meshy.ai/openapi/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_image_to_3d_task(
        self,
        image_data: bytes = None,
        image_url: str = None,
        file_name: str = "image.png",
        ai_model: str = "meshy-6",
        should_texture: bool = True,
        topology: str = "quad",
        target_polycount: int = 60000
    ) -> str:
        """
        创建 Image to 3D 任务
        
        Args:
            image_data: 图片二进制数据 (与 image_url 二选一)
            image_url: 图片公开URL (与 image_data 二选一)
            file_name: 文件名 (用于判断格式)
            ai_model: AI模型 (meshy-5, meshy-6, latest)
            should_texture: 是否生成纹理
            topology: 网格拓扑 (quad, triangle)
            target_polycount: 目标多边形数量
            
        Returns:
            task_id: 任务ID
        """
        url = f"{self.BASE_URL}/image-to-3d"
        
        # 处理图片输入
        if image_data:
            # 转换为 base64 Data URI
            mime_type = "image/png"
            if file_name.lower().endswith(('.jpg', '.jpeg')):
                mime_type = "image/jpeg"
            elif file_name.lower().endswith('.webp'):
                mime_type = "image/webp"
            
            b64_data = base64.b64encode(image_data).decode('utf-8')
            image_uri = f"data:{mime_type};base64,{b64_data}"
            image_input = image_uri
        elif image_url:
            image_input = image_url
        else:
            raise ValueError("必须提供 image_data 或 image_url")
        
        payload = {
            "image_url": image_input,
            "ai_model": ai_model,
            "should_texture": should_texture,
            "topology": topology,
            "target_polycount": target_polycount,
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                verify=False,
                timeout=60
            )
            
            print(f"Meshy API Response Status: {response.status_code}")
            print(f"Meshy API Response: {response.text[:500]}")
            
            if response.status_code == 401:
                raise Exception("API Key 无效或未授权")
            elif response.status_code == 402:
                raise Exception("账户积分不足，请充值后重试")
            elif response.status_code == 429:
                raise Exception("请求过于频繁，请稍后再试")
            
            response.raise_for_status()
            
            data = response.json()
            task_id = data.get("result")
            
            if not task_id:
                raise Exception(f"创建任务失败: {data}")
            
            return task_id
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
    
    def create_text_to_3d_task(
        self,
        prompt: str,
        negative_prompt: str = "low quality, low resolution, low poly, ugly",
        ai_model: str = "meshy-6",
        topology: str = "quad",
        target_polycount: int = 60000,
        should_remesh: bool = True
    ) -> str:
        """
        创建 Text to 3D 任务 (v2 - Meshy-6)
        
        Args:
            prompt: 文本提示词
            negative_prompt: 负面提示词
            ai_model: AI模型 (meshy-6, latest)
            topology: 网格拓扑 (quad, triangle)
            target_polycount: 目标多边形数量
            should_remesh: 是否重新网格化
            
        Returns:
            task_id: 任务ID
        """
        url = "https://api.meshy.ai/openapi/v2/text-to-3d"
        
        payload = {
            "mode": "preview",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "ai_model": ai_model,
            "topology": topology,
            "target_polycount": target_polycount,
            "should_remesh": should_remesh
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                verify=False,
                timeout=60
            )
            
            print(f"Meshy API (Text) Response Status: {response.status_code}")
            
            if response.status_code == 401:
                raise Exception("API Key 无效或未授权")
            elif response.status_code == 402:
                raise Exception("账户积分不足，请充值后重试")
            
            response.raise_for_status()
            
            data = response.json()
            task_id = data.get("result")
            
            if not task_id:
                raise Exception(f"创建任务失败: {data}")
            
            return task_id
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {e}")

    def get_task_result(self, task_id: str) -> dict:
        """
        查询 Image-to-3D 任务状态
        """
        url = f"{self.BASE_URL}/image-to-3d/{task_id}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"查询任务失败: {e}")
            return None

    def get_text_to_3d_result(self, task_id: str) -> dict:
        """
        查询 Text-to-3D 任务状态 (v2)
        """
        url = f"https://api.meshy.ai/openapi/v2/text-to-3d/{task_id}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"查询任务失败: {e}")
            return None

    def poll_task(
        self,
        task_id: str,
        task_type: str = "image-to-3d",
        interval: int = 3,
        max_wait: int = 900,
        progress_callback=None
    ) -> dict:
        """
        轮询任务直到完成
        
        Args:
            task_id: 任务ID
            task_type: 任务类型 "image-to-3d" 或 "text-to-3d"
            ...
        """
        elapsed = 0
        
        while elapsed < max_wait:
            if task_type == "text-to-3d":
                result = self.get_text_to_3d_result(task_id)
            else:
                result = self.get_task_result(task_id)
            
            if not result:
                raise Exception("无法获取任务状态")
            
            status = result.get("status", "")
            progress = result.get("progress", 0)
            
            print(f"Task {task_id}: Status={status}, Progress={progress}%")
            
            if progress_callback:
                progress_callback(status, progress)
            
            if status == "SUCCEEDED":
                return result
            elif status == "FAILED":
                error_msg = result.get("error", "未知错误")
                raise Exception(f"任务失败: {error_msg}")
            elif status == "CANCELED":
                raise Exception("任务被取消")
            
            time.sleep(interval)
            elapsed += interval
        
        raise Exception(f"任务超时 (超过 {max_wait} 秒)")
    
    def download_model(self, model_url: str) -> bytes:
        """
        下载3D模型文件
        
        Args:
            model_url: 模型下载链接
            
        Returns:
            模型文件的二进制数据
        """
        try:
            response = requests.get(model_url, verify=False, timeout=120)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            raise Exception(f"下载模型失败: {e}")
    
    def get_model_urls(self, task_result: dict) -> dict:
        """
        从任务结果中提取模型下载链接
        
        Args:
            task_result: 任务结果字典
            
        Returns:
            模型URL字典 {"glb": url, "stl": url, ...}
        """
        return task_result.get("model_urls", {})
    
    def get_stl_url(self, task_result: dict) -> str:
        """
        获取 STL 格式的下载链接
        
        Args:
            task_result: 任务结果字典
            
        Returns:
            STL 文件下载链接
        """
        model_urls = self.get_model_urls(task_result)
        return model_urls.get("stl") if model_urls else None
    
    def get_glb_url(self, task_result: dict) -> str:
        """
        获取 GLB 格式的下载链接
        
        Args:
            task_result: 任务结果字典
            
        Returns:
            GLB 文件下载链接
        """
        model_urls = self.get_model_urls(task_result)
        return model_urls.get("glb") if model_urls else None


def test_meshy_api():
    """测试 Meshy API 连接"""
    API_KEY = "your-meshy-api-key"
    
    client = MeshyAPI(API_KEY)
    
    # 使用测试图片URL
    test_image_url = "https://via.placeholder.com/256"
    
    try:
        print("创建 Image to 3D 任务...")
        task_id = client.create_image_to_3d_task(
            image_url=test_image_url,
            ai_model="meshy-5",
            should_texture=False
        )
        print(f"任务ID: {task_id}")
        
        print("轮询任务状态...")
        result = client.poll_task(task_id, progress_callback=lambda s, p: print(f"  {s}: {p}%"))
        
        print("任务完成!")
        print(f"模型链接: {client.get_model_urls(result)}")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    test_meshy_api()
