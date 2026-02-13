import requests
import json

# 测试服务器连接
url = "http://localhost:8002/api/auth/login"

# 登录凭据
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
        print(f"Access Token: {data.get('access_token', 'Not found')}")
    else:
        print("登录失败")
        
except requests.exceptions.ConnectionError:
    print("无法连接到服务器，请确保服务器正在运行")
except Exception as e:
    print(f"请求出错: {e}")