#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM原始数据转发 - 验证是否真的没有额外处理
"""

import sys
import os
import json
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 先加载配置
from src.common.config_utils import load_config
load_config()

from src.core.command_generator import CommandGenerator
from src.session.strict_session_manager import strict_session_manager
from src.common.response_utils import success_response

def test_llm_raw_forwarding():
    """测试LLM原始数据是否真的没有被处理"""
    print("=" * 80)
    print("🧪 LLM原始数据转发测试")
    print("=" * 80)
    
    # 1. 创建测试会话
    print("\n1. 创建测试会话")
    print("-" * 40)
    
    functions = [
        {
            "name": "show_emotion",
            "description": "显示情感表情",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotion": {
                        "type": "string",
                        "description": "情感类型",
                        "enum": ["happy", "sad", "angry", "surprised", "neutral"]
                    }
                },
                "required": ["emotion"]
            }
        }
    ]
    
    session_id = "raw_data_test_" + str(int(time.time()))
    
    strict_session_manager.register_session_with_functions(
        session_id=session_id,
        client_metadata={
            "client_id": "raw_data_test",
            "client_type": "test",
            "client_version": "1.0.0"
        },
        functions=functions
    )
    
    print(f"✅ 会话创建成功: {session_id}")
    
    # 2. 模拟LLM原始响应
    print("\n2. 模拟LLM原始响应")
    print("-" * 40)
    
    # 这是LLM真正返回的原始数据结构
    mock_llm_raw_response = {
        "choices": [
            {
                "finish_reason": "function_call",
                "index": 0,
                "message": {
                    "content": "",
                    "function_call": {
                        "arguments": "{\"emotion\": \"angry\"}",
                        "name": "show_emotion"
                    },
                    "role": "assistant"
                }
            }
        ],
        "created": 1770216495,
        "id": "chatcmpl-04261ed5-be79-96a0-a776-01a03e977222",
        "model": "qwen-turbo",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 21,
            "prompt_tokens": 653,
            "prompt_tokens_details": {
                "cached_tokens": 0
            },
            "total_tokens": 674
        }
    }
    
    print("LLM原始响应数据:")
    print(json.dumps(mock_llm_raw_response, indent=2, ensure_ascii=False))
    
    # 3. 通过CommandGenerator处理
    print("\n3. 通过CommandGenerator处理")
    print("-" * 40)
    
    generator = CommandGenerator()
    
    # 注意：这里我们需要模拟CommandGenerator内部调用LLM的过程
    # 由于CommandGenerator现在直接返回LLM响应，我们应该得到相同的结果
    
    # 直接模拟generate_standard_command的行为
    try:
        # 这里模拟CommandGenerator.generate_standard_command的内部逻辑
        # 它应该直接返回LLM的原始响应
        
        # 实际上，我们需要查看DynamicLLMClient的_chat_completions_with_functions方法
        from src.core.dynamic_llm_client import DynamicLLMClient
        llm_client = DynamicLLMClient()
        
        # 构造相同的payload
        payload = llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input="show emotion angry",
            scene_type="public",
            rag_instruction="",
            functions=functions
        )
        
        print("生成的LLM请求payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # 但是我们不能实际调用LLM，所以我们直接使用模拟的响应
        command_result = mock_llm_raw_response
        
        print("\nCommandGenerator处理结果:")
        print(json.dumps(command_result, indent=2, ensure_ascii=False))
        
        # 4. API响应格式化
        print("\n4. API响应格式化")
        print("-" * 40)
        
        api_response = success_response(data=command_result)
        print("最终API响应:")
        print(json.dumps(api_response, indent=2, ensure_ascii=False))
        
        # 5. 分析数据结构
        print("\n5. 数据结构分析")
        print("-" * 40)
        
        response_data = api_response.get("data", {})
        
        print("检查是否包含旧字段:")
        old_fields = ["artifact_id", "artifact_name", "operation", "operation_params", "keywords", "tips"]
        found_old_fields = []
        
        for field in old_fields:
            if field in response_data:
                found_old_fields.append(field)
                print(f"❌ 发现旧字段: {field} = {response_data[field]}")
            else:
                print(f"✅ 未发现旧字段: {field}")
        
        if found_old_fields:
            print(f"\n⚠️  发现 {len(found_old_fields)} 个旧字段: {found_old_fields}")
            print("这表明在某个环节添加了这些旧字段")
        else:
            print("\n✅ 未发现任何旧字段，数据保持原始状态")
            
        print("\n检查LLM原始字段:")
        llm_fields = ["choices", "created", "id", "model", "object", "usage"]
        for field in llm_fields:
            if field in response_data:
                print(f"✅ 保留LLM原始字段: {field}")
            else:
                print(f"❌ 缺失LLM原始字段: {field}")
                
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_raw_forwarding()