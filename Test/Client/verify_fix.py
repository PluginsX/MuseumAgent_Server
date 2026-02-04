#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证客户端修复的脚本
测试会话注册和心跳功能
"""

import requests
import json
import time

def test_session_registration():
    """测试会话注册功能"""
    print("=" * 50)
    print("测试会话注册功能")
    print("=" * 50)
    
    base_url = "https://localhost:8000"
    
    # 测试数据
    registration_data = {
        "client_metadata": {
            "client_id": "test_client_" + str(int(time.time())),
            "client_type": "test",
            "client_version": "1.0.0",
            "platform": "web-test-client",
            "capabilities": {
                "max_concurrent_requests": 3,
                "supported_scenes": ["study", "leisure", "public"],
                "preferred_response_format": "json",
                "function_calling_supported": True
            }
        },
        "functions": [
            {
                "name": "test_function",
                "description": "测试函数",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_param": {
                            "type": "string",
                            "description": "测试参数"
                        }
                    },
                    "required": ["test_param"]
                }
            }
        ]
    }
    
    try:
        print("发送注册请求...")
        response = requests.post(
            f"{base_url}/api/session/register",
            headers={"Content-Type": "application/json"},
            json=registration_data,
            verify=False,
            timeout=10
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 会话注册成功!")
            print(f"会话ID: {result.get('session_id')}")
            print(f"过期时间: {result.get('expires_at')}")
            print(f"支持功能: {result.get('supported_features', [])}")
            return result.get('session_id')
        else:
            print(f"❌ 注册失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None

def test_heartbeat(session_id):
    """测试心跳功能"""
    if not session_id:
        print("没有有效的会话ID，跳过心跳测试")
        return False
        
    print("\n" + "=" * 50)
    print("测试心跳功能")
    print("=" * 50)
    
    base_url = "https://localhost:8000"
    
    try:
        print("发送心跳请求...")
        response = requests.post(
            f"{base_url}/api/session/heartbeat",
            headers={
                "Content-Type": "application/json",
                "session-id": session_id
            },
            verify=False,
            timeout=10
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 心跳成功!")
            print(f"状态: {result.get('status')}")
            print(f"会话有效: {result.get('session_valid')}")
            return True
        else:
            print(f"❌ 心跳失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 心跳异常: {str(e)}")
        return False

def test_message_processing(session_id):
    """测试消息处理功能"""
    if not session_id:
        print("没有有效的会话ID，跳过消息处理测试")
        return False
        
    print("\n" + "=" * 50)
    print("测试消息处理功能")
    print("=" * 50)
    
    base_url = "https://localhost:8000"
    
    message_data = {
        "user_input": "你好，这是一个测试消息",
        "client_type": "test",
        "scene_type": "public"
    }
    
    try:
        print("发送消息处理请求...")
        response = requests.post(
            f"{base_url}/api/agent/parse",
            headers={
                "Content-Type": "application/json",
                "session-id": session_id
            },
            json=message_data,
            verify=False,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 消息处理成功!")
            print(f"响应码: {result.get('code')}")
            print(f"消息: {result.get('msg')}")
            if result.get('data'):
                print(f"数据: {json.dumps(result['data'], ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 消息处理失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 消息处理异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始客户端修复验证测试")
    
    # 测试会话注册
    session_id = test_session_registration()
    
    # 如果注册成功，继续测试
    if session_id:
        # 等待一下再测试心跳
        time.sleep(1)
        heartbeat_success = test_heartbeat(session_id)
        
        # 测试消息处理
        time.sleep(1)
        message_success = test_message_processing(session_id)
        
        print("\n" + "=" * 50)
        print("测试总结")
        print("=" * 50)
        print(f"会话注册: {'✅ 成功' if session_id else '❌ 失败'}")
        print(f"心跳功能: {'✅ 成功' if heartbeat_success else '❌ 失败'}")
        print(f"消息处理: {'✅ 成功' if message_success else '❌ 失败'}")
        
        if session_id and heartbeat_success and message_success:
            print("\n🎉 所有测试通过！客户端修复成功！")
        else:
            print("\n⚠️  部分测试失败，请检查相关功能")
    else:
        print("\n❌ 会话注册失败，无法继续测试")

if __name__ == "__main__":
    main()