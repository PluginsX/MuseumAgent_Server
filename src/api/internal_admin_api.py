# -*- coding: utf-8 -*-
"""内部管理员API - 供独立管理员系统调用（已迁移到database_service）"""
from datetime import datetime
from typing import Optional, Dict, Any
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.common.auth_utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    get_current_user
)
from src.services import database_service
from src.common.enhanced_logger import get_enhanced_logger


# 定义API模型
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class ClientCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "client"
    remark: Optional[str] = None


class APIKeyResetRequest(BaseModel):
    client_id: int


class GetAuditLogsRequest(BaseModel):
    page: int = 1
    size: int = 20
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    admin_user_id: Optional[int] = None
    client_user_id: Optional[int] = None
    action: Optional[str] = None


# 内部管理员API路由器
internal_router = APIRouter(prefix="/api/internal", tags=["internal_admin"])


def verify_admin_token(token: str) -> Optional[Dict[str, Any]]:
    """管理员Token校验（使用database_service）"""
    payload = decode_access_token(token)
    if not payload:
        return None
    
    # 验证用户是否存在且为管理员
    user = database_service.get_admin_user_by_id(payload.get("user_id"))
    if not user or not user.is_active or user.role not in ["admin", "Admin", "Administrator", "Operator"]:
        return None
    
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }


def log_audit_action(admin_user_id: Optional[int], action: str, ip_address: str, details: str = ""):
    """记录审计日志（使用日志系统）"""
    try:
        logger = get_enhanced_logger()
        logger.auth.info(f"Audit action: {action}", {
            "admin_user_id": admin_user_id,
            "ip_address": ip_address,
            "details": details
        })
    except Exception as e:
        logger = get_enhanced_logger()
        logger.sys.error(f"Log audit action error: {str(e)}")


@internal_router.post("/admin/auth")
def admin_auth(request: AdminLoginRequest, ip: str = None):
    """管理员认证接口（使用database_service）"""
    logger = get_enhanced_logger()
    
    try:
        # 使用 database_service 查询管理员用户
        admin_user = database_service.get_admin_user_by_username(request.username)
        
        if not admin_user or not admin_user.is_active or admin_user.role not in ["admin", "Admin", "Administrator", "Operator"]:
            log_audit_action(None, "ADMIN_LOGIN_FAILED", ip or "", f"Invalid username: {request.username}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        if not verify_password(request.password, admin_user.password_hash):
            log_audit_action(admin_user.id, "ADMIN_LOGIN_FAILED", ip or "", f"Invalid password for: {request.username}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 更新最后登录时间
        database_service.update_admin_user(admin_user.id, last_login=datetime.utcnow())
        
        # 生成JWT令牌
        token = create_access_token(
            subject=admin_user.username,
            user_id=admin_user.id,
            role=admin_user.role
        )
        
        log_audit_action(admin_user.id, "ADMIN_LOGIN_SUCCESS", ip or "", f"Admin logged in: {admin_user.username}")
        
        return {
            "code": 200,
            "data": {
                "access_token": token,
                "token_type": "bearer",
                "admin_info": {
                    "user_id": admin_user.id,
                    "username": admin_user.username,
                    "role": admin_user.role
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.auth.error(f"Admin auth error: {str(e)}")
        raise HTTPException(status_code=500, detail="认证服务异常")


@internal_router.post("/client/user/create")
def create_client(request: ClientCreateRequest, current_user: dict = Depends(get_current_user), ip: str = None):
    """创建客户账号接口（使用database_service）"""
    logger = get_enhanced_logger()
    
    # 验证管理员权限
    if current_user.get("role") not in ["admin", "Admin", "Administrator", "Operator"]:
        log_audit_action(current_user.get("user_id"), "CLIENT_CREATE_FAILED", ip or "", "Insufficient permissions")
        raise HTTPException(status_code=403, detail="无创建客户权限")
    
    admin_info = current_user
    
    try:
        # 检查用户名是否已存在
        existing_user = database_service.get_client_user_by_username(request.username)
        if existing_user:
            log_audit_action(admin_info["user_id"], "CLIENT_CREATE_FAILED", ip or "", f"Username already exists: {request.username}")
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 生成API密钥
        api_key_plaintext = f"museum_{secrets.token_urlsafe(32)}"
        
        # 创建新客户用户
        new_user = database_service.create_client_user(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            api_key=api_key_plaintext,
            role=request.role,
            is_active=True
        )
        
        log_audit_action(admin_info["user_id"], "CLIENT_CREATE_SUCCESS", ip or "", f"Created client: {request.username}")
        
        return {
            "code": 200,
            "data": {
                "client_id": new_user.id,
                "api_key": api_key_plaintext  # 返回明文API密钥给管理员
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.auth.error(f"Create client error: {str(e)}")
        raise HTTPException(status_code=500, detail="创建客户失败")


@internal_router.post("/client/api_key/reset")
def reset_api_key(request: APIKeyResetRequest, current_user: dict = Depends(get_current_user), ip: str = None):
    """重置客户API密钥（使用database_service）"""
    logger = get_enhanced_logger()
    
    # 验证管理员权限
    if current_user.get("role") not in ["admin", "Admin", "Administrator", "Operator"]:
        log_audit_action(current_user.get("user_id"), "API_KEY_RESET_FAILED", ip or "", "Insufficient permissions")
        raise HTTPException(status_code=403, detail="无重置API密钥权限")
    
    admin_info = current_user
    
    try:
        # 检查客户是否存在
        client = database_service.get_client_user_by_id(request.client_id)
        if not client:
            log_audit_action(admin_info["user_id"], "API_KEY_RESET_FAILED", ip or "", f"Client not found: {request.client_id}")
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 生成新的API密钥
        new_api_key_plaintext = f"museum_{secrets.token_urlsafe(32)}"
        
        # 更新API密钥
        database_service.update_client_user(request.client_id, api_key=new_api_key_plaintext)
        
        log_audit_action(admin_info["user_id"], "API_KEY_RESET_SUCCESS", ip or "", f"Reset API key for client: {client.username}")
        
        return {
            "code": 200,
            "data": {
                "api_key": new_api_key_plaintext
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.auth.error(f"Reset API key error: {str(e)}")
        raise HTTPException(status_code=500, detail="重置API密钥失败")


@internal_router.get("/audit/logs")
def get_audit_logs(
    page: int = 1, 
    size: int = 20, 
    start_time: Optional[str] = None, 
    end_time: Optional[str] = None, 
    admin_user_id: Optional[int] = None, 
    client_user_id: Optional[int] = None, 
    action: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    ip: str = None
):
    """获取审计日志（已迁移到日志系统，使用database_service）"""
    logger = get_enhanced_logger()
    
    # 验证管理员权限
    if current_user.get("role") not in ["admin", "Admin", "Administrator", "Operator"]:
        log_audit_action(current_user.get("user_id"), "AUDIT_LOG_ACCESS_FAILED", ip or "", "Insufficient permissions")
        raise HTTPException(status_code=403, detail="无查看审计日志权限")
    
    admin_info = current_user
    
    try:
        log_audit_action(admin_info["user_id"], "AUDIT_LOG_ACCESS_SUCCESS", ip or "", f"Requested audit logs")
        
        # 审计日志已迁移到日志系统，返回空列表
        return {
            "code": 200,
            "data": {
                "logs": [],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": 0,
                    "pages": 0
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.sys.error(f"Get audit logs error: {str(e)}")
        raise HTTPException(status_code=500, detail="获取审计日志失败")