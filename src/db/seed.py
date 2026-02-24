# -*- coding: utf-8 -*-
"""初始化默认管理员用户和API密钥"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import secrets

from src.common.auth_utils import hash_password
from src.services import database_service


def seed_admin():
    """若不存在用户则创建默认 admin"""
    try:
        # 检查是否已存在管理员用户
        users, total = database_service.list_admin_users(page=1, size=1)
        if total > 0:
            return
        
        # 创建默认管理员用户
        admin_username = "123"
        admin_password = "123"
        admin_email = "1609018168@qq.com"
        admin_hash = hash_password(admin_password)
        admin = database_service.create_admin_user(
            username=admin_username,
            email=admin_email,
            password_hash=admin_hash,
            role="admin",
            is_active=True,
        )
        
        # 创建默认客户用户
        client_username = "123"
        client_password = "123"
        client_email = "1609018168@qq.com"
        client_hash = hash_password(client_password)
        client_api_key = f"museum_{secrets.token_urlsafe(32)}"
        client = database_service.create_client_user(
            username=client_username,
            password_hash=client_hash,
            api_key=client_api_key,
            email=client_email,
            role="client",
            is_active=True,
        )
        
        print("默认用户创建成功:")
        print(f"  管理员: {admin_username} / {admin_password}")
        print(f"  管理员邮箱: {admin_email}")
        print(f"  客户: {client_username} / {client_password}")
        print(f"  客户邮箱: {client_email}")
        print(f"  客户API密钥: {client_api_key}")
        
    except Exception as e:
        print(f"初始化默认用户失败: {e}")
