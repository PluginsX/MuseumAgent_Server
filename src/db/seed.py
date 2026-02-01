# -*- coding: utf-8 -*-
"""初始化默认管理员用户"""
from src.common.auth_utils import hash_password
from src.db.database import SessionLocal, get_engine, init_db
from src.db.models import User


def seed_admin():
    """若不存在用户则创建默认 admin"""
    init_db()
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        # 默认 admin / Admin@123
        default_hash = hash_password("Admin@123")
        admin = User(
            username="admin",
            email="admin@museum-agent.local",
            password_hash=default_hash,
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()
