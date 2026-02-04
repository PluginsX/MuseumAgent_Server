from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from typing import Literal
import re

# OpenAI Function Calling标准参数类型
ALLOWED_TYPES = {"string", "number", "boolean", "object", "array"}

class FunctionParameterProperty(BaseModel):
    """OpenAI标准的函数参数属性定义"""
    type: str = Field(..., description="参数类型: string, number, boolean, object, array")
    description: Optional[str] = Field(None, description="参数描述")
    enum: Optional[List[str]] = Field(None, description="枚举值列表")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ALLOWED_TYPES:
            raise ValueError(f"参数类型必须是以下之一: {', '.join(ALLOWED_TYPES)}")
        return v

class FunctionParameters(BaseModel):
    """OpenAI标准的函数参数定义"""
    type: Literal["object"] = Field("object", description="必须为'object'")
    properties: Dict[str, FunctionParameterProperty] = Field(..., description="参数属性映射")
    required: Optional[List[str]] = Field(None, description="必需参数列表")

class OpenAIFunctionDefinition(BaseModel):
    """完全符合OpenAI Function Calling标准的函数定义"""
    name: str = Field(..., description="函数名称", max_length=64)
    description: str = Field(..., description="函数功能描述", min_length=1, max_length=1000)
    parameters: FunctionParameters = Field(..., description="参数定义")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError("函数名称只能包含字母、数字和下划线，且不能以数字开头")
        if len(v) > 64:
            raise ValueError("函数名称长度不能超过64个字符")
        return v

class FunctionCallRequest(BaseModel):
    """函数调用请求 - OpenAI标准格式"""
    name: str = Field(..., description="要调用的函数名称")
    arguments: Dict[str, Any] = Field(..., description="函数参数")

class ChatCompletionMessage(BaseModel):
    """聊天完成消息 - OpenAI标准格式"""
    role: str = Field(..., description="角色: system, user, assistant, function")
    content: Optional[str] = Field(None, description="消息内容")
    function_call: Optional[FunctionCallRequest] = Field(None, description="函数调用信息")

class FunctionCallResponse(BaseModel):
    """函数调用响应 - OpenAI标准格式"""
    name: str = Field(..., description="被调用的函数名称")
    arguments: str = Field(..., description="函数参数的JSON字符串")

class FunctionRegistrationRequest(BaseModel):
    """函数注册请求 - 严格OpenAI标准"""
    client_id: str = Field(..., description="客户端ID")
    functions: List[Dict] = Field(..., description="OpenAI标准函数定义列表")
    
    @field_validator('functions')
    @classmethod
    def validate_functions(cls, v):
        """验证每个函数定义是否符合OpenAI标准"""
        for func_def in v:
            try:
                OpenAIFunctionDefinition(**func_def)
            except Exception as e:
                raise ValueError(f"函数定义不符合OpenAI标准: {str(e)}")
        return v

def is_valid_openai_function(func_dict: Dict) -> bool:
    """严格验证是否符合OpenAI Function Calling标准"""
    try:
        OpenAIFunctionDefinition(**func_dict)
        return True
    except Exception:
        return False

def normalize_to_openai_format(func_dict: Dict) -> Dict:
    """将任意格式的函数定义规范化为OpenAI标准格式"""
    # 只保留OpenAI标准字段
    standard_fields = {"name", "description", "parameters"}
    normalized = {k: v for k, v in func_dict.items() if k in standard_fields}
    
    # 规范化参数定义
    if "parameters" in normalized:
        params = normalized["parameters"]
        if isinstance(params, dict):
            # 只保留标准参数字段
            param_fields = {"type", "properties", "required"}
            normalized["parameters"] = {k: v for k, v in params.items() if k in param_fields}
            
            # 规范化参数属性
            if "properties" in normalized["parameters"]:
                properties = normalized["parameters"]["properties"]
                if isinstance(properties, dict):
                    for prop_name, prop_def in properties.items():
                        if isinstance(prop_def, dict):
                            # 只保留标准属性字段
                            prop_fields = {"type", "description", "enum"}
                            properties[prop_name] = {k: v for k, v in prop_def.items() if k in prop_fields}
    
    return normalized