# -*- coding: utf-8 -*-
"""
强化版会话管理器
实现严格的会话生命周期管理，确保资源及时释放
"""
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

from ..common.config_utils import get_global_config
from ..common.log_formatter import log_step, log_communication

@dataclass
class EnhancedClientSession:
    """增强版客户端会话数据结构"""
    session_id: str
    client_metadata: Dict[str, Any]
    operation_set: List[str]
    created_at: datetime
    last_heartbeat: datetime
    last_activity: datetime  # 新增：最后活动时间
    expires_at: datetime
    is_registered: bool = True
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now() > self.expires_at
    
    def is_inactive(self, timeout_minutes: int = 5) -> bool:
        """检查会话是否长期不活跃"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def is_disconnected(self, heartbeat_timeout: timedelta = None) -> bool:
        """检查会话是否断开连接"""
        timeout = heartbeat_timeout or timedelta(minutes=2)  # 默认2分钟心跳超时
        return datetime.now() - self.last_heartbeat > timeout
    
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return (not self.is_expired() and 
                not self.is_inactive() and 
                not self.is_disconnected())
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
        # 延长会话有效期
        self.expires_at = datetime.now() + timedelta(minutes=15)
    
    def update_activity(self):
        """更新活动时间"""
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换datetime为字符串
        data['created_at'] = self.created_at.isoformat()
        data['last_heartbeat'] = self.last_heartbeat.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return data


class StrictSessionManager:
    """严格会话管理器 - 强制注册+主动清理"""
    
    def __init__(self):
        # 从配置文件读取参数
        self._load_config()
        
        self.sessions: Dict[str, EnhancedClientSession] = {}
        self.session_timeout = timedelta(minutes=self.config['session_timeout_minutes'])
        self.inactivity_timeout = timedelta(minutes=self.config['inactivity_timeout_minutes'])
        self.heartbeat_timeout = timedelta(minutes=self.config['heartbeat_timeout_minutes'])
        self.cleanup_interval = self.config['cleanup_interval_seconds']
        self.deep_validation_interval = self.config['deep_validation_interval_seconds']
        self.enable_auto_cleanup = self.config['enable_auto_cleanup']
        self.enable_heartbeat_monitoring = self.config['enable_heartbeat_monitoring']
        self.log_level = self.config['log_level']
        
        self._lock = threading.RLock()
        self._cleanup_thread = None
        self._running = False
        
        if self.enable_auto_cleanup:
            self._start_enhanced_cleanup_daemon()
        
        print(log_step('SESSION', 'CONFIG', '会话管理器配置加载完成', self.config))
    def _load_config(self):
        """加载会话管理配置"""
        try:
            config = get_global_config()
            session_config = config.get('session_management', {})
            
            # 默认配置
            default_config = {
                'session_timeout_minutes': 15,
                'inactivity_timeout_minutes': 5,
                'heartbeat_timeout_minutes': 2,
                'cleanup_interval_seconds': 30,
                'deep_validation_interval_seconds': 300,
                'enable_auto_cleanup': True,
                'enable_heartbeat_monitoring': True,
                'log_level': 'INFO'
            }
            
            # 合并配置
            self.config = {**default_config, **session_config}
            
        except Exception as e:
            print(log_step('SESSION', 'ERROR', '加载会话配置失败，使用默认配置', {'error': str(e)}))
            self.config = default_config
    def _start_enhanced_cleanup_daemon(self):
        """启动增强清理守护线程"""
        if not self.enable_auto_cleanup:
            print(log_step('SESSION', 'INFO', '自动清理已禁用'))
            return
            
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._strict_cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        print(log_step('SESSION', 'START', '启动严格会话管理守护进程', 
                      {'session_timeout': f'{self.session_timeout.total_seconds()/60}分钟',
                       'inactivity_timeout': f'{self.inactivity_timeout.total_seconds()/60}分钟',
                       'cleanup_interval': f'{self.cleanup_interval}秒'}))
    
    def _strict_cleanup_loop(self):
        """严格的清理循环"""
        print(log_step('SESSION', 'INFO', '严格会话清理循环已启动'))
        
        last_deep_validation = time.time()
        
        while self._running:
            try:
                time.sleep(self.cleanup_interval)
                self._perform_strict_cleanup()
                
                # 检查是否需要执行深度验证
                current_time = time.time()
                if current_time - last_deep_validation >= self.deep_validation_interval:
                    self._perform_deep_validation()
                    last_deep_validation = current_time
                    
            except Exception as e:
                print(log_step('SESSION', 'ERROR', '会话清理循环异常', {'error': str(e)}))
                time.sleep(10)
    
    def _perform_strict_cleanup(self):
        """执行严格的会话清理"""
        with self._lock:
            now = datetime.now()
            cleanup_actions = []
            
            print(log_step('SESSION', 'CHECK', '开始严格会话状态检查', 
                          {'total_sessions': len(self.sessions)}))
            
            for session_id, session in list(self.sessions.items()):
                session_info = {
                    'session_id': session_id,
                    'is_expired': session.is_expired(),
                    'is_inactive': session.is_inactive(self.inactivity_timeout.total_seconds()/60),
                    'is_disconnected': session.is_disconnected(),
                    'time_since_heartbeat': (now - session.last_heartbeat).total_seconds()/60,
                    'time_since_activity': (now - session.last_activity).total_seconds()/60
                }
                
                print(log_step('SESSION', 'DETAIL', f'检查会话 {session_id[:8]}...', session_info))
                
                # 优先级清理：
                # 1. 已过期的会话
                if session.is_expired():
                    cleanup_actions.append(('expired', session_id, session))
                    print(log_step('SESSION', 'CLEANUP', f'清理过期会话 {session_id[:8]}...', 
                                  {'expired_at': session.expires_at.isoformat()}))
                    continue
                
                # 2. 断开连接的会话（心跳超时）
                if session.is_disconnected(self.heartbeat_timeout):
                    cleanup_actions.append(('disconnected', session_id, session))
                    print(log_step('SESSION', 'CLEANUP', f'清理断开会话 {session_id[:8]}...', 
                                  {'disconnected_time': (now - session.last_heartbeat).total_seconds()/60,
                                   'timeout_setting': self.heartbeat_timeout.total_seconds()/60}))
                    continue
                
                # 3. 长期不活跃的会话
                if session.is_inactive(self.inactivity_timeout.total_seconds()/60):
                    cleanup_actions.append(('inactive', session_id, session))
                    print(log_step('SESSION', 'CLEANUP', f'清理不活跃会话 {session_id[:8]}...', 
                                  {'inactive_time': (now - session.last_activity).total_seconds()/60,
                                   'timeout_setting': self.inactivity_timeout.total_seconds()/60}))
                    continue
            
            # 执行清理
            for action_type, session_id, session in cleanup_actions:
                del self.sessions[session_id]
                print(log_step('SESSION', 'SUCCESS', f'会话已清理 {session_id[:8]}', 
                              {'cleanup_reason': action_type,
                               'remaining_sessions': len(self.sessions)}))
            
            if cleanup_actions:
                print(log_step('SESSION', 'SUMMARY', '本轮清理完成', 
                              {'cleaned_count': len(cleanup_actions),
                               'remaining_total': len(self.sessions)}))
            else:
                print(log_step('SESSION', 'INFO', '本轮检查未发现需要清理的会话'))
    
    def _perform_deep_validation(self):
        """深度验证会话有效性"""
        with self._lock:
            print(log_step('SESSION', 'VALIDATE', '执行深度会话验证'))
            
            valid_sessions = {}
            invalid_count = 0
            
            for session_id, session in self.sessions.items():
                # 严格验证条件
                if (session.is_registered and 
                    not session.is_expired() and 
                    session.operation_set and
                    len(session.operation_set) > 0):
                    valid_sessions[session_id] = session
                else:
                    invalid_count += 1
                    print(log_step('SESSION', 'INVALID', f'发现无效会话 {session_id[:8]}', 
                                  {'registered': session.is_registered,
                                   'expired': session.is_expired(),
                                   'operations': len(session.operation_set)}))
            
            if invalid_count > 0:
                self.sessions = valid_sessions
                print(log_step('SESSION', 'REPAIR', '深度验证修复完成', 
                              {'removed_invalid': invalid_count,
                               'remaining_valid': len(valid_sessions)}))
    
    def register_session(self, session_id: str, client_metadata: Dict[str, Any], 
                        operation_set: List[str]) -> EnhancedClientSession:
        """严格会话注册"""
        with self._lock:
            # 检查是否已存在相同会话
            if session_id in self.sessions:
                print(log_step('SESSION', 'WARNING', '重复会话注册尝试', 
                              {'session_id': session_id[:8]}))
                # 移除旧会话
                old_session = self.sessions.pop(session_id)
                print(log_step('SESSION', 'CLEANUP', '清理重复会话', 
                              {'old_session': old_session.session_id[:8]}))
            
            # 创建新会话
            now = datetime.now()
            session = EnhancedClientSession(
                session_id=session_id,
                client_metadata=client_metadata,
                operation_set=operation_set,
                created_at=now,
                last_heartbeat=now,
                last_activity=now,
                expires_at=now + self.session_timeout,
                is_registered=True
            )
            
            self.sessions[session_id] = session
            
            print(log_step('SESSION', 'REGISTER', '新会话注册成功', 
                          {'session_id': session_id[:8],
                           'client_type': client_metadata.get('client_type', 'unknown'),
                           'operations_count': len(operation_set),
                           'expires_in': self.session_timeout.total_seconds()/60}))
            
            print(log_communication('SESSION', 'CREATE', 'Session Registration',
                                  session.to_dict()))
            
            return session
    
    def validate_session(self, session_id: str) -> Optional[EnhancedClientSession]:
        """严格会话验证"""
        with self._lock:
            session = self.sessions.get(session_id)
            
            if not session:
                print(log_step('SESSION', 'MISSING', '会话不存在', 
                              {'session_id': session_id[:8]}))
                return None
            
            # 检查会话状态
            validation_checks = {
                'exists': True,
                'registered': session.is_registered,
                'not_expired': not session.is_expired(),
                'connected': not session.is_disconnected(self.heartbeat_timeout),
                'active': not session.is_inactive(self.inactivity_timeout.total_seconds()/60)
            }
            
            print(log_step('SESSION', 'VALIDATE', f'会话验证 {session_id[:8]}', validation_checks))
            
            # 如果会话无效，立即清理
            if not all(validation_checks.values()):
                print(log_step('SESSION', 'REJECT', '无效会话被拒绝', 
                              {'session_id': session_id[:8], 'checks': validation_checks}))
                del self.sessions[session_id]
                return None
            
            # 更新活动时间
            session.update_activity()
            print(log_step('SESSION', 'ACCEPT', '会话验证通过', 
                          {'session_id': session_id[:8]}))
            
            return session
    
    def heartbeat(self, session_id: str) -> bool:
        """心跳更新"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and session.is_registered and not session.is_expired():
                session.update_heartbeat()
                session.update_activity()
                print(log_step('SESSION', 'HEARTBEAT', '心跳更新成功', 
                              {'session_id': session_id[:8]}))
                return True
            
            print(log_step('SESSION', 'HEARTBEAT_FAIL', '心跳更新失败', 
                          {'session_id': session_id[:8], 'reason': '会话不存在或已过期'}))
            return False
    
    def get_operations_for_session(self, session_id: str) -> List[str]:
        """获取会话操作集"""
        session = self.validate_session(session_id)
        if session:
            operations = session.operation_set.copy()
            if "general_chat" not in operations:
                operations.append("general_chat")
            return operations
        return ["general_chat"]
    
    def unregister_session(self, session_id: str) -> bool:
        """主动注销会话"""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions.pop(session_id)
                print(log_step('SESSION', 'UNREGISTER', '会话主动注销', 
                              {'session_id': session_id[:8],
                               'was_active': session.is_active()}))
                print(log_communication('SESSION', 'DESTROY', 'Session Unregistration',
                                      {'session_id': session_id, 'reason': 'client_request'}))
                return True
            return False
    
    def get_all_sessions(self) -> Dict[str, EnhancedClientSession]:
        """获取所有活跃会话"""
        with self._lock:
            # 先执行清理
            self._perform_strict_cleanup()
            # 返回活跃会话
            return {sid: session for sid, session in self.sessions.items() 
                   if session.is_active()}
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        with self._lock:
            total = len(self.sessions)
            active = len([s for s in self.sessions.values() if s.is_active()])
            expired = len([s for s in self.sessions.values() if s.is_expired()])
            disconnected = len([s for s in self.sessions.values() if s.is_disconnected(self.heartbeat_timeout)])
            inactive = len([s for s in self.sessions.values() if s.is_inactive(self.inactivity_timeout.total_seconds()/60)])
            
            stats = {
                'total_sessions': total,
                'active_sessions': active,
                'expired_sessions': expired,
                'disconnected_sessions': disconnected,
                'inactive_sessions': inactive,
                'cleanup_pending': expired + disconnected + inactive
            }
            
            print(log_step('SESSION', 'STATS', '会话统计信息', stats))
            return stats
    
    def shutdown(self):
        """关闭会话管理器"""
        print(log_step('SESSION', 'SHUTDOWN', '开始关闭会话管理器'))
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        with self._lock:
            cleanup_count = len(self.sessions)
            self.sessions.clear()
        
        print(log_step('SESSION', 'SHUTDOWN_COMPLETE', '会话管理器已关闭', 
                      {'cleaned_sessions': cleanup_count}))


# 全局会话管理器实例
strict_session_manager = StrictSessionManager()

# 优雅关闭处理
import atexit
atexit.register(strict_session_manager.shutdown)