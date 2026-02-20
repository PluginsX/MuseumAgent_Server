# -*- coding: utf-8 -*-
"""
会话管理API（完整版 V2.0）
提供完整的会话配置和管理功能
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json

from ..session.strict_session_manager import strict_session_manager
from ..common.enhanced_logger import get_enhanced_logger

router = APIRouter(prefix="/api/session", tags=["会话管理"])
logger = get_enhanced_logger()


# ===== 新增：配置模型 =====

class SystemPromptConfig(BaseModel):
    """系统提示词配置"""
    role_description: str = Field(..., description="LLM 角色描述")
    response_requirements: str = Field(..., description="LLM 响应要求")


class SceneContextConfig(BaseModel):
    """场景上下文配置"""
    current_scene: str = Field(..., description="当前场景名称")
    scene_description: str = Field(..., description="场景描述")
    keywords: List[str] = Field(default_factory=list, description="场景关键词")
    scene_specific_prompt: Optional[str] = Field(None, description="场景特定提示")


class ClientRegistrationRequest(BaseModel):
    """客户端注册请求（完整版）"""
    client_metadata: Dict[str, Any] = Field(..., description="客户端元数据")
    functions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="函数定义列表")
    system_prompt: Optional[SystemPromptConfig] = Field(None, description="系统提示词配置")
    scene_context: Optional[SceneContextConfig] = Field(None, description="场景上下文配置")
    client_signature: Optional[str] = Field(None, description="客户端签名")


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
    客户端注册接口（完整版 V2.0）
    支持系统提示词和场景上下文配置
    """
    try:
        # 记录客户端注册请求
        logger.sess.info("Client registration request received (V2.0)", 
                        {'client_type': registration.client_metadata.get('client_type'),
                         'has_system_prompt': registration.system_prompt is not None,
                         'has_scene_context': registration.scene_context is not None})
        
        # 验证基本字段
        if not registration.client_metadata:
            logger.sess.error("Invalid client registration data format")
            raise HTTPException(status_code=400, detail="无效的客户端注册数据格式")
        
        # 验证客户端类型
        client_type_str = registration.client_metadata.get("client_type", "WEB")
        if not client_type_str:
            registration.client_metadata["client_type"] = "WEB"
            logger.sess.info("Set default client type to WEB")
        
        # 生成唯一会话ID
        session_id = str(uuid.uuid4())
        logger.sess.info("New session ID generated", {'session_id': session_id[:8]})
        
        # ✅ 添加系统提示词配置
        if registration.system_prompt:
            registration.client_metadata["system_prompt"] = {
                "role_description": registration.system_prompt.role_description,
                "response_requirements": registration.system_prompt.response_requirements
            }
            logger.sess.info("System prompt configured", 
                          {'session_id': session_id[:8],
                           'role_length': len(registration.system_prompt.role_description)})
        else:
            # 使用默认值
            registration.client_metadata["system_prompt"] = {
                "role_description": "你是智能助手。",
                "response_requirements": "请用友好、专业的语言回答问题。"
            }
            logger.sess.info("Using default system prompt")
        
        # ✅ 添加场景上下文配置
        if registration.scene_context:
            registration.client_metadata["scene_context"] = {
                "current_scene": registration.scene_context.current_scene,
                "scene_description": registration.scene_context.scene_description,
                "keywords": registration.scene_context.keywords,
                "scene_specific_prompt": registration.scene_context.scene_specific_prompt or ""
            }
            logger.sess.info("Scene context configured", 
                          {'session_id': session_id[:8],
                           'scene': registration.scene_context.current_scene})
        else:
            # 使用默认值
            registration.client_metadata["scene_context"] = {
                "current_scene": "公共场景",
                "scene_description": "通用对话场景",
                "keywords": [],
                "scene_specific_prompt": ""
            }
            logger.sess.info("Using default scene context")
        
        # 函数定义是可选的
        if registration.functions and len(registration.functions) > 0:
            logger.sess.info("Client provided function definitions", 
                          {'function_count': len(registration.functions)})
        else:
            logger.sess.info("No function definitions provided, general chat mode")
            registration.functions = []
        
        # 使用支持完整配置的会话注册
        session = strict_session_manager.register_session_with_functions(
            session_id=session_id,
            client_metadata=registration.client_metadata,
            functions=registration.functions
        )
        
        logger.sess.info("Session registration successful (V2.0)", 
                      {'session_id': session_id[:8],
                       'functions': len(registration.functions),
                       'has_system_prompt': 'system_prompt' in registration.client_metadata,
                       'has_scene_context': 'scene_context' in registration.client_metadata,
                       'expires_at': session.expires_at.isoformat()})
        
        # 返回注册成功响应
        return ClientRegistrationResponse(
            session_id=session_id,
            expires_at=session.expires_at.isoformat(),
            server_timestamp=datetime.now().isoformat(),
            supported_features=[
                "dynamic_operations", 
                "session_management", 
                "heartbeat", 
                "function_calling",
                "system_prompt_config",  # ✅ 新增特性
                "scene_context_config"   # ✅ 新增特性
            ]
        )
        
    except Exception as e:
        logger.sess.error(f"Session registration failed: {str(e)}")
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
async def get_session_functions(session_id: str = Header(...)):
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