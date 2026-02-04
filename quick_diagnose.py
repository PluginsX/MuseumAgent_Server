#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速诊断测试 - 直接检查数据流转问题
"""

import requests
import json
import ssl
from datetime import datetime

def quick_test():
    """快速测试函数"""
    print("⚡ 快速诊断测试")
    print("=" * 40)
    
    # 创建SSL上下文
    session = requests.Session()
    session.verify = False
    requests.packages.urllib3.disable_warnings()
    
    base_url = "https://localhost:8000"
    
    # 1. 注册会话
    print("1. 注册会话...")
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
        response = session.post(
            f"{base_url}/api/session/register",
            json={
                "client_metadata": {
                    "client_id": "quick_test",
                    "client_type": "test",
                    "client_version": "1.0.0"
                },
                "functions": functions
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 会话注册失败: {response.status_code}")
            print(response.text)
            return
            
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✅ 会话ID: {session_id[:8]}...")
        
        # 2. 发送测试消息
        print("\n2. 发送测试消息...")
        test_message = "移动到(0，0)"
        
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
        
        print(f"📤 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 响应码: {result.get('code')}")
            
            if result.get('code') == 200 and result.get('data'):
                data = result['data']
                print(f"\n📊 关键字段检查:")
                
                # 检查传统字段
                print("传统字段:")
                for field in ['artifact_id', 'artifact_name', 'operation', 'operation_params']:
                    value = data.get(field)
                    status = "✅" if value is not None else "❌"
                    print(f"  {status} {field}: {repr(value)}")
                
                # 检查OpenAI字段（重点）
                print("\nOpenAI函数调用字段:")
                openai_fields = ['command', 'parameters', 'type', 'format']
                for field in openai_fields:
                    value = data.get(field)
                    status = "✅" if value is not None else "❌"
                    print(f"  {status} {field}: {repr(value)}")
                
                # 检查响应内容
                print(f"\n💬 对话内容: {repr(data.get('response'))}")
                
                # 统计null字段
                null_fields = []
                for field in openai_fields:
                    if data.get(field) is None:
                        null_fields.append(field)
                
                if null_fields:
                    print(f"\n⚠️  NULL字段: {null_fields}")
                    print("❌ 问题确认：OpenAI函数调用字段确实为null")
                else:
                    print("\n✅ 所有OpenAI字段都有值")
                    
                print(f"\n📄 完整响应:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
            else:
                print(f"❌ 响应数据异常: {result}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()