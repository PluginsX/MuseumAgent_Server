#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试API响应结构 - 绕过RAG模块
"""

import requests
import json
import ssl
from datetime import datetime

def test_api_response_structure():
    """直接测试API响应结构"""
    print("🧪 API响应结构测试")
    print("=" * 50)
    
    # 创建SSL上下文
    session = requests.Session()
    session.verify = False
    requests.packages.urllib3.disable_warnings()
    
    base_url = "https://localhost:8000"
    
    # 1. 注册会话（无函数定义的普通对话模式）
    print("1. 注册普通对话会话...")
    
    try:
        response = session.post(
            f"{base_url}/api/session/register",
            json={
                "client_metadata": {
                    "client_id": "structure_test",
                    "client_type": "test",
                    "client_version": "1.0.0"
                },
                "functions": []  # 空函数列表 = 普通对话模式
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 会话注册失败: {response.status_code}")
            return
            
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✅ 会话ID: {session_id[:8]}...")
        
        # 2. 测试普通对话响应结构
        print("\n2. 测试普通对话响应结构...")
        test_message = "你好"
        
        response = session.post(
            f"{base_url}/api/agent/parse",
            headers={"session-id": session_id},
            json={
                "user_input": test_message,
                "client_type": "test",
                "scene_type": "public"
            },
            timeout=15
        )
        
        print(f"📤 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 API响应码: {result.get('code')}")
            
            if result.get('code') == 200 and result.get('data'):
                data = result['data']
                print(f"\n📊 响应结构:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 验证字段结构
                print(f"\n🔍 字段验证:")
                expected_fields = ['response', 'timestamp', 'session_id', 'processing_mode', 'type']
                for field in expected_fields:
                    if field in data:
                        print(f"  ✅ {field}: {repr(data[field])}")
                    else:
                        print(f"  ❌ 缺少字段: {field}")
                
                # 检查是否还有旧的冗余字段
                legacy_fields = ['command', 'parameters', 'format', 'artifact_id', 'artifact_name', 'operation', 'operation_params', 'keywords', 'tips']
                found_legacy = []
                for field in legacy_fields:
                    if field in data and data[field] is not None:
                        found_legacy.append(field)
                
                if found_legacy:
                    print(f"\n⚠️  发现遗留字段: {found_legacy}")
                else:
                    print(f"\n✅ 无遗留冗余字段")
                    
                # 检查是否有function_call字段
                if 'function_call' in data:
                    print(f"  ✅ function_call字段存在")
                else:
                    print(f"  ⚠️  无function_call字段（普通对话模式正常）")
                    
            else:
                print(f"❌ API响应异常: {result}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_with_simple_mock():
    """使用简单模拟测试数据结构"""
    print("\n🎭 简单模拟测试")
    print("=" * 50)
    
    # 模拟CommandGenerator应该返回的数据结构
    mock_response = {
        "response": "你好！有什么我可以帮助你的吗？",
        "timestamp": "2026-02-04T20:47:00.000000",
        "session_id": "mock_session_id",
        "processing_mode": "openai_function_calling",
        "type": "direct_response"
    }
    
    print("模拟普通对话响应:")
    print(json.dumps(mock_response, indent=2, ensure_ascii=False))
    
    # 模拟函数调用响应
    mock_function_response = {
        "response": "我将为您显示愤怒的表情。",
        "function_call": {
            "name": "show_emotion",
            "arguments": "{\n  \"emotion\": \"angry\"\n}"
        },
        "timestamp": "2026-02-04T20:47:00.000000",
        "session_id": "mock_session_id",
        "processing_mode": "openai_function_calling",
        "type": "function_call"
    }
    
    print("\n模拟函数调用响应:")
    print(json.dumps(mock_function_response, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("🚀 API响应结构验证测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试API响应结构
    test_api_response_structure()
    
    # 模拟测试
    test_with_simple_mock()
    
    print(f"\n🏁 测试完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")