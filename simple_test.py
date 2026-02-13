#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试服务器端点
"""

import requests
import json

def test_endpoint():
    print("测试服务器端点...")
    
    # 测试根路径
    try:
        response = requests.get("http://localhost:8080/")
        print(f"根路径响应: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"根路径请求失败: {e}")
    
    # 测试会话注册
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            "client_metadata": {
                "client_type": "test_client",
                "version": "1.0.0",
                "capabilities": ["text", "audio", "voice"]
            },
            "functions": []
        }
        response = requests.post("http://localhost:8080/api/session/register", 
                                headers=headers, json=data)
        print(f"会话注册响应: {response.status_code}")
        if response.status_code == 200:
            print(f"会话注册成功: {response.json()}")
        else:
            print(f"会话注册失败: {response.text}")
    except Exception as e:
        print(f"会话注册请求失败: {e}")

if __name__ == "__main__":
    test_endpoint()