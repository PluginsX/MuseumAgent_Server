# -*- coding: utf-8 -*-
"""
响应数据模型 - 定义通用化标准化指令、响应体结构
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class StandardCommand(BaseModel):
    """博物馆智能体通用标准化指令模型，所有客户端均按此格式解析"""
    
    artifact_id: Optional[str] = None
    artifact_name: Optional[str] = None
    operation: Optional[str] = None
    operation_params: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    tips: Optional[str] = None


class AgentParseResponse(BaseModel):
    """博物馆智能体通用响应模型，所有客户端均按此格式接收响应"""
    
    code: int
    msg: str
    data: Optional[StandardCommand] = None
