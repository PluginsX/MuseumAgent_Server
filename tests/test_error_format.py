# -*- coding: utf-8 -*-
"""测试错误响应格式"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试错误响应格式 ===")

# 1. 登录获取 token
print("\n1. 登录获取 token...")
login_data = {
    "username": "123",
    "password": "123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
result = response.json()

if result.get("code") == 200:
    token = result["data"]["access_token"]
    print(f"✅ 登录成功!")
else:
    print(f"❌ 登录失败: {result.get('msg', '未知错误')}")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}"
}

# 2. 测试用户名唯一性错误
print("\n2. 测试用户名唯一性错误（使用已存在的用户名）...")
update_data = {
    "username": "admin",  # 已存在的用户名
    "email": "test@test.com",
    "role": "admin",
    "is_active": True
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/1",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应头: {dict(response.headers)}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

# 3. 测试邮箱唯一性错误
print("\n3. 测试邮箱唯一性错误（使用已存在的邮箱）...")
update_data = {
    "username": "test_user",
    "email": "admin@museum-agent.local",  # 已存在的邮箱
    "role": "admin",
    "is_active": True
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/1",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

print("\n=== 测试完成 ===")
