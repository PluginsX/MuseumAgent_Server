#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试访问记录功能

验证server_access_logs表是否正确记录了访问日志
"""
import sys
import os
import sqlite3
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import get_engine
from src.common.access_log_manager import access_log_manager


def test_access_log_table_exists():
    """测试访问日志表是否存在"""
    print("=== 测试访问日志表是否存在 ===")
    
    try:
        engine = get_engine()
        with engine.connect() as connection:
            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'server_access_logs' in tables:
                print("✅ 访问日志表存在")
                
                # 查看表结构
                columns = inspector.get_columns('server_access_logs')
                print("表结构:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
                
                return True
            else:
                print("❌ 访问日志表不存在")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_manual_log_insert():
    """测试手动插入访问日志"""
    print("\n=== 测试手动插入访问日志 ===")
    
    try:
        # 插入一条测试日志
        test_log = {
            'client_user_id': 1,
            'request_type': 'TEST_REQUEST',
            'endpoint': '/test/endpoint',
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Agent/1.0',
            'status_code': 200,
            'response_time': 150,
            'details': 'Test access log entry'
        }
        
        access_log_manager.add_log(test_log)
        print("✅ 手动插入访问日志成功")
        
        # 等待一段时间，让工作线程处理日志
        import time
        time.sleep(3)  # 等待3秒
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_log_records_exist():
    """测试访问日志记录是否存在"""
    print("\n=== 测试访问日志记录是否存在 ===")
    
    try:
        engine = get_engine()
        with engine.connect() as connection:
            # 查询最近的访问日志记录
            from sqlalchemy import text
            result = connection.execute(
                text("""
                SELECT id, request_type, endpoint, ip_address, status_code, created_at 
                FROM server_access_logs 
                ORDER BY created_at DESC 
                LIMIT 10
                """)
            )
            
            rows = result.fetchall()
            
            if rows:
                print(f"✅ 找到 {len(rows)} 条访问日志记录")
                print("最近的访问日志记录:")
                
                for i, row in enumerate(rows[:5]):  # 只显示前5条
                    print(f"  {i+1}. [{row.created_at}] {row.request_type} {row.endpoint} - {row.status_code} - {row.ip_address}")
                
                return True
            else:
                print("❌ 没有找到访问日志记录")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_log_count_increase():
    """测试访问日志计数是否增加"""
    print("\n=== 测试访问日志计数是否增加 ===")
    
    try:
        engine = get_engine()
        
        # 获取当前日志计数
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(
                text("SELECT COUNT(*) FROM server_access_logs")
            )
            initial_count = result.scalar()
            print(f"初始日志计数: {initial_count}")
        
        # 插入多条测试日志
        for i in range(5):
            test_log = {
                'client_user_id': i + 1,
                'request_type': f'TEST_REQUEST_{i}',
                'endpoint': f'/test/endpoint/{i}',
                'ip_address': '127.0.0.1',
                'status_code': 200 + i % 5,
                'details': f'Test access log entry {i}'
            }
            access_log_manager.add_log(test_log)
        
        print("✅ 插入5条测试日志")
        
        # 等待工作线程处理
        import time
        time.sleep(3)
        
        # 再次获取日志计数
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(
                text("SELECT COUNT(*) FROM server_access_logs")
            )
            final_count = result.scalar()
            print(f"最终日志计数: {final_count}")
        
        if final_count > initial_count:
            print(f"✅ 日志计数增加了 {final_count - initial_count} 条")
            return True
        else:
            print("❌ 日志计数没有增加")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("开始测试访问记录功能\n")
    
    # 运行所有测试
    tests = [
        test_access_log_table_exists,
        test_manual_log_insert,
        test_log_records_exist,
        test_log_count_increase
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    # 测试总结
    print(f"=== 测试总结 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
