# -*- coding: utf-8 -*-
"""直接测试 session_service 的登录功能"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.config_utils import load_config
from src.services.session_service import SessionService

async def test_login():
    """测试登录功能"""
    print("=== 测试 session_service 登录功能 ===")
    
    # 加载配置
    load_config("./config/config.json")
    
    session_service = SessionService()
    
    # 测试登录
    print("\n1. 测试登录...")
    credentials = {
        "username": "123",
        "password": "123"
    }
    
    try:
        result = await session_service.login(credentials)
        print(f"登录结果: {result}")
        
        if result.get("code") == 200:
            print("\n✅ 登录成功!")
            print(f"访问令牌: {result.get('data', {}).get('access_token', '')[:50]}...")
        else:
            print(f"\n❌ 登录失败: {result.get('msg', '未知错误')}")
    except Exception as e:
        print(f"\n❌ 登录异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_login())
