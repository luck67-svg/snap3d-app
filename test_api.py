"""
Tripo3D API Key 测试脚本
运行此脚本来诊断 API Key 问题
"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "your_api_key_here"
BASE_URL = "https://api.tripo3d.ai/v2/openapi"

def test_api_key():
    print("=" * 50)
    print("Tripo3D API Key 测试")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    print(f"\n1. 测试 API Key 格式...")
    if API_KEY.startswith("tsk_"):
        print("   ✅ API Key 格式正确 (以 tsk_ 开头)")
    else:
        print("   ❌ API Key 格式可能不正确")
    
    print(f"\n2. 测试 API 连接...")
    
    # 测试用户信息端点 (如果存在)
    try:
        response = requests.get(f"{BASE_URL}/user", headers=headers, verify=False, timeout=30)
        print(f"   用户端点响应: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应内容: {response.text[:500]}")
        elif response.status_code == 404:
            print("   (用户端点不存在，这是正常的)")
    except Exception as e:
        print(f"   请求失败: {e}")
    
    print(f"\n3. 测试任务创建端点 (POST /task)...")
    
    # 使用一个测试图片 URL
    test_payload = {
        "type": "image_to_model",
        "file": {
            "type": "jpg",
            "url": "https://via.placeholder.com/256"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/task", 
            headers=headers, 
            json=test_payload, 
            verify=False, 
            timeout=30
        )
        
        print(f"   响应状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                print("   ✅ API Key 有效！任务创建成功")
                task_id = data.get('data', {}).get('task_id')
                if task_id:
                    print(f"   任务ID: {task_id}")
            else:
                print(f"   ❌ API 返回错误: {data.get('message')}")
        elif response.status_code == 401:
            print("   ❌ 401 Unauthorized - API Key 无效或已过期")
        elif response.status_code == 403:
            print("   ❌ 403 Forbidden - 可能原因:")
            print("      - API Key 权限不足")
            print("      - 账户积分用完")
            print("      - 账户被暂停")
            try:
                error_data = response.json()
                print(f"      - 错误详情: {error_data}")
            except:
                print(f"      - 响应内容: {response.text}")
        elif response.status_code == 429:
            print("   ❌ 429 Too Many Requests - 请求过于频繁，请稍后再试")
        else:
            print(f"   ❌ 其他错误: {response.status_code}")
            
    except Exception as e:
        print(f"   请求异常: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
    
    print("\n📋 如果遇到 403 错误，请检查:")
    print("   1. 登录 https://platform.tripo3d.ai 查看账户状态")
    print("   2. 检查 API Key 是否正确复制")
    print("   3. 确认账户有可用积分")
    print("   4. 尝试在 Tripo 平台网页上重新生成 API Key")

if __name__ == "__main__":
    test_api_key()
