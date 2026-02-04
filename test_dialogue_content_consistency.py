#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的对话内容一致性
验证函数调用模式和普通对话模式都包含对话内容
"""

import sys
import os
import json
sys.path.append('.')

from src.common.config_utils import load_config
load_config()

from src.core.dynamic_llm_client import DynamicLLMClient
from src.session.strict_session_manager import strict_session_manager

def test_dialogue_content_consistency():
    """测试对话内容一致性"""
    print("=== 测试对话内容一致性 ===\n")
    
    llm_client = DynamicLLMClient()
    
    # 测试用例1: 普通对话模式
    print("📱 测试用例1: 普通对话模式")
    print("-" * 50)
    
    session_id_1 = "test-session-dialogue-001"
    user_input_1 = "你好，介绍一下辽宁省博物馆"
    
    # 注册普通对话会话
    strict_session_manager.register_session_with_functions(
        session_id=session_id_1,
        client_metadata={
            "client_id": "test_client_1",
            "client_type": "demo",
            "client_version": "1.0.0"
        },
        functions=[]  # 空函数列表 = 普通对话模式
    )
    
    # 生成负载
    payload_1 = llm_client.generate_function_calling_payload(
        session_id=session_id_1,
        user_input=user_input_1,
        scene_type="public",
        rag_instruction="",
        functions=[]
    )
    
    print("请求负载已生成")
    
    # 模拟普通对话响应
    mock_response_1 = {
        "id": "chatcmpl-test001",
        "object": "chat.completion",
        "created": 1707064800,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "您好！辽宁省博物馆是位于中国辽宁省沈阳市的一座大型综合性博物馆。该馆成立于1949年，是国家一级博物馆，也是辽宁省最大的文物收藏、保护、研究和展示机构。\n\n辽宁省博物馆馆藏丰富，涵盖了从史前时期到近现代的各类文物，包括青铜器、陶瓷、书画、玉器、金银器等。其中尤以辽代文物最为著名，展示了契丹族和辽代文化的独特魅力。\n\n博物馆建筑宏伟，展览内容丰富多样，既有常设展览，也有临时特展。通过现代化的展示手段和详实的解说，为观众呈现了辽宁地区深厚的历史文化底蕴。\n\n如果您有机会到沈阳旅游，辽宁省博物馆绝对是值得一游的文化圣地！",
                    "function_call": None
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
    
    # 解析响应
    parsed_result_1 = llm_client.parse_function_call_response(mock_response_1)
    
    print("解析结果:")
    print(f"  命令类型: {parsed_result_1.get('type')}")
    print(f"  命令名称: {parsed_result_1.get('command')}")
    print(f"  是否包含对话内容: {'✅ 是' if 'response' in parsed_result_1 and parsed_result_1['response'] else '❌ 否'}")
    if 'response' in parsed_result_1:
        print(f"  对话内容预览: {parsed_result_1['response'][:100]}...")
    print()
    
    # 测试用例2: 函数调用模式（有对话内容）
    print("📱 测试用例2: 函数调用模式（有对话内容）")
    print("-" * 50)
    
    session_id_2 = "test-session-dialogue-002"
    user_input_2 = "请介绍蟠龙盖罍这件文物"
    
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
    
    # 注册函数调用会话
    strict_session_manager.register_session_with_functions(
        session_id=session_id_2,
        client_metadata={
            "client_id": "test_client_2",
            "client_type": "demo", 
            "client_version": "1.0.0"
        },
        functions=functions_2
    )
    
    # 生成负载
    payload_2 = llm_client.generate_function_calling_payload(
        session_id=session_id_2,
        user_input=user_input_2,
        scene_type="study",
        rag_instruction="",
        functions=functions_2
    )
    
    print("请求负载已生成")
    
    # 模拟函数调用响应（包含对话内容）
    mock_response_2 = {
        "id": "chatcmpl-test002",
        "object": "chat.completion",
        "created": 1707064900,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "好的，我来为您详细介绍蟠龙盖罍这件珍贵的文物。",
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
            "completion_tokens": 35,
            "total_tokens": 191
        }
    }
    
    # 解析响应
    parsed_result_2 = llm_client.parse_function_call_response(mock_response_2)
    
    print("解析结果:")
    print(f"  命令类型: {parsed_result_2.get('type')}")
    print(f"  命令名称: {parsed_result_2.get('command')}")
    print(f"  是否包含对话内容: {'✅ 是' if 'response' in parsed_result_2 and parsed_result_2['response'] else '❌ 否'}")
    if 'response' in parsed_result_2:
        print(f"  对话内容: {parsed_result_2['response']}")
        print(f"  函数参数: {parsed_result_2.get('parameters', {})}")
    print()
    
    # 测试用例3: 函数调用模式（无对话内容，测试兜底机制）
    print("📱 测试用例3: 函数调用模式（无对话内容，测试兜底机制）")
    print("-" * 50)
    
    session_id_3 = "test-session-dialogue-003"
    user_input_3 = "查询文物信息"
    
    functions_3 = [
        {
            "name": "query_artifact_info",
            "description": "查询文物基本信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "文物ID"
                    }
                },
                "required": ["artifact_id"]
            }
        }
    ]
    
    # 注册函数调用会话
    strict_session_manager.register_session_with_functions(
        session_id=session_id_3,
        client_metadata={
            "client_id": "test_client_3",
            "client_type": "demo",
            "client_version": "1.0.0"
        },
        functions=functions_3
    )
    
    # 模拟函数调用响应（不包含对话内容）
    mock_response_3 = {
        "id": "chatcmpl-test003",
        "object": "chat.completion",
        "created": 1707065000,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,  # 故意设置为None来测试兜底机制
                    "function_call": {
                        "name": "query_artifact_info",
                        "arguments": "{\n  \"artifact_id\": \"artifact_001\"\n}"
                    }
                },
                "finish_reason": "function_call"
            }
        ],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 25,
            "total_tokens": 145
        }
    }
    
    # 解析响应
    parsed_result_3 = llm_client.parse_function_call_response(mock_response_3)
    
    print("解析结果:")
    print(f"  命令类型: {parsed_result_3.get('type')}")
    print(f"  命令名称: {parsed_result_3.get('command')}")
    print(f"  是否包含对话内容: {'✅ 是' if 'response' in parsed_result_3 and parsed_result_3['response'] else '❌ 否'}")
    if 'response' in parsed_result_3:
        print(f"  自动生成的对话内容: {parsed_result_3['response']}")
        print(f"  函数参数: {parsed_result_3.get('parameters', {})}")
    print()
    
    # 验证结果汇总
    print("📋 验证结果汇总")
    print("=" * 60)
    
    test_results = [
        ("普通对话模式", 'response' in parsed_result_1 and parsed_result_1['response']),
        ("函数调用模式（有对话）", 'response' in parsed_result_2 and parsed_result_2['response']),
        ("函数调用模式（无对话兜底）", 'response' in parsed_result_3 and parsed_result_3['response'])
    ]
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} {test_name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 所有测试通过！对话内容一致性验证成功！")
        print("   ✅ 普通对话模式包含对话内容")
        print("   ✅ 函数调用模式包含对话内容") 
        print("   ✅ 无对话内容时有兜底机制")
    else:
        print("❌ 部分测试失败，请检查实现")
    
    return all_passed

def demonstrate_improved_workflow():
    """演示改进后的工作流程"""
    print("\n" + "=" * 80)
    print("🔄 改进后的工作流程演示")
    print("=" * 80)
    
    print("""
改进后的工作流程：

1. 用户输入: "请介绍蟠龙盖罍这件文物"

2. 系统处理:
   - 识别为函数调用请求
   - 同时生成自然语言对话内容
   - 调用introduce_artifact函数

3. LLM响应包含两部分:
   - content: "好的，我来为您详细介绍蟠龙盖罍这件珍贵的文物。"
   - function_call: {"name": "introduce_artifact", "arguments": "..."}
   
4. 客户端接收:
   - 可以先显示对话内容："好的，我来为您详细介绍蟠龙盖罍这件珍贵的文物。"
   - 然后执行函数调用获取详细信息
   - 最终提供完整的用户体验

这样既保持了函数调用的精确性，又确保了对话的自然流畅性！
    """)

if __name__ == "__main__":
    print("开始测试改进后的对话内容一致性...")
    
    # 执行测试
    success = test_dialogue_content_consistency()
    
    # 演示改进
    demonstrate_improved_workflow()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 对话内容一致性改进验证完成！")
        print("   系统现在确保每次调用都包含对话内容")
        print("   函数调用不再是对话的替代，而是对话的补充")
    else:
        print("❌ 验证过程中发现问题，请检查实现")
    print("=" * 80)