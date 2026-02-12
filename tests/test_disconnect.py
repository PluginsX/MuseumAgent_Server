#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试断开客户端会话接口
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"

def test_disconnect_session():
    """
    测试断开会话接口
    """
    print("=== 测试断开会话接口 ===")
    
    # 步骤1：先获取当前连接的客户端列表
    print("1. 获取当前客户端列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/clients/connected")
        if response.status_code == 200:
            clients = response.json()
            print(f"   成功获取 {len(clients)} 个客户端")
            
            if len(clients) > 0:
                # 选择第一个客户端进行测试
                client = clients[0]
                session_id = client.get('session_id')
                client_type = client.get('client_type')
                
                print(f"   选择测试客户端: {client_type} (session_id: {session_id[:8]}...)")
                
                # 步骤2：测试断开连接
                print(f"2. 测试断开会话 {session_id[:8]}...")
                try:
                    disconnect_response = requests.delete(f"{BASE_URL}/api/admin/clients/session/{session_id}")
                    print(f"   断开请求状态码: {disconnect_response.status_code}")
                    print(f"   断开请求响应: {json.dumps(disconnect_response.json(), indent=2, ensure_ascii=False)}")
                    
                    if disconnect_response.status_code == 200:
                        print("   ✅ 断开成功！")
                    else:
                        print("   ❌ 断开失败！")
                        
                except Exception as e:
                    print(f"   ❌ 断开请求失败: {e}")
            else:
                print("   ℹ 没有活跃客户端，无法测试断开功能")
        else:
            print(f"   ❌ 获取客户端列表失败: {response.status_code} - {response.text}")
            
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

if __name__ == "__main__":
    test_disconnect_session()
