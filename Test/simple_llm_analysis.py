#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单分析LLM通信数据结构
展示请求和响应的原始格式
"""

import json
import os

def show_sample_requests():
    """展示典型的请求和响应样本"""
    
    print("=" * 80)
    print("LLM通信数据结构分析")
    print("=" * 80)
    print()
    
    # 示例1: 普通对话请求
    print("📋 示例1: 普通对话模式请求")
    print("-" * 50)
    
    normal_request = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。\n\n当前处于普通对话模式，请以友好、专业的态度回答用户问题。"
            },
            {
                "role": "user", 
                "content": "场景：public\n\n用户输入：你好，能介绍一下辽宁省博物馆吗？"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
        "top_p": 0.1
    }
    
    print("📤 发送到LLM的原始请求:")
    print(json.dumps(normal_request, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    
    # 示例2: 函数调用请求
    print("📋 示例2: 函数调用模式请求")
    print("-" * 50)
    
    function_request = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。"
            },
            {
                "role": "user",
                "content": "场景：public\n\n用户输入：请告诉我博物馆的历史"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
        "top_p": 0.1,
        "functions": [
            {
                "name": "get_museum_info",
                "description": "获取博物馆基本信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "info_type": {
                            "type": "string",
                            "enum": ["history", "exhibitions", "location"],
                            "description": "信息类型"
                        }
                    },
                    "required": ["info_type"]
                }
            }
        ],
        "function_call": "auto"
    }
    
    print("📤 发送到LLM的原始请求:")
    print(json.dumps(function_request, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    
    # 示例3: 带RAG的复杂请求
    print("📋 示例3: 带RAG检索的复杂请求")
    print("-" * 50)
    
    rag_request = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。"
            },
            {
                "role": "user",
                "content": "场景：study\n根据知识库检索，辽宁省博物馆成立于1949年，是东北地区重要的综合性博物馆...\n\n用户输入：我想查找关于青铜器的文物资料"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
        "top_p": 0.1,
        "functions": [
            {
                "name": "search_artifacts",
                "description": "搜索文物信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "搜索关键词"},
                        "category": {"type": "string", "description": "文物类别"}
                    },
                    "required": ["keyword"]
                }
            }
        ],
        "function_call": "auto"
    }
    
    print("📤 发送到LLM的原始请求:")
    print(json.dumps(rag_request, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    
    # 示例4: 函数调用响应
    print("📋 示例4: LLM函数调用响应")
    print("-" * 50)
    
    function_response = {
        "id": "chatcmpl-example",
        "object": "chat.completion",
        "created": 1707037200,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "我将为您查询博物馆的历史信息。",
                    "function_call": {
                        "name": "get_museum_info",
                        "arguments": "{\n  \"info_type\": \"history\"\n}"
                    }
                },
                "finish_reason": "function_call"
            }
        ],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 45,
            "total_tokens": 165
        }
    }
    
    print("📥 从LLM接收的原始响应:")
    print(json.dumps(function_response, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    
    # 示例5: 普通对话响应
    print("📋 示例5: LLM普通对话响应")
    print("-" * 50)
    
    normal_response = {
        "id": "chatcmpl-example2",
        "object": "chat.completion",
        "created": 1707037300,
        "model": "qwen-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "辽宁省博物馆成立于1949年，位于沈阳市，是东北地区重要的综合性博物馆。馆内收藏了大量珍贵的文物，包括青铜器、陶瓷、书画等，展现了辽宁地区悠久的历史文化。"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 85,
            "completion_tokens": 67,
            "total_tokens": 152
        }
    }
    
    print("📥 从LLM接收的原始响应:")
    print(json.dumps(normal_response, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    
    # 示例6: 解析后的标准化结果
    print("📋 示例6: 服务器解析后的标准化结果")
    print("-" * 50)
    
    # 函数调用模式的结果
    parsed_function_result = {
        "command": "get_museum_info",
        "parameters": {
            "info_type": "history"
        },
        "type": "function_call",
        "format": "openai_standard",
        "response": "我将为您查询博物馆的历史信息。"
    }
    
    print("🔧 函数调用模式解析结果:")
    print(json.dumps(parsed_function_result, ensure_ascii=False, indent=2))
    
    print()
    
    # 普通对话模式的结果
    parsed_normal_result = {
        "command": "general_chat",
        "response": "辽宁省博物馆成立于1949年，位于沈阳市，是东北地区重要的综合性博物馆。馆内收藏了大量珍贵的文物，包括青铜器、陶瓷、书画等，展现了辽宁地区悠久的历史文化。",
        "type": "direct_response",
        "format": "openai_standard"
    }
    
    print("💬 普通对话模式解析结果:")
    print(json.dumps(parsed_normal_result, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("📊 通信协议特点总结")
    print("=" * 80)
    
    print("""
🎯 核心特点分析:

1. 请求格式标准:
   • 严格遵循OpenAI Chat Completions API格式
   • messages数组包含system和user角色
   • 支持functions和function_call参数
   • 所有参数均可配置（来自config.json）

2. 响应格式统一:
   • 标准的choices/message结构
   • function_call字段用于函数调用指示
   • content字段始终包含对话内容
   • usage字段提供token使用统计

3. 双模式无缝切换:
   • 有函数定义 → function_call="auto" + functions列表
   • 无函数定义 → 纯对话模式，content字段为主
   • 两种模式响应结构一致

4. 数据完整性保证:
   • 原始请求数据完整记录
   • 原始响应数据原样保存
   • 解析过程透明可追溯
   • 错误信息详细记录

5. 配置驱动特性:
   • 模型参数来自config.json
   • 系统提示词可配置
   • API端点和密钥支持环境变量
   • 支持热更新配置
    """)

if __name__ == "__main__":
    show_sample_requests()