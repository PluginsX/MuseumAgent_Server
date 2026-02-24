# -*- coding: utf-8 -*-
"""直接测试登录 API"""
import requests
import json

BASE_URL = "http://localhost:12301"

print("=== 直接测试登录 API ===")

# 1. 测试登录
print("\n1. 测试登录...")
login_data = {
    "username": "123",
    "password": "123"
}
try:
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"\n解析后的 JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except:
            print("无法解析 JSON")
except Exception as e:
    print(f"请求失败: {e}")
