# -*- coding: utf-8 -*-
"""测试用户管理 API"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试用户管理 API ===")

# 1. 首先登录获取 token
print("\n1. 登录获取 token...")
login_data = {
    "username": "123",
    "password": "123"
}
try:
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        token = response.json()["data"]["access_token"]
        print(f"Token: {token[:50]}...")
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 2. 测试获取管理员用户列表
        print("\n2. 获取管理员用户列表...")
        response = requests.get(f"{BASE_URL}/api/admin/users/admins?page=1&size=10", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        # 3. 测试获取客户用户列表
        print("\n3. 获取客户用户列表...")
        response = requests.get(f"{BASE_URL}/api/admin/users/clients?page=1&size=10", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        # 4. 测试创建管理员用户
        print("\n4. 创建管理员用户...")
        create_admin_data = {
            "username": "test_admin",
            "email": "test_admin@example.com",
            "password": "test123",
            "role": "admin"
        }
        response = requests.post(f"{BASE_URL}/api/admin/users/admins", json=create_admin_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        # 5. 测试创建客户用户
        print("\n5. 创建客户用户...")
        create_client_data = {
            "username": "test_client",
            "email": "test_client@example.com",
            "password": "test123",
            "role": "client"
        }
        response = requests.post(f"{BASE_URL}/api/admin/users/clients", json=create_client_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        # 6. 再次获取管理员用户列表
        print("\n6. 再次获取管理员用户列表...")
        response = requests.get(f"{BASE_URL}/api/admin/users/admins?page=1&size=10", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        # 7. 再次获取客户用户列表
        print("\n7. 再次获取客户用户列表...")
        response = requests.get(f"{BASE_URL}/api/admin/users/clients?page=1&size=10", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
    else:
        print("登录失败!")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
