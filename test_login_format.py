#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试服务器登录API返回的数据格式
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_login_format():
    """测试登录API返回的数据格式"""
    print("=" * 60)
    print("测试服务器登录API返回格式")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            print("\n发送登录请求...")
            async with session.post(
                f"{base_url}/api/auth/login",
                json={"username": "123", "password": "123"}
            ) as response:
                result = await response.json()
                status_code = response.status
                
                print(f"HTTP状态码: {status_code}")
                print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 检查返回的数据结构
                print(f"\n响应结构分析:")
                print(f"- 是否包含 'code': {'code' in result}")
                print(f"- 是否包含 'data': {'data' in result}")
                print(f"- 是否包含 'msg': {'msg' in result}")
                print(f"- 是否包含 'timestamp': {'timestamp' in result}")
                
                if 'data' in result and isinstance(result['data'], dict):
                    data = result['data']
                    print(f"- data中是否包含 'access_token': {'access_token' in data}")
                    print(f"- data中是否包含 'session_id': {'session_id' in data}")
                    print(f"- data中是否包含 'expires_in': {'expires_in' in data}")
                
                # 检查是否符合前端期望的格式
                print(f"\n格式检查:")
                if result.get('code') == 200 and 'data' in result:
                    if 'access_token' in result['data']:
                        token = result['data']['access_token']
                        print(f"- access_token 存在: {len(token)} 字符")
                        if isinstance(token, str) and len(token) > 10:
                            print("  ✓ access_token 格式正确")
                        else:
                            print("  ✗ access_token 格式可能有问题")
                    else:
                        print("  ✗ 缺少 access_token")
                else:
                    print("  ✗ 响应格式不符合预期")
                
    except Exception as e:
        print(f"请求失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_login_format())