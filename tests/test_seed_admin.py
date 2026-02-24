# -*- coding: utf-8 -*-
"""测试默认用户自动创建功能"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.db.seed import seed_admin
from src.db.database import SessionLocal
from src.db.models import AdminUser, ClientUser


def test_seed_admin():
    """测试默认用户创建"""
    print("=" * 60)
    print("测试默认用户自动创建")
    print("=" * 60)
    
    # 先检查当前用户数量
    with SessionLocal() as db:
        admin_count = db.query(AdminUser).count()
        client_count = db.query(ClientUser).count()
        print(f"\n当前状态:")
        print(f"  管理员用户数量: {admin_count}")
        print(f"  客户用户数量: {client_count}")
    
    # 调用 seed_admin
    print(f"\n调用 seed_admin()...")
    seed_admin()
    
    # 检查创建后的用户
    with SessionLocal() as db:
        admin_users = db.query(AdminUser).all()
        client_users = db.query(ClientUser).all()
        
        print(f"\n创建后状态:")
        print(f"  管理员用户数量: {len(admin_users)}")
        for admin in admin_users:
            print(f"    - ID: {admin.id}, 用户名: {admin.username}, 邮箱: {admin.email}, 角色: {admin.role}")
        
        print(f"  客户用户数量: {len(client_users)}")
        for client in client_users:
            print(f"    - ID: {client.id}, 用户名: {client.username}, 邮箱: {client.email}, 角色: {client.role}, API Key: {client.api_key[:20]}...")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_seed_admin()
