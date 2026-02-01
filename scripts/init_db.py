# -*- coding: utf-8 -*-
"""
初始化 SQLite 文物知识库 - 创建表结构并插入示例数据
"""
import os
import sys
import sqlite3

# 项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "data", "museum_artifact.db")
TABLE_NAME = "museum_artifact_info"


def init_database():
    """创建数据库表并插入示例数据"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artifact_id TEXT NOT NULL UNIQUE,
            artifact_name TEXT NOT NULL,
            resource_path TEXT,
            operation_params TEXT,
            intro TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_artifact_name 
        ON {TABLE_NAME}(artifact_name)
    """)
    
    # 检查是否已有数据
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    if cursor.fetchone()[0] > 0:
        print("知识库已存在数据，跳过示例数据插入")
        conn.commit()
        conn.close()
        return
    
    # 插入示例文物数据（参考文档中的蟠龙盖罍、卷体夔纹蟠龙盖罍等）
    sample_data = [
        (
            "artifact_001",
            "蟠龙盖罍",
            "/models/panlonggailei.glb",
            '{"zoom": 1.2, "rotate": true}',
            "蟠龙盖罍是商周时期青铜礼器，器盖铸有蟠龙纹饰，造型精美。"
        ),
        (
            "artifact_002",
            "卷体夔纹蟠龙盖罍",
            "/models/juantikuilonggailei.glb",
            '{"zoom": 1.0, "highlight": "夔纹"}',
            "卷体夔纹蟠龙盖罍，盖顶饰卷体蟠龙，器身饰夔纹，纹样繁复精致。"
        ),
        (
            "artifact_003",
            "青铜鼎",
            "/models/qingtongding.glb",
            '{"zoom": 1.5}',
            "青铜鼎是古代重要的饪食器和礼器，象征权力与地位。"
        ),
    ]
    
    cursor.executemany(
        f"""
        INSERT INTO {TABLE_NAME} (artifact_id, artifact_name, resource_path, operation_params, intro)
        VALUES (?, ?, ?, ?, ?)
        """,
        sample_data
    )
    
    conn.commit()
    conn.close()
    print(f"知识库初始化完成: {DB_PATH}")
    print(f"已插入 {len(sample_data)} 条示例文物数据")


if __name__ == "__main__":
    init_database()
