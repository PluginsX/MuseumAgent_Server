# -*- coding: utf-8 -*-
"""
数据库服务层 - 统一的数据库操作接口

所有数据库操作必须通过此模块进行，禁止其他模块直接导入 database.py 或 models.py
遵循原则：模块化、低耦合、职责单一
"""
from typing import List, Optional, Dict, Any, Generator
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from src.db.database import get_engine, SessionLocal, init_db
from src.db.models import AdminUser, ClientUser, ServerAccessLog


# ==================== 数据库连接管理 ====================

def get_db_engine():
    """获取数据库引擎"""
    return get_engine()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """获取数据库会话上下文管理器"""
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
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库表结构"""
    init_db()


# ==================== 管理员用户服务 ====================

def create_admin_user(
    username: str,
    email: str,
    password_hash: str,
    role: str = "admin",
    is_active: bool = True
) -> AdminUser:
    """创建管理员用户"""
    with get_db_context() as db:
        user = AdminUser(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=is_active
        )
        db.add(user)
        db.flush()
        db.refresh(user)
        db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def get_admin_user_by_id(user_id: int) -> Optional[AdminUser]:
    """根据ID获取管理员用户"""
    with get_db_context() as db:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if user:
            db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def get_admin_user_by_username(username: str) -> Optional[AdminUser]:
    """根据用户名获取管理员用户"""
    with get_db_context() as db:
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if user:
            db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def get_admin_user_by_email(email: str) -> Optional[AdminUser]:
    """根据邮箱获取管理员用户"""
    with get_db_context() as db:
        user = db.query(AdminUser).filter(AdminUser.email == email).first()
        if user:
            db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def update_admin_user(
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    password_hash: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    last_login: Optional[datetime] = None
) -> Optional[AdminUser]:
    """更新管理员用户"""
    with get_db_context() as db:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            return None
        
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if password_hash is not None:
            user.password_hash = password_hash
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if last_login is not None:
            user.last_login = last_login
        
        db.flush()
        db.refresh(user)
        db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def delete_admin_user(user_id: int) -> bool:
    """删除管理员用户"""
    with get_db_context() as db:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            return False
        db.delete(user)
        return True


def list_admin_users(
    page: int = 1,
    size: int = 10,
    search: Optional[str] = None
) -> tuple[List[AdminUser], int]:
    """列出管理员用户（分页）"""
    with get_db_context() as db:
        query = db.query(AdminUser)
        
        if search:
            query = query.filter(
                or_(
                    AdminUser.username.ilike(f"%{search}%"),
                    AdminUser.email.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()
        
        # 从会话中分离所有用户对象，避免延迟加载问题
        for user in users:
            db.expunge(user)
        
        return users, total


# ==================== 客户用户服务 ====================

def create_client_user(
    username: str,
    password_hash: str,
    api_key: str,
    email: Optional[str] = None,
    role: str = "client",
    is_active: bool = True
) -> ClientUser:
    """创建客户用户"""
    with get_db_context() as db:
        user = ClientUser(
            username=username,
            email=email,
            password_hash=password_hash,
            api_key=api_key,
            role=role,
            is_active=is_active
        )
        db.add(user)
        db.flush()
        db.refresh(user)
        db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def get_client_user_by_id(user_id: int) -> Optional[ClientUser]:
    """根据ID获取客户用户"""
    with get_db_context() as db:
        user = db.query(ClientUser).filter(ClientUser.id == user_id).first()
        if user:
            db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def get_client_user_by_username(username: str) -> Optional[ClientUser]:
    """根据用户名获取客户用户"""
    with get_db_context() as db:
        user = db.query(ClientUser).filter(ClientUser.username == username).first()
        if user:
            db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def get_client_user_by_api_key(api_key: str) -> Optional[ClientUser]:
    """根据API密钥获取客户用户"""
    with get_db_context() as db:
        user = db.query(ClientUser).filter(ClientUser.api_key == api_key).first()
        if user:
            db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def get_client_user_by_email(email: str) -> Optional[ClientUser]:
    """根据邮箱获取客户用户"""
    with get_db_context() as db:
        user = db.query(ClientUser).filter(ClientUser.email == email).first()
        if user:
            db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def update_client_user(
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    password_hash: Optional[str] = None,
    api_key: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    last_login: Optional[datetime] = None
) -> Optional[ClientUser]:
    """更新客户用户"""
    with get_db_context() as db:
        user = db.query(ClientUser).filter(ClientUser.id == user_id).first()
        if not user:
            return None
        
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if password_hash is not None:
            user.password_hash = password_hash
        if api_key is not None:
            user.api_key = api_key
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if last_login is not None:
            user.last_login = last_login
        
        db.flush()
        db.refresh(user)
        db.expunge(user)  # 从会话中分离对象，避免延迟加载问题
        return user


def delete_client_user(user_id: int) -> bool:
    """删除客户用户"""
    with get_db_context() as db:
        user = db.query(ClientUser).filter(ClientUser.id == user_id).first()
        if not user:
            return False
        db.delete(user)
        return True


def list_client_users(
    page: int = 1,
    size: int = 10,
    search: Optional[str] = None
) -> tuple[List[ClientUser], int]:
    """列出客户用户（分页）"""
    with get_db_context() as db:
        query = db.query(ClientUser)
        
        if search:
            query = query.filter(
                or_(
                    ClientUser.username.ilike(f"%{search}%"),
                    ClientUser.email.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()
        
        # 从会话中分离所有用户对象，避免延迟加载问题
        for user in users:
            db.expunge(user)
        
        return users, total


# ==================== 访问日志服务 ====================

def create_access_log(
    request_type: str,
    endpoint: str,
    status_code: int,
    admin_user_id: Optional[int] = None,
    client_user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    response_time: Optional[int] = None,
    details: Optional[str] = None
) -> ServerAccessLog:
    """创建访问日志"""
    with get_db_context() as db:
        log = ServerAccessLog(
            admin_user_id=admin_user_id,
            client_user_id=client_user_id,
            request_type=request_type,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            response_time=response_time,
            details=details
        )
        db.add(log)
        db.flush()
        db.refresh(log)
        return log


def batch_create_access_logs(logs: List[Dict[str, Any]]) -> int:
    """批量创建访问日志"""
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            # 构建批量插入参数
            values_list = []
            params = {}
            
            for i, record in enumerate(logs):
                values = {
                    'admin_user_id': record.get('admin_user_id'),
                    'client_user_id': record.get('client_user_id'),
                    'request_type': record.get('request_type'),
                    'endpoint': record.get('endpoint'),
                    'ip_address': record.get('ip_address'),
                    'user_agent': record.get('user_agent'),
                    'status_code': record.get('status_code'),
                    'response_time': record.get('response_time'),
                    'details': record.get('details'),
                    'created_at': record.get('created_at', datetime.now())
                }
                
                # 为每条记录构建占位符
                placeholders = []
                for k, v in values.items():
                    param_name = f"{k}_{i}"
                    placeholders.append(f":{param_name}")
                    params[param_name] = v
                
                values_list.append(f"({', '.join(placeholders)})")
            
            # 构建完整的SQL语句
            columns = ', '.join(['admin_user_id', 'client_user_id', 'request_type', 'endpoint', 
                                'ip_address', 'user_agent', 'status_code', 'response_time', 
                                'details', 'created_at'])
            values_part = ', '.join(values_list)
            sql = f"INSERT INTO server_access_logs ({columns}) VALUES {values_part}"
            
            # 执行插入
            connection.execute(text(sql), params)
            connection.commit()
            
            return len(logs)
    except Exception:
        # 失败时尝试逐条插入
        success_count = 0
        with engine.connect() as connection:
            for record in logs:
                try:
                    values = {
                        'admin_user_id': record.get('admin_user_id'),
                        'client_user_id': record.get('client_user_id'),
                        'request_type': record.get('request_type'),
                        'endpoint': record.get('endpoint'),
                        'ip_address': record.get('ip_address'),
                        'user_agent': record.get('user_agent'),
                        'status_code': record.get('status_code'),
                        'response_time': record.get('response_time'),
                        'details': record.get('details'),
                        'created_at': record.get('created_at', datetime.now())
                    }
                    
                    columns = ', '.join(values.keys())
                    placeholders = ', '.join([f":{k}" for k in values.keys()])
                    sql = f"INSERT INTO server_access_logs ({columns}) VALUES ({placeholders})"
                    
                    connection.execute(text(sql), values)
                    success_count += 1
                except Exception:
                    continue
            
            connection.commit()
        
        return success_count


def query_access_logs(
    page: int = 1,
    size: int = 10,
    admin_user_id: Optional[int] = None,
    client_user_id: Optional[int] = None,
    request_type: Optional[str] = None
) -> tuple[List[ServerAccessLog], int]:
    """查询访问日志（分页）"""
    with get_db_context() as db:
        query = db.query(ServerAccessLog)
        
        if admin_user_id is not None:
            query = query.filter(ServerAccessLog.admin_user_id == admin_user_id)
        if client_user_id is not None:
            query = query.filter(ServerAccessLog.client_user_id == client_user_id)
        if request_type is not None:
            query = query.filter(ServerAccessLog.request_type == request_type)
        
        total = query.count()
        logs = query.order_by(ServerAccessLog.created_at.desc()).offset((page - 1) * size).limit(size).all()
        
        return logs, total

