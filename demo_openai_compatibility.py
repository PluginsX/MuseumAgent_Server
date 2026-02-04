# -*- coding: utf-8 -*-
"""
OpenAI Function Calling标准兼容性演示
展示重构后的系统如何完全符合OpenAI Function Calling标准
"""

import json
from typing import Dict, Any

from src.models.function_calling_models import (
    OpenAIFunctionDefinition,
    is_valid_openai_function,
    normalize_to_openai_format,
    FunctionRegistrationRequest
)

def demonstrate_openai_compatibility():
    """演示OpenAI标准兼容性"""
    
    print("=== OpenAI Function Calling标准兼容性演示 ===\n")
    
    # 1. 标准OpenAI函数定义示例
    print("1. 标准OpenAI函数定义示例:")
    standard_function = {
        "name": "get_current_weather",
        "description": "获取指定城市的当前天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，例如：北京、上海、纽约"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位"
                }
            },
            "required": ["location"]
        }
    }
    
    print("输入函数定义:")
    print(json.dumps(standard_function, indent=2, ensure_ascii=False))
    
    # 验证标准兼容性
    is_valid = is_valid_openai_function(standard_function)
    print(f"\n✅ 标准验证结果: {is_valid}")
    
    # 使用Pydantic模型验证
    try:
        validated = OpenAIFunctionDefinition(**standard_function)
        print(f"✅ Pydantic模型验证通过")
        print(f"   - 函数名称: {validated.name}")
        print(f"   - 参数数量: {len(validated.parameters.properties)}")
        print(f"   - 必需参数: {validated.parameters.required}")
    except Exception as e:
        print(f"❌ Pydantic验证失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 2. 非标准函数定义的规范化
    print("2. 非标准函数定义规范化:")
    non_standard_function = {
        "name": "search_museum_artifacts",
        "description": "搜索博物馆文物藏品",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词",
                    "default": "青铜器",      # 非标准字段
                    "minLength": 1,          # 非标准字段
                    "maxLength": 100         # 非标准字段
                },
                "category": {
                    "type": "string",
                    "description": "文物分类",
                    "enum": ["陶瓷", "书画", "青铜器", "玉器"]
                },
                "dynasty": {
                    "type": "string",
                    "description": "朝代信息"
                }
            },
            "required": ["keyword"],
            "additionalProperties": False     # 非标准字段
        },
        "return_type": "object",              # 非标准字段
        "timeout": 30,                        # 非标准字段
        "retry_count": 3                      # 非标准字段
    }
    
    print("原始非标准函数定义:")
    print(json.dumps(non_standard_function, indent=2, ensure_ascii=False))
    
    # 规范化为OpenAI标准
    normalized = normalize_to_openai_format(non_standard_function)
    print(f"\n规范化后的OpenAI标准函数定义:")
    print(json.dumps(normalized, indent=2, ensure_ascii=False))
    
    # 验证规范化后的函数
    is_normalized_valid = is_valid_openai_function(normalized)
    print(f"\n✅ 规范化后验证结果: {is_normalized_valid}")
    
    print("\n" + "="*50 + "\n")
    
    # 3. 函数注册请求演示
    print("3. 函数注册请求演示:")
    registration_data = {
        "client_id": "museum_client_001",
        "functions": [
            {
                "name": "get_exhibition_info",
                "description": "获取展览详细信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "exhibition_id": {
                            "type": "string",
                            "description": "展览ID"
                        }
                    },
                    "required": ["exhibition_id"]
                }
            },
            {
                "name": "navigate_to_location",
                "description": "导航到指定位置",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "目标位置"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["walking", "wheelchair"],
                            "description": "导航模式"
                        }
                    },
                    "required": ["target"]
                }
            }
        ]
    }
    
    print("注册请求数据:")
    print(json.dumps(registration_data, indent=2, ensure_ascii=False))
    
    try:
        # 验证注册请求
        registration_request = FunctionRegistrationRequest(**registration_data)
        print(f"\n✅ 函数注册请求验证通过")
        print(f"   - 客户端ID: {registration_request.client_id}")
        print(f"   - 函数数量: {len(registration_request.functions)}")
        
        # 验证每个函数
        for i, func in enumerate(registration_request.functions):
            func_valid = is_valid_openai_function(func)
            print(f"   - 函数 {i+1} '{func['name']}': {'✅ 有效' if func_valid else '❌ 无效'}")
            
    except Exception as e:
        print(f"\n❌ 函数注册请求验证失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 4. 边界情况测试
    print("4. 边界情况测试:")
    
    edge_cases = [
        {
            "name": "empty_parameters",
            "description": "无参数函数",
            "function": {
                "name": "ping",
                "description": "心跳检测",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "name": "complex_nested",
            "description": "复杂嵌套参数",
            "function": {
                "name": "advanced_search",
                "description": "高级搜索",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "搜索文本"},
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "date_range": {
                                            "type": "object",
                                            "properties": {
                                                "start": {"type": "string", "description": "开始日期"},
                                                "end": {"type": "string", "description": "结束日期"}
                                            },
                                            "required": ["start", "end"]
                                        }
                                    }
                                }
                            },
                            "required": ["text"]
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    for case in edge_cases:
        print(f"\n测试: {case['description']}")
        is_valid = is_valid_openai_function(case['function'])
        print(f"结果: {'✅ 通过' if is_valid else '❌ 失败'}")
        if is_valid:
            validated = OpenAIFunctionDefinition(**case['function'])
            print(f"验证成功: {validated.name}")

if __name__ == "__main__":
    demonstrate_openai_compatibility()