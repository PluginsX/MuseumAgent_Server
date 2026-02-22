#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API响应结构的脚本
"""
import requests
import json

# 服务器地址
BASE_URL = "http://localhost:8001"

# 登录信息
LOGIN_DATA = {
    "username": "123",
    "password": "123"
}

# 登录获取token
def login():
    """登录获取token"""
    url = f"{BASE_URL}/api/auth/login"
    try:
        print(f"发送登录请求到：{url}")
        print(f"登录数据：{LOGIN_DATA}")
        # 忽略SSL证书验证
        response = requests.post(url, json=LOGIN_DATA, timeout=10, verify=False)
        print(f"响应状态码：{response.status_code}")
        print(f"响应内容：{response.text}")
        response.raise_for_status()
        data = response.json()
        print(f"响应数据：{data}")
        # 从data字段中获取token
        token = data.get("data", {}).get("access_token")
        if token:
            print("登录成功，获取到token")
            return token
        else:
            print("登录失败：未获取到token")
            return None
    except Exception as e:
        print(f"登录失败：{str(e)}")
        return None

# 测试TTS配置API
def test_tts_config(token):
    """测试TTS配置API"""
    url = f"{BASE_URL}/api/admin/config/tts/raw"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        print(f"\n发送TTS配置请求到：{url}")
        # 忽略SSL证书验证
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"响应状态码：{response.status_code}")
        print(f"响应内容：{response.text}")
        response.raise_for_status()
        data = response.json()
        print(f"响应数据：{data}")
        print(f"响应数据类型：{type(data)}")
        print(f"响应数据键值：{list(data.keys())}")
        return data
    except Exception as e:
        print(f"\n获取TTS配置失败：{str(e)}")
        return None

# 测试LLM配置API
def test_llm_config(token):
    """测试LLM配置API"""
    url = f"{BASE_URL}/api/admin/config/llm/raw"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        print(f"\n发送LLM配置请求到：{url}")
        # 忽略SSL证书验证
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"响应状态码：{response.status_code}")
        print(f"响应内容：{response.text}")
        response.raise_for_status()
        data = response.json()
        print(f"响应数据：{data}")
        print(f"响应数据类型：{type(data)}")
        print(f"响应数据键值：{list(data.keys())}")
        return data
    except Exception as e:
        print(f"\n获取LLM配置失败：{str(e)}")
        return None

# 主函数
def main():
    """主函数"""
    print("开始测试API响应结构...")
    
    # 登录获取token
    token = login()
    if not token:
        print("测试失败：无法获取token")
        return
    
    # 测试TTS配置API
    tts_config = test_tts_config(token)
    if tts_config:
        print("\nTTS配置API测试成功")
    else:
        print("\nTTS配置API测试失败")
    
    # 测试LLM配置API
    llm_config = test_llm_config(token)
    if llm_config:
        print("\nLLM配置API测试成功")
    else:
        print("\nLLM配置API测试失败")

if __name__ == "__main__":
    main()
