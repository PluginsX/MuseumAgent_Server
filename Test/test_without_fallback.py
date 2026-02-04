#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证移除后备机制后的行为
测试在没有后备机制的情况下，系统如何处理content为空的情况
"""

import sys
import os
import json

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

# 动态导入模块
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 加载必要的模块
dynamic_llm_client = load_module_from_path('dynamic_llm_client', 
                                          os.path.join(project_root, 'src', 'core', 'dynamic_llm_client.py'))

# 获取类引用
DynamicLLMClient = getattr(dynamic_llm_client, 'DynamicLLMClient')

def test_without_fallback():
    """测试移除后备机制后的行为"""
    
    print("=" * 80)
    print("移除后备机制后的行为验证")
    print("=" * 80)
    print()
    
    client = DynamicLLMClient()
    print("✅ LLM客户端初始化完成")
    print()
    
    # 模拟不同类型的LLM响应
    test_cases = [
        {
            "name": "正常情况 - 有content和函数调用",
            "response": {
                "choices": [{
                    "message": {
                        "content": "好的，我将为您执行这个操作。",
                        "function_call": {
                            "name": "move_to_position",
                            "arguments": "{\"x\": 100, \"y\": 100}"
                        }
                    }
                }]
            }
        },
        {
            "name": "边界情况 - 只有函数调用，content为空",
            "response": {
                "choices": [{
                    "message": {
                        "content": "",
                        "function_call": {
                            "name": "play_animation",
                            "arguments": "{\"animation_type\": \"happy\"}"
                        }
                    }
                }]
            }
        },
        {
            "name": "普通对话情况 - 只有content，无函数调用",
            "response": {
                "choices": [{
                    "message": {
                        "content": "您好！有什么我可以帮助您的吗？",
                        "function_call": None
                    }
                }]
            }
        },
        {
            "name": "极端情况 - content和函数调用都为空",
            "response": {
                "choices": [{
                    "message": {
                        "content": "",
                        "function_call": None
                    }
                }]
            }
        }
    ]
    
    print("📋 测试不同响应场景:")
    print("-" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试 {i}: {test_case['name']}")
        
        try:
            result = client.parse_function_call_response(test_case["response"])
            print(f"   解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 分析结果
            has_content = bool(result.get("response", "").strip())
            has_function = result.get("type") == "function_call"
            
            print(f"   有对话内容: {'✓' if has_content else '✗'}")
            print(f"   有函数调用: {'✓' if has_function else '✗'}")
            
            if has_function and not has_content:
                print("   ⚠️  函数调用但无对话内容（符合用户接受的情况）")
            elif not has_function and not has_content:
                print("   ⚠️  既无函数调用也无对话内容（需要关注）")
            else:
                print("   ✅  正常情况")
                
        except Exception as e:
            print(f"   ❌ 解析出错: {e}")
    
    print("\n" + "=" * 80)
    print("📊 移除后备机制的影响分析")
    print("=" * 80)
    
    print("""
🎯 移除后备机制后的变化:

1. 正面影响:
   • 代码更简洁，逻辑更清晰
   • 减少了不必要的内容生成开销
   • 系统行为更贴近LLM的原始意图
   • 符合用户对"偶尔接受无内容"的期望

2. 需要注意的情况:
   • 函数调用时可能偶尔缺少自然语言反馈
   • 客户端需要能够处理content为空的情况
   • 用户体验可能会有轻微波动

3. 建议的客户端处理方式:
   • 当收到content为空的函数调用响应时，可以显示默认提示
   • 例如："正在执行操作..." 或 "已处理您的请求"
   • 保持界面的友好性和连贯性

4. 监控建议:
   • 统计content为空的频率
   • 收集用户反馈
   • 必要时可以重新评估是否需要某种形式的后备机制
    """)

if __name__ == "__main__":
    test_without_fallback()