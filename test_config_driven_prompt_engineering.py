#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置驱动的提示词工程
验证系统提示词从硬编码转移到配置文件的效果
"""

import sys
import os
import json
sys.path.append('.')

from src.common.config_utils import load_config
load_config()

from src.core.modules.prompt_builder import PromptBuilder

def test_config_driven_prompt_engineering():
    """测试配置驱动的提示词工程"""
    print("=== 测试配置驱动的提示词工程 ===\n")
    
    prompt_builder = PromptBuilder()
    
    # 测试用例1: 验证配置加载
    print("🔧 测试用例1: 配置加载验证")
    print("-" * 50)
    
    print("系统提示词配置:")
    system_prompts = prompt_builder.system_prompts
    for key, value in system_prompts.items():
        print(f"  {key}: {value[:100]}..." if len(value) > 100 else f"  {key}: {value}")
    print()
    
    # 测试用例2: 函数调用提示词生成
    print("📱 测试用例2: 函数调用提示词生成")
    print("-" * 50)
    
    user_input = "请介绍蟠龙盖罍这件文物"
    scene_type = "study"
    functions = [
        {
            "name": "introduce_artifact",
            "description": "介绍文物的详细信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "artifact_name": {
                        "type": "string",
                        "description": "文物名称"
                    }
                },
                "required": ["artifact_name"]
            }
        }
    ]
    
    function_calling_prompt = prompt_builder.build_function_calling_prompt(
        user_input=user_input,
        scene_type=scene_type,
        functions=functions
    )
    
    print("生成的函数调用提示词:")
    print(function_calling_prompt)
    print()
    
    # 验证关键要素
    key_elements = [
        "调用适当的函数",
        "自然语言回应",
        "introduce_artifact",
        "蟠龙盖罍"
    ]
    
    print("验证关键要素:")
    for element in key_elements:
        status = "✅ 包含" if element in function_calling_prompt else "❌ 缺少"
        print(f"  {status} {element}")
    print()
    
    # 测试用例3: 基础对话提示词生成
    print("💬 测试用例3: 基础对话提示词生成")
    print("-" * 50)
    
    basic_prompt = prompt_builder.build_final_prompt(
        user_input="你好，介绍一下博物馆",
        scene_type="public",
        functions=None  # 无函数定义
    )
    
    print("生成的基础对话提示词:")
    print(basic_prompt)
    print()
    
    # 验证基础对话要素
    basic_elements = [
        "自然语言与用户进行友好交流",
        "友好交流",
        "博物馆"
    ]
    
    print("验证基础对话要素:")
    for element in basic_elements:
        status = "✅ 包含" if element in basic_prompt else "❌ 缺少"
        print(f"  {status} {element}")
    print()
    
    # 测试用例4: 有RAG上下文的提示词
    print("📚 测试用例4: 带RAG上下文的提示词")
    print("-" * 50)
    
    rag_instruction = "请参考以下相关文物信息来回答：1. 文物名称: 蟠龙盖罍\n   文物ID: artifact_001\n   相关描述: 这是一件精美的青铜器..."
    
    rag_prompt = prompt_builder.build_final_prompt(
        user_input="这件文物有什么特点？",
        scene_type="study",
        functions=functions,
        rag_instruction=rag_instruction
    )
    
    print("生成的RAG提示词:")
    print(rag_prompt)
    print()
    
    # 验证RAG要素
    rag_elements = [
        "相关文物信息",
        "文物信息",
        "蟠龙盖罍"
    ]
    
    print("验证RAG要素:")
    for element in rag_elements:
        status = "✅ 包含" if element in rag_prompt else "❌ 缺少"
        print(f"  {status} {element}")
    print()
    
    # 配置灵活性测试
    print("⚙️ 配置灵活性测试")
    print("-" * 50)
    
    print("当前配置支持的提示词类型:")
    config_types = list(prompt_builder.system_prompts.keys())
    for prompt_type in config_types:
        print(f"  • {prompt_type}")
    
    print(f"\n总共支持 {len(config_types)} 种提示词模板")
    print()
    
    # 验证结果汇总
    print("📋 验证结果汇总")
    print("=" * 60)
    
    test_results = [
        ("配置加载", len(system_prompts) >= 3),
        ("函数调用提示词生成", all(element in function_calling_prompt for element in key_elements)),
        ("基础对话提示词生成", all(element in basic_prompt for element in basic_elements)),
        ("RAG提示词生成", all(element in rag_prompt for element in rag_elements)),
        ("配置灵活性", len(config_types) >= 3)
    ]
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} {test_name}")
        if not result:
            all_passed = False
    
    return all_passed

def demonstrate_config_advantages():
    """演示配置驱动的优势"""
    print("\n" + "=" * 80)
    print("🌟 配置驱动提示词工程的优势")
    print("=" * 80)
    
    advantages = [
        {
            "feature": "易于维护",
            "description": "提示词内容可以独立于代码进行修改和优化"
        },
        {
            "feature": "灵活配置", 
            "description": "支持多种提示词模板，适应不同场景需求"
        },
        {
            "feature": "快速迭代",
            "description": "无需修改代码即可调整AI行为和对话风格"
        },
        {
            "feature": "团队协作",
            "description": "产品和运营人员可以直接调整提示词，无需开发介入"
        },
        {
            "feature": "版本控制",
            "description": "提示词变更可以纳入版本控制系统进行追踪"
        },
        {
            "feature": "A/B测试",
            "description": "便于进行不同提示词效果的对比测试"
        }
    ]
    
    print("配置驱动相比硬编码的主要优势:")
    print()
    for i, advantage in enumerate(advantages, 1):
        print(f"{i}. {advantage['feature']}")
        print(f"   {advantage['description']}")
        print()

def show_config_structure():
    """展示配置结构"""
    print("📂 当前配置结构示例:")
    print("-" * 50)
    
    config_example = {
        "llm": {
            "system_prompts": {
                "base": "基础对话系统提示词...",
                "function_calling": "函数调用系统提示词...{functions_list}...",
                "fallback": "后备系统提示词...{scene_type}..."
            }
        }
    }
    
    print(json.dumps(config_example, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("开始测试配置驱动的提示词工程...")
    
    # 执行测试
    success = test_config_driven_prompt_engineering()
    
    # 演示优势
    demonstrate_config_advantages()
    
    # 展示配置结构
    show_config_structure()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 配置驱动提示词工程验证完成！")
        print("   系统现在支持灵活的提示词配置")
        print("   所有系统提示词都已从硬编码转移到配置文件")
    else:
        print("❌ 验证过程中发现问题，请检查实现")
    print("=" * 80)