# -*- coding: utf-8 -*-
"""
检查server_access_logs表中的访问记录
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import get_engine
from sqlalchemy import text

def check_access_logs():
    """检查server_access_logs表中的访问记录"""
    print("检查server_access_logs表中的访问记录...")
    
    try:
        engine = get_engine()
        with engine.connect() as connection:
            # 查询表中的所有记录
            result = connection.execute(text("SELECT * FROM server_access_logs ORDER BY created_at DESC"))
            records = result.fetchall()
            
            print(f"\n找到 {len(records)} 条访问记录:")
            print("=" * 100)
            
            # 打印每条记录
            for record in records:
                print(f"ID: {record.id}")
                print(f"时间: {record.created_at}")
                print(f"请求类型: {record.request_type}")
                print(f"端点: {record.endpoint}")
                print(f"IP地址: {record.ip_address}")
                print(f"状态码: {record.status_code}")
                print(f"响应时间: {record.response_time}ms")
                print(f"详细信息: {record.details}")
                print(f"管理员用户ID: {record.admin_user_id}")
                print(f"客户用户ID: {record.client_user_id}")
                print("-" * 100)
                
            if not records:
                print("表中没有记录，访问日志功能可能未正常工作。")
                
    except Exception as e:
        print(f"查询数据库时出错: {e}")
        
if __name__ == "__main__":
    check_access_logs()
