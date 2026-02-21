# -*- coding: utf-8 -*-
"""SQLAlchemy 模型 - 按照设计文档实现独立的管理员和客户用户表"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# 直接从sqlalchemy导入Base
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AdminUser(Base):
    """管理员用户表 - 按照设计文档创建独立表"""
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
    """客户用户表 - 按照设计文档创建独立表"""
    __tablename__ = "client_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)  # 客户邮箱可选
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="client", nullable=False)  # client
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class APIKey(Base):
    """API密钥表 - 关联到客户用户"""
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    key_plaintext: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # 存储明文API密钥
    client_user_id: Mapped[int] = mapped_column(ForeignKey("client_users.id"), nullable=False)  # 仅关联客户用户
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class AuditLog(Base):
    """审计日志表 - 可关联到管理员或客户用户"""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"), nullable=True)  # 管理员操作
    client_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("client_users.id"), nullable=True)  # 客户操作
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Configuration(Base):
    """配置表"""
    __tablename__ = "configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    config_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"), nullable=True)  # 由管理员创建
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ConfigHistory(Base):
    """配置历史表"""
    __tablename__ = "config_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_id: Mapped[Optional[int]] = mapped_column(ForeignKey("configurations.id"), nullable=True)
    old_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"), nullable=True)  # 由管理员修改
    change_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    module: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    admin_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"), nullable=True)
    client_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("client_users.id"), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())