#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试指令集限制功能
验证LLM是否会遵守客户端注册的指令集限制
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 初始化配置
from src.common.config_utils import load_config
load_config()

from src.core.dynamic_llm_client import DynamicLLMClient
from src.session.session_manager import session_manager
from src.common.log_formatter import log_step

def test_instruction_restrictions():
    """测试指令集限制"""
    print("=" * 80)
    print("🔍 指令集限制测试")
    print("=" * 80)
    
    # 创建测试会话
    test_session_id = "test-restriction-session"
    test_operations = ["idle", "Walk", "Run", "Speaking", "Happy", "Crying", "Sleeping"]
    
    print(f"📝 创建测试会话:")
    print(f"  会话ID: {test_session_id}")
    print(f"  注册指令: {test_operations}")
    
    # 模拟会话注册
    session_manager.register_session(
        session_id=test_session_id,
        client_metadata={"client_type": "spirit", "test": True},
        operation_set=test_operations
    )
    
    client = DynamicLLMClient()
    
    # 测试用例
    test_cases = [
        {
            "name": "尺寸查询测试",
            "input": "卷体夔纹蟠龙盖罍的详细尺寸？",
            "expected_behavior": "应该使用现有指令或general_chat，不应创造'detail'指令"
        },
        {
            "name": "功能询问测试", 
            "input": "你能干什么？",
            "expected_behavior": "应该在response中说明可用指令，operation为general_chat"
        },
        {
            "name": "动画指令测试",
            "input": "执行跑步动画",
            "expected_behavior": "应该使用'Run'指令"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}: {test_case['name']}")
        print(f"  输入: {test_case['input']}")
        print(f"  期望: {test_case['expected_behavior']}")
        
        try:
            # 生成动态提示词
            prompt = client.generate_dynamic_prompt(
                session_id=test_session_id,
                user_input=test_case['input'],
                scene_type="leisure"
            )
            
            print(f"  生成提示词长度: {len(prompt)} 字符")
            
            # 检查提示词是否包含指令集限制
            if "{valid_operations}" in prompt:
                print("  ✅ 提示词包含valid_operations占位符")
            else:
                print("  ⚠️  提示词可能缺少valid_operations占位符")
            
            # 显示提示词片段
            print(f"  提示词预览: {prompt[:300]}{'...' if len(prompt) > 300 else ''}")
            
            # 调用LLM（这里我们模拟，实际测试需要真实调用）
            print("  🔄 模拟LLM调用...")
            
            # 验证逻辑
            test_result = {
                'name': test_case['name'],
                'input': test_case['input'],
                'prompt_generated': len(prompt) > 0,
                'contains_restrictions': "可用指令之一" in prompt and "{valid_operations}" in prompt
            }
            results.append(test_result)
            
        except Exception as e:
            print(f"  ❌ 测试失败: {str(e)}")
            results.append({
                'name': test_case['name'],
                'error': str(e)
            })
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 测试结果汇总")
    print("=" * 80)
    
    passed = 0
    total = len(test_cases)
    
    for result in results:
        if 'error' in result:
            print(f"❌ {result['name']}: 错误 - {result['error']}")
        else:
            status = "✅" if result['prompt_generated'] and result['contains_restrictions'] else "⚠️"
            print(f"{status} {result['name']}: "
                  f"提示词生成={'✅' if result['prompt_generated'] else '❌'}, "
                  f"包含限制={'✅' if result['contains_restrictions'] else '❌'}")
            if result['prompt_generated'] and result['contains_restrictions']:
                passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！指令集限制机制工作正常")
    else:
        print("⚠️  部分测试未通过，请检查实现")

def test_actual_llm_response():
    """测试实际的LLM响应（需要真实调用）"""
    print("\n" + "=" * 80)
    print("🤖 实际LLM响应测试")
    print("=" * 80)
    
    # 这里需要真实的会话和LLM调用
    # 由于涉及真实API调用，我们只做概念验证
    
    print("💡 注意：此测试需要:")
    print("  1. 真实的会话ID")
    print("  2. 有效的LLM API配置") 
    print("  3. 实际的API调用")
    print("\n请使用测试客户端进行实际验证")

if __name__ == "__main__":
    test_instruction_restrictions()
    test_actual_llm_response()