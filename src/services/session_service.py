# -*- coding: utf-8 -*-
"""
会话管理服务模块
管理用户会话和认证 - 现在统一使用StrictSessionManager
"""
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from passlib.context import CryptContext

from src.common.enhanced_logger import get_enhanced_logger
from src.common.config_utils import get_global_config
from src.session.strict_session_manager import strict_session_manager


class SessionService:
    """会话管理服务 - 现在整合了StrictSessionManager功能"""
    
    def __init__(self):
        """初始化会话管理服务"""
        self.logger = get_enhanced_logger()
        self.config = get_global_config()
        
        # JWT配置
        admin_config = self.config.get("admin_panel", {})
        self.jwt_secret = admin_config.get("jwt_secret", "museum-agent-jwt-secret-change-in-production")
        self.jwt_expire_seconds = admin_config.get("jwt_expire_seconds", 3600)
        
        # 密码哈希配置
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # 现在使用统一的StrictSessionManager，不再维护本地active_sessions
        # self.active_sessions = {}

    @property
    def active_sessions(self):
        """提供active_sessions属性以兼容原有代码，但现在使用StrictSessionManager的数据"""
        # 返回StrictSessionManager中的活跃会话
        return strict_session_manager.get_all_sessions()

    @property
    def users(self):
        """懒加载用户数据"""
        if not hasattr(self, '_users'):
            # 为避免bcrypt长度限制，使用较短的密码或备用哈希算法
            try:
                hashed_password = self.pwd_context.hash("123")  # 默认密码
            except ValueError:
                # 如果bcrypt失败，使用SHA256作为备选方案
                import hashlib
                hashed_password = hashlib.sha256("123".encode()).hexdigest()
            
            self._users = {
                "123": {  # 默认用户名
                    "username": "123",
                    "hashed_password": hashed_password,
                    "active": True
                }
            }
        return self._users
    
    async def login(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            credentials: 登录凭据 {"username": "...", "password": "..."}
            
        Returns:
            登录结果
        """
        self.logger.sess.info('User login attempt', {'username': credentials.get('username', 'unknown')})
        
        try:
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            
            # 记录客户端消息接收
            self.logger.sess.info('Received login request', 
                                   {'username': username})
            
            # 验证用户凭据
            user = await self._authenticate_user(username, password)
            if not user:
                return {
                    "code": 401,
                    "msg": "用户名或密码错误",
                    "data": None
                }
            
            # 生成JWT令牌
            access_token = await self._create_access_token(
                data={"sub": username}
            )
            
            # 构建响应 - 不包含session_id，会话必须通过/api/session/register单独注册
            result = {
                "code": 200,
                "msg": "登录成功，请调用/api/session/register注册会话",
                "data": {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": self.jwt_expire_seconds
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.sess.info('User login successful', 
                          {'username': username})
            return result
            
        except Exception as e:
            self.logger.sess.error('Login failed', {'error': str(e)})
            return {
                "code": 500,
                "msg": f"登录失败: {str(e)}",
                "data": None
            }
    
    async def _authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户凭据"""
        if username in self.users:
            user = self.users[username]
            if user["active"]:
                # 尝试使用bcrypt验证
                try:
                    if self.pwd_context.verify(password, user["hashed_password"]):
                        return user
                except ValueError:
                    # 如果bcrypt验证失败，尝试SHA256验证
                    import hashlib
                    expected_hash = hashlib.sha256(password.encode()).hexdigest()
                    if expected_hash == user["hashed_password"]:
                        return user
        return None
    
    async def _create_access_token(self, data: Dict[str, Any]) -> str:
        """创建JWT访问令牌"""
        to_encode = data.copy()
        expire = datetime.now() + timedelta(seconds=self.jwt_expire_seconds)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm="HS256")
        return encoded_jwt
    
    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            token: 认证令牌
            
        Returns:
            用户信息
        """
        try:
            # 解码JWT令牌
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            username = payload.get("sub")
            
            if username not in self.users:
                return {
                    "code": 401,
                    "msg": "用户不存在",
                    "data": None
                }
            
            user = self.users[username]
            
            # 构建响应
            result = {
                "code": 200,
                "msg": "获取用户信息成功",
                "data": {
                    "username": user["username"],
                    "active": user["active"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.sess.info('User information retrieved successfully', 
                          {'username': username})
            return result
            
        except jwt.ExpiredSignatureError:
            return {
                "code": 401,
                "msg": "令牌已过期",
                "data": None
            }
        except Exception:
            return {
                "code": 401,
                "msg": "无效的令牌",
                "data": None
            }
        except Exception as e:
            self.logger.sess.error('Get user info failed', {'error': str(e)})
            return {
                "code": 500,
                "msg": f"获取用户信息失败: {str(e)}",
                "data": None
            }
    
    async def validate_session(self, session_id: str) -> bool:
        """
        验证会话有效性 - 现在使用StrictSessionManager
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话是否有效
        """
        # 现在使用统一的StrictSessionManager进行验证
        session = strict_session_manager.validate_session(session_id)
        is_valid = session is not None
        self.logger.sess.info(f'Session validation result: {is_valid}', 
                      {'session_id': session_id[:8] if session_id else None})
        return is_valid
    
    async def logout(self, session_id: str) -> Dict[str, Any]:
        """
        用户登出
        
        Args:
            session_id: 会话ID
            
        Returns:
            登出结果
        """
        try:
            # 使用StrictSessionManager注销会话
            success = strict_session_manager.unregister_session(session_id)
            
            result = {
                "code": 200,
                "msg": "登出成功",
                "data": {"session_id": session_id, "unregistered": success},
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.sess.info('User logout successful', 
                          {'session_id': session_id, 'success': success})
            return result
            
        except Exception as e:
            self.logger.sess.error('Logout failed', {'error': str(e)})
            return {
                "code": 500,
                "msg": f"登出失败: {str(e)}",
                "data": None
            }
    
    async def get_session_operations(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的操作集合（兼容旧版API）
        
        Args:
            session_id: 会话ID
            
        Returns:
            操作集合
        """
        try:
            operations = strict_session_manager.get_operation_set_for_session(session_id)
            
            result = {
                "code": 200,
                "msg": "获取操作集合成功",
                "data": {
                    "session_id": session_id,
                    "operations": operations
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.sess.info('Session operations retrieved', 
                          {'session_id': session_id, 'operation_count': len(operations)})
            return result
            
        except Exception as e:
            self.logger.sess.error('Get session operations failed', {'error': str(e)})
            return {
                "code": 500,
                "msg": f"获取操作集合失败: {str(e)}",
                "data": None
            }
    
    async def get_session_functions(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的函数定义
        
        Args:
            session_id: 会话ID
            
        Returns:
            函数定义列表
        """
        try:
            functions = strict_session_manager.get_functions_for_session(session_id)
            
            result = {
                "code": 200,
                "msg": "获取函数定义成功",
                "data": {
                    "session_id": session_id,
                    "functions": functions
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.sess.info('Session functions retrieved', 
                          {'session_id': session_id, 'function_count': len(functions)})
            return result
            
        except Exception as e:
            self.logger.sess.error('Get session functions failed', {'error': str(e)})
            return {
                "code": 500,
                "msg": f"获取函数定义失败: {str(e)}",
                "data": None
            }
    
    async def refresh_session(self, token: str) -> Dict[str, Any]:
        """
        刷新会话
        
        Args:
            token: 当前令牌
            
        Returns:
            刷新结果
        """
        try:
            # 解码当前令牌
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            username = payload.get("sub")
            
            if username not in self.users:
                return {
                    "code": 401,
                    "msg": "用户不存在",
                    "data": None
                }
            
            # 生成新令牌
            new_token = await self._create_access_token(
                data={"sub": username, "session_id": payload.get("session_id")}
            )
            
            result = {
                "code": 200,
                "msg": "会话刷新成功",
                "data": {
                    "access_token": new_token,
                    "token_type": "bearer",
                    "expires_in": self.jwt_expire_seconds
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.sess.info('Session refreshed successfully', 
                          {'username': username})
            return result
            
        except jwt.ExpiredSignatureError:
            return {
                "code": 401,
                "msg": "令牌已过期，需要重新登录",
                "data": None
            }
        except Exception:
            return {
                "code": 401,
                "msg": "无效的令牌",
                "data": None
            }
        except Exception as e:
            self.logger.sess.error('Session refresh failed', {'error': str(e)})
            return {
                "code": 500,
                "msg": f"会话刷新失败: {str(e)}",
                "data": None
            }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息
        """
        try:
            # 使用strict_session_manager获取会话
            session = strict_session_manager.get_session(session_id)
            if not session:
                return {
                    "code": 404,
                    "msg": "会话不存在",
                    "data": None
                }
            
            # 计算剩余有效期
            remaining_time = (session.expires_at - datetime.now()).total_seconds()
            
            result = {
                "code": 200,
                "msg": "获取会话信息成功",
                "data": {
                    "session_id": session.session_id,
                    "username": session.client_metadata.get("user_id", "unknown"),
                    "login_time": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "remaining_seconds": max(0, int(remaining_time)),
                    "active": session.is_active()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.sess.error('Get session info failed', {'error': str(e)})
            return {
                "code": 500,
                "msg": f"获取会话信息失败: {str(e)}",
                "data": None
            }