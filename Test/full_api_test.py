#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整API流程测试 - 从请求到响应的全流程验证
"""

import sys
import os
import json
import time
import requests
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_full_api_flow():
    """测试完整的API流程"""
    print("=" * 80)
    print("🧪 完整API流程测试")
    print("=" * 80)
    
    base_url = "https://localhost:8000"
    
    # 1. 注册普通对话会话
    print("\n1. 注册普通对话会话")
    print("-" * 40)
    
    session = requests.Session()
    session.verify = False
    
    try:
        response = session.post(
            f"{base_url}/api/session/register",
            json={
                "client_metadata": {
                    "client_id": "api_flow_test",
                    "client_type": "test",
                    "client_version": "1.0.0"
                },
                "functions": []  # 空函数列表 = 普通对话模式
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 会话注册失败: {response.status_code}")
            print(response.text)
            return
            
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✅ 会话注册成功: {session_id[:8]}...")
        
        # 2. 发送普通对话请求
        print("\n2. 发送普通对话请求")
        print("-" * 40)
        
        test_messages = [
            "你好",
            "你会干什么",
            "介绍一下辽宁省博物馆"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 测试消息 {i}: {message}")
            print("-" * 30)
            
            try:
                response = session.post(
                    f"{base_url}/api/agent/parse",
                    headers={"session-id": session_id},
                    json={
                        "user_input": message,
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
                        print(f"📊 完整响应数据:")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        
                        # 分析字段结构
                        print(f"\n🔍 字段分析:")
                        
                        # 检查旧字段
                        old_fields = ["artifact_id", "artifact_name", "operation", "operation_params", "keywords", "tips"]
                        found_old = []
                        for field in old_fields:
                            if field in data and data[field] is not None:
                                found_old.append((field, data[field]))
                        
                        if found_old:
                            print(f"❌ 发现旧字段:")
                            for field, value in found_old:
                                print(f"   {field}: {value}")
                        else:
                            print("✅ 无旧字段")
                            
                        # 检查LLM原始字段
                        llm_fields = ["choices", "created", "id", "model", "object", "usage"]
                        found_llm = [field for field in llm_fields if field in data]
                        print(f"✅ LLM原始字段: {found_llm}")
                        
                        # 检查OpenAI标准字段
                        openai_fields = ["command", "parameters", "type", "format"]
                        found_openai = [field for field in openai_fields if field in data and data[field] is not None]
                        print(f"✅ OpenAI字段: {found_openai}")
                        
                        # 检查对话内容
                        response_content = data.get("response", "")
                        print(f"💬 对话内容: {repr(response_content)}")
                        
                    else:
                        print(f"❌ API响应异常: {result}")
                else:
                    print(f"❌ API请求失败: {response.status_code}")
                    print(response.text)
                    
            except Exception as e:
                print(f"❌ 请求异常: {e}")
                
    except Exception as e:
        print(f"❌ 会话注册异常: {e}")

def compare_responses():
    """对比不同场景下的响应结构"""
    print("\n" + "=" * 80)
    print("🔄 响应结构对比分析")
    print("=" * 80)
    
    # 模拟用户看到的有问题的响应
    problematic_response = {
        "artifact_id": None,
        "artifact_name": None,
        "operation": None,
        "operation_params": None,
        "keywords": None,
        "tips": None,
        "response": None,
        "command": None,
        "parameters": None,
        "type": None,
        "format": None,
        "timestamp": None,
        "session_id": None,
        "processing_mode": None,
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "我可以帮助你了解各种文物的详细信息，比如它们的历史背景、艺术特色等。此外，我还可以控制桌面宠物移动到指定的位置，或者表达不同的情绪状态。如果你有任何问题或需要帮助，请随时告诉我！",
                    "role": "assistant"
                }
            }
        ],
        "created": 1770216830,
        "id": "chatcmpl-c8bead38-2d76-90ef-a6df-415a7101adff",
        "model": "qwen-turbo",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 47,
            "prompt_tokens": 650,
            "prompt_tokens_details": {
                "cached_tokens": 0
            },
            "total_tokens": 697
        }
    }
    
    # 我们期望的干净响应
    clean_response = {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "我可以帮助你了解各种文物的详细信息，比如它们的历史背景、艺术特色等。此外，我还可以控制桌面宠物移动到指定的位置，或者表达不同的情绪状态。如果你有任何问题或需要帮助，请随时告诉我！",
                    "role": "assistant"
                }
            }
        ],
        "created": 1770216830,
        "id": "chatcmpl-c8bead38-2d76-90ef-a6df-415a7101adff",
        "model": "qwen-turbo",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 47,
            "prompt_tokens": 650,
            "prompt_tokens_details": {
                "cached_tokens": 0
            },
            "total_tokens": 697
        }
    }
    
    print("问题响应字段数:", len(problematic_response))
    print("干净响应字段数:", len(clean_response))
    print("多余字段数:", len(problematic_response) - len(clean_response))
    
    # 找出多余的字段
    extra_fields = set(problematic_response.keys()) - set(clean_response.keys())
    print(f"多余字段: {sorted(extra_fields)}")
    
    print(f"\n问题响应大小: {len(json.dumps(problematic_response))} 字符")
    print(f"干净响应大小: {len(json.dumps(clean_response))} 字符")
    print(f"减少大小: {len(json.dumps(problematic_response)) - len(json.dumps(clean_response))} 字符")

if __name__ == "__main__":
    print("🚀 完整API流程测试")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试完整API流程
    test_full_api_flow()
    
    # 对比响应结构
    compare_responses()
    
    print(f"\n🏁 测试完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")