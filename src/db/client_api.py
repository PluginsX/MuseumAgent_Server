# -*- coding: utf-8 -*-
"""客户API层 - 供智能体服务器本地调用"""
from datetime import datetime
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.common.auth_utils import hash_password, verify_password
from src.db.database import SessionLocal
from src.db.models import ClientUser
from src.common.enhanced_logger import get_enhanced_logger


class ClientLocalAPI:
    def __init__(self):
        self.logger = get_enhanced_logger()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # 简单的内存缓存
        self.cache = {}

    def verify_client_auth(self, auth_type: str, auth_value: str, password: str = None, ip: str = None) -> Optional[Dict[str, Any]]:
        """智能体服务器-客户认证（WebSocket注册阶段）"""
        try:
            # 检查缓存
            cache_key = f"{auth_type}:{auth_value}"
            if cache_key in self.cache:
                cached_item = self.cache[cache_key]
                # 检查缓存是否过期（5分钟）
                if datetime.now().timestamp() - cached_item['timestamp'] < 300:
                    return cached_item['data']

            # 从数据库查询
            with SessionLocal() as db:
                if auth_type == "API_KEY":
                    # 直接在ClientUser表中查找API密钥
                    user = db.query(ClientUser).filter(
                        and_(ClientUser.api_key == auth_value, ClientUser.is_active == True)
                    ).first()
                    
                    if user:
                        result = {
                            "user_id": user.id,
                            "username": user.username,
                            "role": user.role,
                            "is_authenticated": True
                        }
                        # 缓存认证结果
                        self.cache[cache_key] = {
                            'data': result,
                            'timestamp': datetime.now().timestamp()
                        }
                        return result
                elif auth_type == "ACCOUNT":
                    # 账号密码认证
                    # 首先在client_users表中查找
                    user = db.query(ClientUser).filter(
                        and_(ClientUser.username == auth_value, ClientUser.is_active == True)
                    ).first()
                    
                    if user and verify_password(password, user.password_hash):
                        result = {
                            "user_id": user.id,
                            "username": user.username,
                            "role": user.role,
                            "is_authenticated": True
                        }
                        # 缓存认证结果
                        self.cache[cache_key] = {
                            'data': result,
                            'timestamp': datetime.now().timestamp()
                        }
                        return result
                    
                    # 如果在client_users表中没找到，再在admin_users表中查找
                    from src.db.models import AdminUser
                    admin_user = db.query(AdminUser).filter(
                        and_(AdminUser.username == auth_value, AdminUser.is_active == True)
                    ).first()
                    
                    if admin_user and verify_password(password, admin_user.password_hash):
                        result = {
                            "user_id": admin_user.id,
                            "username": admin_user.username,
                            "role": admin_user.role,
                            "is_authenticated": True
                        }
                        # 缓存认证结果
                        self.cache[cache_key] = {
                            'data': result,
                            'timestamp': datetime.now().timestamp()
                        }
                        return result

            # 认证失败
            return None
            
        except Exception as e:
            self.logger.auth.error(f"Client authentication error: {str(e)}")
            return None

    def get_client_session_data(self, client_id: str) -> Dict[str, Any]:
        """获取客户会话数据（仅读user_data）"""
        try:
            with SessionLocal() as db:
                user = db.query(ClientUser).filter(ClientUser.id == client_id).first()
                if user:
                    # 返回用户的基本信息用于会话
                    return {
                        "username": user.username,
                        "role": user.role,
                        "email": user.email
                    }
                return {}
        except Exception as e:
            self.logger.auth.error(f"Get client session data error: {str(e)}")
            return {}

    def update_client_login_info(self, client_id: str, ip: str):
        """更新客户登陆信息 - 支持客户用户和管理员用户"""
        try:
            with SessionLocal() as db:
                # 首先尝试在ClientUser表中查找
                user = db.query(ClientUser).filter(ClientUser.id == client_id).first()
                if user:
                    user.last_login = datetime.utcnow()
                    db.commit()
                    return True
                
                # 如果在ClientUser表中没找到，尝试在AdminUser表中查找
                from src.db.models import AdminUser
                admin_user = db.query(AdminUser).filter(AdminUser.id == client_id).first()
                if admin_user:
                    admin_user.last_login = datetime.utcnow()
                    db.commit()
                    return True
                    
                return False
        except Exception as e:
            self.logger.auth.error(f"Update client login info error: {str(e)}")
            return False