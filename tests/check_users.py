# -*- coding: utf-8 -*-
"""检查数据库中的用户数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import SessionLocal
from src.db.models import AdminUser, ClientUser

print("=== 检查数据库中的用户数据 ===")

with SessionLocal() as db:
    # 检查管理员用户
    admin_users = db.query(AdminUser).all()
    print(f"\n管理员用户数量: {len(admin_users)}")
    for user in admin_users:
        print(f"  - ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}, 激活: {user.is_active}")
    
    # 检查客户用户
    client_users = db.query(ClientUser).all()
    print(f"\n客户用户数量: {len(client_users)}")
    for user in client_users:
        print(f"  - ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}, 激活: {user.is_active}")
