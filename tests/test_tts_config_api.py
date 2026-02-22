#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TTS配置API的脚本
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

# 获取TTS配置
def get_tts_config(token):
    """获取TTS配置"""
    url = f"{BASE_URL}/api/admin/config/tts/raw"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        # 忽略SSL证书验证
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        data = response.json()
        print("\n获取TTS配置成功：")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return data
    except Exception as e:
        print(f"\n获取TTS配置失败：{str(e)}")
        print(f"响应状态码：{response.status_code if 'response' in locals() else '未知'}")
        if 'response' in locals():
            try:
                print(f"响应内容：{response.text}")
            except:
                pass
        return None

# 主函数
def main():
    """主函数"""
    print("开始测试TTS配置API...")
    
    # 登录获取token
    token = login()
    if not token:
        print("测试失败：无法获取token")
        return
    
    # 获取TTS配置
    config = get_tts_config(token)
    if config:
        print("\n测试成功：TTS配置API正常工作")
    else:
        print("\n测试失败：TTS配置API无法正常工作")

if __name__ == "__main__":
    main()
