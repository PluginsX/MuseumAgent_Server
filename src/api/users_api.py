# -*- coding: utf-8 -*-
"""用户管理 API - 分别管理管理员用户和客户用户"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.common.auth_utils import get_current_user, hash_password
from src.db.database import get_db_session
from src.db.models import AdminUser, ClientUser

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
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


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
    db: Session = Depends(get_db_session),
):
    """管理员用户列表"""
    q = db.query(AdminUser)
    if search:
        q = q.filter(or_(AdminUser.username.ilike(f"%{search}%"), AdminUser.email.ilike(f"%{search}%")))
    total = q.count()
    users = q.offset((page - 1) * size).limit(size).all()
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
    db: Session = Depends(get_db_session),
):
    """创建管理员用户"""
    if db.query(AdminUser).filter(AdminUser.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(AdminUser).filter(AdminUser.email == body.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    user = AdminUser(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
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
    db: Session = Depends(get_db_session),
):
    """更新管理员用户"""
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    db.commit()
    db.refresh(user)
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
    db: Session = Depends(get_db_session),
):
    """客户用户列表"""
    q = db.query(ClientUser)
    if search:
        q = q.filter(or_(ClientUser.username.ilike(f"%{search}%"), ClientUser.email.ilike(f"%{search}%")))
    total = q.count()
    users = q.offset((page - 1) * size).limit(size).all()
    
    # 获取每个客户的API密钥
    from src.db.models import APIKey
    responses = []
    for u in users:
        # 查找客户的API密钥
        api_key = db.query(APIKey).filter(APIKey.client_user_id == u.id).first()
        api_key_str = api_key.key_plaintext if api_key else "未生成"
        
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
    db: Session = Depends(get_db_session),
):
    """创建客户用户"""
    if db.query(ClientUser).filter(ClientUser.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if body.email and db.query(ClientUser).filter(ClientUser.email == body.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    user = ClientUser(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ClientUserResponse(
        id=user.id, 
        username=user.username, 
        email=user.email, 
        role=user.role, 
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.put("/clients/{user_id}", response_model=ClientUserResponse)
def update_client_user(
    user_id: int,
    body: UserUpdate,
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """更新客户用户"""
    user = db.query(ClientUser).filter(ClientUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return ClientUserResponse(
        id=user.id, 
        username=user.username, 
        email=user.email, 
        role=user.role, 
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.delete("/admins/{user_id}")
def delete_admin_user(
    user_id: int,
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """删除管理员用户"""
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


@router.delete("/clients/{user_id}")
def delete_client_user(
    user_id: int,
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """删除客户用户"""
    user = db.query(ClientUser).filter(ClientUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}