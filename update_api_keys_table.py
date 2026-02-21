# -*- coding: utf-8 -*-
"""手动更新API密钥表结构"""
from src.db.database import get_engine
import sqlite3

# 获取数据库引擎
engine = get_engine()
db_path = str(engine.url).replace('sqlite:///', '')

# 连接到SQLite数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查api_keys表是否存在key_plaintext列
    cursor.execute("PRAGMA table_info(api_keys)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    print(f'Current columns in api_keys table: {column_names}')
    
    # 如果key_plaintext列不存在，则添加它
    if 'key_plaintext' not in column_names:
        print('Adding key_plaintext column to api_keys table...')
        cursor.execute("ALTER TABLE api_keys ADD COLUMN key_plaintext TEXT")
        conn.commit()
        print('key_plaintext column added successfully!')
    else:
        print('key_plaintext column already exists!')
    
    # 检查api_keys表的结构
    cursor.execute("PRAGMA table_info(api_keys)")
    updated_columns = cursor.fetchall()
    print(f'Updated columns in api_keys table: {[column[1] for column in updated_columns]}')
    
except Exception as e:
    print(f'Error: {str(e)}')
    conn.rollback()
finally:
    conn.close()
