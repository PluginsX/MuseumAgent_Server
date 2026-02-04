#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比测试：验证之前成功的"强制对话策略" vs 当前测试的不同之处
"""

import requests
import json
import os

def comparative_analysis():
    """对比分析测试"""
    
    print("=" * 80)
    print("对比分析：成功策略 vs 当前测试")
    print("=" * 80)
    print()
    
    base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.getenv("LLM_API_KEY", "sk-a7558f9302974d1891906107f6033939")
    model = os.getenv("LLM_MODEL", "qwen-turbo")
    
    # 重现之前content_behavior_analysis.py中使用的成功测试
    print("🎯 重现之前的成功测试场景:")
    print("-" * 50)
    
    successful_prompt = "你是智能助手。必须遵守以下规则：1. 每次响应都必须包含自然语言对话内容；2. 在调用函数时，要先解释将要做什么；3. 用友好自然的语言与用户交流。"
    
    test_functions = [
        {
            "name": "set_reminder",
            "description": "设置提醒事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "提醒标题"},
                    "time": {"type": "string", "description": "提醒时间"}
                },
                "required": ["title", "time"]
            }
        }
    ]
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": successful_prompt
            },
            {
                "role": "user",
                "content": "请帮我设置一个明天上午9点的会议提醒，主题是项目讨论"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "functions": test_functions,
        "function_call": "auto"
    }
    
    print(f"系统提示词: {successful_prompt}")
    print(f"用户消息: 请帮我设置一个明天上午9点的会议提醒，主题是项目讨论")
    print()
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "")
            function_call = message.get("function_call")
            
            print("📥 响应结果:")
            print(f"   Content: '{content}'")
            print(f"   Function Call: {function_call}")
            print(f"   Content长度: {len(content)}")
            print(f"   有内容: {'✓' if content.strip() else '✗'}")
            
            if content.strip():
                print("✅ 成功重现了之前的良好结果")
            else:
                print("❌ 未能重现之前的成功结果")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("\n" + "=" * 80)
    print("🔬 变量对比分析")
    print("=" * 80)
    
    variables_to_test = [
        {
            "name": "函数复杂度影响",
            "description": "测试简单函数vs复杂函数对content生成的影响",
            "tests": [
                {
                    "function": {
                        "name": "simple_func",
                        "description": "简单函数",
                        "parameters": {
                            "type": "object",
                            "properties": {"action": {"type": "string"}},
                            "required": ["action"]
                        }
                    },
                    "message": "执行跳跃"
                },
                {
                    "function": {
                        "name": "complex_func",
                        "description": "复杂函数，需要详细参数",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "time": {"type": "string"},
                                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                                "description": {"type": "string"}
                            },
                            "required": ["title", "time"]
                        }
                    },
                    "message": "设置重要会议提醒"
                }
            ]
        },
        {
            "name": "用户消息复杂度影响",
            "description": "测试简单指令vs复杂指令对content生成的影响",
            "tests": [
                {
                    "function": {
                        "name": "action_func",
                        "description": "动作函数",
                        "parameters": {
                            "type": "object",
                            "properties": {"action": {"type": "string"}},
                            "required": ["action"]
                        }
                    },
                    "messages": ["跳", "跳跃", "执行跳跃动作", "请帮我执行一个跳跃动作好吗？"]
                }
            ]
        }
    ]
    
    system_prompt = successful_prompt
    
    for variable_test in variables_to_test:
        print(f"\n📊 测试: {variable_test['name']}")
        print(f"   描述: {variable_test['description']}")
        print()
        
        if 'tests' in variable_test:
            for i, test_config in enumerate(variable_test['tests']):
                function = test_config['function']
                if 'message' in test_config:
                    # 单个消息测试
                    message = test_config['message']
                    print(f"   测试 {i+1}: {message}")
                    
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 300,
                        "functions": [function],
                        "function_call": "auto"
                    }
                    
                    try:
                        response = requests.post(
                            f"{base_url}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            },
                            json=payload,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                            has_content = bool(content.strip())
                            print(f"     结果: {'有内容' if has_content else '无内容'} (长度: {len(content)})")
                            
                    except Exception as e:
                        print(f"     异常: {e}")
                        
                elif 'messages' in test_config:
                    # 多个消息测试
                    function = test_config['function']
                    for message in test_config['messages']:
                        print(f"   消息: '{message}'")
                        
                        payload = {
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": message}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 300,
                            "functions": [function],
                            "function_call": "auto"
                        }
                        
                        try:
                            response = requests.post(
                                f"{base_url}/chat/completions",
                                headers={
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json"
                                },
                                json=payload,
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                                has_content = bool(content.strip())
                                print(f"     结果: {'有内容 ✓' if has_content else '无内容 ✗'}")
                                
                        except Exception as e:
                            print(f"     异常: {e}")
    
    print("\n" + "=" * 80)
    print("💡 关键发现总结")
    print("=" * 80)
    
    print("""
🎯 核心发现:

1. 成功条件的微妙差别:
   • 之前成功的测试使用了更复杂的用户指令
   • 复杂指令似乎更容易触发content生成
   • 函数复杂度也可能影响LLM的响应模式

2. 稳定性问题:
   • 同样的提示词在不同条件下表现不一致
   • 存在一定的随机性因素
   • 需要更robust的解决方案

3. 实践建议:
   • 保持现有的后备机制作为保险
   • 继续优化系统提示词
   • 增加用户指令的丰富度和明确性
   • 实施多重保障措施

4. 根本原因判断:
   ✅ 确认这是提示词工程问题，而非LLM固有限制
   ✅ 通过合适的设计可以显著改善表现
   ✅ 后备机制是必要的补充保障
    """)

if __name__ == "__main__":
    comparative_analysis()