# -*- coding: utf-8 -*-
"""
请求数据模型 - 基于pydantic定义通用字段、约束、描述
"""
from typing import Optional

from pydantic import BaseModel, Field


class AgentParseRequest(BaseModel):
    """博物馆智能体通用请求数据模型，所有客户端均按此格式发送请求"""
    
    user_input: str = Field(
        ...,
        description="用户自然语言输入",
        min_length=1,
        max_length=2000
    )
    client_type: Optional[str] = Field(
        None,
        description="客户端类型（用于日志统计，非业务逻辑）",
        examples=["qiling", "official", "third"]
    )
    spirit_id: Optional[str] = Field(
        None,
        description="器灵ID（第三方客户端可传空，服务端不做业务处理）"
    )
    scene_type: Optional[str] = Field(
        "public",
        description="场景类型：study/leisure/public，默认公共场景",
        pattern="^(study|leisure|public)$"
    )
