#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM原始数据检查 - 查看LLM实际接收到什么以及返回什么
"""

import json
from datetime import datetime

def check_llm_raw_data():
    """检查LLM的原始数据交互"""
    print("🔍 LLM原始数据检查")
    print("=" * 40)
    
    try:
        # 先加载配置
        from src.common.config_utils import load_config
        load_config()
        
        from src.core.dynamic_llm_client import DynamicLLMClient
        from src.session.strict_session_manager import strict_session_manager
        
        llm_client = DynamicLLMClient()
        
        # 创建测试会话
        session_id = "llm_raw_check_" + datetime.now().strftime("%Y%m%d_%H%M%S")
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
                "client_id": "llm_raw_check",
                "client_type": "test",
                "client_version": "1.0.0"
            },
            functions=functions
        )
        
        print(f"✅ 创建测试会话: {session_id}")
        
        # 生成请求负载
        user_input = "移动到(0，0)"
        print(f"\n📤 用户输入: {user_input}")
        
        payload = llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input=user_input,
            scene_type="public",
            functions=functions
        )
        
        print(f"\n📡 发送给LLM的完整请求:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # 实际调用LLM
        print(f"\n📡 调用LLM API...")
        response = llm_client._chat_completions_with_functions(payload)
        
        print(f"\n📥 LLM原始响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 分析响应
        choices = response.get("choices", [])
        if choices:
            first_choice = choices[0]
            message = first_choice.get("message", {})
            function_call = message.get("function_call")
            content = message.get("content", "")
            
            print(f"\n📊 响应分析:")
            print(f"   Content: {repr(content)}")
            print(f"   Has function_call: {function_call is not None}")
            
            if function_call:
                print(f"   Function name: {function_call.get('name')}")
                print(f"   Function arguments: {function_call.get('arguments')}")
            else:
                print(f"   ⚠️  LLM未触发函数调用，选择了普通对话")
                print(f"   这解释了为什么parameters为null")
        
        # 解析最终结果
        parsed_result = llm_client.parse_function_call_response(response)
        print(f"\n📊 最终解析结果:")
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
        
        return response, parsed_result
        
    except Exception as e:
        print(f"❌ LLM原始数据检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def analyze_issue():
    """分析问题根源"""
    print("\n🧩 问题分析")
    print("=" * 40)
    
    response, parsed_result = check_llm_raw_data()
    
    if response and parsed_result:
        # 检查LLM是否真的收到了函数定义
        choices = response.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if "function_call" not in message:
                print(f"\n🔍 问题诊断:")
                print(f"✅ LLM接收到了函数定义")
                print(f"✅ LLM返回了对话内容: {repr(content)}")
                print(f"❌ LLM没有触发函数调用")
                print(f"❓ 可能原因:")
                print(f"   1. 提示词不够明确，LLM认为普通对话就够了")
                print(f"   2. 函数定义格式可能有问题")
                print(f"   3. LLM模型对函数调用的支持程度")
                print(f"   4. 用户输入不够明确触发函数调用")
                
                print(f"\n💡 建议解决方案:")
                print(f"   1. 强化提示词，明确要求函数调用")
                print(f"   2. 修改用户输入，使其更明确地指向函数调用")
                print(f"   3. 检查函数定义是否符合LLM的要求")

if __name__ == "__main__":
    analyze_issue()