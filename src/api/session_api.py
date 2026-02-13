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

from ..session.strict_session_manager import strict_session_manager
# 已移除旧的指令集模型导入 - 现在完全基于OpenAI函数调用标准
from ..common.enhanced_logger import get_enhanced_logger

router = APIRouter(prefix="/api/session", tags=["会话管理"])
logger = get_enhanced_logger()


class ClientRegistrationRequest(BaseModel):
    """客户端注册请求"""
    client_metadata: Dict[str, Any]
    functions: Optional[List[Dict[str, Any]]] = None  # 新增：函数定义列表
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
        logger.sess.info("Client registration request received", 
                        {'client_type': registration.client_metadata.get('client_type')})
        
        # 验证基本字段
        if not registration.client_metadata:
            logger.sess.error("Invalid client registration data format")
            raise HTTPException(status_code=400, detail="无效的客户端注册数据格式")
        
        # 验证客户端类型（简化处理）
        client_type_str = registration.client_metadata.get("client_type", "custom")
        if not client_type_str:
            registration.client_metadata["client_type"] = "custom"
            logger.sess.info("Set default client type to custom")
        
        # 生成唯一会话ID
        session_id = str(uuid.uuid4())
        logger.sess.info("New session ID generated", 
                      {'session_id': session_id})
        
        # 函数定义是可选的 - 支持普通对话模式
        if registration.functions and len(registration.functions) > 0:
            logger.sess.info("Client provided function definitions, enabling function calling mode", 
                          {'function_count': len(registration.functions)})
        else:
            logger.sess.info("Client did not provide function definitions, enabling general chat mode")
            # 设置空函数列表而不是拒绝注册
            registration.functions = []
        
        # 使用支持OpenAI标准函数调用的会话注册
        session = strict_session_manager.register_session_with_functions(
            session_id=session_id,
            client_metadata=registration.client_metadata,
            functions=registration.functions
        )
        
        logger.sess.info("Session registration successful", 
                      {'functions': len(registration.functions),
                       'expires_at': session.expires_at.isoformat()})
        
        # 记录注册成功的响应
        response_data = {
            "session_id": session_id,
            "expires_at": session.expires_at.isoformat(),
            "supported_features": ["dynamic_operations", "session_management", "heartbeat", "function_calling"]
        }
        logger.sess.info("Registration success response sent", response_data)
        
        # 返回注册成功响应
        return ClientRegistrationResponse(
            session_id=session_id,
            expires_at=session.expires_at.isoformat(),
            server_timestamp=datetime.now().isoformat(),
            supported_features=["dynamic_operations", "session_management", "heartbeat", "function_calling"]
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
        logger.sess.info("Heartbeat request received", 
                      {'session_id': session_id})
        
        is_valid = strict_session_manager.heartbeat(session_id)
        if is_valid:
            response_data = {
                "status": "alive",
                "session_valid": True
            }
            logger.sess.info("Heartbeat response sent", response_data)
            return HeartbeatResponse(
                status="alive",
                timestamp=datetime.now().isoformat(),
                session_valid=True
            )
        else:
            logger.sess.error("Heartbeat failed: session does not exist or has expired", 
                          {'session_id': session_id})
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
        logger.sess.info("Unregister request received", 
                      {'session_id': session_id})
        
        if strict_session_manager.unregister_session(session_id):
            response_data = {
                "status": "unregistered",
                "message": "会话已成功注销"
            }
            logger.sess.info("Unregister response sent", response_data)
            return {
                "status": "unregistered", 
                "timestamp": datetime.now().isoformat(),
                "message": "会话已成功注销"
            }
        else:
            logger.sess.error("Unregister failed: session does not exist", 
                          {'session_id': session_id})
            raise HTTPException(status_code=404, detail="会话不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"会话注销失败: {str(e)}")


@router.get("/functions", response_model=SessionOperationsResponse)
async def get_session_functions(session_id: str = Header()):
    """
    获取会话支持的OpenAI标准函数定义
    """
    try:
        # 获取函数名称列表作为操作集的替代
        functions = strict_session_manager.get_functions_for_session(session_id)
        function_names = [func.get("name", "unknown") for func in functions]
        
        if function_names:
            session = strict_session_manager.get_session(session_id)
            client_type = session.client_metadata.get("client_type") if session else None
            
            return SessionOperationsResponse(
                operations=function_names,
                session_id=session_id,
                client_type=client_type
            )
        else:
            # 兼容模式：返回基础操作集
            return SessionOperationsResponse(
                operations=["general_chat"],
                session_id=session_id,
                client_type="basic"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取函数定义失败: {str(e)}")


@router.get("/info", response_model=SessionInfoResponse)
async def get_session_info(session_id: str = Header()):
    """
    获取详细的会话信息
    """
    try:
        session = strict_session_manager.get_session(session_id)
        if session:
            return SessionInfoResponse(
                session_id=session.session_id,
                client_metadata=session.client_metadata,
                operations=session.client_metadata.get("function_names", []),
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
            "active_sessions": len(strict_session_manager.get_all_sessions()),
            "total_sessions": len(strict_session_manager.sessions),
            "server_time": datetime.now().isoformat(),
            "sessions_detail": [{
                "session_id": s.session_id,
                "client_type": s.client_metadata.get("client_type", "unknown"),
                "function_count": len(s.client_metadata.get("functions", [])),
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "is_expired": s.is_expired()
            } for s in strict_session_manager.sessions.values()]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/validate/{session_id}")
async def validate_session_endpoint(session_id: str):
    """
    验证会话是否有效
    """
    try:
        logger.sess.info('Validating session', {'session_id': session_id})
        
        session = strict_session_manager.get_session(session_id)
        if session and not session.is_expired():
            logger.sess.info('Session is valid', {'session_id': session_id})
            return {
                "valid": True,
                "session_id": session_id,
                "expires_at": session.expires_at.isoformat()
            }
        else:
            logger.sess.error('Session is invalid or has expired', {'session_id': session_id})
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证会话失败: {str(e)}")


@router.delete("/{session_id}")
async def disconnect_session_endpoint(session_id: str):
    """
    断开会话连接
    """
    try:
        logger.sess.info('Disconnecting session', {'session_id': session_id})
        
        if strict_session_manager.unregister_session(session_id):
            logger.sess.info('Session disconnected', {'session_id': session_id})
            return {
                "message": "会话已断开",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.sess.error('Failed to disconnect session: session does not exist', {'session_id': session_id})
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开会话失败: {str(e)}")