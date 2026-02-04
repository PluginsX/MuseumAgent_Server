#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端数据流转追踪测试
模拟完整的API调用流程，从请求到响应的全过程
"""

import sys
import os
import json
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.common.config_utils import load_config
from src.core.dynamic_llm_client import DynamicLLMClient
from src.session.strict_session_manager import strict_session_manager
from src.core.command_generator import CommandGenerator
from src.common.response_utils import success_response

def end_to_end_trace_test():
    """端到端数据流转追踪测试"""
    print("=" * 100)
    print("🔍 端到端数据流转追踪测试")
    print("=" * 100)
    
    # 加载配置
    load_config()
    
    # 1. 初始化组件
    print("\n🔧 步骤1: 初始化核心组件")
    print("-" * 50)
    llm_client = DynamicLLMClient()
    command_generator = CommandGenerator()
    
    # 2. 创建测试会话
    print("\n📋 步骤2: 创建测试会话")
    print("-" * 50)
    session_id = "e2e-test-session-001"
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
            "client_id": "e2e_test_client",
            "client_type": "test",
            "client_version": "1.0.0"
        },
        functions=functions
    )
    
    print(f"✅ 会话创建成功: {session_id}")
    print(f"✅ 注册函数数量: {len(functions)}")
    
    # 3. 模拟用户请求
    print("\n💬 步骤3: 模拟用户请求")
    print("-" * 50)
    user_input = "移动到(0，0)"
    scene_type = "public"
    
    print(f"用户输入: {user_input}")
    print(f"场景类型: {scene_type}")
    
    # 4. 模拟LLM原始响应（函数调用）
    print("\n🤖 步骤4: 模拟LLM原始响应")
    print("-" * 50)
    mock_llm_response = {
        "id": "chatcmpl-e2e001",
        "object": "chat.completion",
        "created": 1707064900,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "我将把桌面宠物移动到坐标 (0, 0)。",
                    "function_call": {
                        "name": "move_to_position",
                        "arguments": "{\"x\": 0, \"y\": 0}"
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
    
    # 5. 直接解析LLM响应
    print("\n🔄 步骤5: 直接解析LLM响应")
    print("-" * 50)
    parsed_direct = llm_client.parse_function_call_response(mock_llm_response)
    print("直接解析结果:")
    print(json.dumps(parsed_direct, indent=2, ensure_ascii=False))
    
    # 6. 通过CommandGenerator处理
    print("\n⚙️ 步骤6: 通过CommandGenerator完整流程处理")
    print("-" * 50)
    
    # 模拟CommandGenerator的处理过程（绕过RAG以避免依赖问题）
    try:
        # 手动执行CommandGenerator的关键步骤
        print("执行RAG检索...")
        # 跳过实际RAG调用，直接使用空上下文
        rag_context = {"total_found": 0, "timestamp": "2026-02-04T20:20:00"}
        
        print("获取函数定义...")
        session_functions = strict_session_manager.get_functions_for_session(session_id)
        print(f"会话函数: {len(session_functions)}个")
        
        print("构建提示词...")
        # 简化提示词构建
        rag_instruction = "上下文：无相关文物信息"
        
        print("生成函数调用负载...")
        payload = llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input=user_input,
            scene_type=scene_type,
            rag_instruction=rag_instruction,
            functions=session_functions
        )
        
        print("解析LLM响应...")
        # 使用我们模拟的LLM响应
        command_result = llm_client.parse_function_call_response(mock_llm_response)
        
        # 添加元数据
        command_result["timestamp"] = "2026-02-04T20:20:00"
        command_result["session_id"] = session_id
        command_result["processing_mode"] = "openai_function_calling"
        
        print("CommandGenerator处理结果:")
        print(json.dumps(command_result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ CommandGenerator处理出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 7. API响应格式化
    print("\n🌐 步骤7: API响应格式化")
    print("-" * 50)
    api_response = success_response(data=command_result)
    print("API响应数据:")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    # 8. 检查数据完整性
    print("\n📋 步骤8: 数据完整性检查")
    print("-" * 50)
    response_data = api_response.get("data", {})
    
    print("关键字段检查:")
    key_fields = ["command", "parameters", "type", "format", "response"]
    for field in key_fields:
        if field in response_data:
            value = response_data[field]
            if value is not None:
                print(f"✅ {field}: {value}")
            else:
                print(f"⚠️  {field}: None")
        else:
            print(f"❌ {field}: 不存在")
    
    print("\n传统字段检查:")
    traditional_fields = ["artifact_id", "artifact_name", "operation", "operation_params"]
    for field in traditional_fields:
        if field in response_data:
            value = response_data[field]
            if value is None:
                print(f"✅ {field}: None (预期)")
            else:
                print(f"⚠️  {field}: {value} (意外值)")
        else:
            print(f"✅ {field}: 不存在 (预期)")
    
    # 9. 模拟客户端接收
    print("\n📱 步骤9: 模拟客户端接收处理")
    print("-" * 50)
    
    # 模拟客户端JavaScript的处理逻辑
    if api_response.get("code") == 200 and api_response.get("data"):
        client_command = api_response["data"]
        print("客户端接收到的原始数据:")
        print(json.dumps(client_command, indent=2, ensure_ascii=False))
        
        # 模拟客户端显示逻辑
        print("\n客户端显示逻辑模拟:")
        if "command" in client_command and client_command["command"]:
            print(f"📝 函数调用: {client_command['command']}")
            if "parameters" in client_command and client_command["parameters"]:
                print(f"🔧 参数: {client_command['parameters']}")
        else:
            print("❌ 未检测到函数调用信息")
            
        if "response" in client_command and client_command["response"]:
            print(f"💬 对话内容: {client_command['response']}")
        else:
            print("❌ 未检测到对话内容")
    else:
        print("❌ API响应格式错误")
    
    print("\n" + "=" * 100)
    print("🎯 端到端测试完成")
    print("=" * 100)

if __name__ == "__main__":
    end_to_end_trace_test()