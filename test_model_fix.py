#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试：验证StandardCommand模型能否正确处理OpenAI函数调用字段
"""

import sys
import os
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 移除StandardCommand导入，该模型已被废弃
# from src.models.response_models import StandardCommand
from src.common.response_utils import success_response

def test_model_conversion():
    """测试模型转换是否保留所有字段"""
    print("=" * 80)
    print("🧪 StandardCommand模型字段保留测试")
    print("=" * 80)
    
    # 模拟OpenAI函数调用响应数据
    openai_response_data = {
        "command": "move_to_position",
        "parameters": {
            "x": 100,
            "y": 200
        },
        "type": "function_call",
        "format": "openai_standard",
        "response": "好的，我将移动到坐标(100, 200)位置。",
        "timestamp": "2026-02-04T20:15:30.123456",
        "session_id": "test-session-123",
        "processing_mode": "openai_function_calling"
    }
    
    print("\n📥 原始OpenAI响应数据:")
    print("-" * 40)
    print(json.dumps(openai_response_data, indent=2, ensure_ascii=False))
    
    # 测试直接转换为StandardCommand模型
    print("\n🔄 转换为StandardCommand模型:")
    print("-" * 40)
    
    try:
        # 方法1：直接创建模型实例
        command_model = StandardCommand(**openai_response_data)
        print("✅ 直接模型创建成功")
        print(f"模型字段: {list(command_model.model_fields.keys())}")
        
        # 方法2：通过success_response包装
        print("\n🌐 通过success_response包装:")
        print("-" * 40)
        api_response = success_response(data=openai_response_data)
        print("API响应结构:")
        print(json.dumps(api_response, indent=2, ensure_ascii=False))
        
        # 验证关键字段是否保留
        print("\n🔍 字段保留验证:")
        print("-" * 40)
        data_field = api_response.get("data", {})
        
        required_fields = ["command", "parameters", "type", "format", "response"]
        for field in required_fields:
            if field in data_field:
                print(f"✅ {field}: {data_field[field]}")
            else:
                print(f"❌ {field}: 丢失!")
                
        # 验证传统字段（应该为None）
        traditional_fields = ["artifact_id", "artifact_name", "operation"]
        for field in traditional_fields:
            if field in data_field:
                value = data_field[field]
                if value is None:
                    print(f"✅ {field}: None (预期)")
                else:
                    print(f"⚠️  {field}: {value} (意外值)")
            else:
                print(f"✅ {field}: 不存在 (预期)")
                
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("🎯 测试完成")
    print("=" * 80)
    return True

if __name__ == "__main__":
    test_model_conversion()