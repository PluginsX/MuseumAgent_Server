#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试普通对话场景下的数据结构问题
"""

import sys
import os
import json
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 先加载配置
from src.common.config_utils import load_config
load_config()

from src.core.command_generator import CommandGenerator
from src.session.strict_session_manager import strict_session_manager
from src.common.response_utils import success_response

def test_general_chat_scenario():
    """测试普通对话场景"""
    print("=" * 80)
    print("🧪 普通对话场景数据结构测试")
    print("=" * 80)
    
    # 1. 创建普通对话会话（无函数定义）
    print("\n1. 创建普通对话会话")
    print("-" * 40)
    
    session_id = "general_chat_test_" + str(int(time.time()))
    
    strict_session_manager.register_session_with_functions(
        session_id=session_id,
        client_metadata={
            "client_id": "general_chat_test",
            "client_type": "test",
            "client_version": "1.0.0"
        },
        functions=[]  # 空函数列表 = 普通对话模式
    )
    
    print(f"✅ 会话创建成功: {session_id}")
    
    # 2. 模拟用户输入
    print("\n2. 模拟用户输入")
    print("-" * 40)
    
    user_inputs = [
        "你好",
        "你会干什么",
        "介绍一下辽宁省博物馆"
    ]
    
    generator = CommandGenerator()
    
    for i, user_input in enumerate(user_inputs, 1):
        print(f"\n📝 测试 {i}: {user_input}")
        print("-" * 30)
        
        try:
            # 调用CommandGenerator处理
            command_result = generator.generate_standard_command(
                user_input=user_input,
                scene_type="public",
                session_id=session_id
            )
            
            print("CommandGenerator处理结果:")
            print(json.dumps(command_result, indent=2, ensure_ascii=False))
            
            # 检查是否包含旧字段
            old_fields = ["artifact_id", "artifact_name", "operation", "operation_params", "keywords", "tips"]
            found_old_fields = []
            
            for field in old_fields:
                if field in command_result and command_result[field] is not None:
                    found_old_fields.append((field, command_result[field]))
            
            if found_old_fields:
                print(f"❌ 发现旧字段:")
                for field, value in found_old_fields:
                    print(f"   {field}: {value}")
            else:
                print("✅ 未发现旧字段")
                
            # 检查LLM原始字段
            llm_fields = ["choices", "created", "id", "model", "object", "usage"]
            found_llm_fields = [field for field in llm_fields if field in command_result]
            
            print(f"✅ 保留的LLM原始字段: {found_llm_fields}")
            
            # 通过API响应格式化
            api_response = success_response(data=command_result)
            response_data = api_response.get("data", {})
            
            print(f"\nAPI响应中的data字段:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # 再次检查旧字段
            api_old_fields = [field for field in old_fields if field in response_data and response_data[field] is not None]
            if api_old_fields:
                print(f"❌ API响应中仍有旧字段: {api_old_fields}")
            else:
                print("✅ API响应中无旧字段")
                
        except Exception as e:
            print(f"❌ 处理出错: {e}")
            import traceback
            traceback.print_exc()

def test_direct_llm_call():
    """直接测试LLM调用结果"""
    print("\n" + "=" * 80)
    print("🔍 直接LLM调用测试")
    print("=" * 80)
    
    from src.core.dynamic_llm_client import DynamicLLMClient
    
    llm_client = DynamicLLMClient()
    
    # 创建普通对话负载
    payload = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是智能助手。必须遵守以下规则：1. 每次响应都必须包含自然语言对话内容；2. 在调用函数时，要先解释将要做什么；3. 用友好自然的语言与用户交流。"
            },
            {
                "role": "user",
                "content": "场景：public\n\n用户输入：你会干什么"
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1024,
        "top_p": 0.9
    }
    
    print("发送给LLM的请求:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        # 直接调用LLM
        response = llm_client._chat_completions_with_functions(payload)
        
        print(f"\nLLM原始响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 检查响应结构
        choices = response.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            function_call = message.get("function_call")
            
            print(f"\n响应分析:")
            print(f"   Content: {repr(content)}")
            print(f"   Has function_call: {function_call is not None}")
            if function_call:
                print(f"   Function: {function_call}")
                
    except Exception as e:
        print(f"❌ LLM调用失败: {e}")

if __name__ == "__main__":
    print("🚀 普通对话场景数据结构问题诊断")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试普通对话场景
    test_general_chat_scenario()
    
    # 直接测试LLM调用
    test_direct_llm_call()
    
    print(f"\n🏁 测试完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")