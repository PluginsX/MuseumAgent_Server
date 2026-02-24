# -*- coding: utf-8 -*-
"""清空数据库并重新测试自动初始化"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.db.database import SessionLocal
from src.db.models import AdminUser, ClientUser, ServerAccessLog


def clear_database():
    """清空数据库"""
    print("=" * 60)
    print("清空数据库")
    print("=" * 60)
    
    with SessionLocal() as db:
        # 删除所有访问日志
        db.query(ServerAccessLog).delete()
        
        # 删除所有客户用户
        db.query(ClientUser).delete()
        
        # 删除所有管理员用户
        db.query(AdminUser).delete()
        
        db.commit()
        
        print("数据库已清空！")
        print("管理员用户数量: 0")
        print("客户用户数量: 0")
    
    print("=" * 60)


if __name__ == "__main__":
    clear_database()
