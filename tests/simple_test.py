#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试断开客户端会话接口
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"

def test_disconnect():
    """
    测试断开会话接口
    """
    print("=== 测试断开会话接口 ===")
    
    # 测试获取客户端列表
    print("1. 获取客户端列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/clients/connected")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_disconnect()
