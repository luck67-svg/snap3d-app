from PIL import Image
import io
from typing import Tuple, Optional

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024

def validate_image(uploaded_file) -> Tuple[bool, str]:
    if uploaded_file is None:
        return False, "请先上传图片"
    
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件格式，请上传 {', '.join(ALLOWED_EXTENSIONS)} 格式的图片"
    
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, "文件大小超过10MB限制"
    
    try:
        img = Image.open(uploaded_file)
        img.verify()
        uploaded_file.seek(0)
        return True, "图片验证通过"
    except Exception as e:
        return False, f"图片文件损坏或格式错误: {str(e)}"

def get_image_info(uploaded_file) -> Optional[dict]:
    try:
        img = Image.open(uploaded_file)
        return {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height
        }
    except Exception:
        return None

def create_thumbnail(uploaded_file, max_size: Tuple[int, int] = (300, 300)) -> Optional[bytes]:
    try:
        img = Image.open(uploaded_file)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return None
