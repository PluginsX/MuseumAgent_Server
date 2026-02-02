# -*- coding: utf-8 -*-
"""
标准指令集数据结构模型
定义博物馆智能体系统的统一指令集规范
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
import json
from datetime import datetime


class ClientTypeEnum(str, Enum):
    """客户端类型枚举"""
    WEB3D = "web3d"
    SPIRIT = "spirit"
    MOBILE = "mobile"
    API = "api"
    TEST = "test"
    CUSTOM = "custom"


class ParameterValidation(BaseModel):
    """参数验证规则"""
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    pattern: Optional[str] = Field(None, description="正则表达式模式")
    enum: Optional[List[str]] = Field(None, description="枚举值列表")


class ParameterDefinition(BaseModel):
    """参数定义"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    validation: Optional[ParameterValidation] = Field(None, description="验证规则")
    default: Optional[Any] = Field(None, description="默认值")


class ResponseSchema(BaseModel):
    """响应模式定义"""
    success: Dict[str, Any] = Field(..., description="成功响应结构")
    error: Optional[Dict[str, Any]] = Field(None, description="错误响应结构")


class OperationDefinition(BaseModel):
    """操作指令定义"""
    operation_id: str = Field(..., description="操作指令唯一标识")
    name: str = Field(..., description="人类可读的名称")
    category: str = Field(..., description="操作分类")
    description: str = Field(..., description="详细描述")
    parameters: Dict[str, List[ParameterDefinition]] = Field(
        default_factory=dict,
        description="参数定义，分为required和optional"
    )
    response_schema: ResponseSchema = Field(..., description="响应模式")
    compatibility: Dict[str, Any] = Field(
        default_factory=dict,
        description="兼容性信息"
    )


class ClientCapabilities(BaseModel):
    """客户端能力定义"""
    max_concurrent_requests: int = Field(5, description="最大并发请求数")
    supported_scenes: List[str] = Field(
        default_factory=lambda: ["public"],
        description="支持的场景类型"
    )
    preferred_response_format: str = Field("json", description="偏好的响应格式")


class ClientMetadata(BaseModel):
    """客户端元数据"""
    client_id: str = Field(..., description="客户端唯一标识")
    client_type: ClientTypeEnum = Field(..., description="客户端类型")
    client_version: str = Field(..., description="客户端版本")
    platform: str = Field(..., description="运行平台")
    capabilities: ClientCapabilities = Field(default_factory=ClientCapabilities)


class OperationSet(BaseModel):
    """操作指令集"""
    version: str = Field("1.0.0", description="指令集版本")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间戳")
    operations: List[OperationDefinition] = Field(default_factory=list, description="操作指令列表")


class StandardCommandSet(BaseModel):
    """标准指令集完整定义"""
    spec_version: str = Field("1.0.0", description="规范版本")
    client_metadata: ClientMetadata
    operation_set: OperationSet

    @validator('spec_version')
    def validate_spec_version(cls, v):
        """验证规范版本"""
        if not v.startswith(('1.', '2.')):
            raise ValueError('Unsupported specification version')
        return v

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return json.loads(self.json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardCommandSet':
        """从字典创建实例"""
        return cls(**data)

    def get_operation_ids(self) -> List[str]:
        """获取所有操作指令ID列表"""
        return [op.operation_id for op in self.operation_set.operations]

    def has_operation(self, operation_id: str) -> bool:
        """检查是否包含指定操作"""
        return operation_id in self.get_operation_ids()


# 预定义的标准操作指令
STANDARD_OPERATIONS = {
    "zoom_pattern": OperationDefinition(
        operation_id="zoom_pattern",
        name="纹样放大",
        category="visualization",
        description="对文物特定区域进行放大显示和高亮标注",
        parameters={
            "required": [
                ParameterDefinition(
                    name="zoom_area",
                    type="string",
                    description="需要放大的区域标识",
                    validation=ParameterValidation(pattern=r"^[a-zA-Z0-9_-]+$")
                )
            ],
            "optional": [
                ParameterDefinition(
                    name="zoom_level",
                    type="number",
                    default=2.0,
                    description="放大倍数",
                    validation=ParameterValidation(min_value=1.0, max_value=10.0)
                ),
                ParameterDefinition(
                    name="highlight_color",
                    type="string",
                    default="#FF0000",
                    description="高亮颜色HEX值",
                    validation=ParameterValidation(pattern=r"^#[0-9A-Fa-f]{6}$")
                )
            ]
        },
        response_schema=ResponseSchema(
            success={
                "type": "object",
                "properties": {
                    "zoom_coordinates": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "width": {"type": "number"},
                            "height": {"type": "number"}
                        }
                    }
                }
            }
        )
    ),
    
    "restore_scene": OperationDefinition(
        operation_id="restore_scene",
        name="场景复原",
        category="visualization",
        description="还原文物的历史场景或展示环境",
        parameters={
            "required": [
                ParameterDefinition(
                    name="scene_type",
                    type="string",
                    description="场景类型",
                    validation=ParameterValidation(
                        enum=["excavation", "museum_display", "historical_period"]
                    )
                )
            ]
        },
        response_schema=ResponseSchema(
            success={
                "type": "object",
                "properties": {
                    "scene_loaded": {"type": "boolean"},
                    "environment_details": {"type": "object"}
                }
            }
        )
    ),
    
    "introduce": OperationDefinition(
        operation_id="introduce",
        name="文物介绍",
        category="information",
        description="提供文物的基本介绍和背景信息",
        parameters={
            "optional": [
                ParameterDefinition(
                    name="detail_level",
                    type="string",
                    default="medium",
                    description="介绍详细程度",
                    validation=ParameterValidation(enum=["brief", "medium", "detailed"])
                )
            ]
        },
        response_schema=ResponseSchema(
            success={
                "type": "object",
                "properties": {
                    "introduction_text": {"type": "string"},
                    "estimated_reading_time": {"type": "number"}
                }
            }
        )
    ),
    
    "spirit_interact": OperationDefinition(
        operation_id="spirit_interact",
        name="器灵交互",
        category="interaction",
        description="与文物器灵进行交互对话",
        parameters={
            "required": [
                ParameterDefinition(
                    name="interaction_type",
                    type="string",
                    description="交互类型",
                    validation=ParameterValidation(
                        enum=["greeting", "question", "story", "farewell"]
                    )
                )
            ]
        },
        response_schema=ResponseSchema(
            success={
                "type": "object",
                "properties": {
                    "response_text": {"type": "string"},
                    "emotion_state": {"type": "string"}
                }
            }
        )
    ),
    
    "query_param": OperationDefinition(
        operation_id="query_param",
        name="参数查询",
        category="information",
        description="查询文物的技术参数和详细信息",
        parameters={
            "optional": [
                ParameterDefinition(
                    name="param_type",
                    type="string",
                    default="all",
                    description="参数类型",
                    validation=ParameterValidation(
                        enum=["basic", "technical", "historical", "all"]
                    )
                )
            ]
        },
        response_schema=ResponseSchema(
            success={
                "type": "object",
                "properties": {
                    "parameters": {"type": "object"},
                    "source_reliability": {"type": "string"}
                }
            }
        )
    )
}


def create_standard_command_set(client_type: ClientTypeEnum, 
                              client_id: str,
                              operations: List[str]) -> StandardCommandSet:
    """
    创建标准指令集实例
    
    Args:
        client_type: 客户端类型
        client_id: 客户端ID
        operations: 操作指令ID列表
        
    Returns:
        StandardCommandSet实例
    """
    # 过滤有效的操作指令
    valid_operations = [
        STANDARD_OPERATIONS[op_id] 
        for op_id in operations 
        if op_id in STANDARD_OPERATIONS
    ]
    
    return StandardCommandSet(
        client_metadata=ClientMetadata(
            client_id=client_id,
            client_type=client_type,
            client_version="1.0.0",
            platform="dynamic_registration",
            capabilities=ClientCapabilities(
                max_concurrent_requests=3,
                supported_scenes=["study", "leisure", "public"],
                preferred_response_format="json"
            )
        ),
        operation_set=OperationSet(
            operations=valid_operations
        )
    )


def validate_command_set(command_set_data: Dict[str, Any]) -> bool:
    """
    验证指令集数据的有效性
    
    Args:
        command_set_data: 指令集数据字典
        
    Returns:
        验证是否通过
    """
    try:
        command_set = StandardCommandSet.from_dict(command_set_data)
        # 额外的业务逻辑验证可以在这里添加
        return True
    except Exception as e:
        print(f"Command set validation failed: {e}")
        return False