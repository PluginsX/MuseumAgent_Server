#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新初始化数据库并创建测试账号
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import init_db, get_db
from src.db.models import AdminUser, ClientUser
from src.common.auth_utils import hash_password

def main():
    """主函数"""
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "museum_agent_app.db")
    
    # 删除数据库文件（如果存在）
    if os.path.exists(db_path):
        print(f"删除现有数据库文件: {db_path}")
        os.remove(db_path)
    else:
        print(f"数据库文件不存在: {db_path}")
    
    # 创建 data 目录（如果不存在）
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 初始化数据库表结构
    print("初始化数据库表结构...")
    init_db()
    print("数据库表结构初始化完成!")
    
    # 创建测试账号
    print("创建测试账号...")
    
    # 密码哈希
    password_hash = hash_password("123")
    
    # API密钥（使用固定值）
    api_key = "test-api-key-123"
    
    # 使用上下文管理器创建会话
    with get_db() as db:
        # 创建管理员账号
        admin_user = AdminUser(
            username="123",
            email="admin@example.com",
            password_hash=password_hash,
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        
        # 创建客户账号
        client_user = ClientUser(
            username="123",
            email="client@example.com",
            password_hash=password_hash,
            api_key=api_key,
            role="client",
            is_active=True
        )
        db.add(client_user)
        
        # 提交事务
        db.commit()
        print("测试账号创建完成!")
    
    print("\n操作完成!")
    print("管理员账号: 用户名=123, 密码=123")
    print("客户账号: 用户名=123, 密码=123, API密钥=test-api-key-123")

if __name__ == "__main__":
    main()
