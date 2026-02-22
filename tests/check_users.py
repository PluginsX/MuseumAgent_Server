#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的用户
"""
import sqlite3
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "museum_agent_app.db")

def check_users():
    """检查数据库中的用户"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 查询admin_users表
        print("查询admin_users表中的用户：")
        cursor.execute("SELECT id, username, email, role, is_active FROM admin_users")
        users = cursor.fetchall()
        
        if users:
            print(f"找到 {len(users)} 个用户：")
            for user in users:
                print(f"ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 角色: {user[3]}, 激活状态: {user[4]}")
        else:
            print("admin_users表中没有用户")
        
        # 查询user表（如果存在）
        print("\n查询user表中的用户：")
        try:
            cursor.execute("SELECT id, username, email, role, is_active FROM user")
            users = cursor.fetchall()
            
            if users:
                print(f"找到 {len(users)} 个用户：")
                for user in users:
                    print(f"ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 角色: {user[3]}, 激活状态: {user[4]}")
            else:
                print("user表中没有用户")
        except sqlite3.OperationalError:
            print("user表不存在")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"检查用户失败：{str(e)}")

if __name__ == "__main__":
    check_users()
