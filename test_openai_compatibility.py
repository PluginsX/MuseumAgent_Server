# -*- coding: utf-8 -*-
"""
OpenAI Function Calling标准兼容性测试
验证重构后的系统是否完全符合OpenAI Function Calling标准
"""

import pytest
import json
from typing import Dict, Any

from src.models.function_calling_models import (
    OpenAIFunctionDefinition,
    FunctionParameterProperty,
    FunctionParameters,
    FunctionRegistrationRequest,
    is_valid_openai_function,
    normalize_to_openai_format
)

class TestOpenAIStandardCompatibility:
    """OpenAI Function Calling标准兼容性测试"""
    
    def test_basic_openai_function_definition(self):
        """测试基本的OpenAI标准函数定义"""
        func_def = {
            "name": "get_current_weather",
            "description": "获取指定地点的当前天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海"
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
        
        # 验证应该通过
        assert is_valid_openai_function(func_def) == True
        
        # 验证Pydantic模型也能正确解析
        validated = OpenAIFunctionDefinition(**func_def)
        assert validated.name == "get_current_weather"
        assert validated.description == "获取指定地点的当前天气信息"
        assert len(validated.parameters.properties) == 2
    
    def test_invalid_function_name(self):
        """测试无效的函数名称"""
        invalid_names = [
            "123invalid",  # 不能以数字开头
            "invalid-name",  # 不能包含连字符
            "invalid name",  # 不能包含空格
            "a" * 65,  # 超过64字符限制
            ""  # 空字符串
        ]
        
        for name in invalid_names:
            func_def = {
                "name": name,
                "description": "测试函数",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            assert is_valid_openai_function(func_def) == False
    
    def test_invalid_parameter_types(self):
        """测试无效的参数类型"""
        invalid_types = ["integer", "float", "date", "custom_type"]
        
        for invalid_type in invalid_types:
            func_def = {
                "name": "test_function",
                "description": "测试函数",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_param": {
                            "type": invalid_type,
                            "description": "测试参数"
                        }
                    },
                    "required": []
                }
            }
            assert is_valid_openai_function(func_def) == False
    
    def test_valid_parameter_types(self):
        """测试有效的参数类型"""
        valid_types = ["string", "number", "boolean", "object", "array"]
        
        for valid_type in valid_types:
            func_def = {
                "name": "test_function",
                "description": "测试函数",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_param": {
                            "type": valid_type,
                            "description": "测试参数"
                        }
                    },
                    "required": []
                }
            }
            assert is_valid_openai_function(func_def) == True
    
    def test_normalize_non_standard_function(self):
        """测试将非标准函数定义规范化为OpenAI标准"""
        # 包含额外字段的非标准定义
        non_standard_func = {
            "name": "search_artifacts",
            "description": "搜索文物",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词",
                        "default": "青铜器",  # 非标准字段
                        "minLength": 1,      # 非标准字段
                        "maxLength": 100     # 非标准字段
                    },
                    "category": {
                        "type": "string",
                        "description": "文物类别",
                        "enum": ["陶瓷", "书画", "青铜器"]
                    }
                },
                "required": ["keyword"],
                "additionalProperties": False  # 非标准字段
            },
            "return_type": "object",  # 非标准字段
            "timeout": 30            # 非标准字段
        }
        
        normalized = normalize_to_openai_format(non_standard_func)
        
        # 验证标准化后的结构
        assert "name" in normalized
        assert "description" in normalized
        assert "parameters" in normalized
        assert "return_type" not in normalized  # 非标准字段已被移除
        assert "timeout" not in normalized      # 非标准字段已被移除
        
        # 验证参数属性中的非标准字段被移除
        props = normalized["parameters"]["properties"]
        assert "default" not in props["keyword"]
        assert "minLength" not in props["keyword"]
        assert "maxLength" not in props["keyword"]
        assert "additionalProperties" not in normalized["parameters"]
    
    def test_function_registration_request_validation(self):
        """测试函数注册请求验证"""
        # 有效的函数定义列表
        valid_functions = [
            {
                "name": "get_weather",
                "description": "获取天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市"}
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "search_museum",
                "description": "搜索博物馆",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "博物馆名称"}
                    },
                    "required": ["name"]
                }
            }
        ]
        
        registration_request = {
            "client_id": "test_client_123",
            "functions": valid_functions
        }
        
        # 应该能够成功验证
        request_obj = FunctionRegistrationRequest(**registration_request)
        assert len(request_obj.functions) == 2
        assert request_obj.client_id == "test_client_123"
    
    def test_mixed_valid_invalid_functions(self):
        """测试混合有效和无效函数的注册"""
        mixed_functions = [
            {
                "name": "valid_function",
                "description": "有效函数",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param": {"type": "string", "description": "参数"}
                    },
                    "required": ["param"]
                }
            },
            {
                "name": "123invalid",  # 无效名称
                "description": "无效函数",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        registration_request = {
            "client_id": "test_client",
            "functions": mixed_functions
        }
        
        # 应该抛出验证错误
        with pytest.raises(ValueError):
            FunctionRegistrationRequest(**registration_request)
    
    def test_empty_parameters_handling(self):
        """测试空参数处理"""
        func_def = {
            "name": "simple_function",
            "description": "简单函数，无参数",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        assert is_valid_openai_function(func_def) == True
        validated = OpenAIFunctionDefinition(**func_def)
        assert len(validated.parameters.properties) == 0
        assert validated.parameters.required == []
    
    def test_complex_nested_parameters(self):
        """测试复杂的嵌套参数结构"""
        func_def = {
            "name": "complex_search",
            "description": "复杂搜索功能",
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
                                    "category": {"type": "string", "description": "分类"},
                                    "date_range": {
                                        "type": "object",
                                        "properties": {
                                            "start": {"type": "string", "description": "开始日期"},
                                            "end": {"type": "string", "description": "结束日期"}
                                        },
                                        "required": ["start", "end"]
                                    }
                                },
                                "required": ["category"]
                            }
                        },
                        "required": ["text"]
                    }
                },
                "required": ["query"]
            }
        }
        
        assert is_valid_openai_function(func_def) == True
        validated = OpenAIFunctionDefinition(**func_def)
        assert validated.name == "complex_search"

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])