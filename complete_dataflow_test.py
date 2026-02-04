#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整数据流转测试 - 从LLM响应到API响应的全流程验证
"""

import json
from datetime import datetime
from typing import Dict, Any

def simulate_complete_dataflow():
    """模拟完整的数据流转过程"""
    print("🔄 完整数据流转模拟测试")
    print("=" * 50)
    
    # 先加载配置
    from src.common.config_utils import load_config
    load_config()
    
    from src.core.command_generator import CommandGenerator
    from src.session.strict_session_manager import strict_session_manager
    # 移除StandardCommand导入，该模型已被废弃
    # from src.models.response_models import StandardCommand
    
    print("步骤1: 创建测试会话")
    session_id = "dataflow_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
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
            "client_id": "dataflow_test",
            "client_type": "test",
            "client_version": "1.0.0"
        },
        functions=functions
    )
    print(f"✅ 会话创建成功: {session_id}")
    
    print("\n步骤2: 模拟LLM函数调用响应")
    # 模拟LLM返回的真实函数调用响应
    mock_llm_response = {
        "id": "chatcmpl-dataflow-test",
        "object": "chat.completion",
        "created": 1707064900,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "好的，我将帮您移动到坐标(0,0)的位置。",
                    "function_call": {
                        "name": "move_to_position",
                        "arguments": "{\n  \"x\": 0,\n  \"y\": 0\n}"
                    }
                },
                "finish_reason": "function_call"
            }
        ]
    }
    print("✅ 模拟LLM响应创建完成")
    print(f"   函数调用: {mock_llm_response['choices'][0]['message']['function_call']['name']}")
    print(f"   参数: {mock_llm_response['choices'][0]['message']['function_call']['arguments']}")
    print(f"   对话内容: {repr(mock_llm_response['choices'][0]['message']['content'])}")
    
    print("\n步骤3: 测试CommandGenerator处理")
    generator = CommandGenerator()
    
    # 直接测试解析函数（绕过LLM调用）
    from src.core.dynamic_llm_client import DynamicLLMClient
    llm_client = DynamicLLMClient()
    
    try:
        # 使用LLM客户端解析响应
        parsed_result = llm_client.parse_function_call_response(mock_llm_response)
        print("✅ LLM客户端解析结果:")
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
        
        # 验证关键字段
        required_fields = ['command', 'parameters', 'type', 'format', 'response']
        missing_fields = [field for field in required_fields if parsed_result.get(field) is None]
        
        if missing_fields:
            print(f"❌ 缺失字段: {missing_fields}")
        else:
            print("✅ 所有必需字段都存在")
            
    except Exception as e:
        print(f"❌ LLM客户端解析失败: {e}")
        return
    
    print("\n步骤4: 测试CommandGenerator完整流程")
    try:
        # 模拟完整的generate_standard_command调用
        command_result = generator.generate_standard_command(
            user_input="移动到(0，0)",
            scene_type="public",
            session_id=session_id
        )
        
        print("✅ CommandGenerator处理结果:")
        print(json.dumps(command_result, indent=2, ensure_ascii=False))
        
        # 验证结果字段
        print("\n📊 结果字段验证:")
        openai_fields = ['command', 'parameters', 'type', 'format']
        for field in openai_fields:
            value = command_result.get(field)
            status = "✅" if value is not None else "❌"
            print(f"  {status} {field}: {repr(value)}")
            
        # 检查是否有null字段
        null_fields = [field for field in openai_fields if command_result.get(field) is None]
        if null_fields:
            print(f"\n⚠️  发现null字段: {null_fields}")
        else:
            print(f"\n✅ 所有OpenAI字段都有值")
            
    except Exception as e:
        print(f"❌ CommandGenerator处理失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n步骤5: 模拟API响应构建")
    try:
        # 模拟API层的成功响应构建
        from src.common.response_utils import success_response
        
        # 使用解析后的结果构建API响应
        api_response = success_response(data=command_result)
        print("✅ API响应构建成功:")
        print(json.dumps(api_response, indent=2, ensure_ascii=False))
        
        # 验证响应结构
        if api_response.get('code') == 200 and api_response.get('data'):
            data = api_response['data']
            print(f"\n📊 API响应数据验证:")
            for field in openai_fields:
                value = data.get(field)
                status = "✅" if value is not None else "❌"
                print(f"  {status} {field}: {repr(value)}")
        else:
            print("❌ API响应结构异常")
            
    except Exception as e:
        print(f"❌ API响应构建失败: {e}")
        return

def test_actual_api_call():
    """测试实际的API调用"""
    print("\n🌐 实际API调用测试")
    print("=" * 50)
    
    import requests
    import ssl
    
    # 创建SSL上下文
    session = requests.Session()
    session.verify = False
    requests.packages.urllib3.disable_warnings()
    
    base_url = "https://localhost:8000"
    
    # 1. 注册会话
    print("1. 注册测试会话...")
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
                    "client_id": "api_flow_test",
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
        
        # 2. 发送明确要求函数调用的消息
        print("\n2. 发送函数调用测试消息...")
        test_message = "请调用move_to_position函数移动到坐标(0,0)"
        
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
            api_result = response.json()
            print(f"📥 API响应码: {api_result.get('code')}")
            
            if api_result.get('code') == 200 and api_result.get('data'):
                data = api_result['data']
                print(f"\n📊 最终API响应数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 详细字段检查
                print(f"\n🔍 字段完整性检查:")
                fields_to_check = [
                    ('command', True),
                    ('parameters', True), 
                    ('type', True),
                    ('format', True),
                    ('response', True),  # 对话内容
                    ('artifact_id', False),
                    ('artifact_name', False),
                    ('operation', False),
                    ('operation_params', False)
                ]
                
                for field, required in fields_to_check:
                    value = data.get(field)
                    if required and value is None:
                        print(f"  ❌ {field}: NULL (必需)")
                    elif value is None:
                        print(f"  ⚠️  {field}: NULL (可选)")
                    else:
                        print(f"  ✅ {field}: {repr(value)}")
                        
            else:
                print(f"❌ API响应异常: {api_result}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ API调用测试失败: {e}")

if __name__ == "__main__":
    print("🚀 数据流转完整性测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 模拟数据流转
    simulate_complete_dataflow()
    
    # 实际API调用测试
    test_actual_api_call()
    
    print(f"\n🏁 测试完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")