#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中用户的密码哈希值
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import SessionLocal
from src.db.models import AdminUser
from src.common.auth_utils import verify_password

def check_password_hash():
    """检查数据库中用户的密码哈希值"""
    db = SessionLocal()
    try:
        print("=== 检查用户密码哈希 ===")
        
        # 检查用户名123的用户
        user = db.query(AdminUser).filter(AdminUser.username == "123").first()
        if user:
            print(f"用户: {user.username}")
            print(f"密码哈希: {user.password_hash}")
            print(f"哈希长度: {len(user.password_hash)}")
            print(f"哈希以$2开头: {user.password_hash.startswith('$2')}")
            
            # 测试密码验证
            test_passwords = ["123", "Admin@123", "client", "Client@123"]
            print("\n密码验证测试:")
            for pwd in test_passwords:
                is_valid = verify_password(pwd, user.password_hash)
                print(f"  密码 '{pwd}' -> {'有效' if is_valid else '无效'}")
        else:
            print("未找到用户 '123'")
            
    except Exception as e:
        print(f"检查失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_password_hash()
