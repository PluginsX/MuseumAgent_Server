# -*- coding: utf-8 -*-
"""
会话管理服务模块
管理用户会话和认证
"""
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from passlib.context import CryptContext

from src.common.log_utils import get_logger
from src.common.log_formatter import log_step, log_communication
from src.common.config_utils import get_global_config


class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        """初始化会话管理服务"""
        self.logger = get_logger()
        self.config = get_global_config()
        
        # JWT配置
        admin_config = self.config.get("admin_panel", {})
        self.jwt_secret = admin_config.get("jwt_secret", "museum-agent-jwt-secret-change-in-production")
        self.jwt_expire_seconds = admin_config.get("jwt_expire_seconds", 3600)
        
        # 密码哈希配置
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # 存储活跃会话
        self.active_sessions = {}
        
        # 用户数据（实际应用中应使用数据库）
        # 延迟初始化用户数据，避免在构造函数中进行哈希计算
        self._users = None

    @property
    def users(self):
        """懒加载用户数据"""
        if self._users is None:
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
        self.logger.info(f"用户登录尝试: {credentials.get('username', 'unknown')}")
        
        try:
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            
            # 记录客户端消息接收
            print(log_communication('SESSION_SERVICE', 'RECEIVE', '登录请求', 
                                   {'username': username}))
            
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
                data={"sub": username, "session_id": f"sess_{secrets.token_hex(16)}"}
            )
            
            # 创建会话
            session_id = f"sess_{secrets.token_hex(16)}"
            session_data = {
                "session_id": session_id,
                "username": username,
                "login_time": datetime.now(),
                "expires_at": datetime.now() + timedelta(seconds=self.jwt_expire_seconds),
                "active": True
            }
            
            self.active_sessions[session_id] = session_data
            
            # 构建响应
            result = {
                "code": 200,
                "msg": "登录成功",
                "data": {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "session_id": session_id,
                    "expires_in": self.jwt_expire_seconds
                },
                "timestamp": datetime.now().isoformat()
            }
            
            print(log_step('SESSION_SERVICE', 'SUCCESS', '用户登录成功', 
                          {'username': username, 'session_id': session_id}))
            return result
            
        except Exception as e:
            self.logger.error(f"登录失败: {str(e)}")
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
            
            print(log_step('SESSION_SERVICE', 'SUCCESS', '获取用户信息成功', 
                          {'username': username}))
            return result
            
        except jwt.ExpiredSignatureError:
            return {
                "code": 401,
                "msg": "令牌已过期",
                "data": None
            }
        except jwt.JWTError:
            return {
                "code": 401,
                "msg": "无效的令牌",
                "data": None
            }
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"获取用户信息失败: {str(e)}",
                "data": None
            }
    
    async def validate_session(self, session_id: str) -> bool:
        """
        验证会话有效性
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话是否有效
        """
        if session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        
        # 检查会话是否过期
        if datetime.now() > session_data["expires_at"]:
            # 清理过期会话
            del self.active_sessions[session_id]
            return False
        
        return session_data["active"]
    
    async def logout(self, session_id: str) -> Dict[str, Any]:
        """
        用户登出
        
        Args:
            session_id: 会话ID
            
        Returns:
            登出结果
        """
        try:
            if session_id in self.active_sessions:
                # 标记会话为非活跃
                self.active_sessions[session_id]["active"] = False
                # 可选：立即删除会话
                del self.active_sessions[session_id]
            
            result = {
                "code": 200,
                "msg": "登出成功",
                "data": {"session_id": session_id},
                "timestamp": datetime.now().isoformat()
            }
            
            print(log_step('SESSION_SERVICE', 'SUCCESS', '用户登出成功', 
                          {'session_id': session_id}))
            return result
            
        except Exception as e:
            self.logger.error(f"登出失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"登出失败: {str(e)}",
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
            
            print(log_step('SESSION_SERVICE', 'SUCCESS', '会话刷新成功', 
                          {'username': username}))
            return result
            
        except jwt.ExpiredSignatureError:
            return {
                "code": 401,
                "msg": "令牌已过期，需要重新登录",
                "data": None
            }
        except jwt.JWTError:
            return {
                "code": 401,
                "msg": "无效的令牌",
                "data": None
            }
        except Exception as e:
            self.logger.error(f"会话刷新失败: {str(e)}")
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
            if session_id not in self.active_sessions:
                return {
                    "code": 404,
                    "msg": "会话不存在",
                    "data": None
                }
            
            session_data = self.active_sessions[session_id]
            
            # 计算剩余有效期
            remaining_time = (session_data["expires_at"] - datetime.now()).total_seconds()
            
            result = {
                "code": 200,
                "msg": "获取会话信息成功",
                "data": {
                    "session_id": session_data["session_id"],
                    "username": session_data["username"],
                    "login_time": session_data["login_time"].isoformat(),
                    "expires_at": session_data["expires_at"].isoformat(),
                    "remaining_seconds": max(0, int(remaining_time)),
                    "active": session_data["active"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取会话信息失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"获取会话信息失败: {str(e)}",
                "data": None
            }