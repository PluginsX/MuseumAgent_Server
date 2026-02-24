# -*- coding: utf-8 -*-
"""测试用户名和邮箱空值验证"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试用户名和邮箱空值验证 ===")

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

# 2. 获取管理员用户列表
print("\n2. 获取管理员用户列表...")
response = requests.get(f"{BASE_URL}/api/admin/users/admins", headers=headers)
if response.status_code == 200:
    admins = response.json()
    test_user = admins[0]
    print(f"✅ 获取成功! 测试用户: {test_user['username']} (ID: {test_user['id']})")
else:
    print(f"❌ 获取失败: {response.text}")
    exit(1)

# 3. 测试用户名为空
print("\n3. 测试用户名为空...")
update_data = {
    "username": "",  # 空用户名
    "email": test_user['email'],
    "role": test_user['role'],
    "is_active": test_user['is_active']
}
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_user['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if response.status_code == 400 and "用户名不能为空" in response.json().get('detail', ''):
    print("✅ 用户名空值验证生效！")
else:
    print("❌ 用户名空值验证未生效！")

# 4. 测试邮箱为空
print("\n4. 测试邮箱为空...")
update_data = {
    "username": test_user['username'],
    "email": "",  # 空邮箱
    "role": test_user['role'],
    "is_active": test_user['is_active']
}
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_user['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if response.status_code == 400 and "邮箱不能为空" in response.json().get('detail', ''):
    print("✅ 邮箱空值验证生效！")
else:
    print("❌ 邮箱空值验证未生效！")

# 5. 测试用户名和邮箱都为空
print("\n5. 测试用户名和邮箱都为空...")
update_data = {
    "username": "",  # 空用户名
    "email": "",  # 空邮箱
    "role": test_user['role'],
    "is_active": test_user['is_active']
}
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_user['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if response.status_code == 400:
    print("✅ 空值验证生效！")
else:
    print("❌ 空值验证未生效！")

# 6. 测试用户名只有空格
print("\n6. 测试用户名只有空格...")
update_data = {
    "username": "   ",  # 只有空格
    "email": test_user['email'],
    "role": test_user['role'],
    "is_active": test_user['is_active']
}
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_user['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if response.status_code == 400 and "用户名不能为空" in response.json().get('detail', ''):
    print("✅ 用户名空格验证生效！")
else:
    print("❌ 用户名空格验证未生效！")

# 7. 测试客户用户空值验证
print("\n7. 获取客户用户列表...")
response = requests.get(f"{BASE_URL}/api/admin/users/clients", headers=headers)
if response.status_code == 200:
    clients = response.json()
    test_client = clients[0]
    print(f"✅ 获取成功! 测试用户: {test_client['username']} (ID: {test_client['id']})")
else:
    print(f"❌ 获取失败: {response.text}")
    exit(1)

print("\n8. 测试客户用户邮箱为空...")
update_data = {
    "username": test_client['username'],
    "email": "",  # 空邮箱
    "role": test_client['role'],
    "is_active": test_client['is_active']
}
print(f"  请求体: {json.dumps(update_data, ensure_ascii=False)}")

response = requests.put(
    f"{BASE_URL}/api/admin/users/clients/{test_client['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if response.status_code == 400 and "邮箱不能为空" in response.json().get('detail', ''):
    print("✅ 客户用户邮箱空值验证生效！")
else:
    print("❌ 客户用户邮箱空值验证未生效！")

print("\n=== 测试完成 ===")
