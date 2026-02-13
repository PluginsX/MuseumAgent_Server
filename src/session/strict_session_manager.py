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
from ..common.enhanced_logger import get_enhanced_logger

@dataclass
class EnhancedClientSession:
    """增强版客户端会话数据结构（基于函数调用）"""
    session_id: str
    client_metadata: Dict[str, Any]
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
        # 获取日志记录器
        self.logger = get_enhanced_logger()
        
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
        
        self.logger.sess.info('Session manager configuration loaded', self.config)
    def _load_config(self):
        """加载会话管理配置"""
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
        
        try:
            config = get_global_config()
            session_config = config.get('session_management', {})
            
            # 合并配置
            self.config = {**default_config, **session_config}
            
        except Exception as e:
            self.logger.sess.error('Failed to load session configuration, using defaults', {'error': str(e)})
            self.config = default_config
    def _start_enhanced_cleanup_daemon(self):
        """启动增强清理守护线程"""
        if not self.enable_auto_cleanup:
            self.logger.sess.info('Auto cleanup disabled')
            return
            
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._strict_cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        self.logger.sess.info('Enhanced cleanup daemon started', 
                      {'session_timeout': f'{self.session_timeout.total_seconds()/60}分钟',
                       'inactivity_timeout': f'{self.inactivity_timeout.total_seconds()/60}分钟',
                       'cleanup_interval': f'{self.cleanup_interval}秒'})
    
    def _strict_cleanup_loop(self):
        """严格的清理循环"""
        self.logger.sess.info('Strict session cleanup loop started')
        
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
                self.logger.sess.error('Session cleanup loop exception', {'error': str(e)})
                time.sleep(10)
    
    def _perform_strict_cleanup(self):
        """执行严格的会话清理"""
        with self._lock:
            now = datetime.now()
            cleanup_actions = []
            
            self.logger.sess.info('Starting strict session state check', 
                          {'total_sessions': len(self.sessions)})
            
            for session_id, session in list(self.sessions.items()):
                session_info = {
                    'session_id': session_id,
                    'is_expired': session.is_expired(),
                    'is_inactive': session.is_inactive(self.inactivity_timeout.total_seconds()/60),
                    'is_disconnected': session.is_disconnected(),
                    'time_since_heartbeat': (now - session.last_heartbeat).total_seconds()/60,
                    'time_since_activity': (now - session.last_activity).total_seconds()/60
                }
                
                self.logger.sess.debug(f'Checking session {session_id[:8]}...', session_info)
                
                # 优先级清理：
                # 1. 已过期的会话
                if session.is_expired():
                    cleanup_actions.append(('expired', session_id, session))
                    self.logger.sess.info('Cleaning up expired session', 
                                  {'session_id': session_id[:8], 'expired_at': session.expires_at.isoformat()})
                    continue
                
                # 2. 断开连接的会话（心跳超时）
                if session.is_disconnected(self.heartbeat_timeout):
                    cleanup_actions.append(('disconnected', session_id, session))
                    self.logger.sess.info('Cleaning up disconnected session', 
                                  {'session_id': session_id[:8],
                                   'disconnected_time': (now - session.last_heartbeat).total_seconds()/60,
                                   'timeout_setting': self.heartbeat_timeout.total_seconds()/60})
                    continue
                
                # 3. 长期不活跃的会话
                if session.is_inactive(self.inactivity_timeout.total_seconds()/60):
                    cleanup_actions.append(('inactive', session_id, session))
                    self.logger.sess.info('Cleaning up inactive session', 
                                  {'session_id': session_id[:8],
                                   'inactive_time': (now - session.last_activity).total_seconds()/60,
                                   'timeout_setting': self.inactivity_timeout.total_seconds()/60})
                    continue
            
            # 执行清理
            for action_type, session_id, session in cleanup_actions:
                del self.sessions[session_id]
                self.logger.sess.info('Session cleaned up', 
                              {'session_id': session_id[:8], 'cleanup_reason': action_type,
                               'remaining_sessions': len(self.sessions)})
            
            if cleanup_actions:
                self.logger.sess.info('Cleanup round completed', 
                              {'cleaned_count': len(cleanup_actions),
                               'remaining_total': len(self.sessions)})
            else:
                self.logger.sess.info('No sessions needed cleaning in this round')
    
    def _perform_deep_validation(self):
        """深度验证会话有效性"""
        with self._lock:
            self.logger.sess.info('Performing deep session validation')
            
            valid_sessions = {}
            invalid_count = 0
            
            for session_id, session in self.sessions.items():
                # 严格验证条件
                if (session.is_registered and 
                    not session.is_expired()):
                    valid_sessions[session_id] = session
                else:
                    invalid_count += 1
                    self.logger.sess.warn('Found invalid session', 
                                  {'session_id': session_id[:8],
                                   'registered': session.is_registered,
                                   'expired': session.is_expired(),
                                   'function_count': len(session.client_metadata.get('functions', []))})
            
            if invalid_count > 0:
                self.sessions = valid_sessions
                self.logger.sess.info('Deep validation repair completed', 
                              {'removed_invalid': invalid_count,
                               'remaining_valid': len(valid_sessions)})
    
    def register_session(self, session_id: str, client_metadata: Dict[str, Any]) -> EnhancedClientSession:
        """严格会话注册（基于函数调用）"""
        with self._lock:
            # 检查是否已存在相同会话
            if session_id in self.sessions:
                self.logger.sess.warn('Duplicate session registration attempt', 
                              {'session_id': session_id[:8]})
                # 移除旧会话
                old_session = self.sessions.pop(session_id)
                self.logger.sess.info('Cleaning up duplicate session', 
                              {'old_session': old_session.session_id[:8]})
            
            # 创建新会话
            now = datetime.now()
            session = EnhancedClientSession(
                session_id=session_id,
                client_metadata=client_metadata,
                created_at=now,
                last_heartbeat=now,
                last_activity=now,
                expires_at=now + self.session_timeout,
                is_registered=True
            )
            
            self.sessions[session_id] = session
            
            self.logger.sess.info('New session registered successfully', 
                          {'session_id': session_id[:8],
                           'client_type': client_metadata.get('client_type', 'unknown'),
                           'function_count': len(client_metadata.get('functions', [])),
                           'expires_in': self.session_timeout.total_seconds()/60})
            
            return session
    
    def validate_session(self, session_id: str) -> Optional[EnhancedClientSession]:
        """严格会话验证"""
        with self._lock:
            session = self.sessions.get(session_id)
            
            if not session:
                self.logger.sess.warn('Session does not exist', 
                              {'session_id': session_id[:8]})
                return None
            
            # 检查会话状态
            validation_checks = {
                'exists': True,
                'registered': session.is_registered,
                'not_expired': not session.is_expired(),
                'connected': not session.is_disconnected(self.heartbeat_timeout),
                'active': not session.is_inactive(self.inactivity_timeout.total_seconds()/60)
            }
            
            self.logger.sess.debug(f'Session validation {session_id[:8]}', validation_checks)
            
            # 如果会话无效，立即清理
            if not all(validation_checks.values()):
                self.logger.sess.warn('Invalid session rejected', 
                              {'session_id': session_id[:8], 'checks': validation_checks})
                del self.sessions[session_id]
                return None
            
            # 更新活动时间
            session.update_activity()
            self.logger.sess.info('Session validation passed', 
                          {'session_id': session_id[:8]})
            
            return session
    
    def get_session(self, session_id: str) -> Optional[EnhancedClientSession]:
        """获取会话（不更新活动时间）"""
        with self._lock:
            session = self.sessions.get(session_id)
            return session
    
    def heartbeat(self, session_id: str) -> bool:
        """心跳更新"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and session.is_registered and not session.is_expired():
                session.update_heartbeat()
                session.update_activity()
                self.logger.sess.info('Heartbeat updated successfully', 
                              {'session_id': session_id[:8]})
                return True
            
            self.logger.sess.warn('Heartbeat update failed', 
                          {'session_id': session_id[:8], 'reason': '会话不存在或已过期'})
            return False
    
    def register_session_with_functions(self, session_id: str, client_metadata: Dict[str, Any], 
                                      functions: List[Dict[str, Any]]) -> EnhancedClientSession:
        """注册支持OpenAI标准函数调用的会话
        
        Args:
            session_id: 会话ID
            client_metadata: 客户端元数据
            functions: OpenAI标准函数定义列表
        
        Returns:
            注册的会话对象
        """
        # 验证所有函数定义都符合OpenAI标准
        from ..models.function_calling_models import is_valid_openai_function
        valid_functions = []
        function_names = []
        
        # 支持空函数列表（普通对话模式）
        if functions:
            for func_def in functions:
                if is_valid_openai_function(func_def):
                    valid_functions.append(func_def)
                    function_names.append(func_def.get("name", "unknown"))
                else:
                    self.logger.sess.warn(f'Skipping non-OpenAI compliant function: {func_def.get("name", "unknown")}')
        
        # 存储验证后的函数定义（可能是空列表）
        client_metadata["functions"] = valid_functions
        client_metadata["function_names"] = function_names
        
        self.logger.sess.info(f'Session registered (function count: {len(valid_functions)})', 
                      {'session_id': session_id[:8], 'functions': function_names if function_names else '普通对话模式'})
        
        return self.register_session(session_id, client_metadata)

    def get_functions_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话支持的函数定义"""
        session = self.validate_session(session_id)
        if session:
            return session.client_metadata.get("functions", [])
        return []

    def unregister_session(self, session_id: str) -> bool:
        """主动注销会话"""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions.pop(session_id)
                self.logger.sess.info('Session actively unregistered', 
                              {'session_id': session_id[:8],
                               'was_active': session.is_active()})
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
            
            self.logger.sess.info('Session statistics', stats)
            return stats
    
    def shutdown(self):
        """关闭会话管理器"""
        self.logger.sess.info('Shutting down session manager')
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        with self._lock:
            cleanup_count = len(self.sessions)
            self.sessions.clear()
        
        self.logger.sess.info('Session manager closed', 
                      {'cleaned_sessions': cleanup_count})


# 全局会话管理器实例
strict_session_manager = StrictSessionManager()

# 优雅关闭处理
import atexit
atexit.register(strict_session_manager.shutdown)