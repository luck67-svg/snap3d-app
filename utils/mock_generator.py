import time
import random
import os
from typing import Tuple, Optional

class LoadingMessages:
    MESSAGES = [
        "🎨 AI正在理解你的图片...",
        "🔮 感知图像轮廓中...",
        "📐 构建三维网格...",
        "🧙 施展3D魔法中...",
        "✨ 即将完成，请稍候...",
        "🌈 正在赋予图像生命...",
        "🚀 火箭推进3D转换中...",
        "⭐ 魔法粒子聚集ing...",
    ]
    
    @classmethod
    def get_random_message(cls) -> str:
        return random.choice(cls.MESSAGES)
    
    @classmethod
    def get_sequential_message(cls, index: int) -> str:
        return cls.MESSAGES[index % len(cls.MESSAGES)]

class MockGenerator:
    def __init__(self, demo_stl_path: str):
        self.demo_stl_path = demo_stl_path
        self.simulate_delay = 5
    
    def set_delay(self, seconds: int):
        self.simulate_delay = max(1, min(seconds, 30))
    
    def generate(self, uploaded_file, mode: str = "relief") -> Tuple[bool, Optional[bytes], str]:
        progress_messages = []
        
        steps = 5
        for i in range(steps):
            message = LoadingMessages.get_sequential_message(i)
            progress_messages.append(message)
            time.sleep(self.simulate_delay / steps)
        
        if not os.path.exists(self.demo_stl_path):
            return False, None, f"演示文件不存在: {self.demo_stl_path}"
        
        try:
            with open(self.demo_stl_path, 'rb') as f:
                stl_data = f.read()
            
            return True, stl_data, f"成功生成{mode}模式3D模型！"
        except Exception as e:
            return False, None, f"读取演示文件失败: {str(e)}"
    
    def generate_with_callback(self, uploaded_file, mode: str, progress_callback=None) -> Tuple[bool, Optional[bytes], str]:
        steps = 5
        for i in range(steps):
            message = LoadingMessages.get_sequential_message(i)
            progress = (i + 1) / steps
            
            if progress_callback:
                progress_callback(progress, message)
            
            time.sleep(self.simulate_delay / steps)
        
        if not os.path.exists(self.demo_stl_path):
            return False, None, f"演示文件不存在: {self.demo_stl_path}"
        
        try:
            with open(self.demo_stl_path, 'rb') as f:
                stl_data = f.read()
            
            return True, stl_data, f"成功生成{mode}模式3D模型！"
        except Exception as e:
            return False, None, f"读取演示文件失败: {str(e)}"
    
    @staticmethod
    def get_mode_description(mode: str) -> str:
        descriptions = {
            "relief": "浮雕模式 - 适合制作徽章、挂件、钥匙扣等扁平装饰品",
            "solid": "立体模式 - 适合制作小型摆件、手办原型等3D物件"
        }
        return descriptions.get(mode, "未知模式")
