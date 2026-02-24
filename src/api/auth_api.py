# -*- coding: utf-8 -*-
"""认证 API：登录、刷新、当前用户"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.common.auth_utils import (
    create_access_token,
    get_current_user,
    verify_password,
)
from src.services import database_service

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfoResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    last_login: Optional[datetime]


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """登录，返回 JWT"""
    user = database_service.get_admin_user_by_username(body.username)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 更新最后登录时间
    database_service.update_admin_user(user.id, last_login=datetime.now())
    
    from src.common.auth_utils import _get_jwt_config
    cfg = _get_jwt_config()
    token = create_access_token(
        subject=user.username,
        user_id=user.id,
        role=user.role,
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=cfg["expire_seconds"],
    )


@router.get("/me", response_model=UserInfoResponse)
def get_me(payload: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    user_id = payload.get("user_id")
    user = database_service.get_admin_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserInfoResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        last_login=user.last_login,
    )
