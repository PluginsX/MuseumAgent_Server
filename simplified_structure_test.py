#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证简化数据结构和直通响应的测试
"""

import requests
import json
import ssl
from datetime import datetime

def test_simplified_response():
    """测试简化后的响应结构"""
    print("🧪 简化数据结构测试")
    print("=" * 50)
    
    # 创建SSL上下文
    session = requests.Session()
    session.verify = False
    requests.packages.urllib3.disable_warnings()
    
    base_url = "https://localhost:8000"
    
    # 1. 注册会话
    print("1. 注册测试会话...")
    functions = [
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
                    "client_id": "simplified_test",
                    "client_type": "test",
                    "client_version": "1.0.0"
                },
                "functions": functions
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 会话注册失败: {response.status_code}")
            return
            
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✅ 会话ID: {session_id[:8]}...")
        
        # 2. 测试函数调用
        print("\n2. 测试函数调用响应结构...")
        test_message = "show_emotion 愤怒"
        
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
                print(f"\n📊 简化后的响应结构:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 验证字段结构
                print(f"\n🔍 字段验证:")
                required_fields = ['response', 'timestamp', 'session_id', 'processing_mode', 'type']
                for field in required_fields:
                    if field in data:
                        print(f"  ✅ {field}: {repr(data[field])}")
                    else:
                        print(f"  ❌ 缺少字段: {field}")
                
                # 检查是否有函数调用数据
                if 'function_call' in data:
                    print(f"  ✅ function_call: {data['function_call']}")
                    print(f"     函数名: {data['function_call'].get('name')}")
                    print(f"     参数: {data['function_call'].get('arguments')}")
                else:
                    print(f"  ⚠️  无function_call字段")
                    
                # 检查是否还有旧的冗余字段
                legacy_fields = ['command', 'parameters', 'format', 'artifact_id', 'artifact_name', 'operation', 'operation_params']
                found_legacy = []
                for field in legacy_fields:
                    if field in data:
                        found_legacy.append(field)
                
                if found_legacy:
                    print(f"\n⚠️  发现遗留字段: {found_legacy}")
                else:
                    print(f"\n✅ 无遗留冗余字段")
                    
            else:
                print(f"❌ API响应异常: {result}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def compare_old_vs_new():
    """对比新旧响应结构"""
    print("\n🔄 新旧结构对比")
    print("=" * 50)
    
    # 模拟旧结构
    old_structure = {
        "artifact_id": None,
        "artifact_name": None,
        "operation": None,
        "operation_params": None,
        "keywords": None,
        "tips": None,
        "response": "对话内容",
        "command": "show_emotion",
        "parameters": {"emotion": "angry"},
        "type": "function_call",
        "format": "openai_standard",
        "timestamp": "2026-02-04T20:38:44.685982",
        "session_id": "99970c66-84dd-4fd1-8c01-2ddd71c098cf",
        "processing_mode": "openai_function_calling"
    }
    
    # 模拟新结构
    new_structure = {
        "response": "对话内容",
        "function_call": {
            "name": "show_emotion",
            "arguments": "{\n  \"emotion\": \"angry\"\n}"
        },
        "type": "function_call",
        "timestamp": "2026-02-04T20:38:44.685982",
        "session_id": "99970c66-84dd-4fd1-8c01-2ddd71c098cf",
        "processing_mode": "openai_function_calling"
    }
    
    print("旧结构字段数:", len(old_structure))
    print("新结构字段数:", len(new_structure))
    print("减少字段数:", len(old_structure) - len(new_structure))
    
    print(f"\n旧结构大小: {len(json.dumps(old_structure))} 字符")
    print(f"新结构大小: {len(json.dumps(new_structure))} 字符")
    print(f"减少大小: {len(json.dumps(old_structure)) - len(json.dumps(new_structure))} 字符")

if __name__ == "__main__":
    print("🚀 简化数据结构验证测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试简化响应
    test_simplified_response()
    
    # 对比新旧结构
    compare_old_vs_new()
    
    print(f"\n🏁 测试完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")