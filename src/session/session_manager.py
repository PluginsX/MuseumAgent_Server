# -*- coding: utf-8 -*-
"""
轻量级会话管理器
实现无外部依赖的会话级指令集管理
"""
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json


@dataclass
class ClientSession:
    """客户端会话数据结构"""
    session_id: str
    client_metadata: Dict[str, Any]
    operation_set: List[str]
    created_at: datetime
    last_heartbeat: datetime
    expires_at: datetime
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now() > self.expires_at
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
        # 延长会话有效期
        self.expires_at = datetime.now() + timedelta(minutes=15)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换datetime为字符串
        data['created_at'] = self.created_at.isoformat()
        data['last_heartbeat'] = self.last_heartbeat.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return data


class LightweightSessionManager:
    """轻量级会话管理器"""
    
    def __init__(self, session_timeout_minutes: int = 15):
        self.sessions: Dict[str, ClientSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._lock = threading.RLock()
        self._cleanup_thread = None
        self._running = False
        self._start_cleanup_daemon()
    
    def _start_cleanup_daemon(self):
        """启动清理守护线程"""
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_loop(self):
        """定期清理过期会话"""
        while self._running:
            time.sleep(60)  # 每分钟检查一次
            self._cleanup_expired_sessions()
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        with self._lock:
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if session.is_expired()
            ]
            for session_id in expired_sessions:
                del self.sessions[session_id]
                print(f"[SessionManager] Cleaned up expired session: {session_id}")
    
    def register_session(self, session_id: str, client_metadata: Dict[str, Any], 
                        operation_set: List[str]) -> ClientSession:
        """注册新会话"""
        with self._lock:
            session = ClientSession(
                session_id=session_id,
                client_metadata=client_metadata,
                operation_set=operation_set,
                created_at=datetime.now(),
                last_heartbeat=datetime.now(),
                expires_at=datetime.now() + self.session_timeout
            )
            self.sessions[session_id] = session
            
            print(f"[SessionManager] Registered session: {session_id}")
            print(f"[SessionManager] Operations: {operation_set}")
            
            return session
    
    def get_session(self, session_id: str) -> Optional[ClientSession]:
        """获取会话信息"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and not session.is_expired():
                return session
            elif session:
                # 会话已过期，清理它
                del self.sessions[session_id]
            return None
    
    def heartbeat(self, session_id: str) -> bool:
        """心跳更新"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and not session.is_expired():
                session.update_heartbeat()
                return True
            return False
    
    def get_operations_for_session(self, session_id: str) -> List[str]:
        """获取会话支持的操作指令集（包含内置的基本对话能力）"""
        session = self.get_session(session_id)
        if session:
            # 所有会话都内置支持基本对话能力
            operations = session.operation_set.copy()
            if "general_chat" not in operations:
                operations.append("general_chat")
            return operations
        return ["general_chat"]  # 即使没有会话也支持基本对话
    
    def unregister_session(self, session_id: str) -> bool:
        """主动注销会话"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                print(f"[SessionManager] Unregistered session: {session_id}")
                return True
            return False
    
    def get_active_session_count(self) -> int:
        """获取活跃会话数量"""
        with self._lock:
            return len([s for s in self.sessions.values() if not s.is_expired()])
    
    def get_all_sessions_info(self) -> List[Dict[str, Any]]:
        """获取所有会话信息（用于监控）"""
        with self._lock:
            return [
                {
                    "session_id": session.session_id,
                    "client_type": session.client_metadata.get("client_type", "unknown"),
                    "operations_count": len(session.operation_set),
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "is_expired": session.is_expired()
                }
                for session in self.sessions.values()
            ]
    
    def shutdown(self):
        """关闭会话管理器"""
        print("[SessionManager] Shutting down...")
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        # 清理所有会话
        with self._lock:
            self.sessions.clear()
        print("[SessionManager] Shutdown complete")


# 全局会话管理器实例
session_manager = LightweightSessionManager()


# 优雅关闭处理
import atexit
atexit.register(session_manager.shutdown)