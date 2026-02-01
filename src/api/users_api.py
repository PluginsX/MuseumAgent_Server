# -*- coding: utf-8 -*-
"""用户管理 API"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.common.auth_utils import get_current_user, hash_password
from src.db.database import get_db_session
from src.db.models import User

router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    role: str = "admin"


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool


@router.get("", response_model=List[UserResponse])
def list_users(
    _: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    """用户列表"""
    q = db.query(User)
    if search:
        q = q.filter(or_(User.username.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))
    total = q.count()
    users = q.offset((page - 1) * size).limit(size).all()
    return [UserResponse(id=u.id, username=u.username, email=u.email, role=u.role, is_active=u.is_active) for u in users]


@router.post("", response_model=UserResponse)
def create_user(
    body: UserCreate,
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """创建用户"""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if body.email and db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(id=user.id, username=user.username, email=user.email, role=user.role, is_active=user.is_active)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    body: UserUpdate,
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
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
    return UserResponse(id=user.id, username=user.username, email=user.email, role=user.role, is_active=user.is_active)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"deleted": user_id}
