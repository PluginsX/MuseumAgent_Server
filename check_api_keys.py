# -*- coding: utf-8 -*-
"""检查API密钥的情况"""
from src.db.database import get_db_session
from src.db.models import APIKey, ClientUser

# 获取数据库会话
db = next(get_db_session())

try:
    # 查询所有API密钥
    keys = db.query(APIKey).all()
    print(f'Found {len(keys)} API keys')
    
    for key in keys:
        # 检查key_plaintext字段是否存在
        plaintext = getattr(key, "key_plaintext", "Not found")
        print(f'Key ID: {key.id}, Client ID: {key.client_user_id}, Plaintext: {plaintext}')
    
    # 查询所有客户用户
    clients = db.query(ClientUser).all()
    print(f'\nFound {len(clients)} client users')
    
    for client in clients:
        # 查询客户的API密钥
        api_key = db.query(APIKey).filter(APIKey.client_user_id == client.id).first()
        api_key_str = getattr(api_key, "key_plaintext", "Not found") if api_key else "No API key"
        print(f'Client ID: {client.id}, Username: {client.username}, API Key: {api_key_str}')
        
except Exception as e:
    print(f'Error: {str(e)}')
finally:
    db.close()
