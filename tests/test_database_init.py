# -*- coding: utf-8 -*-
"""测试数据库自动初始化功能"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.db.database import SessionLocal
from src.db.models import AdminUser, ClientUser


def check_database_status():
    """检查数据库状态"""
    print("=" * 60)
    print("数据库状态检查")
    print("=" * 60)
    
    with SessionLocal() as db:
        # 检查管理员用户
        admin_users = db.query(AdminUser).all()
        print(f"\n管理员用户数量: {len(admin_users)}")
        for admin in admin_users:
            print(f"  - ID: {admin.id}, 用户名: {admin.username}, 邮箱: {admin.email}, 角色: {admin.role}, 激活: {admin.is_active}")
        
        # 检查客户用户
        client_users = db.query(ClientUser).all()
        print(f"\n客户用户数量: {len(client_users)}")
        for client in client_users:
            print(f"  - ID: {client.id}, 用户名: {client.username}, 邮箱: {client.email}, 角色: {client.role}, 激活: {client.is_active}")
        
        # 检查表是否存在
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        print(f"\n数据库表数量: {len(tables)}")
        print(f"表列表: {', '.join(tables)}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_database_status()
