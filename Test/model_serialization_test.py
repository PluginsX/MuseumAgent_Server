#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试Pydantic模型序列化效果
"""

import sys
import os
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 移除StandardCommand导入，该模型已被废弃
# from src.models.response_models import StandardCommand

def test_model_serialization():
    """测试模型序列化效果"""
    print("=" * 80)
    print("🧪 Pydantic模型序列化测试")
    print("=" * 80)
    
    # 模拟LLM原始响应数据
    llm_raw_response = {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "你好！有什么我可以帮你的吗？",
                    "role": "assistant"
                }
            }
        ],
        "created": 1770217100,
        "id": "chatcmpl-test-123",
        "model": "qwen-turbo",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 8,
            "prompt_tokens": 332,
            "prompt_tokens_details": {
                "cached_tokens": 0
            },
            "total_tokens": 340
        }
    }
    
    print("原始LLM响应:")
    print(json.dumps(llm_raw_response, indent=2, ensure_ascii=False))
    
    # 1. 直接使用字典（模拟当前行为）
    print("\n1. 直接使用字典序列化:")
    print("-" * 40)
    direct_dict = llm_raw_response.copy()
    print("序列化结果:")
    print(json.dumps(direct_dict, indent=2, ensure_ascii=False))
    print(f"字段数: {len(direct_dict)}")
    
    # 2. 使用StandardCommand模型（修复前）
    print("\n2. 使用StandardCommand模型（修复前）:")
    print("-" * 40)
    # 临时修改模型配置来模拟修复前的行为
    original_config = StandardCommand.Config
    StandardCommand.Config.exclude_none = False
    
    try:
        model_instance = StandardCommand(**llm_raw_response)
        serialized = model_instance.model_dump()
        print("序列化结果:")
        print(json.dumps(serialized, indent=2, ensure_ascii=False))
        print(f"字段数: {len(serialized)}")
        
        # 显示多余的字段
        extra_fields = set(serialized.keys()) - set(llm_raw_response.keys())
        if extra_fields:
            print(f"多余字段: {sorted(extra_fields)}")
    finally:
        # 恢复原始配置
        StandardCommand.Config.exclude_none = True
    
    # 3. 使用StandardCommand模型（修复后）
    print("\n3. 使用StandardCommand模型（修复后）:")
    print("-" * 40)
    model_instance = StandardCommand(**llm_raw_response)
    serialized = model_instance.model_dump()
    print("序列化结果:")
    print(json.dumps(serialized, indent=2, ensure_ascii=False))
    print(f"字段数: {len(serialized)}")
    
    # 验证是否与原始数据一致
    if set(serialized.keys()) == set(llm_raw_response.keys()):
        print("✅ 序列化结果与原始数据字段完全一致")
    else:
        print("❌ 序列化结果与原始数据字段不一致")
        missing = set(llm_raw_response.keys()) - set(serialized.keys())
        extra = set(serialized.keys()) - set(llm_raw_response.keys())
        if missing:
            print(f"缺失字段: {missing}")
        if extra:
            print(f"多余字段: {extra}")

def demonstrate_fix_effect():
    """演示修复效果"""
    print("\n" + "=" * 80)
    print("✨ 修复效果演示")
    print("=" * 80)
    
    # 用户看到的问题响应
    problematic = {
        "artifact_id": None,
        "artifact_name": None,
        "operation": None,
        "operation_params": None,
        "keywords": None,
        "tips": None,
        "response": None,
        "command": None,
        "parameters": None,
        "type": None,
        "format": None,
        "timestamp": None,
        "session_id": None,
        "processing_mode": None,
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "我会帮助您了解和探索各种文物的信息...",
                    "role": "assistant"
                }
            }
        ],
        "created": 1770217100,
        "id": "chatcmpl-problematic",
        "model": "qwen-turbo",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 35,
            "prompt_tokens": 333,
            "prompt_tokens_details": {"cached_tokens": 0},
            "total_tokens": 368
        }
    }
    
    # 修复后的理想响应
    ideal = {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "我会帮助您了解和探索各种文物的信息...",
                    "role": "assistant"
                }
            }
        ],
        "created": 1770217100,
        "id": "chatcmpl-ideal",
        "model": "qwen-turbo",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 35,
            "prompt_tokens": 333,
            "prompt_tokens_details": {"cached_tokens": 0},
            "total_tokens": 368
        }
    }
    
    print("问题响应字段数:", len(problematic))
    print("理想响应字段数:", len(ideal))
    print("减少字段数:", len(problematic) - len(ideal))
    
    print(f"\n问题响应大小: {len(json.dumps(problematic))} 字符")
    print(f"理想响应大小: {len(json.dumps(ideal))} 字符")
    print(f"减少大小: {len(json.dumps(problematic)) - len(json.dumps(ideal))} 字符")
    
    # 找出被移除的字段
    removed_fields = set(problematic.keys()) - set(ideal.keys())
    print(f"\n被移除的字段 ({len(removed_fields)}个):")
    for field in sorted(removed_fields):
        print(f"  - {field}")

if __name__ == "__main__":
    print("🚀 Pydantic模型序列化修复验证")
    print()
    
    # 测试模型序列化
    test_model_serialization()
    
    # 演示修复效果
    demonstrate_fix_effect()
    
    print(f"\n🏁 测试完成")