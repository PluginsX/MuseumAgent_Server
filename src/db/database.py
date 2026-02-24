# -*- coding: utf-8 -*-
"""数据库连接与会话 - 支持MySQL和SQLite"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.common.config_utils import get_global_ini_config

# 默认使用项目 data 目录下的 SQLite
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_default_db_path = os.path.join(_project_root, "data", "museum_agent_app.db")


_engine = None
_SessionLocal = None


def get_engine():
    """获取数据库引擎（懒加载，支持MySQL和SQLite）"""
    global _engine
    if _engine is None:
        try:
            # 从INI配置文件获取数据库配置
            ini_config = get_global_ini_config()
            
            # 获取数据库类型
            db_type = ini_config.get('database', 'db_type', fallback='sqlite').lower()
            
            if db_type == 'mysql':
                # 使用MySQL配置
                mysql_host = ini_config.get('database', 'mysql_host', fallback='127.0.0.1')
                mysql_port = ini_config.getint('database', 'mysql_port', fallback=3306)
                mysql_user = ini_config.get('database', 'mysql_user', fallback='root')
                mysql_password = ini_config.get('database', 'mysql_password', fallback='')
                mysql_db = ini_config.get('database', 'mysql_db', fallback='museum_artifact')
                mysql_charset = ini_config.get('database', 'mysql_charset', fallback='utf8mb4')
                mysql_pool_size = ini_config.getint('database', 'mysql_pool_size', fallback=10)
                mysql_pool_recycle = ini_config.getint('database', 'mysql_pool_recycle', fallback=3600)
                
                url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}?charset={mysql_charset}"
                _engine = create_engine(
                    url,
                    pool_size=mysql_pool_size,
                    pool_recycle=mysql_pool_recycle,
                    pool_pre_ping=True,  # 自动检测连接是否有效
                    echo=False
                )
                print(f"[数据库] 使用MySQL数据库: {mysql_host}:{mysql_port}/{mysql_db}")
            else:
                # 使用SQLite配置（默认）
                sqlite_path = ini_config.get('database', 'sqlite_path', fallback=_default_db_path)
                if not os.path.isabs(sqlite_path):
                    sqlite_path = os.path.normpath(os.path.join(_project_root, sqlite_path))
                os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
                url = f"sqlite:///{sqlite_path}"
                _engine = create_engine(url, connect_args={"check_same_thread": False}, echo=False)
                print(f"[数据库] 使用SQLite数据库: {sqlite_path}")
                
        except Exception as e:
            # 异常时使用默认SQLite
            print(f"[数据库] 配置错误，使用默认SQLite: {e}")
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
    from sqlalchemy import create_engine, text
    
    # 先检查是否需要创建MySQL数据库
    try:
        ini_config = get_global_ini_config()
        db_type = ini_config.get('database', 'db_type', fallback='sqlite').lower()
        
        if db_type == 'mysql':
            mysql_host = ini_config.get('database', 'mysql_host', fallback='127.0.0.1')
            mysql_port = ini_config.getint('database', 'mysql_port', fallback=3306)
            mysql_user = ini_config.get('database', 'mysql_user', fallback='root')
            mysql_password = ini_config.get('database', 'mysql_password', fallback='')
            mysql_db = ini_config.get('database', 'mysql_db', fallback='museum_artifact')
            mysql_charset = ini_config.get('database', 'mysql_charset', fallback='utf8mb4')
            
            # 连接到MySQL服务器（不指定数据库）
            server_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}?charset={mysql_charset}"
            server_engine = create_engine(server_url, echo=False)
            
            # 创建数据库（如果不存在）
            with server_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{mysql_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
            
            server_engine.dispose()
            print(f"[数据库] MySQL数据库 '{mysql_db}' 已就绪")
    except Exception as e:
        print(f"[数据库] 创建MySQL数据库失败: {e}")
    
    # 然后创建表结构
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


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
