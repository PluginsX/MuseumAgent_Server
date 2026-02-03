#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试简化后的LLM响应处理流程
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.modules.response_parser import ResponseParser

def test_simplified_processing():
    """测试简化处理逻辑"""
    print("=== 简化LLM响应处理测试 ===\n")
    
    # 测试用例
    test_cases = [
        {
            "name": "标准JSON格式",
            "response": '{"artifact_name": "蟠龙盖罍", "operation": "introduce", "keywords": ["蟠龙", "青铜器"], "response": "这是一个精美的文物"}',
            "expected": "直接转发"
        },
        {
            "name": "带代码块的JSON",
            "response": '```json\n{"artifact_name": null, "operation": "general_chat", "keywords": ["问候"], "response": "你好！"}\n```',
            "expected": "直接转发"
        },
        {
            "name": "自然语言响应",
            "response": "你好！很高兴为您服务。请问有什么我可以帮助您的吗？",
            "expected": "包装为standard_chat"
        },
        {
            "name": "部分JSON格式",
            "response": '我觉得您想了解文物信息，{"operation": "introduce"} 这件文物很有趣',
            "expected": "包装为standard_chat"
        },
        {
            "name": "空响应",
            "response": "",
            "expected": "包装为standard_chat"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"--- 测试案例 {i}: {case['name']} ---")
        print(f"输入: {case['response'][:50]}{'...' if len(case['response']) > 50 else ''}")
        print(f"预期: {case['expected']}")
        
        try:
            result = ResponseParser.parse_llm_response(case['response'])
            print(f"实际结果:")
            print(f"  operation: {result.get('operation')}")
            print(f"  response: {result.get('response')[:50]}{'...' if len(str(result.get('response'))) > 50 else ''}")
            print(f"  是否包装: {result.get('wrapped', False)}")
            
            # 验证结果
            if case['expected'] == "直接转发":
                success = result.get('operation') != 'general_chat' or not result.get('wrapped')
            else:  # 包装为standard_chat
                success = result.get('operation') == 'general_chat' and result.get('wrapped')
            
            print(f"✅ 测试{'通过' if success else '失败'}")
            
        except Exception as e:
            print(f"❌ 测试异常: {e}")
        
        print()

def test_performance_comparison():
    """性能对比测试"""
    print("=== 性能对比测试 ===\n")
    
    import time
    
    # 模拟大量请求
    test_responses = [
        '{"artifact_name": "文物1", "operation": "introduce", "response": "介绍"}',
        "这是一段自然语言回复，不是JSON格式",
        '{"operation": "query_param", "response": "查询"}',
        "又是自然语言内容...",
        '{"artifact_name": null, "operation": "general_chat", "response": "对话"}'
    ] * 20  # 100个请求
    
    print(f"测试 {len(test_responses)} 个响应处理...")
    
    start_time = time.time()
    for response in test_responses:
        try:
            result = ResponseParser.parse_llm_response(response)
        except:
            pass
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / len(test_responses)
    
    print(f"总耗时: {total_time:.4f} 秒")
    print(f"平均耗时: {avg_time*1000:.2f} 毫秒")
    print(f"处理速度: {len(test_responses)/total_time:.1f} 响应/秒")

if __name__ == "__main__":
    test_simplified_processing()
    test_performance_comparison()
    print("=== 测试完成 ===")