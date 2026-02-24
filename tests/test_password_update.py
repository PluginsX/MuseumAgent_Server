# -*- coding: utf-8 -*-
"""测试用户密码更新功能"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试用户密码更新功能 ===")

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
    # 选择第一个管理员用户进行测试
    if admins:
        test_admin = admins[0]
        print(f"  测试用户: {test_admin['username']} (ID: {test_admin['id']})")
    else:
        print("❌ 没有管理员用户")
        exit(1)
else:
    print(f"❌ 获取失败: {response.text}")
    exit(1)

# 3. 更新管理员用户密码
print("\n3. 更新管理员用户密码...")
update_data = {
    "email": test_admin['email'],
    "role": test_admin['role'],
    "is_active": test_admin['is_active'],
    "password": "new_password_123"
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_admin = response.json()
    print(f"✅ 更新成功!")
    print(f"  用户名: {updated_admin['username']}")
    print(f"  邮箱: {updated_admin['email']}")
else:
    print(f"❌ 更新失败: {response.text}")
    exit(1)

# 4. 测试使用新密码登录
print("\n4. 测试使用新密码登录...")
login_data_new = {
    "username": test_admin['username'],
    "password": "new_password_123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data_new)
print(f"状态码: {response.status_code}")
result = response.json()

if result.get("code") == 200:
    print(f"✅ 使用新密码登录成功!")
else:
    print(f"❌ 使用新密码登录失败: {result.get('msg', '未知错误')}")

# 5. 测试使用旧密码登录（应该失败）
print("\n5. 测试使用旧密码登录（应该失败）...")
login_data_old = {
    "username": test_admin['username'],
    "password": "123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data_old)
print(f"状态码: {response.status_code}")
result = response.json()

if result.get("code") != 200:
    print(f"✅ 使用旧密码登录失败（符合预期）!")
else:
    print(f"❌ 使用旧密码登录成功（不符合预期）!")

# 6. 获取客户用户列表
print("\n6. 获取客户用户列表...")
response = requests.get(f"{BASE_URL}/api/admin/users/clients", headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    clients = response.json()
    print(f"✅ 获取成功! 共 {len(clients)} 个客户用户")
    # 选择第一个客户用户进行测试
    if clients:
        test_client = clients[0]
        print(f"  测试用户: {test_client['username']} (ID: {test_client['id']})")
    else:
        print("❌ 没有客户用户")
        exit(1)
else:
    print(f"❌ 获取失败: {response.text}")
    exit(1)

# 7. 更新客户用户密码
print("\n7. 更新客户用户密码...")
update_data = {
    "email": test_client['email'],
    "role": test_client['role'],
    "is_active": test_client['is_active'],
    "password": "new_client_password_123"
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/clients/{test_client['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_client = response.json()
    print(f"✅ 更新成功!")
    print(f"  用户名: {updated_client['username']}")
    print(f"  邮箱: {updated_client['email']}")
else:
    print(f"❌ 更新失败: {response.text}")
    exit(1)

# 8. 测试不修改密码（留空）
print("\n8. 测试不修改密码（留空）...")
update_data_no_password = {
    "email": test_admin['email'],
    "role": test_admin['role'],
    "is_active": test_admin['is_active']
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data_no_password,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_admin = response.json()
    print(f"✅ 更新成功（未修改密码）!")
    print(f"  用户名: {updated_admin['username']}")
else:
    print(f"❌ 更新失败: {response.text}")

print("\n=== 测试完成 ===")
