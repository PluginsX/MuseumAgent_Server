#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的客户端-服务端通信日志演示
展示统一的日志格式规范在各个模块中的应用
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.common.log_formatter import log_step, log_communication, log_flow_summary

def demo_complete_communication_flow():
    """演示完整的客户端-服务端通信流程"""
    print("=" * 120)
    print("🌐 完整客户端-服务端通信日志演示")
    print("=" * 120)
    
    # 模拟时间戳
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n⏰ 演示时间: {timestamp}")
    print()
    
    # 1. 客户端注册会话
    print("📱 STEP 1: 客户端会话注册")
    print("-" * 60)
    
    registration_request = {
        "client_metadata": {
            "client_type": "spirit",
            "version": "1.0.0",
            "platform": "windows"
        },
        "operation_set": ["idle", "walk", "run", "speak", "happy", "sad"]
    }
    
    print(log_communication('CLIENT', 'RECEIVE', 'Client Registration', 
                           registration_request, 
                           {'client_type': 'spirit'}))
    
    print(log_step('SESSION', 'REGISTER', '生成新会话ID', 
                  {'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'}))
    
    registration_response = {
        "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "expires_at": "2026-02-03T14:18:44.842488",
        "supported_features": ["dynamic_operations", "session_management", "heartbeat"]
    }
    
    print(log_step('SESSION', 'SUCCESS', '会话注册成功', 
                  {'operations': 6, 'expires_at': '2026-02-03T14:18:44.842488'}))
    
    print(log_communication('CLIENT', 'SEND', 'Registration Success', registration_response))
    
    # 2. 客户端发送用户消息
    print("\n💬 STEP 2: 用户消息处理")
    print("-" * 60)
    
    user_message = {
        "user_input": "卷体夔纹蟠龙盖罍的详细尺寸",
        "client_type": "spirit",
        "scene_type": "leisure"
    }
    
    print(log_communication('CLIENT', 'RECEIVE', 'User Message', 
                           user_message, 
                           {'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 
                            'preview': '卷体夔纹蟠龙盖罍的详细尺寸'}))
    
    print(log_step('API', 'START', '开始处理用户请求', 
                  {'client_type': 'spirit', 'scene_type': 'leisure'}))
    
    # 3. 内部处理流程
    print("\n⚙️  STEP 3: 内部处理流程")
    print("-" * 60)
    
    # RAG检索
    rag_query = "卷体夔纹蟠龙盖罍的详细尺寸"
    print(log_step('RAG', 'START', '执行向量检索 (Top-K: 3)', 
                  {'query': rag_query, 'top_k': 3}))
    
    print(log_communication('RAG', 'SEND', 'ChromaDB Vector Store', 
                           {'query_text': rag_query, 'top_k': 3}))
    
    rag_results = [
        {
            "artifact_name": "卷体夔纹蟠龙盖罍",
            "document": "商代晚期青铜器，高38.5厘米，口径23.5厘米...",
            "distance": 0.15
        }
    ]
    
    print(log_communication('RAG', 'RECEIVE', 'ChromaDB Vector Store', 
                           rag_results, 
                           {'result_count': 1}))
    
    print(log_step('RAG', 'PROCESS', '检索完成，找到 1 个相关文档'))
    
    # 提示词构建
    print(log_step('PROMPT', 'INFO', '未检索到相关内容，使用禁用模板', 
                  {'artifact_count': 0}))
    
    print(log_step('PROMPT', 'SUCCESS', '构建RAG指令完成', 
                  {'length': 0, 'artifact_count': 0}))
    
    # LLM处理
    final_prompt = "你是辽宁省博物馆智能助手..."
    llm_response = '''{
  "artifact_name": "卷体夔纹蟠龙盖罍",
  "operation": "query_param",
  "keywords": ["卷体夔纹蟠龙盖罍", "尺寸"],
  "response": "卷体夔纹蟠龙盖罍的具体尺寸为：高38.5厘米，口径23.5厘米，底径20厘米。"
}'''
    
    print(log_step('LLM', 'SEND', '发送提示词到LLM', 
                  {'prompt_length': len(final_prompt), 'model': 'qwen-turbo'}))
    
    print(log_communication('LLM', 'SEND', 'External LLM API', 
                           {'model': 'qwen-turbo', 'messages': [{'role': 'user', 'content': final_prompt[:100]+'...'}]}, 
                           {'endpoint': 'https://api.example.com/chat/completions'}))
    
    print(log_communication('LLM', 'RECEIVE', 'External LLM API', 
                           {'full_response': llm_response, 'usage': {'total_tokens': 85}}, 
                           {'response_length': len(llm_response)}))
    
    print(log_step('LLM', 'RECEIVE', '成功接收LLM响应', 
                  {'response_length': len(llm_response)}))
    
    # 响应解析
    print(log_step('PARSER', 'START', '开始解析LLM响应', 
                  {'response_length': len(llm_response)}))
    
    print(log_step('PARSER', 'SUCCESS', 'JSON解析成功', 
                  {'fields': ['artifact_name', 'operation', 'keywords', 'response']}))
    
    # 4. 返回客户端响应
    print("\n📤 STEP 4: 客户端响应返回")
    print("-" * 60)
    
    print(log_step('API', 'SUCCESS', '请求处理完成', 
                  {'operation': 'query_param', 'artifact_name': '卷体夔纹蟠龙盖罍'}))
    
    agent_response = {
        "artifact_id": "artifact_001",
        "artifact_name": "卷体夔纹蟠龙盖罍",
        "operation": "query_param",
        "operation_params": {},
        "keywords": ["卷体夔纹蟠龙盖罍", "尺寸"],
        "tips": None,
        "response": "卷体夔纹蟠龙盖罍的具体尺寸为：高38.5厘米，口径23.5厘米，底径20厘米。"
    }
    
    print(log_communication('CLIENT', 'SEND', 'Agent Response', agent_response))
    
    # 5. 心跳检测
    print("\n💓 STEP 5: 心跳检测")
    print("-" * 60)
    
    print(log_step('SESSION', 'HEARTBEAT', '收到心跳请求', 
                  {'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'}))
    
    heartbeat_response = {
        "status": "alive",
        "session_valid": True
    }
    
    print(log_communication('CLIENT', 'SEND', 'Heartbeat Response', heartbeat_response))
    
    # 6. 会话注销
    print("\n🗑️  STEP 6: 会话注销")
    print("-" * 60)
    
    print(log_step('SESSION', 'UNREGISTER', '收到注销请求', 
                  {'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'}))
    
    unregister_response = {
        "status": "unregistered",
        "message": "会话已成功注销"
    }
    
    print(log_communication('CLIENT', 'SEND', 'Unregister Response', unregister_response))
    
    # 7. 流程摘要
    print("\n" + "=" * 120)
    print("📋 完整通信流程摘要")
    print("=" * 120)
    
    flow_summary = [
        {'module': 'CLIENT', 'operation': 'REGISTER', 'message': '客户端会话注册'},
        {'module': 'API', 'operation': 'RECEIVE', 'message': '接收用户消息'},
        {'module': 'RAG', 'operation': 'PROCESS', 'message': '向量检索处理'},
        {'module': 'PROMPT', 'operation': 'BUILD', 'message': '提示词构建'},
        {'module': 'LLM', 'operation': 'PROCESS', 'message': 'LLM推理处理'},
        {'module': 'PARSER', 'operation': 'PARSE', 'message': '响应解析'},
        {'module': 'API', 'operation': 'SEND', 'message': '返回客户端响应'},
        {'module': 'SESSION', 'operation': 'HEARTBEAT', 'message': '心跳检测'},
        {'module': 'SESSION', 'operation': 'UNREGISTER', 'message': '会话注销'}
    ]
    
    print(log_flow_summary(flow_summary))
    
    print("✅ 完整通信流程演示完成!")

def demo_error_handling():
    """演示错误处理的日志输出"""
    print("\n" + "=" * 120)
    print("⚠️  错误处理日志演示")
    print("=" * 120)
    
    # 模拟各种错误情况
    error_scenarios = [
        {
            'name': '无效注册数据',
            'log': log_step('CLIENT', 'ERROR', '无效的客户端注册数据格式'),
            'type': '客户端错误'
        },
        {
            'name': '会话不存在',
            'log': log_step('SESSION', 'ERROR', '心跳失败：会话不存在或已过期', 
                           {'session_id': 'invalid-session-id'}),
            'type': '会话错误'
        },
        {
            'name': 'LLM API调用失败',
            'log': log_step('LLM', 'ERROR', 'LLM API调用失败', 
                           {'status_code': 500, 'error': 'Service Unavailable'}),
            'type': '外部服务错误'
        },
        {
            'name': 'JSON解析失败',
            'log': log_step('PARSER', 'ERROR', 'JSON解析失败', 
                           {'error': 'Expecting value: line 1 column 1 (char 0)'}),
            'type': '数据格式错误'
        }
    ]
    
    for scenario in error_scenarios:
        print(f"\n🔴 {scenario['type']}: {scenario['name']}")
        print(scenario['log'])

if __name__ == "__main__":
    demo_complete_communication_flow()
    demo_error_handling()
    print("\n" + "=" * 120)
    print("🎉 所有日志规范演示完成!")
    print("=" * 120)