# -*- coding: utf-8 -*-
"""
会话服务适配器
将StrictSessionManager适配为服务注册表可用的SessionService
"""
from typing import Dict, Any, Optional
from datetime import datetime

from src.session.strict_session_manager import strict_session_manager
from src.common.enhanced_logger import get_enhanced_logger


class SessionServiceAdapter:
    """会话服务适配器 - 将StrictSessionManager包装为服务"""
    
    def __init__(self):
        """初始化会话服务适配器"""
        self.logger = get_enhanced_logger()
        self.strict_manager = strict_session_manager  # 使用全局实例
    
    @property
    def active_sessions(self):
        """提供active_sessions属性以兼容原有代码"""
        # 返回一个模拟的active_sessions字典，键为活跃会话ID
        active_sessions_dict = {}
        with self.strict_manager._lock:  # 使用内部锁确保线程安全
            for session_id, session in self.strict_manager.sessions.items():
                if session.is_active():
                    active_sessions_dict[session_id] = session  # 可以返回session对象或简单的占位符
        return active_sessions_dict
    
    async def validate_session(self, session_id: str) -> bool:
        """
        验证会话是否有效
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话是否有效
        """
        try:
            session = self.strict_manager.validate_session(session_id)
            is_valid = session is not None
            self.logger.sess.info(f'Session validation result: {is_valid}', 
                          {'session_id': session_id[:8] if session_id else None})
            return is_valid
        except Exception as e:
            self.logger.sys.error(f"会话验证异常: {str(e)}")
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息或None
        """
        try:
            session = self.strict_manager.validate_session(session_id)
            if session:
                return {
                    "session_id": session.session_id,
                    "client_metadata": session.client_metadata,
                    "created_at": session.created_at.isoformat(),
                    "last_heartbeat": session.last_heartbeat.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "is_active": session.is_active()
                }
            return None
        except Exception as e:
            self.logger.sys.error(f"获取会话信息异常: {str(e)}")
            return None
    
    async def update_session_activity(self, session_id: str) -> bool:
        """
        更新会话活动时间
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否更新成功
        """
        try:
            session = self.strict_manager.validate_session(session_id)
            if session:
                session.update_activity()
                self.logger.sess.info('Update session activity time', 
                              {'session_id': session_id[:8]})
                return True
            return False
        except Exception as e:
            self.logger.sys.error(f"更新会话活动时间异常: {str(e)}")
            return False