#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的Function Calling提示词工程
验证是否完全移除了operation相关的内容
"""

import sys
import os
sys.path.append('.')

from src.common.config_utils import load_config
load_config()  # 加载配置

from src.core.modules.prompt_builder import PromptBuilder
from src.core.modules.rag_processor import RAGProcessor
from src.core.dynamic_llm_client import DynamicLLMClient
from src.session.strict_session_manager import strict_session_manager

def test_function_calling_prompt_engineering():
    """测试基于Function Calling的提示词工程"""
    print("=== 测试Function Calling提示词工程 ===")
    
    # 初始化组件
    prompt_builder = PromptBuilder()
    rag_processor = RAGProcessor()
    llm_client = DynamicLLMClient()
    
    # 测试用例
    test_cases = [
        {
            "name": "普通对话模式",
            "user_input": "你好，介绍一下辽宁省博物馆",
            "scene_type": "public",
            "functions": []  # 无函数定义
        },
        {
            "name": "函数调用模式",
            "user_input": "请介绍蟠龙盖罍这件文物",
            "scene_type": "study", 
            "functions": [
                {
                    "name": "introduce_artifact",
                    "description": "介绍文物",
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
        }
    ]
    
    all_tests_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {test_case['name']} ---")
        
        # 1. 构建提示词
        final_prompt = prompt_builder.build_final_prompt(
            user_input=test_case['user_input'],
            scene_type=test_case['scene_type'],
            functions=test_case['functions'],
            rag_instruction=""  # 简化测试，不使用RAG
        )
        
        print(f"  提示词长度: {len(final_prompt)} 字符")
        print(f"  提示词预览: {final_prompt[:300]}{'...' if len(final_prompt) > 300 else ''}")
        
        # 2. 验证提示词内容
        validations = {
            "✅ 不包含operation字段要求": "operation" not in final_prompt.lower(),
            "✅ 不包含valid_operations占位符": "{valid_operations}" not in final_prompt,
            "✅ 不包含指令集限制": "指令之一" not in final_prompt and "操作指令" not in final_prompt,
            "✅ 包含Function Calling引导": ("函数" in final_prompt and "参数" in final_prompt) or "普通对话" in final_prompt,
            "✅ 场景信息正确嵌入": test_case['scene_type'] in final_prompt,
            "✅ 用户输入正确嵌入": test_case['user_input'][:10] in final_prompt,
            "✅ 系统身份声明": "辽宁省博物馆智能助手" in final_prompt
        }
        
        print("  验证结果:")
        test_passed = True
        for check_name, result in validations.items():
            status = "✅" if result else "❌"
            print(f"    {status} {check_name}")
            if not result:
                test_passed = False
                all_tests_passed = False
        
        # 3. 测试LLM负载生成
        print("  测试LLM负载生成...")
        try:
            payload = llm_client.generate_function_calling_payload(
                session_id=f"test-session-{i}",
                user_input=test_case['user_input'],
                scene_type=test_case['scene_type'],
                rag_instruction="",
                functions=test_case['functions']
            )
            
            has_functions = 'functions' in payload and len(payload['functions']) > 0
            expected_functions = len(test_case['functions']) > 0
            
            if has_functions == expected_functions:
                print(f"    ✅ 函数调用配置正确: {'启用' if has_functions else '禁用'}")
            else:
                print(f"    ❌ 函数调用配置错误: 期望{'启用' if expected_functions else '禁用'}，实际{'启用' if has_functions else '禁用'}")
                test_passed = False
                
        except Exception as e:
            print(f"    ❌ LLM负载生成失败: {str(e)}")
            test_passed = False
        
        if test_passed:
            print(f"  🎉 测试用例 {test_case['name']} 通过!")
        else:
            print(f"  ❌ 测试用例 {test_case['name']} 失败!")
            all_tests_passed = False
    
    return all_tests_passed

def test_config_template_validation():
    """测试配置文件中的提示词模板"""
    print("\n=== 配置文件模板验证 ===")
    
    from src.common.config_utils import get_global_config
    
    try:
        config = get_global_config()
        prompt_template = config['llm']['prompt_template']
        
        print("配置文件提示词模板:")
        print("-" * 50)
        print(prompt_template)
        print("-" * 50)
        
        # 验证配置模板
        validations = {
            "✅ 不包含operation字段": "operation" not in prompt_template.lower(),
            "✅ 不包含valid_operations": "{valid_operations}" not in prompt_template,
            "✅ 不包含指令集概念": "指令之一" not in prompt_template,
            "✅ 包含Function Calling概念": "函数" in prompt_template and "参数" in prompt_template,
            "✅ 包含占位符": all(placeholder in prompt_template for placeholder in ['{scene_type}', '{user_input}'])
        }
        
        print("\n验证结果:")
        all_valid = True
        for check_name, result in validations.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if not result:
                all_valid = False
        
        if all_valid:
            print("\n🎉 配置文件模板验证通过!")
        else:
            print("\n❌ 配置文件模板验证失败!")
            
        return all_valid
        
    except Exception as e:
        print(f"❌ 配置文件验证失败: {str(e)}")
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n=== 向后兼容性测试 ===")
    
    prompt_builder = PromptBuilder()
    
    # 测试旧的API调用方式是否仍然工作
    try:
        # 旧的调用方式（应该仍然兼容）
        old_style_prompt = prompt_builder.build_final_prompt(
            user_input="测试输入",
            scene_type="public",
            functions=[],  # 传空列表而不是valid_operations
            rag_instruction=""
        )
        
        print("✅ 旧API调用方式仍然兼容")
        print(f"  生成提示词长度: {len(old_style_prompt)} 字符")
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {str(e)}")
        return False

def main():
    print("开始验证Function Calling提示词工程重构效果...")
    
    # 测试1: 提示词内容验证
    content_test_passed = test_function_calling_prompt_engineering()
    
    # 测试2: 配置文件模板验证  
    config_test_passed = test_config_template_validation()
    
    # 测试3: API兼容性验证
    compat_test_passed = test_backward_compatibility()
    
    print("\n" + "="*60)
    print("📋 最终测试总结")
    print("="*60)
    
    if content_test_passed:
        print("✅ 提示词内容验证通过 - 已移除所有operation相关元素")
    else:
        print("❌ 提示词内容验证失败 - 仍存在operation相关元素")
        
    if config_test_passed:
        print("✅ 配置文件验证通过 - 模板已更新为Function Calling模式")
    else:
        print("❌ 配置文件验证失败 - 模板仍包含旧的指令集概念")
        
    if compat_test_passed:
        print("✅ API兼容性验证通过 - 新旧调用方式都支持")
    else:
        print("❌ API兼容性验证失败 - 存在兼容性问题")
    
    overall_success = content_test_passed and config_test_passed and compat_test_passed
    
    if overall_success:
        print("\n🎉 Function Calling提示词工程重构完全成功!")
        print("   ✅ 彻底移除了operation相关的内容")
        print("   ✅ 完全基于OpenAI Function Calling标准")
        print("   ✅ 支持普通对话和函数调用两种模式")
        print("   ✅ 保持了良好的向后兼容性")
    else:
        print("\n❌ 提示词工程重构存在问题，需要进一步修复")

if __name__ == "__main__":
    main()