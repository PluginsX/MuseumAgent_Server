#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API调试测试脚本 - 专门用于诊断函数调用数据null问题
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoints():
    """测试API端点连通性"""
    base_url = "http://localhost:8000"
    
    print("🔍 API端点连通性测试")
    print("=" * 50)
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ 健康检查: HTTP {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False
    
    # 测试会话统计
    try:
        response = requests.get(f"{base_url}/api/session/stats", timeout=5)
        print(f"✅ 会话统计: HTTP {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   活跃会话数: {stats.get('active_sessions', 0)}")
    except Exception as e:
        print(f"⚠️  会话统计接口异常: {e}")
    
    # 测试agent解析接口（不带会话）
    try:
        response = requests.post(
            f"{base_url}/api/agent/parse",
            json={
                "user_input": "你好",
                "client_type": "debug_test",
                "scene_type": "public"
            },
            timeout=10
        )
        print(f"✅ Agent解析接口: HTTP {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   响应码: {result.get('code')}")
            print(f"   响应消息: {result.get('msg')}")
            if result.get('data'):
                print(f"   数据字段: {list(result['data'].keys())}")
        else:
            print(f"   错误详情: {response.text}")
    except Exception as e:
        print(f"❌ Agent解析接口测试失败: {e}")
    
    return True

def test_full_flow():
    """测试完整的数据流转"""
    base_url = "http://localhost:8000"
    
    print("\n🔄 完整数据流测试")
    print("=" * 50)
    
    # 1. 注册会话（带函数定义）
    print("步骤1: 注册会话")
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
    
    try:
        response = requests.post(
            f"{base_url}/api/session/register",
            json={
                "client_metadata": {
                    "client_id": "debug_test_client",
                    "client_type": "debug",
                    "client_version": "1.0.0",
                    "platform": "test"
                },
                "functions": functions
            },
            timeout=10
        )
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get('session_id')
            print(f"✅ 会话注册成功: {session_id[:8]}...")
            print(f"   过期时间: {session_data.get('expires_at')}")
        else:
            print(f"❌ 会话注册失败: HTTP {response.status_code}")
            print(f"   错误: {response.text}")
            return
    except Exception as e:
        print(f"❌ 会话注册异常: {e}")
        return
    
    # 2. 发送测试消息
    print("\n步骤2: 发送测试消息")
    test_message = "移动到(0，0)"
    
    try:
        response = requests.post(
            f"{base_url}/api/agent/parse",
            headers={"session-id": session_id},
            json={
                "user_input": test_message,
                "client_type": "debug_test",
                "scene_type": "public"
            },
            timeout=15
        )
        
        print(f"📤 发送请求: {test_message}")
        print(f"📥 收到响应: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 完整响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 分析响应数据
            if result.get('code') == 200 and result.get('data'):
                data = result['data']
                print(f"\n📊 响应数据分析:")
                print(f"   - artifact_id: {data.get('artifact_id')}")
                print(f"   - artifact_name: {data.get('artifact_name')}")
                print(f"   - operation: {data.get('operation')}")
                print(f"   - operation_params: {data.get('operation_params')}")
                print(f"   - command: {data.get('command')}")
                print(f"   - parameters: {data.get('parameters')}")
                print(f"   - response: {repr(data.get('response'))}")
                print(f"   - type: {data.get('type')}")
                print(f"   - format: {data.get('format')}")
                
                # 检查关键字段是否为null
                null_fields = []
                for field in ['command', 'parameters', 'type', 'format']:
                    if data.get(field) is None:
                        null_fields.append(field)
                
                if null_fields:
                    print(f"\n⚠️  发现null字段: {null_fields}")
                else:
                    print(f"\n✅ 所有关键字段都有值")
            else:
                print(f"❌ 响应格式异常: {result}")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试消息发送异常: {e}")

def test_direct_llm_call():
    """直接测试LLM调用"""
    print("\n🤖 直接LLM调用测试")
    print("=" * 50)
    
    try:
        from src.core.dynamic_llm_client import DynamicLLMClient
        from src.session.strict_session_manager import strict_session_manager
        
        llm_client = DynamicLLMClient()
        
        # 创建测试会话
        session_id = "debug-direct-test"
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
                "client_id": "direct_test",
                "client_type": "test",
                "client_version": "1.0.0"
            },
            functions=functions
        )
        
        print(f"✅ 创建测试会话: {session_id}")
        
        # 生成并发送请求
        user_input = "移动到(0，0)"
        payload = llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input=user_input,
            scene_type="public",
            functions=functions
        )
        
        print(f"\n📤 LLM请求负载:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # 调用LLM
        response = llm_client._chat_completions_with_functions(payload)
        print(f"\n📥 LLM原始响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 解析响应
        parsed_result = llm_client.parse_function_call_response(response)
        print(f"\n📊 解析后的结果:")
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
        
        return parsed_result
        
    except Exception as e:
        print(f"❌ 直接LLM调用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主测试函数"""
    print("🚀 MuseumAgent API调试测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试API端点
    if not test_api_endpoints():
        print("❌ API端点测试失败，退出测试")
        return
    
    # 测试完整流程
    test_full_flow()
    
    # 直接测试LLM调用
    llm_result = test_direct_llm_call()
    
    print(f"\n🏁 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()