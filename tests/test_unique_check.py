# -*- coding: utf-8 -*-
"""测试唯一性检查 - 使用不同用户ID"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试唯一性检查 - 使用不同用户ID ===")

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

# 2. 创建测试用户
print("\n2. 创建测试用户...")
create_data = {
    "username": "test_unique_check",
    "email": "test_unique_check@museum-agent.local",
    "password": "test123",
    "role": "admin"
}
response = requests.post(f"{BASE_URL}/api/admin/users/admins", json=create_data, headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    test_user = response.json()
    print(f"✅ 创建成功! ID: {test_user['id']}")
else:
    print(f"❌ 创建失败: {response.text}")
    exit(1)

# 3. 测试用户名唯一性 - 使用已存在的用户名（admin）
print("\n3. 测试用户名唯一性 - 使用已存在的用户名（admin）...")
update_data = {
    "username": "admin",  # 已存在的用户名（ID=1）
    "email": test_user['email'],
    "role": test_user['role'],
    "is_active": test_user['is_active']
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_user['id']}",  # 更新测试用户，不是admin用户
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

# 4. 测试邮箱唯一性 - 使用已存在的邮箱
print("\n4. 测试邮箱唯一性 - 使用已存在的邮箱...")
update_data = {
    "username": test_user['username'],
    "email": "admin@museum-agent.local",  # 已存在的邮箱（ID=1）
    "role": test_user['role'],
    "is_active": test_user['is_active']
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_user['id']}",  # 更新测试用户，不是admin用户
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

# 5. 清理测试数据
print("\n5. 清理测试数据...")
response = requests.delete(f"{BASE_URL}/api/admin/users/admins/{test_user['id']}", headers=headers)
print(f"删除测试用户: {'成功' if response.status_code == 200 else '失败'}")

print("\n=== 测试完成 ===")
