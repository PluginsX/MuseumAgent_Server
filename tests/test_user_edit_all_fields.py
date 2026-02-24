# -*- coding: utf-8 -*-
"""测试用户编辑功能 - 所有字段和验证规则"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 测试用户编辑功能 - 所有字段和验证规则 ===")

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
else:
    print(f"❌ 登录失败: {result.get('msg', '未知错误')}")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}"
}

# 2. 创建测试管理员用户
print("\n2. 创建测试管理员用户...")
create_admin_data = {
    "username": "test_admin_edit",
    "email": "test_admin_edit@museum-agent.local",
    "password": "test_password_123",
    "role": "admin"
}
response = requests.post(f"{BASE_URL}/api/admin/users/admins", json=create_admin_data, headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    test_admin = response.json()
    print(f"✅ 创建成功! ID: {test_admin['id']}")
else:
    print(f"❌ 创建失败: {response.text}")
    exit(1)

# 3. 测试编辑用户名
print("\n3. 测试编辑用户名...")
update_data = {
    "username": "test_admin_edited",
    "email": test_admin['email'],
    "role": test_admin['role'],
    "is_active": test_admin['is_active']
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_admin = response.json()
    print(f"✅ 用户名更新成功!")
    print(f"  新用户名: {updated_admin['username']}")
else:
    print(f"❌ 更新失败: {response.text}")

# 4. 测试编辑邮箱
print("\n4. 测试编辑邮箱...")
update_data = {
    "username": updated_admin['username'],
    "email": "test_admin_edited@museum-agent.local",
    "role": updated_admin['role'],
    "is_active": updated_admin['is_active']
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_admin = response.json()
    print(f"✅ 邮箱更新成功!")
    print(f"  新邮箱: {updated_admin['email']}")
else:
    print(f"❌ 更新失败: {response.text}")

# 5. 测试编辑密码
print("\n5. 测试编辑密码...")
update_data = {
    "username": updated_admin['username'],
    "email": updated_admin['email'],
    "role": updated_admin['role'],
    "is_active": updated_admin['is_active'],
    "password": "new_password_456"
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_admin = response.json()
    print(f"✅ 密码更新成功!")
else:
    print(f"❌ 更新失败: {response.text}")

# 6. 测试编辑状态
print("\n6. 测试编辑状态（禁用用户）...")
update_data = {
    "username": updated_admin['username'],
    "email": updated_admin['email'],
    "role": updated_admin['role'],
    "is_active": False
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_admin = response.json()
    print(f"✅ 状态更新成功!")
    print(f"  新状态: {'启用' if updated_admin['is_active'] else '禁用'}")
else:
    print(f"❌ 更新失败: {response.text}")

# 7. 测试编辑角色
print("\n7. 测试编辑角色...")
update_data = {
    "username": updated_admin['username'],
    "email": updated_admin['email'],
    "role": "operator",
    "is_active": True
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_admin = response.json()
    print(f"✅ 角色更新成功!")
    print(f"  新角色: {updated_admin['role']}")
else:
    print(f"❌ 更新失败: {response.text}")

# 8. 测试用户名唯一性验证（使用已存在的用户名）
print("\n8. 测试用户名唯一性验证（使用已存在的用户名）...")
update_data = {
    "username": "admin",  # 已存在的用户名
    "email": updated_admin['email'],
    "role": updated_admin['role'],
    "is_active": updated_admin['is_active']
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 400:
    print(f"✅ 用户名唯一性验证成功!")
    print(f"  错误信息: {response.json().get('detail', '未知错误')}")
else:
    print(f"❌ 验证失败: {response.text}")

# 9. 测试邮箱唯一性验证（使用已存在的邮箱）
print("\n9. 测试邮箱唯一性验证（使用已存在的邮箱）...")
update_data = {
    "username": updated_admin['username'],
    "email": "admin@museum-agent.local",  # 已存在的邮箱
    "role": updated_admin['role'],
    "is_active": updated_admin['is_active']
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 400:
    print(f"✅ 邮箱唯一性验证成功!")
    print(f"  错误信息: {response.json().get('detail', '未知错误')}")
else:
    print(f"❌ 验证失败: {response.text}")

# 10. 测试同时编辑多个字段
print("\n10. 测试同时编辑多个字段...")
update_data = {
    "username": "test_admin_final",
    "email": "test_admin_final@museum-agent.local",
    "role": "admin",
    "is_active": True,
    "password": "final_password_789"
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_admin = response.json()
    print(f"✅ 多字段同时更新成功!")
    print(f"  用户名: {updated_admin['username']}")
    print(f"  邮箱: {updated_admin['email']}")
    print(f"  角色: {updated_admin['role']}")
    print(f"  状态: {'启用' if updated_admin['is_active'] else '禁用'}")
else:
    print(f"❌ 更新失败: {response.text}")

# 11. 测试客户用户编辑
print("\n11. 创建测试客户用户...")
create_client_data = {
    "username": "test_client_edit",
    "email": "test_client_edit@museum-agent.local",
    "password": "test_password_123",
    "role": "client"
}
response = requests.post(f"{BASE_URL}/api/admin/users/clients", json=create_client_data, headers=headers)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    test_client = response.json()
    print(f"✅ 创建成功! ID: {test_client['id']}")
else:
    print(f"❌ 创建失败: {response.text}")
    exit(1)

print("\n12. 测试编辑客户用户...")
update_data = {
    "username": "test_client_edited",
    "email": "test_client_edited@museum-agent.local",
    "role": "client",
    "is_active": True,
    "password": "new_client_password_456"
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/clients/{test_client['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    updated_client = response.json()
    print(f"✅ 客户用户更新成功!")
    print(f"  用户名: {updated_client['username']}")
    print(f"  邮箱: {updated_client['email']}")
else:
    print(f"❌ 更新失败: {response.text}")

# 13. 测试客户用户邮箱唯一性验证
print("\n13. 测试客户用户邮箱唯一性验证...")
update_data = {
    "username": updated_client['username'],
    "email": "client@museum-agent.local",  # 已存在的邮箱
    "role": updated_client['role'],
    "is_active": updated_client['is_active']
}
response = requests.put(
    f"{BASE_URL}/api/admin/users/clients/{test_client['id']}",
    json=update_data,
    headers=headers
)
print(f"状态码: {response.status_code}")
if response.status_code == 400:
    print(f"✅ 客户用户邮箱唯一性验证成功!")
    print(f"  错误信息: {response.json().get('detail', '未知错误')}")
else:
    print(f"❌ 验证失败: {response.text}")

# 14. 清理测试数据
print("\n14. 清理测试数据...")
response = requests.delete(f"{BASE_URL}/api/admin/users/admins/{test_admin['id']}", headers=headers)
print(f"删除测试管理员用户: {'成功' if response.status_code == 200 else '失败'}")

response = requests.delete(f"{BASE_URL}/api/admin/users/clients/{test_client['id']}", headers=headers)
print(f"删除测试客户用户: {'成功' if response.status_code == 200 else '失败'}")

print("\n=== 测试完成 ===")
