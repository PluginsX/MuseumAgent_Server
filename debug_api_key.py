# -*- coding: utf-8 -*-
"""
调试API密钥存储问题
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db.database import SessionLocal
from src.db.models import AdminUser, ClientUser, APIKey
from src.common.auth_utils import hash_password, verify_password

def debug_api_key_storage():
    """调试API密钥存储问题"""
    print("调试API密钥存储问题...")
    
    db = SessionLocal()
    try:
        # 查询所有管理员用户
        admin_users = db.query(AdminUser).all()
        print(f"管理员用户数: {len(admin_users)}")
        
        # 查询所有客户用户和对应的API密钥
        client_users = db.query(ClientUser).all()
        print(f"客户用户数: {len(client_users)}")
        
        for user in client_users:
            print(f"\n客户用户: {user.username} (ID: {user.id})")
            
            # 查找该用户的API密钥
            api_keys = db.query(APIKey).filter(APIKey.client_user_id == user.id).all()
            for api_key in api_keys:
                print(f"  API密钥: ID={api_key.id}, Active={api_key.is_active}")
                print(f"  存储的哈希: {api_key.key_hash[:30]}..." if len(api_key.key_hash) > 30 else f"  存储的哈希: {api_key.key_hash}")
                print(f"  备注: {api_key.remark}")
        
        # 检查孤立的API密钥（没有对应用户）
        all_api_keys = db.query(APIKey).all()
        for api_key in all_api_keys:
            client_user = db.query(ClientUser).filter(ClientUser.id == api_key.client_user_id).first()
            if not client_user:
                print(f"\n⚠ 发现孤立API密钥 (ID: {api_key.id})，没有对应的客户用户")
    
    except Exception as e:
        print(f"✗ 调试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_api_key_storage()