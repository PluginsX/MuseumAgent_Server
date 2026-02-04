# -*- coding: utf-8 -*-
"""
OpenAI Function Calling标准兼容的函数管理API
完全移除旧的指令集兼容，100%遵循OpenAI标准
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import json

from ..models.function_calling_models import (
    FunctionRegistrationRequest,
    OpenAIFunctionDefinition,
    is_valid_openai_function,
    normalize_to_openai_format
)
from ..common.log_formatter import log_step, log_communication

router = APIRouter(prefix="/api/v1/functions", tags=["函数管理"])

@router.post("/register")
async def register_functions(request: FunctionRegistrationRequest):
    """
    注册客户端自定义函数 - 严格遵循OpenAI Function Calling标准
    """
    try:
        print(log_step('FUNCTION', 'INFO', '开始函数注册', {
            'client_id': request.client_id,
            'function_count': len(request.functions)
        }))
        
        validation_results = []
        registered_functions = []
        
        for i, func_def in enumerate(request.functions):
            func_name = func_def.get("name", f"function_{i}")
            
            # 严格验证OpenAI标准
            if not is_valid_openai_function(func_def):
                validation_results.append({
                    "name": func_name,
                    "status": "rejected",
                    "reason": "函数定义不符合OpenAI Function Calling标准"
                })
                print(log_step('FUNCTION', 'WARNING', f'函数验证失败: {func_name}'))
                continue
            
            # 规范化为标准格式
            try:
                normalized_func = normalize_to_openai_format(func_def)
                registered_functions.append(normalized_func)
                validation_results.append({
                    "name": normalized_func["name"],
                    "status": "approved",
                    "reason": "符合OpenAI标准"
                })
                print(log_step('FUNCTION', 'SUCCESS', f'函数注册成功: {func_name}'))
                
            except Exception as e:
                validation_results.append({
                    "name": func_name,
                    "status": "rejected", 
                    "reason": f"函数格式规范化失败: {str(e)}"
                })
                print(log_step('FUNCTION', 'ERROR', f'函数规范化失败: {func_name}', {'error': str(e)}))
        
        response = {
            "status": "success",
            "client_id": request.client_id,
            "registered_functions": registered_functions,
            "validation_results": validation_results,
            "timestamp": datetime.now().isoformat()
        }
        
        print(log_step('FUNCTION', 'SUCCESS', '函数注册完成', {
            'total': len(request.functions),
            'approved': len(registered_functions),
            'rejected': len(request.functions) - len(registered_functions)
        }))
        
        return response
        
    except Exception as e:
        print(log_step('FUNCTION', 'ERROR', '函数注册过程异常', {'error': str(e)}))
        raise HTTPException(status_code=500, detail=f"函数注册失败: {str(e)}")

@router.post("/validate")
async def validate_function(function_def: Dict[str, Any]):
    """
    验证单个函数定义是否符合OpenAI标准
    """
    try:
        is_valid = is_valid_openai_function(function_def)
        
        result = {
            "is_valid": is_valid,
            "function_name": function_def.get("name", "unknown"),
            "validation_details": {}
        }
        
        if not is_valid:
            try:
                # 尝试找出具体的验证错误
                OpenAIFunctionDefinition(**function_def)
            except Exception as e:
                result["validation_details"] = {
                    "error": str(e),
                    "suggested_fix": "请确保遵循OpenAI Function Calling标准格式"
                }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"验证过程出错: {str(e)}")

@router.post("/normalize")
async def normalize_function(function_def: Dict[str, Any]):
    """
    将函数定义规范化为OpenAI标准格式
    """
    try:
        if not is_valid_openai_function(function_def):
            raise HTTPException(status_code=400, detail="输入函数定义不符合基本要求")
        
        normalized = normalize_to_openai_format(function_def)
        
        return {
            "status": "success",
            "original_function": function_def,
            "normalized_function": normalized,
            "is_already_standard": function_def == normalized
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"规范化过程出错: {str(e)}")

# 移除所有旧的指令集相关接口
# 不再提供 /api/v1/instructions/* 相关路由
# 不再提供 /api/v1/commands/* 相关路由
# 不再提供任何向后兼容的指令集转换功能