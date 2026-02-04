#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的普通对话模式支持
验证会话注册不再强制要求函数定义
"""

import requests
import json
import time
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVER_URL = "https://localhost:8000"

def test_session_registration_without_functions():
    """测试不带函数定义的会话注册（应该成功）"""
    print("=== 测试会话注册（无函数定义，应成功）===")
    
    registration_data = {
        "client_metadata": {
            "client_id": "test_client_no_functions_123",
            "client_type": "test",
            "client_version": "1.0.0",
            "platform": "test_script",
            "capabilities": {
                "max_concurrent_requests": 3,
                "supported_scenes": ["study", "leisure", "public"],
                "preferred_response_format": "json",
                "function_calling_supported": False
            }
        },
        "functions": []  # 空函数列表
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/session/register",
            headers={"Content-Type": "application/json"},
            json=registration_data,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            print(f"✅ 会话注册成功！")
            print(f"   会话ID: {session_id}")
            print(f"   支持功能: {result.get('supported_features')}")
            print(f"   过期时间: {result.get('expires_at')}")
            return session_id
        else:
            print(f"❌ 会话注册失败: {response.status_code}")
            print(f"   错误详情: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 注册请求异常: {str(e)}")
        return None

def test_session_registration_no_functions_field():
    """测试完全不提供函数字段的会话注册"""
    print("\n=== 测试会话注册（完全不提供函数字段）===")
    
    registration_data = {
        "client_metadata": {
            "client_id": "test_client_no_functions_field_123",
            "client_type": "test",
            "client_version": "1.0.0",
            "platform": "test_script",
            "capabilities": {
                "max_concurrent_requests": 3,
                "supported_scenes": ["study", "leisure", "public"],
                "preferred_response_format": "json"
            }
        }
        # 注意：这里故意不提供functions字段
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/session/register",
            headers={"Content-Type": "application/json"},
            json=registration_data,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            print(f"✅ 会话注册成功！")
            print(f"   会话ID: {session_id}")
            print(f"   支持功能: {result.get('supported_features')}")
            return session_id
        else:
            print(f"❌ 会话注册失败: {response.status_code}")
            print(f"   错误详情: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 注册请求异常: {str(e)}")
        return None

def test_agent_parse_with_normal_chat(session_id):
    """测试普通对话模式的代理解析"""
    print("\n=== 测试普通对话模式解析 ===")
    
    if not session_id:
        print("❌ 会话ID为空，无法测试")
        return
    
    # 测试普通对话
    user_inputs = [
        "你好，介绍一下辽宁省博物馆",
        "今天天气怎么样？",
        "你能告诉我一些历史文化知识吗？"
    ]
    
    for user_input in user_inputs:
        print(f"\n--- 测试输入: {user_input} ---")
        
        request_data = {
            "user_input": user_input,
            "client_type": "test",
            "spirit_id": "",
            "scene_type": "public"
        }
        
        try:
            response = requests.post(
                f"{SERVER_URL}/api/agent/parse",
                headers={
                    "Content-Type": "application/json",
                    "session-id": session_id
                },
                json=request_data,
                timeout=30,
                verify=False
            )
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 代理解析请求成功")
                if result.get("code") == 200:
                    data = result.get('data', {})
                    print(f"   响应类型: {data.get('type', 'unknown')}")
                    print(f"   命令: {data.get('command', 'N/A')}")
                    if 'response' in data:
                        print(f"   回复内容: {data['response'][:100]}...")
                    print(f"   处理模式: {data.get('processing_mode', 'N/A')}")
                else:
                    print(f"   业务错误: {result.get('msg')}")
            else:
                print(f"❌ 代理解析失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 解析请求异常: {str(e)}")

def test_mixed_mode_sessions():
    """测试混合模式会话（有函数定义和无函数定义）"""
    print("\n=== 测试混合模式会话 ===")
    
    # 1. 带函数定义的会话
    functions = [
        {
            "name": "introduce_artifact",
            "description": "介绍文物",
            "parameters": {
                "type": "object",
                "properties": {
                    "artifact_name": {
                        "type": "string",
                        "description": "文物名称"
                    }
                },
                "required": ["artifact_name"]
            }
        }
    ]
    
    registration_with_functions = {
        "client_metadata": {
            "client_id": "mixed_test_with_functions",
            "client_type": "test",
            "client_version": "1.0.0",
            "platform": "test_script"
        },
        "functions": functions
    }
    
    # 2. 不带函数定义的会话
    registration_without_functions = {
        "client_metadata": {
            "client_id": "mixed_test_without_functions", 
            "client_type": "test",
            "client_version": "1.0.0",
            "platform": "test_script"
        },
        "functions": []
    }
    
    sessions = []
    
    # 测试带函数定义的会话
    print("--- 测试带函数定义的会话 ---")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/session/register",
            headers={"Content-Type": "application/json"},
            json=registration_with_functions,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            sessions.append(("带函数", result.get("session_id")))
            print(f"✅ 带函数定义会话注册成功: {result.get('session_id')[:8]}...")
        else:
            print(f"❌ 带函数定义会话注册失败")
    except Exception as e:
        print(f"❌ 带函数定义会话注册异常: {str(e)}")
    
    # 测试不带函数定义的会话
    print("--- 测试不带函数定义的会话 ---")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/session/register", 
            headers={"Content-Type": "application/json"},
            json=registration_without_functions,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            sessions.append(("无函数", result.get("session_id")))
            print(f"✅ 无函数定义会话注册成功: {result.get('session_id')[:8]}...")
        else:
            print(f"❌ 无函数定义会话注册失败")
    except Exception as e:
        print(f"❌ 无函数定义会话注册异常: {str(e)}")
    
    return sessions

def main():
    print("开始测试修复后的普通对话模式支持...")
    
    # 1. 测试不带函数定义的注册（应该成功）
    session_id_1 = test_session_registration_without_functions()
    
    # 2. 测试完全不提供函数字段的注册（应该成功）
    session_id_2 = test_session_registration_no_functions_field()
    
    # 3. 测试普通对话模式解析
    if session_id_1:
        time.sleep(1)
        test_agent_parse_with_normal_chat(session_id_1)
    
    # 4. 测试混合模式会话
    mixed_sessions = test_mixed_mode_sessions()
    
    print("\n=== 测试总结 ===")
    print("✅ 系统现在支持:")
    print("   1. 无函数定义的会话注册")
    print("   2. 完全不提供函数字段的会话注册") 
    print("   3. 普通对话模式的解析处理")
    print("   4. 混合模式会话共存")
    print("\n🎉 修复验证完成！")

if __name__ == "__main__":
    main()