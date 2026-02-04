#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
函数调用信息丢失问题调试脚本
追踪从LLM响应到客户端数据的完整转换流程
"""

import json
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.common.config_utils import load_config
from src.core.dynamic_llm_client import DynamicLLMClient
from src.session.strict_session_manager import strict_session_manager
from src.core.command_generator import CommandGenerator

# 加载配置
load_config()

def debug_function_call_transformation():
    """调试函数调用信息的完整转换流程"""
    print("=" * 80)
    print("🔍 函数调用信息转换流程调试")
    print("=" * 80)
    
    # 1. 初始化组件
    print("\n🔧 步骤1: 初始化核心组件")
    print("-" * 40)
    llm_client = DynamicLLMClient()
    command_generator = CommandGenerator()
    
    # 创建测试会话
    session_id = "debug-session-func-call"
    functions = [
        {
            "name": "introduce_artifact",
            "description": "介绍指定文物的详细信息",
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
    
    # 注册会话
    strict_session_manager.register_session_with_functions(
        session_id=session_id,
        client_metadata={
            "client_id": "debug_client",
            "client_type": "debug",
            "client_version": "1.0.0"
        },
        functions=functions
    )
    
    print(f"✅ 已注册测试会话: {session_id}")
    print(f"✅ 已注册函数数量: {len(functions)}")
    
    # 2. 模拟用户输入
    print("\n💬 步骤2: 模拟用户输入")
    print("-" * 40)
    user_input = "请介绍蟠龙盖罍这件文物"
    scene_type = "study"
    
    print(f"用户输入: {user_input}")
    print(f"场景类型: {scene_type}")
    
    # 3. 生成函数调用负载
    print("\n📤 步骤3: 生成LLM请求负载")
    print("-" * 40)
    payload = llm_client.generate_function_calling_payload(
        session_id=session_id,
        user_input=user_input,
        scene_type=scene_type,
        rag_instruction="",
        functions=functions
    )
    
    print("发送给LLM的请求负载:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # 4. 模拟LLM响应（包含函数调用）
    print("\n📥 步骤4: 模拟LLM原始响应")
    print("-" * 40)
    mock_llm_response = {
        "id": "chatcmpl-debug001",
        "object": "chat.completion",
        "created": 1707064900,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "好的，我来为您详细介绍蟠龙盖罍这件珍贵文物。",
                    "function_call": {
                        "name": "introduce_artifact",
                        "arguments": "{\"artifact_name\": \"蟠龙盖罍\"}"
                    }
                },
                "finish_reason": "function_call"
            }
        ],
        "usage": {
            "prompt_tokens": 85,
            "completion_tokens": 42,
            "total_tokens": 127
        }
    }
    
    print("LLM原始响应:")
    print(json.dumps(mock_llm_response, indent=2, ensure_ascii=False))
    
    # 5. 解析LLM响应
    print("\n🔄 步骤5: 解析LLM响应")
    print("-" * 40)
    parsed_result = llm_client.parse_function_call_response(mock_llm_response)
    
    print("解析后的中间结果:")
    print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
    
    # 6. 通过命令生成器处理
    print("\n⚙️ 步骤6: 通过CommandGenerator处理")
    print("-" * 40)
    try:
        command_result = command_generator.generate_standard_command(
            user_input=user_input,
            scene_type=scene_type,
            session_id=session_id
        )
        
        print("CommandGenerator处理结果:")
        print(json.dumps(command_result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ CommandGenerator处理出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 7. 最终API响应格式
    print("\n🌐 步骤7: 最终API响应格式")
    print("-" * 40)
    from src.common.response_utils import success_response
    
    final_response = success_response(data=command_result)
    print("发送给客户端的最终响应:")
    print(json.dumps(final_response, indent=2, ensure_ascii=False))
    
    # 8. 数据流对比分析
    print("\n📊 步骤8: 数据流对比分析")
    print("-" * 40)
    
    print("LLM原始响应中的函数调用信息:")
    llm_function_call = mock_llm_response["choices"][0]["message"].get("function_call")
    if llm_function_call:
        print(f"  函数名: {llm_function_call.get('name')}")
        print(f"  参数: {llm_function_call.get('arguments')}")
        print(f"  对话内容: {mock_llm_response['choices'][0]['message'].get('content')}")
    
    print("\n最终客户端接收到的数据:")
    client_data = final_response.get("data", {})
    print(f"  command: {client_data.get('command')}")
    print(f"  parameters: {client_data.get('parameters')}")
    print(f"  response: {client_data.get('response')}")
    print(f"  type: {client_data.get('type')}")
    
    # 9. 问题诊断
    print("\n🔍 步骤9: 问题诊断")
    print("-" * 40)
    
    # 检查函数调用信息是否完整传递
    if llm_function_call and client_data.get('command'):
        if llm_function_call.get('name') == client_data.get('command'):
            print("✅ 函数名传递正确")
        else:
            print("❌ 函数名传递错误")
            
        llm_args = llm_function_call.get('arguments', '{}')
        client_params = client_data.get('parameters', {})
        try:
            llm_parsed_args = json.loads(llm_args)
            if llm_parsed_args == client_params:
                print("✅ 函数参数传递正确")
            else:
                print("❌ 函数参数传递错误")
                print(f"  LLM原始参数: {llm_parsed_args}")
                print(f"  客户端接收参数: {client_params}")
        except json.JSONDecodeError:
            print("❌ LLM参数JSON解析失败")
    else:
        print("⚠️  函数调用信息缺失")
    
    # 检查对话内容
    llm_content = mock_llm_response["choices"][0]["message"].get("content", "")
    client_response = client_data.get("response", "")
    if llm_content == client_response:
        print("✅ 对话内容传递正确")
    else:
        print("❌ 对话内容传递错误")
        print(f"  LLM原始内容: '{llm_content}'")
        print(f"  客户端接收内容: '{client_response}'")
    
    print("\n" + "=" * 80)
    print("🎯 调试完成")
    print("=" * 80)

if __name__ == "__main__":
    debug_function_call_transformation()