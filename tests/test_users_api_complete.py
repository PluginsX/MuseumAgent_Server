# -*- coding: utf-8 -*-
"""完整测试用户管理 API"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 完整测试用户管理 API ===")

# 1. 登录获取 token
print("\n1. 登录获取 token...")
login_data = {
    "username": "123",
    "password": "123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
print(f"状态码: {response.status_code}")
result = response.json()

if result.get("code") == 200:
    token = result["data"]["access_token"]
    print(f"✅ 登录成功!")
    print(f"Token: {token[:50]}...")
else:
    print(f"❌ 登录失败: {result.get('msg', '未知错误')}")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}"
}

# 2. 获取管理员用户列表
print("\n2. 获取管理员用户列表...")
response = requests.get(f"{BASE_URL}/api/admin/users/admins", headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    admins = response.json()
    print(f"✅ 获取成功! 共 {len(admins)} 个管理员用户")
    for admin in admins:
        print(f"  - {admin['username']} ({admin['email']})")
else:
    print(f"❌ 获取失败: {response.text}")

# 3. 获取客户用户列表
print("\n3. 获取客户用户列表...")
response = requests.get(f"{BASE_URL}/api/admin/users/clients", headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    clients = response.json()
    print(f"✅ 获取成功! 共 {len(clients)} 个客户用户")
    for client in clients:
        print(f"  - {client['username']} ({client['email']})")
else:
    print(f"❌ 获取失败: {response.text}")

# 4. 创建新的管理员用户
print("\n4. 创建新的管理员用户...")
new_admin_data = {
    "username": f"new_admin_{int(__import__('time').time())}",
    "email": f"new_admin_{int(__import__('time').time())}@example.com",
    "password": "password123",
    "role": "admin"
}
response = requests.post(f"{BASE_URL}/api/admin/users/admins", json=new_admin_data, headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    new_admin = response.json()
    print(f"✅ 创建成功!")
    print(f"  用户名: {new_admin['username']}")
    print(f"  邮箱: {new_admin['email']}")
    print(f"  角色: {new_admin['role']}")
else:
    print(f"❌ 创建失败: {response.text}")

# 5. 创建新的客户用户
print("\n5. 创建新的客户用户...")
new_client_data = {
    "username": f"new_client_{int(__import__('time').time())}",
    "email": f"new_client_{int(__import__('time').time())}@example.com",
    "password": "password123",
    "role": "client"
}
response = requests.post(f"{BASE_URL}/api/admin/users/clients", json=new_client_data, headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    new_client = response.json()
    print(f"✅ 创建成功!")
    print(f"  用户名: {new_client['username']}")
    print(f"  邮箱: {new_client['email']}")
    print(f"  角色: {new_client['role']}")
    print(f"  API密钥: {new_client['api_key'][:30]}...")
else:
    print(f"❌ 创建失败: {response.text}")

# 6. 再次获取管理员用户列表
print("\n6. 再次获取管理员用户列表...")
response = requests.get(f"{BASE_URL}/api/admin/users/admins", headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    admins = response.json()
    print(f"✅ 获取成功! 共 {len(admins)} 个管理员用户")
else:
    print(f"❌ 获取失败: {response.text}")

# 7. 再次获取客户用户列表
print("\n7. 再次获取客户用户列表...")
response = requests.get(f"{BASE_URL}/api/admin/users/clients", headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    clients = response.json()
    print(f"✅ 获取成功! 共 {len(clients)} 个客户用户")
else:
    print(f"❌ 获取失败: {response.text}")

print("\n=== 测试完成 ===")
