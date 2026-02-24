# -*- coding: utf-8 -*-
"""测试邮箱空值验证 - 只修改邮箱"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试邮箱空值验证 - 只修改邮箱 ===")

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

# 3. 测试只修改邮箱为空
print("\n3. 测试只修改邮箱为空...")
update_data = {
    "email": ""  # 只修改邮箱为空
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

print("\n=== 测试完成 ===")
