# -*- coding: utf-8 -*-
"""更新MySQL数据库中的用户密码"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.config_utils import load_config
from src.common.auth_utils import hash_password
from src.db.database import SessionLocal
from src.db.models import AdminUser

# 加载配置
load_config("./config/config.json")

print("=== 更新MySQL数据库中的用户密码 ===")

# 更新管理员用户密码
username = "123"
password = "123"
password_hash = hash_password(password)

print(f"\n用户名: {username}")
print(f"密码: {password}")
print(f"密码哈希: {password_hash}")

# 使用MySQL数据库连接
with SessionLocal() as db:
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if user:
        user.password_hash = password_hash
        db.commit()
        print(f"\n✅ 密码更新成功!")
        print(f"用户ID: {user.id}")
        print(f"用户名: {user.username}")
    else:
        print(f"\n❌ 未找到用户!")
