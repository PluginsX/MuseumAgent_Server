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
    
    def is_active(self) -> bool:
        """检查会话是否活跃（综合判断）"""
        if self.is_expired():
            return False
        
        # 多重活跃性判断
        now = datetime.now()
        time_since_heartbeat = now - self.last_heartbeat
        
        # 1. 心跳超时判断（紧急情况：5分钟无心跳视为断开）
        if time_since_heartbeat > timedelta(minutes=5):
            print(f"[SessionManager] Session {self.session_id} marked inactive - no heartbeat for {time_since_heartbeat}")
            return False
            
        # 2. 会话即将过期判断
        time_until_expiry = self.expires_at - now
        if time_until_expiry < timedelta(minutes=2):
            print(f"[SessionManager] Session {self.session_id} marked inactive - expiring soon")
            return False
            
        return True
    
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
    
    def __init__(self, session_timeout_minutes: int = 1):
        self.sessions: Dict[str, ClientSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._lock = threading.RLock()
        self._cleanup_thread = None
        self._running = False
        self._start_cleanup_daemon()
    
    def _start_cleanup_daemon(self):
        """启动清理守护线程（增强版）"""
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._enhanced_cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
    def _enhanced_cleanup_loop(self):
        """增强的清理循环 - 主动检测僵尸会话"""
        print("[SessionManager] 启动增强会话清理守护进程")
        
        while self._running:
            try:
                # 每15秒执行一次全面检查
                time.sleep(15)
                self._comprehensive_session_check()
                
                # 每60秒执行一次深度清理
                if int(time.time()) % 60 == 0:
                    self._deep_cleanup_sessions()
                    
            except Exception as e:
                print(f"[SessionManager] 清理循环异常: {e}")
                time.sleep(5)  # 异常时短暂等待
    
    def _comprehensive_session_check(self):
        """全面会话状态检查"""
        with self._lock:
            now = datetime.now()
            cleanup_count = 0
            
            print(f"[SessionManager] 开始全面会话检查 - 当前时间: {now}")
            print(f"[SessionManager] 当前会话总数: {len(self.sessions)}")
            
            for session_id, session in list(self.sessions.items()):
                print(f"[SessionManager] 检查会话 {session_id}:")
                print(f"  - 是否过期: {session.is_expired()}")
                print(f"  - 过期时间: {session.expires_at}")
                print(f"  - 距离过期: {session.expires_at - now}")
                
                time_since_heartbeat = now - session.last_heartbeat
                print(f"  - 上次心跳: {session.last_heartbeat}")
                print(f"  - 距离上次心跳: {time_since_heartbeat}")
                
                # 1. 标准过期检查
                if session.is_expired():
                    del self.sessions[session_id]
                    cleanup_count += 1
                    print(f"[SessionManager] 清理过期会话: {session_id}")
                    continue
                
                # 2. 心跳超时检查（5分钟无响应）
                if time_since_heartbeat > timedelta(minutes=5):
                    del self.sessions[session_id]
                    cleanup_count += 1
                    print(f"[SessionManager] 清理僵尸会话: {session_id} (无心跳 {time_since_heartbeat})")
                    continue
                
                # 3. 即将过期预警（1分钟内）
                time_until_expiry = session.expires_at - now
                if timedelta(seconds=30) < time_until_expiry < timedelta(minutes=1):
                    print(f"[SessionManager] 会话即将过期: {session_id} ({time_until_expiry.seconds}秒后)")
            
            if cleanup_count > 0:
                print(f"[SessionManager] 本轮清理完成: {cleanup_count} 个会话")
            else:
                print("[SessionManager] 本轮检查未发现需要清理的会话")
    
    def _deep_cleanup_sessions(self):
        """深度清理 - 更严格的会话验证"""
        with self._lock:
            now = datetime.now()
            initial_count = len(self.sessions)
            
            # 深度验证每个会话
            valid_sessions = {}
            for session_id, session in self.sessions.items():
                # 多重验证条件
                if (not session.is_expired() and 
                    (now - session.last_heartbeat) < timedelta(minutes=10) and
                    session.operation_set):  # 确保有有效的指令集
                    valid_sessions[session_id] = session
                else:
                    print(f"[SessionManager] 深度清理无效会话: {session_id}")
            
            self.sessions = valid_sessions
            cleaned_count = initial_count - len(valid_sessions)
            
            if cleaned_count > 0:
                print(f"[SessionManager] 深度清理完成: 移除 {cleaned_count} 个无效会话")
    
    def _cleanup_expired_sessions(self):
        """清理过期会话（增强版）"""
        with self._lock:
            now = datetime.now()
            sessions_to_remove = []
            
            for session_id, session in self.sessions.items():
                # 1. 标准过期检查
                if session.is_expired():
                    sessions_to_remove.append(session_id)
                    print(f"[SessionManager] Removing expired session: {session_id}")
                    continue
                
                # 2. 心跳超时检查（紧急断开检测）
                time_since_heartbeat = now - session.last_heartbeat
                if time_since_heartbeat > timedelta(minutes=5):
                    sessions_to_remove.append(session_id)
                    print(f"[SessionManager] Removing zombie session {session_id} - no heartbeat for {time_since_heartbeat}")
                    continue
                
                # 3. 会话即将过期预警
                time_until_expiry = session.expires_at - now
                if time_until_expiry < timedelta(minutes=1) and time_until_expiry > timedelta(seconds=0):
                    print(f"[SessionManager] Session {session_id} will expire in {time_until_expiry}")
            
            # 执行清理
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
                print(f"[SessionManager] Cleaned up session: {session_id}")
            
            if sessions_to_remove:
                print(f"[SessionManager] Cleanup completed - removed {len(sessions_to_remove)} sessions")
    
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
            print(f"[SessionManager] Expires at: {session.expires_at}")
            print(f"[SessionManager] Current session count: {len(self.sessions)}")
            
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
        """获取会话支持的函数名称（已废弃，建议使用strict_session_manager）"""
        session = self.get_session(session_id)
        if session:
            # 从函数定义中提取名称
            functions = session.client_metadata.get("functions", [])
            function_names = [func.get("name", "unknown") for func in functions]
            if "general_chat" not in function_names:
                function_names.append("general_chat")
            return function_names
        return ["general_chat"]  # 兼容模式
    
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
    
    def get_all_sessions(self) -> Dict[str, ClientSession]:
        """获取所有会话对象（用于客户端管理API）"""
        with self._lock:
            # 先清理过期会话
            self._cleanup_expired_sessions()
            # 返回未过期的会话
            return {sid: session for sid, session in self.sessions.items() 
                   if not session.is_expired()}
    
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