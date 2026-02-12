#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试断开特定客户端会话
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"
SESSION_ID = "ec3b8f22-1785-4cf0-b526-bf9406027420"

def test_disconnect_specific_session():
    """
    测试断开特定会话
    """
    print("=== 测试断开特定会话 ===")
    print(f"会话ID: {SESSION_ID}")
    
    # 测试断开连接
    print("1. 发送断开请求...")
    try:
        response = requests.delete(f"{BASE_URL}/api/admin/clients/session/{SESSION_ID}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ 断开成功！")
        else:
            print("❌ 断开失败！")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_disconnect_specific_session()
