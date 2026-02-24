# -*- coding: utf-8 -*-
"""客户API层 - 供智能体服务器本地调用（已迁移到database_service）"""
from datetime import datetime
from typing import Optional, Dict, Any

from src.common.auth_utils import verify_password
from src.services import database_service
from src.common.enhanced_logger import get_enhanced_logger


class ClientLocalAPI:
    def __init__(self):
        self.logger = get_enhanced_logger()
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

            # 使用 database_service 进行认证
            if auth_type == "API_KEY":
                # 通过API密钥获取客户用户
                user = database_service.get_client_user_by_api_key(auth_value)
                
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
                # 首先在客户用户中查找
                user = database_service.get_client_user_by_username(auth_value)
                
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
                
                # 如果在客户用户中没找到，再在管理员用户中查找
                admin_user = database_service.get_admin_user_by_username(auth_value)
                
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
            user = database_service.get_client_user_by_id(client_id)
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
            # 首先尝试更新客户用户
            user = database_service.update_client_user(client_id, last_login=datetime.utcnow())
            if user:
                return True
            
            # 如果客户用户更新失败，尝试更新管理员用户
            admin_user = database_service.update_admin_user(client_id, last_login=datetime.utcnow())
            if admin_user:
                return True
                
            return False
        except Exception as e:
            self.logger.auth.error(f"Update client login info error: {str(e)}")
            return False