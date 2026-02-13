import requests
import json

# 测试登录
url = "http://localhost:8001/api/auth/login"
credentials = {
    "username": "123",
    "password": "123"
}

try:
    response = requests.post(url, json=credentials, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("登录成功！")
        data = response.json()
        token = data.get('access_token')
        print(f"Access Token: {token[:20] if token else 'None'}...")
        
        # 测试会话注册
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        session_url = "http://localhost:8001/api/session/register"
        session_response = requests.post(session_url, headers=headers, timeout=10)
        print(f"Session Registration Status: {session_response.status_code}")
        print(f"Session Response: {session_response.text}")
    else:
        print("登录失败")
        
except requests.exceptions.ConnectionError:
    print("无法连接到服务器，请确保服务器正在运行")
except Exception as e:
    print(f"请求出错: {e}")