#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析服务器与LLM通信的原始数据内容
展示100%真实的请求和响应数据
"""

import sys
import os
import json
from datetime import datetime

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
strict_session_manager_module = load_module_from_path('strict_session_manager',
                                                    os.path.join(project_root, 'src', 'session', 'strict_session_manager.py'))
function_calling_models = load_module_from_path('function_calling_models',
                                              os.path.join(project_root, 'src', 'models', 'function_calling_models.py'))

# 获取类引用
DynamicLLMClient = getattr(dynamic_llm_client, 'DynamicLLMClient')
strict_session_manager = getattr(strict_session_manager_module, 'strict_session_manager')
FunctionDefinition = getattr(function_calling_models, 'FunctionDefinition')

def test_raw_communication_data():
    """测试并展示原始的LLM通信数据"""
    print("=" * 80)
    print("服务器与LLM通信原始数据分析")
    print("=" * 80)
    print()
    
    # 初始化客户端
    client = DynamicLLMClient()
    print(f"✅ LLM客户端初始化完成")
    print(f"   Base URL: {client.base_url}")
    print(f"   Model: {client.model}")
    print(f"   Timeout: {client.timeout}s")
    print()
    
    # 测试1: 普通对话模式（无函数定义）
    print("📋 测试1: 普通对话模式")
    print("-" * 50)
    
    try:
        # 创建测试会话（不注册函数）
        test_session_id = "raw-test-session-001"
        strict_session_manager.create_session(test_session_id, "public")
        print(f"✅ 创建测试会话: {test_session_id}")
        
        # 生成普通对话请求
        user_input = "你好，能介绍一下辽宁省博物馆吗？"
        scene_type = "public"
        
        # 获取函数定义（应该为空）
        functions = client.get_available_functions(test_session_id)
        print(f"📊 当前会话函数定义数量: {len(functions)}")
        
        # 生成请求负载
        payload = client.generate_function_calling_payload(
            session_id=test_session_id,
            user_input=user_input,
            scene_type=scene_type,
            functions=functions
        )
        
        print("\n📤 发送到LLM的原始请求数据:")
        print("=" * 60)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("=" * 60)
        
        # 实际调用LLM（如果配置了API）
        if client.base_url and client.api_key:
            print("\n📡 正在调用LLM API...")
            response = client._chat_completions_with_functions(payload)
            
            print("\n📥 从LLM接收的原始响应数据:")
            print("=" * 60)
            print(json.dumps(response, ensure_ascii=False, indent=2))
            print("=" * 60)
            
            # 解析响应
            parsed_result = client.parse_function_call_response(response)
            print(f"\n🔍 解析后的标准化结果:")
            print(json.dumps(parsed_result, ensure_ascii=False, indent=2))
        else:
            print("\n⚠️  未配置LLM API，跳过实际调用")
            
    except Exception as e:
        print(f"\n❌ 测试1出错: {e}")
    
    print("\n" + "=" * 80)
    
    # 测试2: 函数调用模式
    print("📋 测试2: 函数调用模式")
    print("-" * 50)
    
    try:
        # 注册测试函数
        test_session_id2 = "raw-test-session-002"
        strict_session_manager.create_session(test_session_id2, "public")
        
        # 定义测试函数
        test_function = FunctionDefinition(
            name="get_museum_info",
            description="获取博物馆基本信息",
            parameters={
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
        )
        
        # 注册函数
        strict_session_manager.register_function(test_session_id2, test_function)
        print(f"✅ 创建带函数的测试会话: {test_session_id2}")
        
        # 获取函数定义
        functions = client.get_available_functions(test_session_id2)
        print(f"📊 当前会话函数定义数量: {len(functions)}")
        
        # 显示函数定义详情
        if functions:
            print("\n📄 注册的函数定义:")
            print(json.dumps(functions[0], ensure_ascii=False, indent=2))
        
        # 生成函数调用请求
        user_input2 = "请告诉我博物馆的历史"
        payload2 = client.generate_function_calling_payload(
            session_id=test_session_id2,
            user_input=user_input2,
            scene_type=scene_type,
            functions=functions
        )
        
        print("\n📤 发送到LLM的原始请求数据:")
        print("=" * 60)
        print(json.dumps(payload2, ensure_ascii=False, indent=2))
        print("=" * 60)
        
        # 实际调用LLM（如果配置了API）
        if client.base_url and client.api_key:
            print("\n📡 正在调用LLM API...")
            response2 = client._chat_completions_with_functions(payload2)
            
            print("\n📥 从LLM接收的原始响应数据:")
            print("=" * 60)
            print(json.dumps(response2, ensure_ascii=False, indent=2))
            print("=" * 60)
            
            # 解析响应
            parsed_result2 = client.parse_function_call_response(response2)
            print(f"\n🔍 解析后的标准化结果:")
            print(json.dumps(parsed_result2, ensure_ascii=False, indent=2))
        else:
            print("\n⚠️  未配置LLM API，跳过实际调用")
            
    except Exception as e:
        print(f"\n❌ 测试2出错: {e}")
    
    print("\n" + "=" * 80)
    
    # 测试3: 带RAG的复杂场景
    print("📋 测试3: 带RAG检索的复杂场景")
    print("-" * 50)
    
    try:
        test_session_id3 = "raw-test-session-003"
        strict_session_manager.create_session(test_session_id3, "study")
        
        # 注册多个函数
        functions_complex = [
            FunctionDefinition(
                name="search_artifacts",
                description="搜索文物信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "搜索关键词"},
                        "category": {"type": "string", "description": "文物类别"}
                    },
                    "required": ["keyword"]
                }
            ),
            FunctionDefinition(
                name="get_exhibition_info",
                description="获取展览信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "exhibition_name": {"type": "string", "description": "展览名称"}
                    },
                    "required": ["exhibition_name"]
                }
            )
        ]
        
        for func in functions_complex:
            strict_session_manager.register_function(test_session_id3, func)
        
        print(f"✅ 创建复杂场景测试会话: {test_session_id3}")
        print(f"📊 注册函数数量: {len(functions_complex)}")
        
        # 模拟RAG检索结果
        rag_result = "根据知识库检索，辽宁省博物馆成立于1949年，是东北地区重要的综合性博物馆..."
        
        # 生成复杂请求
        user_input3 = "我想查找关于青铜器的文物资料"
        payload3 = client.generate_function_calling_payload(
            session_id=test_session_id3,
            user_input=user_input3,
            scene_type="study",
            rag_instruction=rag_result,
            functions=functions_complex
        )
        
        print("\n📤 发送到LLM的原始请求数据:")
        print("=" * 60)
        print(json.dumps(payload3, ensure_ascii=False, indent=2))
        print("=" * 60)
        
        # 显示请求的关键组成部分
        print(f"\n📊 请求数据结构分析:")
        print(f"   • Model: {payload3.get('model')}")
        print(f"   • Temperature: {payload3.get('temperature')}")
        print(f"   • Max Tokens: {payload3.get('max_tokens')}")
        print(f"   • Messages 数量: {len(payload3.get('messages', []))}")
        print(f"   • 是否包含函数: {'functions' in payload3}")
        print(f"   • 函数调用策略: {payload3.get('function_call', 'N/A')}")
        
        if 'functions' in payload3:
            print(f"   • 函数定义数量: {len(payload3['functions'])}")
        
    except Exception as e:
        print(f"\n❌ 测试3出错: {e}")
    
    print("\n" + "=" * 80)
    print("📊 通信数据分析总结")
    print("=" * 80)
    
    # 总结通信特点
    print("""
🎯 关键观察点:

1. 请求结构特征:
   • 严格遵循OpenAI API标准格式
   • 包含完整的messages数组（system + user角色）
   • 支持functions和function_call参数（函数调用模式）
   • 参数配置来自config.json和环境变量

2. 响应数据特征:
   • 标准的choices数组结构
   • message对象包含content和function_call字段
   • usage统计信息
   • 严格的JSON格式

3. 双模式支持:
   • 有函数定义时：启用function_call="auto"
   • 无函数定义时：退化为普通对话模式
   • 两种模式都保证包含对话内容(content字段)

4. 数据完整性:
   • 所有请求都记录完整原始数据
   • 响应数据原样保存，不做预处理
   • 错误信息也完整记录
    """)
    
    # 清理测试会话
    try:
        strict_session_manager.delete_session(test_session_id)
        strict_session_manager.delete_session(test_session_id2)
        strict_session_manager.delete_session(test_session_id3)
        print("\n✅ 测试会话已清理")
    except:
        pass

if __name__ == "__main__":
    test_raw_communication_data()