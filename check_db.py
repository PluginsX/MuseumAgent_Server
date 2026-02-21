# -*- coding: utf-8 -*-
"""检查数据库文件的位置"""
from src.db.database import get_engine
import os

# 获取数据库引擎
engine = get_engine()
print(f'Database URL: {engine.url}')

# 提取数据库文件路径
db_path = str(engine.url).replace('sqlite:///', '')
print(f'Database file exists: {os.path.exists(db_path)}')
print(f'Database file path: {db_path}')
print(f'Directory exists: {os.path.exists(os.path.dirname(db_path))}')

# 列出目录中的文件
if os.path.exists(os.path.dirname(db_path)):
    print('Files in directory:')
    for file in os.listdir(os.path.dirname(db_path)):
        print(f'  - {file}')
