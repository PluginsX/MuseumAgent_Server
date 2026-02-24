# -*- coding: utf-8 -*-
"""更新用户密码"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.auth_utils import hash_password
from src.services import database_service

print("=== 更新用户密码 ===")

# 更新管理员用户密码
username = "123"
password = "123"
password_hash = hash_password(password)

print(f"\n用户名: {username}")
print(f"密码: {password}")
print(f"密码哈希: {password_hash}")

# 更新数据库中的用户
user = database_service.update_admin_user(
    user_id=1,
    password_hash=password_hash
)

if user:
    print(f"\n✅ 密码更新成功!")
    print(f"用户ID: {user.id}")
    print(f"用户名: {user.username}")
else:
    print(f"\n❌ 密码更新失败!")
