import sqlite3
import os

# 连接数据库
db_path = './data/chroma_db/chroma.sqlite3'
print(f"Database path: {os.path.abspath(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看所有表
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", tables)

# 查看collections表
try:
    collections = cursor.execute("SELECT * FROM collections").fetchall()
    print("Collections:", collections)
except Exception as e:
    print("Error querying collections:", e)

# 查看embeddings表
try:
    embeddings_count = cursor.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    print("Embeddings count:", embeddings_count)
    
    # 查看前几条记录
    if embeddings_count > 0:
        sample = cursor.execute("SELECT id, document FROM embeddings LIMIT 3").fetchall()
        print("Sample embeddings:", sample)
except Exception as e:
    print("Error querying embeddings:", e)

conn.close()