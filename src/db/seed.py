# -*- coding: utf-8 -*-
"""初始化默认管理员用户和API密钥"""
import secrets
from datetime import datetime

from src.common.auth_utils import hash_password
from src.db.database import SessionLocal, get_engine, init_db
from src.db.models import AdminUser, ClientUser


def seed_admin():
    """若不存在用户则创建默认 admin"""
    init_db()
    db = SessionLocal()
    try:
        # 检查是否已存在管理员用户
        if db.query(AdminUser).count() > 0:
            return
        
        # 创建默认管理员用户
        admin_password = "Admin@123"
        admin_hash = hash_password(admin_password)
        admin = AdminUser(
            username="admin",
            email="admin@museum-agent.local",
            password_hash=admin_hash,
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.flush()  # 获取ID但不提交
        
        # 创建默认客户用户
        client_password = "Client@123"
        client_hash = hash_password(client_password)
        # 为客户生成API密钥
        client_api_key = f"museum_{secrets.token_urlsafe(32)}"
        client = ClientUser(
            username="client",
            email="client@museum-agent.local",
            password_hash=client_hash,
            api_key=client_api_key,
            role="client",
            is_active=True,
        )
        db.add(client)
        
        db.commit()
        
        print("默认用户创建成功:")
        print(f"  管理员: admin / {admin_password}")
        print(f"  客户: client / {client_password}")
        print(f"  客户API密钥: {client_api_key}")
        
    except Exception as e:
        print(f"初始化默认用户失败: {e}")
        db.rollback()
    finally:
        db.close()
