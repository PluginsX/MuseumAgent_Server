#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM数据交互100%原始数据显示演示
展示服务器调用LLM时发送的完整原始数据和接收的完整原始响应
"""

import sys
import os
import json
sys.path.append('.')

from src.common.config_utils import load_config
load_config()

from src.core.dynamic_llm_client import DynamicLLMClient
from src.session.strict_session_manager import strict_session_manager

def demonstrate_raw_llm_interaction():
    """演示LLM原始数据交互过程"""
    print("=== LLM数据交互100%原始数据显示 ===\n")
    
    # 初始化LLM客户端
    llm_client = DynamicLLMClient()
    
    print("🔧 LLM客户端配置信息:")
    print("-" * 50)
    print(f"Base URL: {llm_client.base_url}")
    print(f"Model: {llm_client.model}")
    print(f"Parameters: {json.dumps(llm_client.parameters, indent=2, ensure_ascii=False)}")
    print()
    
    # 测试用例1: 普通对话模式
    print("📱 测试用例1: 普通对话模式")
    print("=" * 60)
    
    session_id_1 = "demo-session-001"
    user_input_1 = "你好，介绍一下辽宁省博物馆"
    scene_type_1 = "public"
    
    # 注册空函数定义的会话（普通对话模式）
    strict_session_manager.register_session_with_functions(
        session_id=session_id_1,
        client_metadata={
            "client_id": "demo_client_1",
            "client_type": "demo",
            "client_version": "1.0.0"
        },
        functions=[]  # 空函数列表 = 普通对话模式
    )
    
    # 生成函数调用负载
    print("📤 步骤1: 生成发送给LLM的原始请求负载")
    print("-" * 40)
    payload_1 = llm_client.generate_function_calling_payload(
        session_id=session_id_1,
        user_input=user_input_1,
        scene_type=scene_type_1,
        rag_instruction="",
        functions=[]
    )
    
    print("原始请求负载 (JSON格式):")
    print(json.dumps(payload_1, indent=2, ensure_ascii=False))
    print()
    
    # 显示HTTP请求详情
    print("🌐 HTTP请求详情:")
    print("-" * 40)
    print(f"Method: POST")
    print(f"URL: {llm_client.base_url}/chat/completions")
    print(f"Headers: {{'Authorization': 'Bearer ***', 'Content-Type': 'application/json'}}")
    print(f"Timeout: {llm_client.timeout}秒")
    print()
    
    # 模拟LLM响应（展示真实的响应格式）
    print("📥 步骤2: 模拟接收的LLM原始响应")
    print("-" * 40)
    
    # 普通对话模式的典型响应
    mock_response_1 = {
        "id": "chatcmpl-demo001",
        "object": "chat.completion",
        "created": 1707064800,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "您好！辽宁省博物馆是位于中国辽宁省沈阳市的一座大型综合性博物馆。该馆成立于1949年，是国家一级博物馆，也是辽宁省最大的文物收藏、保护、研究和展示机构。\n\n辽宁省博物馆馆藏丰富，涵盖了从史前时期到近现代的各类文物，包括青铜器、陶瓷、书画、玉器、金银器等。其中尤以辽代文物最为著名，展示了契丹族和辽代文化的独特魅力。\n\n博物馆建筑宏伟，展览内容丰富多样，既有常设展览，也有临时特展。通过现代化的展示手段和详实的解说，为观众呈现了辽宁地区深厚的历史文化底蕴。\n\n如果您有机会到沈阳旅游，辽宁省博物馆绝对是值得一游的文化圣地！"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 85,
            "completion_tokens": 215,
            "total_tokens": 300
        }
    }
    
    print("原始响应数据 (JSON格式):")
    print(json.dumps(mock_response_1, indent=2, ensure_ascii=False))
    print()
    
    # 解析响应
    print("🔄 步骤3: 解析LLM响应")
    print("-" * 40)
    parsed_result_1 = llm_client.parse_function_call_response(mock_response_1)
    print("解析后的标准化指令:")
    print(json.dumps(parsed_result_1, indent=2, ensure_ascii=False))
    print()
    
    # 测试用例2: 函数调用模式
    print("📱 测试用例2: 函数调用模式")
    print("=" * 60)
    
    session_id_2 = "demo-session-002"
    user_input_2 = "请介绍蟠龙盖罍这件文物"
    scene_type_2 = "study"
    
    # 定义函数
    functions_2 = [
        {
            "name": "introduce_artifact",
            "description": "介绍文物的详细信息",
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
    
    # 注册带函数定义的会话
    strict_session_manager.register_session_with_functions(
        session_id=session_id_2,
        client_metadata={
            "client_id": "demo_client_2", 
            "client_type": "demo",
            "client_version": "1.0.0"
        },
        functions=functions_2
    )
    
    # 生成函数调用负载
    print("📤 步骤1: 生成发送给LLM的原始请求负载")
    print("-" * 40)
    payload_2 = llm_client.generate_function_calling_payload(
        session_id=session_id_2,
        user_input=user_input_2,
        scene_type=scene_type_2,
        rag_instruction="",
        functions=functions_2
    )
    
    print("原始请求负载 (JSON格式):")
    print(json.dumps(payload_2, indent=2, ensure_ascii=False))
    print()
    
    # 函数调用模式的典型响应
    print("📥 步骤2: 模拟接收的LLM原始响应")
    print("-" * 40)
    
    mock_response_2 = {
        "id": "chatcmpl-demo002",
        "object": "chat.completion", 
        "created": 1707064900,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": "introduce_artifact",
                        "arguments": "{\n  \"artifact_name\": \"蟠龙盖罍\"\n}"
                    }
                },
                "finish_reason": "function_call"
            }
        ],
        "usage": {
            "prompt_tokens": 156,
            "completion_tokens": 28,
            "total_tokens": 184
        }
    }
    
    print("原始响应数据 (JSON格式):")
    print(json.dumps(mock_response_2, indent=2, ensure_ascii=False))
    print()
    
    # 解析函数调用响应
    print("🔄 步骤3: 解析函数调用响应")
    print("-" * 40)
    parsed_result_2 = llm_client.parse_function_call_response(mock_response_2)
    print("解析后的标准化指令:")
    print(json.dumps(parsed_result_2, indent=2, ensure_ascii=False))
    print()
    
    # 参数配置详情
    print("⚙️ LLM参数配置详情")
    print("=" * 60)
    print("当前使用的参数配置:")
    print("-" * 30)
    config_params = llm_client.parameters
    param_details = {
        "temperature": f"{config_params.get('temperature', 0.1)} (控制随机性，0-2)",
        "max_tokens": f"{config_params.get('max_tokens', 1024)} (最大输出长度)",
        "top_p": f"{config_params.get('top_p', 0.1)} (核采样，0-1)", 
        "stream": f"{config_params.get('stream', False)} (是否流式响应)",
        "presence_penalty": f"{config_params.get('presence_penalty', 0)} (重复惩罚，-2到2)",
        "frequency_penalty": f"{config_params.get('frequency_penalty', 0)} (频率惩罚，-2到2)"
    }
    
    for param, description in param_details.items():
        print(f"{param:20} : {description}")
    
    print()
    print("📊 数据传输统计:")
    print("-" * 30)
    print(f"普通对话请求大小: {len(json.dumps(payload_1))} 字节")
    print(f"普通对话响应大小: {len(json.dumps(mock_response_1))} 字节")
    print(f"函数调用请求大小: {len(json.dumps(payload_2))} 字节") 
    print(f"函数调用响应大小: {len(json.dumps(mock_response_2))} 字节")

def show_actual_api_call_example():
    """展示实际API调用示例"""
    print("\n" + "=" * 80)
    print("📡 实际API调用示例")
    print("=" * 80)
    
    print("curl命令示例:")
    print("-" * 40)
    
    # 普通对话模式的curl示例
    payload_example = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。\n\n当前处于普通对话模式，请以友好、专业的态度回答用户问题。"
            },
            {
                "role": "user", 
                "content": "场景：public\n\n用户输入：你好，介绍一下辽宁省博物馆"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
        "top_p": 0.1
    }
    
    print("普通对话模式:")
    print(f"curl -X POST '{llm_client.base_url}/chat/completions' \\")
    print(f"  -H 'Authorization: Bearer YOUR_API_KEY' \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json.dumps(payload_example, ensure_ascii=False)}'")
    print()
    
    # 函数调用模式的curl示例
    function_payload_example = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。"
            },
            {
                "role": "user",
                "content": "场景：study\n\n用户输入：请介绍蟠龙盖罍这件文物"
            }
        ],
        "functions": [
            {
                "name": "introduce_artifact",
                "description": "介绍文物的详细信息",
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
        ],
        "function_call": "auto",
        "temperature": 0.1,
        "max_tokens": 1024,
        "top_p": 0.1
    }
    
    print("函数调用模式:")
    print(f"curl -X POST '{llm_client.base_url}/chat/completions' \\")
    print(f"  -H 'Authorization: Bearer YOUR_API_KEY' \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json.dumps(function_payload_example, ensure_ascii=False)}'")

if __name__ == "__main__":
    # 全局变量用于后续使用
    llm_client = DynamicLLMClient()
    demonstrate_raw_llm_interaction()
    show_actual_api_call_example()
    print("\n✅ LLM数据交互演示完成！")