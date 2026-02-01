# -*- coding: utf-8 -*-
"""数据库连接与会话"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.common.config_utils import get_global_config

# 默认使用项目 data 目录下的 SQLite
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_default_db_path = os.path.join(_project_root, "data", "museum_agent_app.db")


_engine = None
_SessionLocal = None


def get_engine():
    """获取数据库引擎（懒加载）"""
    global _engine
    if _engine is None:
        try:
            config = get_global_config()
            kb = config.get("artifact_knowledge_base", {})
            db_path = kb.get("app_db_path") or _default_db_path
        except Exception:
            db_path = _default_db_path
        if not os.path.isabs(db_path):
            db_path = os.path.normpath(os.path.join(_project_root, db_path))
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        url = f"sqlite:///{db_path}"
        _engine = create_engine(url, connect_args={"check_same_thread": False}, echo=False)
    return _engine


def _get_session_factory():
    """获取 Session 工厂（内部）"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def SessionLocal() -> Session:
    """创建新的数据库会话"""
    return _get_session_factory()()


def init_db():
    """初始化表结构"""
    # 延迟导入，避免循环导入
    from src.db.models import Base
    Base.metadata.create_all(bind=get_engine())


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（上下文管理器）"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI 依赖：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
