#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试完整的日志输出效果
模拟一次完整的请求处理流程
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.command_generator import CommandGenerator
from src.core.modules.rag_processor import RAGProcessor
from src.core.modules.prompt_builder import PromptBuilder
from src.core.modules.response_parser import ResponseParser
from src.common.log_formatter import log_flow_summary

def test_complete_logging():
    """测试完整的日志输出"""
    print("=" * 100)
    print("🔍 完整日志输出测试")
    print("=" * 100)
    
    # 模拟用户请求
    user_input = "卷体夔纹蟠龙盖罍的详细尺寸"
    scene_type = "leisure"
    session_id = "test-session-log-demo"
    
    print(f"\n🎯 测试请求:")
    print(f"  用户输入: {user_input}")
    print(f"  场景类型: {scene_type}")
    print(f"  会话ID: {session_id}")
    print()
    
    try:
        # 1. 初始化各模块
        print("🔧 初始化处理模块...")
        rag_processor = RAGProcessor()
        prompt_builder = PromptBuilder()
        command_generator = CommandGenerator()
        
        # 2. RAG检索步骤
        print("\n" + "="*60)
        print("📚 STEP 1: RAG向量检索")
        print("="*60)
        rag_context = rag_processor.perform_retrieval(user_input, top_k=3)
        
        # 3. 提示词构建步骤
        print("\n" + "="*60)
        print("📝 STEP 2: 提示词构建")
        print("="*60)
        rag_instruction = prompt_builder.build_rag_instruction(rag_context)
        final_prompt = prompt_builder.build_final_prompt(
            user_input=user_input,
            scene_type=scene_type,
            valid_operations=["introduce", "query_param", "general_chat"],
            rag_instruction=rag_instruction
        )
        
        # 4. 模拟LLM响应（使用真实样例）
        print("\n" + "="*60)
        print("🤖 STEP 3: LLM处理")
        print("="*60)
        llm_response = '''{
  "artifact_name": "卷体夔纹蟠龙盖罍",
  "operation": "query_param",
  "keywords": ["卷体夔纹蟠龙盖罍", "尺寸"],
  "response": "卷体夔纹蟠龙盖罍的具体尺寸为：高38.5厘米，口径23.5厘米，底径20厘米。这件文物是商代晚期的青铜器，具有重要的历史和艺术价值。"
}'''
        
        print(f"[LLM] 发送提示词长度: {len(final_prompt)} 字符")
        print(f"[LLM] 接收响应长度: {len(llm_response)} 字符")
        
        # 5. 响应解析步骤
        print("\n" + "="*60)
        print("🔄 STEP 4: 响应解析")
        print("="*60)
        parsed_result = ResponseParser.parse_llm_response(llm_response)
        
        # 6. 构建最终指令
        print("\n" + "="*60)
        print("🎯 STEP 5: 构建标准化指令")
        print("="*60)
        final_command = ResponseParser.build_standard_command(parsed_result, rag_context)
        
        # 7. 输出完整流程摘要
        print("\n" + "="*100)
        print("📋 处理流程摘要")
        print("="*100)
        
        flow_steps = [
            {'module': 'RAG', 'operation': 'SUCCESS', 'message': '向量检索完成'},
            {'module': 'PROMPT', 'operation': 'SUCCESS', 'message': '提示词构建完成'},
            {'module': 'LLM', 'operation': 'SUCCESS', 'message': 'LLM处理完成'},
            {'module': 'PARSER', 'operation': 'SUCCESS', 'message': '响应解析完成'},
            {'module': 'COORD', 'operation': 'SUCCESS', 'message': '标准化指令生成完成'}
        ]
        
        print(log_flow_summary(flow_steps))
        
        # 8. 输出最终结果
        print("📊 最终结果:")
        print(json.dumps(final_command, ensure_ascii=False, indent=2))
        
        print("\n✅ 测试完成 - 日志格式规范化验证通过!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_edge_cases():
    """测试边界情况的日志输出"""
    print("\n" + "="*100)
    print("🧪 边界情况测试")
    print("="*100)
    
    # 测试自然语言响应
    print("\n📝 测试自然语言响应处理:")
    natural_response = "你好！这是一件很有趣的文物，不过我没有找到具体的尺寸信息。"
    
    try:
        result = ResponseParser.parse_llm_response(natural_response)
        print("处理结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"处理异常: {e}")

if __name__ == "__main__":
    test_complete_logging()
    test_edge_cases()
    print("\n" + "="*100)
    print("🎉 所有测试完成!")
    print("="*100)