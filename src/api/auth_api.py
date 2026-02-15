# -*- coding: utf-8 -*-
"""认证 API：登录、刷新、当前用户"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.common.auth_utils import (
    create_access_token,
    get_current_user,
    verify_password,
)
from src.db.database import get_db_session
from src.db.models import AdminUser

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
def login(
    body: LoginRequest,
    db: Session = Depends(get_db_session),
):
    """登录，返回 JWT"""
    user = db.query(AdminUser).filter(AdminUser.username == body.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    user.last_login = datetime.utcnow()
    db.commit()
    from src.common.auth_utils import _get_jwt_config
    cfg = _get_jwt_config()  # noqa: F811
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
def get_me(payload: dict = Depends(get_current_user), db: Session = Depends(get_db_session)):
    """获取当前用户信息"""
    user_id = payload.get("user_id")
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserInfoResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        last_login=user.last_login,
    )
