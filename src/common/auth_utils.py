# -*- coding: utf-8 -*-
"""JWT 认证工具"""
from datetime import datetime, timedelta
from typing import Any, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer

from src.common.config_utils import get_global_config

# 从配置读取 JWT 密钥与过期时间
def _get_jwt_config() -> dict:
    try:
        cfg = get_global_config()
        admin = cfg.get("admin_panel", {})
        return {
            "secret": admin.get("jwt_secret") or admin.get("session_secret") or "museum-agent-jwt-secret",
            "expire_seconds": admin.get("jwt_expire_seconds", 3600),
            "algorithm": "HS256",
        }
    except Exception:
        return {"secret": "museum-agent-jwt-secret", "expire_seconds": 3600, "algorithm": "HS256"}


def hash_password(password: str) -> str:
    """密码哈希"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    if not hashed or not plain:
        return False
    if hashed.startswith("$2"):
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    return plain == hashed


def create_access_token(
    subject: str,
    user_id: int,
    role: str = "admin",
    extra: Optional[dict] = None,
) -> str:
    """生成 JWT access_token"""
    cfg = _get_jwt_config()
    expire = datetime.utcnow() + timedelta(seconds=cfg["expire_seconds"])
    payload = {
        "sub": subject,
        "user_id": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(
        payload,
        cfg["secret"],
        algorithm=cfg["algorithm"],
    )


def decode_access_token(token: str) -> Optional[dict]:
    """解码并验证 JWT"""
    try:
        cfg = _get_jwt_config()
        return jwt.decode(
            token,
            cfg["secret"],
            algorithms=[cfg["algorithm"]],
        )
    except jwt.PyJWTError:
        return None


# FastAPI 依赖
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> dict:
    """依赖：从 Bearer token 解析当前用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
