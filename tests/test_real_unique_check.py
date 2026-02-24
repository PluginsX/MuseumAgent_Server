# -*- coding: utf-8 -*-
"""测试用户名唯一性检查 - 使用真实存在的用户名"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试用户名唯一性检查 - 使用真实存在的用户名 ===")

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

# 2. 获取所有管理员用户
print("\n2. 获取所有管理员用户...")
response = requests.get(f"{BASE_URL}/api/admin/users/admins", headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    admins = response.json()
    print(f"✅ 获取成功! 共 {len(admins)} 个管理员用户")
    for admin in admins:
        print(f"  ID: {admin['id']}, 用户名: {admin['username']}, 邮箱: {admin['email']}")
else:
    print(f"❌ 获取失败: {response.text}")
    exit(1)

# 3. 创建测试用户
print("\n3. 创建测试用户...")
create_data = {
    "username": "test_user_new",
    "email": "test_user_new@museum-agent.local",
    "password": "test123",
    "role": "admin"
}
response = requests.post(f"{BASE_URL}/api/admin/users/admins", json=create_data, headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    test_user = response.json()
    print(f"✅ 创建成功! ID: {test_user['id']}, 用户名: {test_user['username']}")
else:
    print(f"❌ 创建失败: {response.text}")
    exit(1)

# 4. 尝试将测试用户的用户名改为已存在的用户名（test_user, ID=1）
print("\n4. 尝试将测试用户的用户名改为已存在的用户名（test_user, ID=1）...")
update_data = {
    "username": "test_user",  # 已存在的用户名（ID=1）
    "email": test_user['email'],
    "role": test_user['role'],
    "is_active": test_user['is_active']
}
print(f"  测试用户ID: {test_user['id']}")
print(f"  目标用户名: test_user (ID=1)")
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_user['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if response.status_code == 400:
    print("✅ 用户名唯一性检查生效！")
else:
    print("❌ 用户名唯一性检查未生效！")

# 5. 尝试将测试用户的邮箱改为已存在的邮箱
print("\n5. 尝试将测试用户的邮箱改为已存在的邮箱...")
update_data = {
    "username": test_user['username'],
    "email": "admin@museum-agent.local",  # 已存在的邮箱（ID=1）
    "role": test_user['role'],
    "is_active": test_user['is_active']
}
print(f"  测试用户ID: {test_user['id']}")
print(f"  目标邮箱: admin@museum-agent.local (ID=1)")
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_user['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if response.status_code == 400:
    print("✅ 邮箱唯一性检查生效！")
else:
    print("❌ 邮箱唯一性检查未生效！")

# 6. 清理测试数据
print("\n6. 清理测试数据...")
response = requests.delete(f"{BASE_URL}/api/admin/users/admins/{test_user['id']}", headers=headers)
print(f"删除测试用户: {'成功' if response.status_code == 200 else '失败'}")

print("\n=== 测试完成 ===")
