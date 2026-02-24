# -*- coding: utf-8 -*-
"""测试ID=5的用户编辑错误"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试ID=5的用户编辑错误 ===")

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

# 2. 获取ID=5的用户信息
print("\n2. 获取ID=5的用户信息...")
response = requests.get(f"{BASE_URL}/api/admin/users/admins/5", headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    user = response.json()
    print(f"✅ 获取成功!")
    print(f"  用户名: {user['username']}")
    print(f"  邮箱: {user['email']}")
else:
    print(f"❌ 获取失败: {response.text}")
    exit(1)

# 3. 尝试使用已存在的用户名
print("\n3. 尝试使用已存在的用户名（123）...")
update_data = {
    "username": "123",  # 已存在的用户名
    "email": user['email'],
    "role": user['role'],
    "is_active": user['is_active']
}
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/5",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应头: {dict(response.headers)}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

# 4. 尝试使用已存在的邮箱
print("\n4. 尝试使用已存在的邮箱...")
update_data = {
    "username": user['username'],
    "email": "lhxcrl@gmail.com",  # 已存在的邮箱
    "role": user['role'],
    "is_active": user['is_active']
}
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/5",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

print("\n=== 测试完成 ===")
