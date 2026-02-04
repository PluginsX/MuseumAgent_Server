#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细数据流转测试脚本 - 诊断函数调用字段为null的问题
"""

import requests
import json
import ssl
from datetime import datetime

def create_ssl_context():
    """创建忽略证书验证的SSL上下文"""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

def test_api_connectivity():
    """测试API连接性"""
    print("🔍 API连接性测试")
    print("=" * 50)
    
    # 使用自定义SSL上下文
    session = requests.Session()
    session.verify = False
    requests.packages.urllib3.disable_warnings()
    
    base_url = "https://localhost:8000"
    
    try:
        # 测试根路径
        response = session.get(f"{base_url}/", timeout=5)
        print(f"✅ 健康检查: HTTP {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 测试会话统计
        response = session.get(f"{base_url}/api/session/stats", timeout=5)
        print(f"✅ 会话统计: HTTP {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   活跃会话数: {stats.get('active_sessions', 0)}")
            print(f"   总会话数: {stats.get('total_sessions', 0)}")
            
        return True, session
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False, None

def test_session_registration(session):
    """测试会话注册"""
    print("\n📝 会话注册测试")
    print("=" * 50)
    
    base_url = "https://localhost:8000"
    
    # 准备函数定义
    functions = [
        {
            "name": "move_to_position",
            "description": "移动到指定坐标位置",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "X坐标"},
                    "y": {"type": "number", "description": "Y坐标"}
                },
                "required": ["x", "y"]
            }
        },
        {
            "name": "show_emotion",
            "description": "显示情感表情",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotion": {
                        "type": "string", 
                        "description": "情感类型",
                        "enum": ["happy", "sad", "angry", "surprised", "neutral"]
                    }
                },
                "required": ["emotion"]
            }
        }
    ]
    
    try:
        response = session.post(
            f"{base_url}/api/session/register",
            json={
                "client_metadata": {
                    "client_id": "debug_client_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "client_type": "desktop_pet",
                    "client_version": "1.0.0",
                    "platform": "windows",
                    "capabilities": ["function_calling", "real_time_interaction"]
                },
                "functions": functions
            },
            timeout=10
        )
        
        print(f"📤 注册请求状态: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            print(f"✅ 会话注册成功")
            print(f"   会话ID: {session_id}")
            print(f"   过期时间: {result.get('expires_at')}")
            print(f"   支持功能: {result.get('supported_features', [])}")
            return session_id
        else:
            print(f"❌ 注册失败: {response.status_code}")
            print(f"   错误详情: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 注册过程异常: {e}")
        return None

def test_chat_interaction(session, session_id):
    """测试聊天交互"""
    print("\n💬 聊天交互测试")
    print("=" * 50)
    
    base_url = "https://localhost:8000"
    test_messages = [
        "移动到(0，0)",
        "显示开心的表情",
        "你好，我是桌宠小助手"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- 测试消息 {i}: {message} ---")
        
        try:
            response = session.post(
                f"{base_url}/api/agent/parse",
                headers={"session-id": session_id},
                json={
                    "user_input": message,
                    "client_type": "desktop_pet",
                    "scene_type": "public"
                },
                timeout=15
            )
            
            print(f"📤 请求状态: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📥 响应码: {result.get('code')}")
                print(f"📥 响应消息: {result.get('msg')}")
                
                if result.get('code') == 200 and result.get('data'):
                    data = result['data']
                    print(f"\n📊 详细数据字段:")
                    
                    # 按类别显示字段
                    traditional_fields = ['artifact_id', 'artifact_name', 'operation', 'operation_params', 'keywords', 'tips', 'response']
                    openai_fields = ['command', 'parameters', 'type', 'format']
                    metadata_fields = ['timestamp', 'session_id', 'processing_mode']
                    
                    print("传统字段:")
                    for field in traditional_fields:
                        value = data.get(field)
                        status = "✅" if value is not None else "❌"
                        print(f"  {status} {field}: {repr(value)}")
                    
                    print("\nOpenAI函数调用字段:")
                    for field in openai_fields:
                        value = data.get(field)
                        status = "✅" if value is not None else "❌"
                        print(f"  {status} {field}: {repr(value)}")
                    
                    print("\n元数据字段:")
                    for field in metadata_fields:
                        value = data.get(field)
                        status = "✅" if value is not None else "❌"
                        print(f"  {status} {field}: {repr(value)}")
                    
                    # 检查关键问题
                    null_openai_fields = [field for field in openai_fields if data.get(field) is None]
                    if null_openai_fields:
                        print(f"\n⚠️  发现null的OpenAI字段: {null_openai_fields}")
                    else:
                        print(f"\n✅ 所有OpenAI字段都有值")
                        
                    # 显示完整响应内容
                    print(f"\n📄 完整响应数据:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                else:
                    print(f"❌ 响应数据异常: {result}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"   错误详情: {response.text}")
                
        except Exception as e:
            print(f"❌ 消息处理异常: {e}")

def trace_llm_process():
    """追踪LLM处理过程"""
    print("\n🤖 LLM处理过程追踪")
    print("=" * 50)
    
    try:
        from src.core.dynamic_llm_client import DynamicLLMClient
        from src.session.strict_session_manager import strict_session_manager
        
        llm_client = DynamicLLMClient()
        
        # 创建测试会话
        session_id = "llm_trace_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        functions = [
            {
                "name": "move_to_position",
                "description": "移动到指定坐标位置",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "X坐标"},
                        "y": {"type": "number", "description": "Y坐标"}
                    },
                    "required": ["x", "y"]
                }
            }
        ]
        
        strict_session_manager.register_session_with_functions(
            session_id=session_id,
            client_metadata={
                "client_id": "llm_trace_client",
                "client_type": "test",
                "client_version": "1.0.0"
            },
            functions=functions
        )
        
        print(f"✅ 创建LLM测试会话: {session_id}")
        
        # 生成请求负载
        user_input = "移动到(0，0)"
        payload = llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input=user_input,
            scene_type="public",
            functions=functions
        )
        
        print(f"\n📤 LLM请求负载:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # 实际调用LLM
        print(f"\n📡 调用LLM API...")
        response = llm_client._chat_completions_with_functions(payload)
        
        print(f"\n📥 LLM原始响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 解析响应
        parsed_result = llm_client.parse_function_call_response(response)
        print(f"\n📊 解析后结果:")
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
        
        return parsed_result
        
    except Exception as e:
        print(f"❌ LLM过程追踪失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主测试函数"""
    print("🚀 MuseumAgent 数据流转诊断测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 测试API连接性
    connected, session = test_api_connectivity()
    if not connected:
        print("❌ 无法连接到服务器，测试终止")
        return
    
    # 2. 测试会话注册
    session_id = test_session_registration(session)
    if not session_id:
        print("❌ 会话注册失败，测试终止")
        return
    
    # 3. 测试聊天交互
    test_chat_interaction(session, session_id)
    
    # 4. 追踪LLM处理过程
    trace_llm_process()
    
    print(f"\n🏁 诊断测试完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()