# -*- coding: utf-8 -*-
"""数据库模块"""
from src.db.database import get_db, get_engine, init_db
from src.db.models import AdminUser, ClientUser, Configuration, ConfigHistory, SystemLog

# 直接从sqlalchemy导入Base
from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__ = [
    "Base",
    "get_engine",
    "get_db",
    "init_db",
    "AdminUser",
    "ClientUser",
    "Configuration",
    "ConfigHistory",
    "SystemLog",
]
