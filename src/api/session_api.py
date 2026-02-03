# -*- coding: utf-8 -*-
"""
会话管理API
提供客户端指令集动态注册和会话管理功能
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json

from ..session.session_manager import session_manager
from ..models.command_set_models import validate_command_set, StandardCommandSet
from ..common.log_formatter import log_step, log_communication

router = APIRouter(prefix="/api/session", tags=["会话管理"])


class ClientRegistrationRequest(BaseModel):
    """客户端注册请求"""
    client_metadata: Dict[str, Any]
    operation_set: List[str]
    client_signature: Optional[str] = None


class ClientRegistrationResponse(BaseModel):
    """客户端注册响应"""
    session_id: str
    expires_at: str
    server_timestamp: str
    supported_features: List[str]


class HeartbeatResponse(BaseModel):
    """心跳响应"""
    status: str
    timestamp: str
    session_valid: bool = True


class SessionOperationsResponse(BaseModel):
    """会话操作集响应"""
    operations: List[str]
    session_id: str
    client_type: Optional[str] = None


class SessionInfoResponse(BaseModel):
    """会话信息响应"""
    session_id: str
    client_metadata: Dict[str, Any]
    operations: List[str]
    created_at: str
    expires_at: str
    is_active: bool


@router.post("/register", response_model=ClientRegistrationResponse)
async def register_client_session(registration: ClientRegistrationRequest):
    """
    客户端注册接口
    客户端首次连接时调用此接口注册自己的能力集
    """
    try:
        # 记录客户端注册请求
        print(log_communication('CLIENT', 'RECEIVE', 'Client Registration', 
                               registration.dict(), 
                               {'client_type': registration.client_metadata.get('client_type')}))
        
        # 简化验证：只要求基本字段存在
        if not registration.client_metadata or not isinstance(registration.operation_set, list):
            print(log_step('CLIENT', 'ERROR', '无效的客户端注册数据格式'))
            raise HTTPException(status_code=400, detail="无效的客户端注册数据格式")
        
        # 验证客户端类型
        from ..models.command_set_models import ClientTypeEnum
        client_type_str = registration.client_metadata.get("client_type", "")
        if client_type_str not in [t.value for t in ClientTypeEnum]:
            # 如果不是标准类型，使用CUSTOM
            registration.client_metadata["client_type"] = "custom"
            print(log_step('CLIENT', 'WARNING', '非标准客户端类型，使用custom', 
                          {'original_type': client_type_str}))
        
        # 生成唯一会话ID
        session_id = str(uuid.uuid4())
        print(log_step('SESSION', 'REGISTER', '生成新会话ID', 
                      {'session_id': session_id}))
        
        # 注册会话
        session = session_manager.register_session(
            session_id=session_id,
            client_metadata=registration.client_metadata,
            operation_set=registration.operation_set
        )
        
        print(log_step('SESSION', 'SUCCESS', '会话注册成功', 
                      {'operations': len(registration.operation_set), 
                       'expires_at': session.expires_at.isoformat()}))
        
        # 记录注册成功的响应
        response_data = {
            "session_id": session_id,
            "expires_at": session.expires_at.isoformat(),
            "supported_features": ["dynamic_operations", "session_management", "heartbeat"]
        }
        print(log_communication('CLIENT', 'SEND', 'Registration Success', response_data))
        
        # 返回注册成功响应
        return ClientRegistrationResponse(
            session_id=session_id,
            expires_at=session.expires_at.isoformat(),
            server_timestamp=datetime.now().isoformat(),
            supported_features=["dynamic_operations", "session_management", "heartbeat"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"会话注册失败: {str(e)}")


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def session_heartbeat(session_id: str = Header()):
    """
    会话心跳接口
    客户端定期调用以维持会话活跃
    """
    try:
        print(log_step('SESSION', 'HEARTBEAT', '收到心跳请求', 
                      {'session_id': session_id}))
        
        is_valid = session_manager.heartbeat(session_id)
        if is_valid:
            response_data = {
                "status": "alive",
                "session_valid": True
            }
            print(log_communication('CLIENT', 'SEND', 'Heartbeat Response', response_data))
            return HeartbeatResponse(
                status="alive",
                timestamp=datetime.now().isoformat(),
                session_valid=True
            )
        else:
            print(log_step('SESSION', 'ERROR', '心跳失败：会话不存在或已过期', 
                          {'session_id': session_id}))
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"心跳处理失败: {str(e)}")


@router.delete("/unregister")
async def unregister_session(session_id: str = Header()):
    """
    注销会话接口
    客户端主动断开连接时调用
    """
    try:
        print(log_step('SESSION', 'UNREGISTER', '收到注销请求', 
                      {'session_id': session_id}))
        
        if session_manager.unregister_session(session_id):
            response_data = {
                "status": "unregistered",
                "message": "会话已成功注销"
            }
            print(log_communication('CLIENT', 'SEND', 'Unregister Response', response_data))
            return {
                "status": "unregistered", 
                "timestamp": datetime.now().isoformat(),
                "message": "会话已成功注销"
            }
        else:
            print(log_step('SESSION', 'ERROR', '注销失败：会话不存在', 
                          {'session_id': session_id}))
            raise HTTPException(status_code=404, detail="会话不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"会话注销失败: {str(e)}")


@router.get("/operations", response_model=SessionOperationsResponse)
async def get_session_operations(session_id: str = Header()):
    """
    获取会话支持的操作指令集
    """
    try:
        operations = session_manager.get_operations_for_session(session_id)
        if operations:
            session = session_manager.get_session(session_id)
            client_type = session.client_metadata.get("client_type") if session else None
            
            return SessionOperationsResponse(
                operations=operations,
                session_id=session_id,
                client_type=client_type
            )
        else:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取操作集失败: {str(e)}")


@router.get("/info", response_model=SessionInfoResponse)
async def get_session_info(session_id: str = Header()):
    """
    获取详细的会话信息
    """
    try:
        session = session_manager.get_session(session_id)
        if session:
            return SessionInfoResponse(
                session_id=session.session_id,
                client_metadata=session.client_metadata,
                operations=session.operation_set,
                created_at=session.created_at.isoformat(),
                expires_at=session.expires_at.isoformat(),
                is_active=not session.is_expired()
            )
        else:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话信息失败: {str(e)}")


@router.get("/stats")
async def get_session_stats():
    """
    获取会话统计信息
    """
    try:
        return {
            "active_sessions": session_manager.get_active_session_count(),
            "total_sessions": len(session_manager.sessions),
            "server_time": datetime.now().isoformat(),
            "sessions_detail": session_manager.get_all_sessions_info()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/validate")
async def validate_command_set_endpoint(command_set: Dict[str, Any]):
    """
    验证指令集格式接口
    """
    try:
        is_valid = validate_command_set(command_set)
        return {
            "valid": is_valid,
            "timestamp": datetime.now().isoformat(),
            "message": "指令集格式正确" if is_valid else "指令集格式错误"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"验证失败: {str(e)}")


# 注意：APIRouter不支持exception_handler，异常处理在主应用中统一处理