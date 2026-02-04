#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制函数调用测试 - 修改提示词和输入来强制触发函数调用
"""

import json
from datetime import datetime

def force_function_call_test():
    """强制函数调用测试"""
    print("💪 强制函数调用测试")
    print("=" * 40)
    
    # 先加载配置
    from src.common.config_utils import load_config
    load_config()
    
    from src.core.dynamic_llm_client import DynamicLLMClient
    from src.session.strict_session_manager import strict_session_manager
    
    llm_client = DynamicLLMClient()
    
    # 创建测试会话
    session_id = "force_call_" + datetime.now().strftime("%Y%m%d_%H%M%S")
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
            "client_id": "force_call",
            "client_type": "test",
            "client_version": "1.0.0"
        },
        functions=functions
    )
    
    print(f"✅ 创建测试会话: {session_id}")
    
    # 测试不同的用户输入和提示词组合
    test_cases = [
        {
            "name": "明确指令式输入",
            "user_input": "请调用move_to_position函数，将坐标设置为x=0,y=0",
            "system_prompt": "你是一个函数调用助手。当用户要求执行具体动作时，必须调用相应的函数。请分析用户需求并调用合适的函数。"
        },
        {
            "name": "强指示提示词",
            "user_input": "移动到坐标(0,0)",
            "system_prompt": "你必须调用move_to_position函数来处理坐标移动请求。这是强制要求。"
        },
        {
            "name": "混合模式",
            "user_input": "我现在需要移动到(0,0)这个位置，请执行移动操作",
            "system_prompt": "对于移动请求，你必须调用move_to_position函数。先解释你要做什么，然后调用函数。"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {test_case['name']} ---")
        print(f"用户输入: {test_case['user_input']}")
        
        # 构建自定义payload
        messages = [
            {"role": "system", "content": test_case['system_prompt']},
            {"role": "user", "content": f"场景：public\n用户输入：{test_case['user_input']}"}
        ]
        
        payload = {
            "model": llm_client.model,
            "messages": messages,
            "temperature": 0.1,  # 更低的温度增加确定性
            "max_tokens": 512,
            "top_p": 0.1,
            "functions": functions,
            "function_call": "auto"
        }
        
        print(f"📡 发送请求...")
        
        try:
            response = llm_client._chat_completions_with_functions(payload)
            
            # 分析响应
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                function_call = message.get("function_call")
                content = message.get("content", "")
                
                print(f"📥 响应分析:")
                print(f"   对话内容: {repr(content)}")
                print(f"   触发函数调用: {function_call is not None}")
                
                if function_call:
                    print(f"   ✅ 成功触发函数调用!")
                    print(f"   函数名: {function_call.get('name')}")
                    print(f"   参数: {function_call.get('arguments')}")
                else:
                    print(f"   ❌ 仍未触发函数调用")
                    
        except Exception as e:
            print(f"❌ 测试失败: {e}")

def test_with_different_models():
    """测试不同模型的行为"""
    print("\n🔬 不同模型行为测试")
    print("=" * 40)
    
    # 先加载配置
    from src.common.config_utils import load_config, get_global_config
    load_config()
    
    config = get_global_config()
    llm_config = config.get("llm", {})
    
    print(f"当前模型: {llm_config.get('model', 'unknown')}")
    print(f"Base URL: {llm_config.get('base_url', 'unknown')}")
    
    print(f"\n💡 建议:")
    print(f"1. 尝试使用不同的模型（如qwen-plus, qwen-max等）")
    print(f"2. 调整temperature参数（更低的值增加确定性）")
    print(f"3. 修改提示词策略，更加明确地指示函数调用")
    print(f"4. 考虑使用'function_call': 'required'强制模式")

if __name__ == "__main__":
    force_function_call_test()
    test_with_different_models()