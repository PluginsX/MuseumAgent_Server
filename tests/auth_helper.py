#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证工具模块
用于获取访问令牌和会话ID
"""

import requests
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.common.config_utils import load_config, get_global_config

def get_auth_tokens():
    """获取认证令牌和会话ID"""
    try:
        # 加载配置
        load_config()
        config = get_global_config()
        
        # 使用默认的测试账户
        credentials = {
            "username": "123",
            "password": "123"
        }
        
        # 登录获取访问令牌
        login_url = "http://localhost:8001/api/auth/login"
        response = requests.post(login_url, json=credentials, timeout=10)
        
        if response.status_code != 200:
            print(f"登录失败: {response.status_code} - {response.text}")
            return None
        
        auth_data = response.json()
        access_token = auth_data.get('access_token')
        
        if not access_token:
            print("未能获取访问令牌")
            return None
        
        # 注册会话获取session_id
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        session_url = "http://localhost:8001/api/session/register"
        session_data_payload = {"action": "register"}  # 提供数据以满足FastAPI参数要求
        session_response = requests.post(session_url, headers=headers, json=session_data_payload, timeout=10)
        
        if session_response.status_code != 200:
            print(f"会话注册失败: {session_response.status_code} - {session_response.text}")
            return None
        
        session_data = session_response.json()
        session_id = session_data.get('session_id')
        
        if not session_id:
            print("未能获取会话ID")
            return None
        
        print(f"认证成功 - 令牌: {access_token[:10]}..., 会话ID: {session_id}")
        return {
            "access_token": access_token,
            "session_id": session_id
        }
        
    except requests.exceptions.ConnectionError:
        print("无法连接到服务器，请确保服务器正在运行")
        return None
    except Exception as e:
        print(f"认证过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_auth_tokens_async():
    """异步版本的认证函数"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_auth_tokens)


if __name__ == "__main__":
    tokens = get_auth_tokens()
    if tokens:
        print("认证信息获取成功:")
        print(f"  Access Token: {tokens['access_token']}")
        print(f"  Session ID: {tokens['session_id']}")
    else:
        print("认证失败")