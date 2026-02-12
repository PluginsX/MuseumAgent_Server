#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模拟前端登录响应处理
用于调试前端可能存在的数据访问问题
"""

import asyncio
import aiohttp
import json


async def simulate_frontend_processing():
    """模拟前端处理登录响应"""
    print("=" * 60)
    print("模拟前端登录响应处理")
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
                
                print(f"服务器响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 模拟前端可能的处理逻辑
                print("\n模拟前端处理逻辑:")
                
                # 1. 检查是否有code字段
                print(f"1. 检查code: {result.get('code')}")
                
                # 2. 检查data字段是否存在
                print(f"2. 检查data字段: {'data' in result}")
                
                if 'data' in result:
                    data = result['data']
                    print(f"3. data内容: {data}")
                    
                    # 4. 检查access_token是否存在
                    if 'access_token' in data:
                        token = data['access_token']
                        print(f"4. access_token存在: {len(token)} 字符")
                        
                        # 模拟前端可能执行的操作 - 这可能导致substring错误
                        try:
                            # 模拟前端可能的JWT解码操作
                            parts = token.split('.')
                            print(f"5. JWT token parts: {len(parts)} 部分")
                            
                            if len(parts) >= 2:
                                # 尝试获取payload部分
                                import base64
                                payload = parts[1]
                                # 确保是正确的base64格式
                                payload += '=' * (4 - len(payload) % 4)  # 补齐
                                
                                decoded = base64.b64decode(payload)
                                print(f"6. 解码成功: {decoded.decode('utf-8', errors='ignore')[:100]}...")
                                
                        except Exception as e:
                            print(f"6. JWT处理异常 (这可能是前端错误原因): {e}")
                            
                        # 模拟一些可能的字符串操作
                        try:
                            # 这种操作可能导致substring错误
                            if token is not None:
                                sub_part = token[:10] if len(token) > 10 else token
                                print(f"7. 子串操作成功: {sub_part}")
                            else:
                                print("7. 令牌为None，会导致substring错误")
                        except Exception as e:
                            print(f"7. 子串操作异常: {e}")
                    else:
                        print("4. access_token 不存在 - 这可能导致前端错误")
                else:
                    print("3. data字段不存在 - 这是前端错误的根本原因!")
                
                # 检查前端可能错误访问的路径
                print(f"\n检查前端可能错误访问的路径:")
                print(f"- response.access_token: {result.get('access_token', 'NOT_FOUND')}")
                print(f"- response.data.access_token: {result.get('data', {}).get('access_token', 'NOT_FOUND')}")
                
                print(f"\n前端应使用: response.data.access_token")
                print(f"前端不应使用: response.access_token")
                
    except Exception as e:
        print(f"请求失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simulate_frontend_processing())