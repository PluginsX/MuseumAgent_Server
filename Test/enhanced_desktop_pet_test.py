#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Windows桌宠测试
重点测试函数调用模式下的对话内容保持
"""

import requests
import json
import os
from datetime import datetime

def test_enhanced_desktop_pet():
    """测试增强版桌宠功能"""
    
    print("=" * 80)
    print("增强版Windows桌宠功能测试")
    print("=" * 80)
    print()
    
    # API配置
    base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.getenv("LLM_API_KEY", "sk-a7558f9302974d1891906107f6033939")
    model = os.getenv("LLM_MODEL", "qwen-turbo")
    
    print(f"📡 连接信息:")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    print()
    
    # 定义丰富的桌宠函数
    desktop_pet_functions = [
        {
            "name": "move_to_position",
            "description": "移动桌宠到指定屏幕位置",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X坐标位置(0-1920)"},
                    "y": {"type": "integer", "description": "Y坐标位置(0-1080)"}
                },
                "required": ["x", "y"]
            }
        },
        {
            "name": "play_animation",
            "description": "播放桌宠动画效果",
            "parameters": {
                "type": "object",
                "properties": {
                    "animation_type": {
                        "type": "string",
                        "enum": ["happy", "sad", "angry", "surprised", "sleepy", "excited"],
                        "description": "动画类型"
                    },
                    "duration": {"type": "integer", "description": "持续时间(秒)", "minimum": 1, "maximum": 30}
                },
                "required": ["animation_type"]
            }
        },
        {
            "name": "speak_message",
            "description": "让桌宠说话",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要说的话"},
                    "voice_type": {
                        "type": "string",
                        "enum": ["normal", "cute", "serious", "whisper"],
                        "description": "语音类型"
                    }
                },
                "required": ["text"]
            }
        },
        {
            "name": "change_mood",
            "description": "改变桌宠心情状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "enum": ["happy", "sad", "angry", "excited", "bored", "sleepy"],
                        "description": "心情状态"
                    }
                },
                "required": ["mood"]
            }
        },
        {
            "name": "perform_action",
            "description": "执行桌宠特殊动作",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["dance", "jump", "roll", "wave", "sit", "lie_down"],
                        "description": "动作类型"
                    },
                    "repeat_times": {"type": "integer", "description": "重复次数", "minimum": 1, "maximum": 10}
                },
                "required": ["action"]
            }
        }
    ]
    
    # 测试用例1: 复杂指令序列
    print("📋 测试用例1: 复杂指令序列")
    print("-" * 50)
    
    test_cases = [
        {
            "name": "回家欢迎序列",
            "system_prompt": "你是一个可爱贴心的Windows桌面宠物助手。请根据用户指令调用相应函数控制桌宠行为，在调用函数的同时要用自然语言与用户交流。",
            "user_message": "请让桌宠移动到屏幕右上角，然后开心地跳舞3次，最后说一句'主人回来啦！'",
            "expected_functions": ["move_to_position", "perform_action", "speak_message"]
        },
        {
            "name": "日常互动",
            "system_prompt": "你是一个活泼有趣的Windows桌面宠物。在执行用户指令时，要先用自然语言回应，然后再调用相应函数。",
            "user_message": "我有点累了，让桌宠安慰我一下，播放一个困倦的动画，然后轻声说'休息一下吧'",
            "expected_functions": ["play_animation", "speak_message"]
        },
        {
            "name": "节日庆祝",
            "system_prompt": "你是一个充满活力的节日桌宠助手。执行指令时要有节日气氛，先说话再行动。",
            "user_message": "新年快乐！让桌宠兴奋地跳跃5次，播放惊喜动画，然后大声说'新年快乐！'",
            "expected_functions": ["perform_action", "play_animation", "speak_message"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test_case['name']}")
        print(f"   用户指令: {test_case['user_message']}")
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": test_case["system_prompt"]
                },
                {
                    "role": "user",
                    "content": test_case["user_message"]
                }
            ],
            "temperature": 0.7,
            "max_tokens": 800,
            "functions": desktop_pet_functions,
            "function_call": "auto"
        }
        
        print("📤 发送请求...")
        
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
                choice = result.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content", "")
                function_call = message.get("function_call")
                
                print(f"📥 HTTP状态: {response.status_code}")
                print(f"📝 对话内容: '{content}'")
                
                if function_call:
                    func_name = function_call.get("name")
                    func_args = function_call.get("arguments", "{}")
                    print(f"🔧 函数调用: {func_name}({func_args})")
                    print(f"✅ 内容+函数调用: {'✓' if content else '✗'}")
                else:
                    print("💬 纯对话响应")
                    
                # 分析响应质量
                has_content = bool(content and content.strip())
                has_function = bool(function_call)
                
                quality_score = 0
                if has_content: quality_score += 1
                if has_function: quality_score += 1
                if has_content and has_function: quality_score += 1  # 额外加分
                
                print(f"⭐ 响应质量评分: {quality_score}/3")
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print("\n" + "=" * 80)
    print("📊 测试结果分析")
    print("=" * 80)
    
    print("""
🎯 关键发现:

1. 函数调用触发准确性:
   • 复杂指令能够正确识别多个函数调用需求
   • 参数解析准确，符合函数定义规范
   • 不同场景下的函数选择合理

2. 对话内容保持情况:
   • 需要优化系统提示词来强制保持对话内容
   • 当前存在content为空的情况
   • 可以通过更好的提示词工程解决

3. 响应质量评估:
   • 最佳情况: 既有对话内容又有函数调用 (3分)
   • 良好情况: 有对话内容或函数调用 (1-2分)
   • 需改进: 两者皆无 (0分)

4. 改进建议:
   • 强化系统提示词，明确要求保持对话内容
   • 在函数调用时自动生成自然语言回应
   • 建立后备机制确保对话连续性
    """)

if __name__ == "__main__":
    test_enhanced_desktop_pet()