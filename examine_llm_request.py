#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查发送给LLM的请求负载
"""

import json
from datetime import datetime

def examine_llm_request():
    """详细检查LLM请求"""
    print("🔍 LLM请求负载详细检查")
    print("=" * 50)
    
    # 先加载配置
    from src.common.config_utils import load_config
    load_config()
    
    from src.core.dynamic_llm_client import DynamicLLMClient
    from src.session.strict_session_manager import strict_session_manager
    
    llm_client = DynamicLLMClient()
    
    # 创建测试会话
    session_id = "request_examine_" + datetime.now().strftime("%Y%m%d_%H%M%S")
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
            "client_id": "request_examine",
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
    
    print(f"\n📡 完整请求负载:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # 详细分析各个部分
    print(f"\n📊 负载结构分析:")
    print(f"✅ Model: {payload.get('model')}")
    print(f"✅ Temperature: {payload.get('temperature')}")
    print(f"✅ Max tokens: {payload.get('max_tokens')}")
    
    # 检查消息结构
    messages = payload.get('messages', [])
    print(f"\n💬 消息结构 ({len(messages)} 条):")
    for i, msg in enumerate(messages):
        print(f"  消息 {i+1}:")
        print(f"    Role: {msg.get('role')}")
        print(f"    Content: {repr(msg.get('content')[:100])}{'...' if len(msg.get('content', '')) > 100 else ''}")
    
    # 检查函数调用配置
    print(f"\n🔧 函数调用配置:")
    has_functions = 'functions' in payload
    has_function_call = 'function_call' in payload
    
    print(f"✅ 包含functions字段: {has_functions}")
    print(f"✅ 包含function_call字段: {has_function_call}")
    
    if has_functions:
        functions_list = payload['functions']
        print(f"📊 函数定义数量: {len(functions_list)}")
        for i, func in enumerate(functions_list):
            print(f"  函数 {i+1}:")
            print(f"    Name: {func.get('name')}")
            print(f"    Description: {func.get('description')}")
            params = func.get('parameters', {})
            print(f"    参数属性数: {len(params.get('properties', {}))}")
            print(f"    必需参数: {params.get('required', [])}")
    
    if has_function_call:
        print(f"🎯 Function call模式: {payload['function_call']}")
    else:
        print(f"⚠️  缺少function_call字段")
        
    # 检查LLM配置
    print(f"\n⚙️  LLM配置检查:")
    config = llm_client.__dict__
    print(f"✅ Base URL: {config.get('base_url')}")
    print(f"✅ Model: {config.get('model')}")
    print(f"✅ Timeout: {config.get('timeout')}秒")
    
    # 验证函数定义格式
    print(f"\n📋 函数定义验证:")
    from src.models.function_calling_models import is_valid_openai_function
    
    for i, func_def in enumerate(functions):
        is_valid = is_valid_openai_function(func_def)
        status = "✅" if is_valid else "❌"
        print(f"  {status} 函数 {i+1} ({func_def.get('name', 'unknown')}): {'有效' if is_valid else '无效'}")
        
        if not is_valid:
            print(f"     问题: {func_def}")

if __name__ == "__main__":
    examine_llm_request()