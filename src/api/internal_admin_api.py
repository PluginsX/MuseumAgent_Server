# -*- coding: utf-8 -*-
"""内部管理员API - 供独立管理员系统调用"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from src.common.auth_utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password
)
from src.db.database import get_db_session
from src.db.models import AdminUser, ClientUser, APIKey, AuditLog
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


def verify_admin_token(token: str, db: Session) -> Optional[Dict[str, Any]]:
    """管理员Token校验"""
    payload = decode_access_token(token)
    if not payload:
        return None
    
    # 验证用户是否存在且为管理员
    user = db.query(AdminUser).filter(AdminUser.id == payload.get("user_id")).first()
    if not user or not user.is_active or user.role not in ["admin", "Admin", "Administrator", "Operator"]:
        return None
    
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }


def log_audit_action(db: Session, admin_user_id: Optional[int], action: str, ip_address: str, details: str = ""):
    """记录审计日志"""
    try:
        audit_log = AuditLog(
            admin_user_id=admin_user_id,
            action=action,
            ip_address=ip_address,
            details=details,
            created_at=datetime.now()
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger = get_enhanced_logger()
        logger.audit.error(f"Log audit action error: {str(e)}")


@internal_router.post("/admin/auth")
def admin_auth(request: AdminLoginRequest, ip: str = None, db: Session = Depends(get_db_session)):
    """管理员认证接口"""
    logger = get_enhanced_logger()
    
    try:
        # 查询管理员用户
        admin_user = db.query(AdminUser).filter(AdminUser.username == request.username).first()
        
        if not admin_user or not admin_user.is_active or admin_user.role not in ["admin", "Admin", "Administrator", "Operator"]:
            log_audit_action(db, None, "ADMIN_LOGIN_FAILED", ip or "", f"Invalid username: {request.username}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        if not verify_password(request.password, admin_user.password_hash):
            log_audit_action(db, admin_user.id, "ADMIN_LOGIN_FAILED", ip or "", f"Invalid password for: {request.username}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 更新最后登录时间
        admin_user.last_login = datetime.utcnow()
        db.commit()
        
        # 生成JWT令牌
        token = create_access_token(
            subject=admin_user.username,
            user_id=admin_user.id,
            role=admin_user.role
        )
        
        log_audit_action(db, admin_user.id, "ADMIN_LOGIN_SUCCESS", ip or "", f"Admin logged in: {admin_user.username}")
        
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
def create_client(request: ClientCreateRequest, token: str = None, ip: str = None, db: Session = Depends(get_db_session)):
    """创建客户账号接口"""
    logger = get_enhanced_logger()
    
    # 验证管理员权限
    admin_info = verify_admin_token(token, db)
    if not admin_info or admin_info["role"] not in ["admin", "Admin", "Administrator", "Operator"]:
        log_audit_action(db, admin_info["user_id"] if admin_info else None, "CLIENT_CREATE_FAILED", ip or "", "Insufficient permissions")
        raise HTTPException(status_code=403, detail="无创建客户权限")
    
    try:
        # 检查用户名是否已存在
        existing_user = db.query(ClientUser).filter(ClientUser.username == request.username).first()
        if existing_user:
            log_audit_action(db, admin_info["user_id"], "CLIENT_CREATE_FAILED", ip or "", f"Username already exists: {request.username}")
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 创建新客户用户
        new_user = ClientUser(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            role=request.role,
            is_active=True
        )
        db.add(new_user)
        db.flush()  # 获取ID但不提交
        
        # 为客户生成API密钥
        api_key_plaintext = f"museum_{secrets.token_urlsafe(32)}"
        api_key_hash = hash_password(api_key_plaintext)
        
        api_key = APIKey(
            key_hash=api_key_hash,
            client_user_id=new_user.id,
            is_active=True,
            remark=request.remark or f"API Key for {request.username}"
        )
        db.add(api_key)
        db.commit()
        
        log_audit_action(db, admin_info["user_id"], "CLIENT_CREATE_SUCCESS", ip or "", f"Created client: {request.username}")
        
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
        db.rollback()
        logger.auth.error(f"Create client error: {str(e)}")
        raise HTTPException(status_code=500, detail="创建客户失败")


@internal_router.post("/client/api_key/reset")
def reset_api_key(request: APIKeyResetRequest, token: str = None, ip: str = None, db: Session = Depends(get_db_session)):
    """重置客户API密钥"""
    logger = get_enhanced_logger()
    
    # 验证管理员权限
    admin_info = verify_admin_token(token, db)
    if not admin_info or admin_info["role"] not in ["admin", "Admin", "Administrator", "Operator"]:
        log_audit_action(db, admin_info["user_id"] if admin_info else None, "API_KEY_RESET_FAILED", ip or "", "Insufficient permissions")
        raise HTTPException(status_code=403, detail="无重置API密钥权限")
    
    try:
        # 检查客户是否存在
        client = db.query(ClientUser).filter(ClientUser.id == request.client_id).first()
        if not client:
            log_audit_action(db, admin_info["user_id"], "API_KEY_RESET_FAILED", ip or "", f"Client not found: {request.client_id}")
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 删除旧的API密钥
        old_api_key = db.query(APIKey).filter(APIKey.client_user_id == request.client_id).first()
        if old_api_key:
            db.delete(old_api_key)
        
        # 生成新的API密钥
        new_api_key_plaintext = f"museum_{secrets.token_urlsafe(32)}"
        new_api_key_hash = hash_password(new_api_key_plaintext)
        
        new_api_key = APIKey(
            key_hash=new_api_key_hash,
            client_user_id=request.client_id,
            is_active=True,
            remark=f"Reset API Key for {client.username}"
        )
        db.add(new_api_key)
        db.commit()
        
        log_audit_action(db, admin_info["user_id"], "API_KEY_RESET_SUCCESS", ip or "", f"Reset API key for client: {client.username}")
        
        return {
            "code": 200,
            "data": {
                "api_key": new_api_key_plaintext
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
    token: str = None,
    ip: str = None,
    db: Session = Depends(get_db_session)
):
    """获取审计日志"""
    logger = get_enhanced_logger()
    
    # 验证管理员权限
    admin_info = verify_admin_token(token, db)
    if not admin_info or admin_info["role"] not in ["admin", "Admin", "Administrator", "Operator"]:
        log_audit_action(db, admin_info["user_id"] if admin_info else None, "AUDIT_LOG_ACCESS_FAILED", ip or "", "Insufficient permissions")
        raise HTTPException(status_code=403, detail="无查看审计日志权限")
    
    try:
        query = db.query(AuditLog).order_by(desc(AuditLog.created_at))
        
        # 应用过滤条件
        if start_time:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at >= start_dt)
        
        if end_time:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at <= end_dt)
        
        if admin_user_id:
            query = query.filter(AuditLog.admin_user_id == admin_user_id)
        
        if client_user_id:
            query = query.filter(AuditLog.client_user_id == client_user_id)
        
        if action:
            query = query.filter(AuditLog.action.like(f"%{action}%"))
        
        # 分页
        total = query.count()
        logs = query.offset((page - 1) * size).limit(size).all()
        
        log_audit_action(db, admin_info["user_id"], "AUDIT_LOG_ACCESS_SUCCESS", ip or "", f"Retrieved {len(logs)} audit logs")
        
        return {
            "code": 200,
            "data": {
                "logs": [{
                    "id": log.id,
                    "admin_user_id": log.admin_user_id,
                    "client_user_id": log.client_user_id,
                    "action": log.action,
                    "ip_address": log.ip_address,
                    "details": log.details,
                    "created_at": log.created_at.isoformat()
                } for log in logs],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.audit.error(f"Get audit logs error: {str(e)}")
        raise HTTPException(status_code=500, detail="获取审计日志失败")