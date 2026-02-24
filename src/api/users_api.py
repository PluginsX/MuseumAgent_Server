# -*- coding: utf-8 -*-
"""用户管理 API - 分别管理管理员用户和客户用户"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.common.auth_utils import get_current_user, hash_password
from src.services import database_service
import secrets

router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])


class AdminUserCreate(BaseModel):
    username: str
    email: str  # 管理员邮箱是必需的
    password: str
    role: str = "admin"


class ClientUserCreate(BaseModel):
    username: str
    email: Optional[str] = None  # 客户邮箱是可选的
    password: str
    role: str = "client"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str]


class ClientUserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str]
    api_key: Optional[str] = None


# 管理员用户相关API
@router.get("/admins", response_model=List[AdminUserResponse])
def list_admin_users(
    _: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
):
    """管理员用户列表"""
    users, total = database_service.list_admin_users(page=page, size=size, search=search)
    return [AdminUserResponse(
        id=u.id, 
        username=u.username, 
        email=u.email, 
        role=u.role, 
        is_active=u.is_active,
        created_at=u.created_at.isoformat() if u.created_at else None,
        last_login=u.last_login.isoformat() if u.last_login else None
    ) for u in users]


@router.post("/admins", response_model=AdminUserResponse)
def create_admin_user(
    body: AdminUserCreate,
    _: dict = Depends(get_current_user),
):
    """创建管理员用户"""
    if database_service.get_admin_user_by_username(body.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if database_service.get_admin_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    user = database_service.create_admin_user(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    
    return AdminUserResponse(
        id=user.id, 
        username=user.username, 
        email=user.email, 
        role=user.role, 
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.put("/admins/{user_id}", response_model=AdminUserResponse)
def update_admin_user(
    user_id: int,
    body: UserUpdate,
    _: dict = Depends(get_current_user),
):
    """更新管理员用户"""
    # 验证用户名和邮箱不为空
    if body.username is not None and body.username.strip() == "":
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if body.email is not None and body.email.strip() == "":
        raise HTTPException(status_code=400, detail="邮箱不能为空")
    
    # 检查用户名是否已被其他用户使用
    if body.username and body.username.strip():
        existing_user = database_service.get_admin_user_by_username(body.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="用户名已被其他用户使用")
    
    # 检查邮箱是否已被其他用户使用
    if body.email and body.email.strip():
        existing_user = database_service.get_admin_user_by_email(body.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
    
    password_hash = None
    if body.password:
        password_hash = hash_password(body.password)
    
    user = database_service.update_admin_user(
        user_id=user_id,
        username=body.username,
        email=body.email,
        role=body.role,
        is_active=body.is_active,
        password_hash=password_hash
    )
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return AdminUserResponse(
        id=user.id, 
        username=user.username, 
        email=user.email, 
        role=user.role, 
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


# 客户用户相关API
@router.get("/clients", response_model=List[ClientUserResponse])
def list_client_users(
    _: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
):
    """客户用户列表"""
    users, total = database_service.list_client_users(page=page, size=size, search=search)
    
    responses = []
    for u in users:
        api_key_str = u.api_key if u.api_key else "未生成"
        
        responses.append(ClientUserResponse(
            id=u.id, 
            username=u.username, 
            email=u.email, 
            role=u.role, 
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else None,
            last_login=u.last_login.isoformat() if u.last_login else None,
            api_key=api_key_str
        ))
    return responses


@router.post("/clients", response_model=ClientUserResponse)
def create_client_user(
    body: ClientUserCreate,
    _: dict = Depends(get_current_user),
):
    """创建客户用户"""
    if database_service.get_client_user_by_username(body.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 生成API密钥
    api_key = f"museum_{secrets.token_urlsafe(32)}"
    
    user = database_service.create_client_user(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        api_key=api_key,
        role=body.role,
    )
    
    return ClientUserResponse(
        id=user.id, 
        username=user.username, 
        email=user.email, 
        role=user.role, 
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None,
        api_key=user.api_key
    )


@router.put("/clients/{user_id}", response_model=ClientUserResponse)
def update_client_user(
    user_id: int,
    body: UserUpdate,
    _: dict = Depends(get_current_user),
):
    """更新客户用户"""
    # 验证用户名不为空
    if body.username is not None and body.username.strip() == "":
        raise HTTPException(status_code=400, detail="用户名不能为空")
    
    # 验证邮箱不为空（如果提供了邮箱）
    if body.email is not None and body.email.strip() == "":
        raise HTTPException(status_code=400, detail="邮箱不能为空")
    
    # 检查用户名是否已被其他用户使用
    if body.username and body.username.strip():
        existing_user = database_service.get_client_user_by_username(body.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="用户名已被其他用户使用")
    
    # 检查邮箱是否已被其他用户使用（如果提供了邮箱）
    if body.email and body.email.strip():
        existing_user = database_service.get_client_user_by_email(body.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
    
    password_hash = None
    if body.password:
        password_hash = hash_password(body.password)
    
    user = database_service.update_client_user(
        user_id=user_id,
        username=body.username,
        email=body.email,
        role=body.role,
        is_active=body.is_active,
        password_hash=password_hash
    )
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return ClientUserResponse(
        id=user.id, 
        username=user.username, 
        email=user.email, 
        role=user.role, 
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None,
        api_key=user.api_key
    )


@router.delete("/admins/{user_id}")
def delete_admin_user(
    user_id: int,
    _: dict = Depends(get_current_user),
):
    """删除管理员用户"""
    if not database_service.delete_admin_user(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "删除成功"}


@router.delete("/clients/{user_id}")
def delete_client_user(
    user_id: int,
    _: dict = Depends(get_current_user),
):
    """删除客户用户"""
    if not database_service.delete_client_user(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "删除成功"}