# -*- coding: utf-8 -*-
"""测试密码哈希和验证"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.auth_utils import hash_password, verify_password
from src.db.database import SessionLocal
from src.db.models import AdminUser

print("=== 测试密码哈希和验证 ===")

# 测试密码哈希
password = "123"
password_hash = hash_password(password)
print(f"\n密码: {password}")
print(f"密码哈希: {password_hash}")

# 测试密码验证
is_valid = verify_password(password, password_hash)
print(f"密码验证结果: {is_valid}")

# 从数据库中获取用户并验证
with SessionLocal() as db:
    user = db.query(AdminUser).filter(AdminUser.username == "123").first()
    if user:
        print(f"\n数据库中的用户:")
        print(f"  用户名: {user.username}")
        print(f"  邮箱: {user.email}")
        print(f"  密码哈希: {user.password_hash}")
        print(f"  激活: {user.is_active}")
        
        # 验证密码
        is_valid = verify_password(password, user.password_hash)
        print(f"\n密码验证结果: {is_valid}")
    else:
        print("\n未找到用户!")
