#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际网络通信测试
展示真实的LLM API调用过程和原始数据
"""

import requests
import json
import os
from datetime import datetime

def test_actual_llm_communication():
    """测试实际的LLM通信过程"""
    
    print("=" * 80)
    print("实际LLM通信测试")
    print("=" * 80)
    print()
    
    # 从环境变量或配置获取API信息
    base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.getenv("LLM_API_KEY", "sk-a7558f9302974d1891906107f6033939")
    model = os.getenv("LLM_MODEL", "qwen-turbo")
    
    if not api_key:
        print("⚠️  未配置LLM_API_KEY环境变量，使用模拟数据展示")
        show_mock_communication()
        return
    
    print(f"📡 连接信息:")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    print(f"   API Key: {api_key[:8]}..." if api_key else "None")
    print()
    
    # 测试1: 普通对话
    print("📋 测试1: 普通对话请求")
    print("-" * 50)
    
    normal_payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是辽宁省博物馆智能助手。请以友好、专业的态度回答用户问题。"
            },
            {
                "role": "user",
                "content": "你好，请简单介绍一下辽宁省博物馆。"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    print("📤 发送的原始请求:")
    print(json.dumps(normal_payload, ensure_ascii=False, indent=2))
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=normal_payload,
            timeout=30
        )
        
        print(f"\n📥 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            raw_response = response.json()
            print("\n📥 原始响应数据:")
            print(json.dumps(raw_response, ensure_ascii=False, indent=2))
            
            # 分析响应
            message = raw_response.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "")
            print(f"\n📝 提取的对话内容: {content}")
            
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")
    
    print("\n" + "=" * 80)
    
    # 测试2: Windows桌宠函数调用
    print("📋 测试2: Windows桌宠函数调用请求")
    print("-" * 50)
    
    desktop_pet_functions = [
        {
            "name": "move_to_position",
            "description": "移动桌宠到指定屏幕位置",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "X坐标位置(0-1920)"
                    },
                    "y": {
                        "type": "integer", 
                        "description": "Y坐标位置(0-1080)"
                    }
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
                    "duration": {
                        "type": "integer",
                        "description": "持续时间(秒)",
                        "minimum": 1,
                        "maximum": 30
                    }
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
                    "text": {
                        "type": "string",
                        "description": "要说的话"
                    },
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
                    "repeat_times": {
                        "type": "integer",
                        "description": "重复次数",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["action"]
            }
        }
    ]
    
    function_payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个可爱的Windows桌面宠物助手。根据用户的需求调用相应的函数来控制桌宠的行为。"
            },
            {
                "role": "user",
                "content": "请让桌宠移动到屏幕右上角，然后开心地跳舞3次，最后说一句'主人回来啦！'"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500,
        "functions": desktop_pet_functions,
        "function_call": "auto"
    }
    
    print("📤 发送的原始请求:")
    print(json.dumps(function_payload, ensure_ascii=False, indent=2))
    
    try:
        response2 = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=function_payload,
            timeout=30
        )
        
        print(f"\n📥 HTTP状态码: {response2.status_code}")
        
        if response2.status_code == 200:
            raw_response2 = response2.json()
            print("\n📥 原始响应数据:")
            print(json.dumps(raw_response2, ensure_ascii=False, indent=2))
            
            # 分析响应
            message2 = raw_response2.get("choices", [{}])[0].get("message", {})
            content2 = message2.get("content", "")
            function_call = message2.get("function_call")
            
            print(f"\n📝 对话内容: {content2}")
            if function_call:
                print(f"🔧 函数调用: {function_call.get('name')}({function_call.get('arguments')})")
            else:
                print("💬 纯对话响应")
                
        else:
            print(f"❌ 请求失败: {response2.text}")
            
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")

def show_mock_communication():
    """展示模拟的通信数据（当无真实API时）"""
    
    print("📋 模拟通信数据展示")
    print("-" * 50)
    
    # 模拟请求1
    mock_request1 = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是辽宁省博物馆智能助手。请以友好、专业的态度回答用户问题。"
            },
            {
                "role": "user",
                "content": "辽宁省博物馆有哪些特色展品？"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    print("📤 模拟发送的请求:")
    print(json.dumps(mock_request1, ensure_ascii=False, indent=2))
    
    # 模拟响应1
    mock_response1 = {
        "id": "chatcmpl-mock-001",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "辽宁省博物馆拥有丰富的特色展品，主要包括：\n\n1. 红山文化玉器：包括著名的玉猪龙等珍贵文物\n2. 商周青铜器：展示了中国古代青铜文化的精湛工艺\n3. 历代陶瓷：从汉唐到明清各时期的代表性瓷器\n4. 书画珍品：收藏了大量古代名家书画作品\n5. 满族文物：体现了满族历史文化特色"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 45,
            "completion_tokens": 128,
            "total_tokens": 173
        }
    }
    
    print("\n📥 模拟接收的响应:")
    print(json.dumps(mock_response1, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    
    # 模拟请求2（Windows桌宠函数调用）
    desktop_pet_mock_functions = [
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
        }
    ]
    
    mock_request2 = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system", 
                "content": "你是一个可爱的Windows桌面宠物助手。根据用户的需求调用相应的函数来控制桌宠的行为。"
            },
            {
                "role": "user",
                "content": "请让桌宠移动到屏幕中央(960,540)，播放开心的动画5秒钟，然后说'欢迎回来，主人！'"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500,
        "functions": desktop_pet_mock_functions,
        "function_call": "auto"
    }
    
    print("📤 模拟函数调用请求:")
    print(json.dumps(mock_request2, ensure_ascii=False, indent=2))
    
    # 模拟响应2
    mock_response2 = {
        "id": "chatcmpl-mock-002",
        "object": "chat.completion", 
        "created": int(datetime.now().timestamp()),
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "好的！我来控制桌宠执行您的指令。首先移动到屏幕中央，然后播放开心动画，最后说欢迎词。",
                    "function_call": {
                        "name": "move_to_position",
                        "arguments": "{\n  \"x\": 960,\n  \"y\": 540\n}"
                    }
                },
                "finish_reason": "function_call"
            }
        ],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 75,
            "total_tokens": 195
        }
    }
    
    print("\n📥 模拟函数调用响应:")
    print(json.dumps(mock_response2, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("📊 通信流程说明")
    print("=" * 80)
    
    print("""
🎯 实际通信流程:

1. 请求构建阶段:
   • 根据会话状态确定是否启用函数调用
   • 构造符合OpenAI标准的messages数组
   • 添加必要的functions和function_call参数
   • 设置温度、token限制等模型参数

2. 网络传输阶段:
   • 通过HTTPS POST请求发送到LLM API
   • 请求头包含Authorization和Content-Type
   • 完整的JSON负载作为请求体

3. 响应处理阶段:
   • 接收标准的Chat Completion响应格式
   • 解析choices数组中的message对象
   • 提取content字段的对话内容
   • 处理function_call字段的函数调用信息

4. 结果标准化:
   • 将原始响应转换为统一的内部格式
   • 保持content对话内容的完整性
   • 提供清晰的函数调用指示
   • 记录完整的使用统计信息
    """)

if __name__ == "__main__":
    test_actual_llm_communication()