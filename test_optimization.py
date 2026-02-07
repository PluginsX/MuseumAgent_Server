#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证架构优化后的MuseumAgent Server功能测试脚本
"""
import requests
import json
import uuid

def test_server_health():
    """测试服务器健康状况"""
    try:
        response = requests.get("http://localhost:8000/api/health")
        print(f"Health check status: {response.status_code}")
        print(f"Health check response: {response.text}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_agent_api():
    """测试代理API功能"""
    # 创建一个模拟会话ID
    session_id = str(uuid.uuid4())
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    
    payload = {
        'user_input': '你好',
        'client_type': 'web3d',
        'spirit_id': '',
        'scene_type': 'public'
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/agent/parse",
            headers=headers,
            json=payload
        )
        print(f"Agent API status: {response.status_code}")
        print(f"Agent API response: {response.text}")
        return True
    except Exception as e:
        print(f"Agent API test failed: {e}")
        return False

if __name__ == "__main__":
    print("开始测试优化后的MuseumAgent Server...")
    print("="*50)
    
    print("\n1. 测试服务器健康状况:")
    test_server_health()
    
    print("\n2. 测试代理API功能:")
    test_agent_api()
    
    print("\n测试完成！")