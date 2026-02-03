#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试提示词构建修复效果
验证RAG上下文能否正确嵌入最终提示词
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 初始化配置
from src.common.config_utils import load_config
load_config()

from src.core.modules.prompt_builder import PromptBuilder
from src.core.modules.rag_processor import RAGProcessor
from src.common.log_formatter import log_step

def test_rag_context_integration():
    """测试RAG上下文与提示词的集成"""
    print("=" * 80)
    print("🔍 RAG上下文集成测试")
    print("=" * 80)
    
    # 初始化组件
    rag_processor = RAGProcessor()
    prompt_builder = PromptBuilder()
    
    # 测试用户输入
    user_input = "卷体夔纹蟠龙盖罍的详细尺寸？"
    scene_type = "leisure"
    valid_operations = ["introduce", "query_param", "general_chat"]
    
    print(f"📝 测试输入:")
    print(f"  用户输入: {user_input}")
    print(f"  场景类型: {scene_type}")
    print(f"  可用操作: {valid_operations}")
    print()
    
    # 1. 执行RAG检索
    print("📚 步骤1: 执行RAG检索")
    rag_context = rag_processor.perform_retrieval(user_input, top_k=2)
    print(f"  检索到 {rag_context.get('total_found', 0)} 个相关文档")
    
    # 显示检索到的内容预览
    relevant_artifacts = rag_context.get('relevant_artifacts', [])
    for i, artifact in enumerate(relevant_artifacts[:2]):
        print(f"  文档{i+1}: {artifact.get('artifact_name', 'Unknown')}")
        print(f"    描述预览: {artifact.get('document', '')[:100]}...")
        print(f"    距离: {artifact.get('distance', 'N/A')}")
    print()
    
    # 2. 构建RAG指令
    print("⚙️  步骤2: 构建RAG指令")
    rag_instruction = prompt_builder.build_rag_instruction(rag_context)
    print(f"  RAG指令长度: {len(rag_instruction)} 字符")
    print(f"  RAG指令预览: {rag_instruction[:200]}{'...' if len(rag_instruction) > 200 else ''}")
    print()
    
    # 3. 构建最终提示词
    print("📝 步骤3: 构建最终提示词")
    final_prompt = prompt_builder.build_final_prompt(
        user_input=user_input,
        scene_type=scene_type,
        valid_operations=valid_operations,
        rag_instruction=rag_instruction
    )
    
    print(f"  最终提示词长度: {len(final_prompt)} 字符")
    print(f"  最终提示词预览:")
    print("-" * 60)
    print(final_prompt[:500] + ("..." if len(final_prompt) > 500 else ""))
    print("-" * 60)
    print()
    
    # 4. 验证RAG上下文是否正确嵌入
    print("✅ 验证结果:")
    if rag_instruction and rag_instruction in final_prompt:
        print("  ✅ RAG上下文已成功嵌入最终提示词")
    else:
        print("  ❌ RAG上下文未正确嵌入最终提示词")
        
    if "卷体夔纹蟠龙盖罍" in final_prompt:
        print("  ✅ 文物名称已包含在提示词中")
    else:
        print("  ⚠️  文物名称未包含在提示词中")
        
    if "尺寸" in final_prompt:
        print("  ✅ 查询关键词已包含在提示词中")
    else:
        print("  ⚠️  查询关键词未包含在提示词中")
    
    return {
        'rag_context_built': len(rag_instruction) > 0,
        'final_prompt_built': len(final_prompt) > 0,
        'rag_integrated': rag_instruction in final_prompt if rag_instruction else False
    }

def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 80)
    print("🧪 边界情况测试")
    print("=" * 80)
    
    prompt_builder = PromptBuilder()
    
    # 测试空RAG指令
    print("测试1: 空RAG指令")
    empty_prompt = prompt_builder.build_final_prompt(
        user_input="你好",
        scene_type="public", 
        valid_operations=["general_chat"],
        rag_instruction=""
    )
    print(f"  结果: 成功构建，长度 {len(empty_prompt)} 字符")
    
    # 测试无检索结果的情况
    print("测试2: 无RAG检索结果")
    no_rag_context = {'relevant_artifacts': [], 'total_found': 0}
    rag_instruction = prompt_builder.build_rag_instruction(no_rag_context)
    no_rag_prompt = prompt_builder.build_final_prompt(
        user_input="随便聊聊",
        scene_type="leisure",
        valid_operations=["general_chat"],
        rag_instruction=rag_instruction
    )
    print(f"  RAG指令: '{rag_instruction}'")
    print(f"  最终提示词长度: {len(no_rag_prompt)} 字符")

def main():
    """主测试函数"""
    print("🔍 博物馆智能体提示词构建测试")
    print("=" * 80)
    
    # 主要功能测试
    results = test_rag_context_integration()
    
    # 边界情况测试
    test_edge_cases()
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)
    
    if results['rag_context_built']:
        print("✅ RAG上下文构建: 通过")
    else:
        print("❌ RAG上下文构建: 失败")
        
    if results['final_prompt_built']:
        print("✅ 最终提示词构建: 通过")
    else:
        print("❌ 最终提示词构建: 失败")
        
    if results['rag_integrated']:
        print("✅ RAG上下文集成: 通过")
        print("\n🎉 修复成功！RAG检索到的相关资料现在能够正确嵌入最终提示词中")
    else:
        print("❌ RAG上下文集成: 失败")
        print("\n⚠️  仍存在问题需要进一步排查")

if __name__ == "__main__":
    main()