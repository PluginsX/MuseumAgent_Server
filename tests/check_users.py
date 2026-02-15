#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的用户
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import SessionLocal
from src.db.models import AdminUser, ClientUser

def check_users():
    """检查数据库中的用户"""
    db = SessionLocal()
    try:
        print("=== 管理员用户 ===")
        admin_users = db.query(AdminUser).all()
        if not admin_users:
            print("  无管理员用户")
        else:
            for user in admin_users:
                print(f"  ID: {user.id}")
                print(f"  用户名: {user.username}")
                print(f"  邮箱: {user.email}")
                print(f"  角色: {user.role}")
                print(f"  活跃: {user.is_active}")
                print(f"  创建时间: {user.created_at}")
                print(f"  最后登录: {user.last_login}")
                print()
        
        print("=== 客户用户 ===")
        client_users = db.query(ClientUser).all()
        if not client_users:
            print("  无客户用户")
        else:
            for user in client_users:
                print(f"  ID: {user.id}")
                print(f"  用户名: {user.username}")
                print(f"  邮箱: {user.email}")
                print(f"  角色: {user.role}")
                print(f"  活跃: {user.is_active}")
                print(f"  创建时间: {user.created_at}")
                print(f"  最后登录: {user.last_login}")
                print()
                
    except Exception as e:
        print(f"检查用户失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
