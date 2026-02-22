# -*- coding: utf-8 -*-
"""SQLAlchemy 模型 - 简化版数据表结构"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# 直接从sqlalchemy导入Base
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AdminUser(Base):
    """管理员用户表 - 存储管理员账号数据"""
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="admin", nullable=False)  # admin, operator 等
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ClientUser(Base):
    """客户用户表 - 存储客户账号数据"""
    __tablename__ = "client_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)  # 客户邮箱可选
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)  # 存储明文API密钥
    role: Mapped[str] = mapped_column(String(20), default="client", nullable=False)  # client
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ServerAccessLog(Base):
    """服务器访问日志表 - 记录服务器访问记录"""
    __tablename__ = "server_access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"), nullable=True)  # 管理员操作
    client_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("client_users.id"), nullable=True)  # 客户操作
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 请求类型
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)  # 请求端点
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 用户代理
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)  # 状态码
    response_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 响应时间
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 详细信息
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())  # 请求时间