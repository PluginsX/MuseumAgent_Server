# -*- coding: utf-8 -*-
"""调试登录过程"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.config_utils import load_config
from src.services.session_service import SessionService
from src.services import database_service
from src.common.auth_utils import verify_password

async def test_login_debug():
    """测试登录功能 - 调试版本"""
    print("=== 调试登录过程 ===")
    
    # 加载配置
    load_config("./config/config.json")
    
    # 1. 直接从数据库获取用户
    print("\n1. 从数据库获取用户...")
    user = database_service.get_admin_user_by_username("123")
    if user:
        print(f"✅ 找到用户:")
        print(f"   用户名: {user.username}")
        print(f"   邮箱: {user.email}")
        print(f"   激活: {user.is_active}")
        print(f"   角色: {user.role}")
        print(f"   密码哈希: {user.password_hash}")
        
        # 2. 测试密码验证
        print("\n2. 测试密码验证...")
        password = "123"
        is_valid = verify_password(password, user.password_hash)
        print(f"   密码 '{password}' 验证结果: {is_valid}")
        
        if not is_valid:
            print("   ❌ 密码验证失败!")
            return
    else:
        print("❌ 未找到用户!")
        return
    
    # 3. 测试 session_service 的登录
    print("\n3. 测试 session_service 登录...")
    session_service = SessionService()
    
    credentials = {
        "username": "123",
        "password": "123"
    }
    
    # 手动调用 _authenticate_user
    print("\n4. 手动调用 _authenticate_user...")
    authenticated_user = await session_service._authenticate_user("123", "123")
    if authenticated_user:
        print(f"✅ 用户认证成功:")
        print(f"   用户名: {authenticated_user.get('username')}")
        print(f"   角色: {authenticated_user.get('role')}")
        print(f"   激活: {authenticated_user.get('active')}")
    else:
        print("❌ 用户认证失败!")
        return
    
    # 5. 调用完整的登录方法
    print("\n5. 调用完整的登录方法...")
    result = await session_service.login(credentials)
    print(f"登录结果: {result}")
    
    if result.get("code") == 200:
        print("\n✅ 登录成功!")
    else:
        print(f"\n❌ 登录失败: {result.get('msg', '未知错误')}")

if __name__ == "__main__":
    asyncio.run(test_login_debug())
