#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话内容保持测试
专门测试如何在函数调用模式下保持自然语言对话内容
"""

import requests
import json
import os
from datetime import datetime

def test_content_preservation():
    """测试对话内容保持机制"""
    
    print("=" * 80)
    print("对话内容保持机制测试")
    print("=" * 80)
    print()
    
    base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.getenv("LLM_API_KEY", "sk-a7558f9302974d1891906107f6033939")
    model = os.getenv("LLM_MODEL", "qwen-turbo")
    
    # 定义测试函数
    test_functions = [
        {
            "name": "set_reminder",
            "description": "设置提醒事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "提醒标题"},
                    "time": {"type": "string", "description": "提醒时间"},
                    "content": {"type": "string", "description": "提醒内容"}
                },
                "required": ["title", "time"]
            }
        }
    ]
    
    # 测试不同的系统提示词策略
    prompt_strategies = [
        {
            "name": "基础策略",
            "system_prompt": "你是一个智能助手。根据用户需求调用相应函数。"
        },
        {
            "name": "对话优先策略", 
            "system_prompt": "你是一个友好的智能助手。在调用任何函数之前，都要先用自然语言回应用户，然后再执行相应操作。"
        },
        {
            "name": "强制对话策略",
            "system_prompt": "你是智能助手。必须遵守以下规则：1. 每次响应都必须包含自然语言对话内容；2. 在调用函数时，要先解释将要做什么；3. 用友好自然的语言与用户交流。"
        },
        {
            "name": "角色扮演策略",
            "system_prompt": "你是一个贴心的生活助理。我会用自然语言告诉你我想做什么，然后你会调用相应功能来帮助我。记得在每次操作前后都要和我聊天。"
        }
    ]
    
    test_message = "请帮我设置一个明天上午9点的会议提醒，主题是项目讨论"
    
    print(f"📝 测试指令: {test_message}")
    print(f"🔧 测试函数: set_reminder")
    print()
    
    results = []
    
    for strategy in prompt_strategies:
        print(f"🧪 测试策略: {strategy['name']}")
        print(f"   提示词: {strategy['system_prompt']}")
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": strategy["system_prompt"]
                },
                {
                    "role": "user", 
                    "content": test_message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500,
            "functions": test_functions,
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
                message = result.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                function_call = message.get("function_call")
                
                has_content = bool(content and content.strip())
                has_function = bool(function_call)
                
                result_data = {
                    "strategy": strategy["name"],
                    "content": content,
                    "has_content": has_content,
                    "has_function": has_function,
                    "function_call": function_call,
                    "quality_score": (1 if has_content else 0) + (1 if has_function else 0) + (1 if has_content and has_function else 0)
                }
                
                results.append(result_data)
                
                print(f"   📝 对话内容: '{content}'")
                print(f"   🔧 函数调用: {function_call.get('name') if function_call else '无'}")
                print(f"   ✅ 内容保持: {'✓' if has_content else '✗'}")
                print(f"   ⭐ 质量评分: {result_data['quality_score']}/3")
                print()
                
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 结果分析
    print("=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    
    print("\n📈 各策略表现对比:")
    print("策略名称".ljust(20) + "内容保持".ljust(15) + "函数调用".ljust(15) + "综合评分")
    print("-" * 60)
    
    for result in results:
        content_status = "✓" if result["has_content"] else "✗"
        function_status = "✓" if result["has_function"] else "✗"
        print(f"{result['strategy']:<20}{content_status:<15}{function_status:<15}{result['quality_score']}/3")
    
    best_strategy = max(results, key=lambda x: x["quality_score"])
    print(f"\n🏆 最佳策略: {best_strategy['strategy']} (评分: {best_strategy['quality_score']}/3)")
    
    print("\n🎯 关键结论:")
    
    content_success_rate = sum(1 for r in results if r["has_content"]) / len(results) * 100
    function_success_rate = sum(1 for r in results if r["has_function"]) / len(results) * 100
    dual_success_rate = sum(1 for r in results if r["has_content"] and r["has_function"]) / len(results) * 100
    
    print(f"• 内容保持成功率: {content_success_rate:.1f}%")
    print(f"• 函数调用成功率: {function_success_rate:.1f}%") 
    print(f"• 双重成功率: {dual_success_rate:.1f}%")
    
    if dual_success_rate > 0:
        print("✅ 找到了有效的提示词策略来同时保持对话内容和函数调用")
        print(f"💡 推荐使用: {best_strategy['strategy']}")
        print(f"   提示词: {next(s['system_prompt'] for s in prompt_strategies if s['name'] == best_strategy['strategy'])}")
    else:
        print("⚠️  需要进一步优化提示词工程")
        print("💡 建议方向:")
        print("   1. 更加强调必须包含对话内容的要求")
        print("   2. 提供具体的对话内容生成模板")
        print("   3. 建立后备机制自动生成对话内容")

def test_backfill_mechanism():
    """测试后备对话内容生成机制"""
    
    print("\n" + "=" * 80)
    print("后备对话内容生成机制测试")
    print("=" * 80)
    
    # 模拟服务器端的后备机制
    test_responses = [
        {
            "function_call": {"name": "set_reminder", "arguments": '{"title": "会议", "time": "明天上午9点"}'},
            "content": ""
        },
        {
            "function_call": {"name": "move_to_position", "arguments": '{"x": 100, "y": 100}'},
            "content": ""
        },
        {
            "function_call": {"name": "play_animation", "arguments": '{"animation_type": "happy"}'},
            "content": ""
        }
    ]
    
    function_templates = {
        "set_reminder": "我将为您设置{name}提醒，时间是{time}。",
        "move_to_position": "我将把桌宠移动到指定位置。",
        "play_animation": "我将为您播放{animation_type}动画效果。"
    }
    
    print("🔧 后备机制处理结果:")
    print("-" * 40)
    
    for i, response in enumerate(test_responses, 1):
        function_call = response["function_call"]
        func_name = function_call["name"]
        arguments = json.loads(function_call["arguments"])
        
        # 应用后备机制
        if not response["content"]:
            template = function_templates.get(func_name, "我将执行{name}操作。")
            # 简单的参数替换
            fallback_content = template.format(**arguments, name=func_name)
        else:
            fallback_content = response["content"]
        
        print(f"测试 {i}:")
        print(f"  原始内容: '{response['content']}'")
        print(f"  函数调用: {func_name}")
        print(f"  后备内容: '{fallback_content}'")
        print(f"  改进效果: {'✓' if fallback_content else '✗'}")
        print()

if __name__ == "__main__":
    test_content_preservation()
    test_backfill_mechanism()