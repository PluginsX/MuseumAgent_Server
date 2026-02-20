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
    operation_set: List[str] = None  # 新增：操作集合，保持向后兼容
    
    def __post_init__(self):
        """初始化后处理"""
        if self.operation_set is None:
            # 从client_metadata中提取操作集合，如果有的话
            self.operation_set = self.client_metadata.get("operation_set", [])
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now() > self.expires_at
    
    def is_inactive(self, timeout_minutes: int = 5) -> bool:
        """检查会话是否长期不活跃"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def is_disconnected(self, heartbeat_timeout: timedelta = None) -> bool:
        """检查会话是否断开连接（使用最后活动时间，而非心跳时间）"""
        timeout = heartbeat_timeout or timedelta(minutes=2)  # 默认2分钟心跳超时
        # ✅ 关键修复：使用 last_activity 而非 last_heartbeat
        # 任何业务请求都会更新 last_activity，避免误判
        return datetime.now() - self.last_activity > timeout
    
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return (not self.is_expired() and 
                not self.is_inactive() and 
                not self.is_disconnected())
    
    def update_heartbeat(self):
        """更新心跳时间（同时更新活动时间）"""
        now = datetime.now()
        self.last_heartbeat = now
        self.last_activity = now  # ✅ 心跳也算活动
        # 延长会话有效期到120分钟（与配置保持一致）
        self.expires_at = now + timedelta(minutes=120)
    
    def update_activity(self):
        """更新活动时间（业务请求时调用）"""
        now = datetime.now()
        self.last_activity = now
        # ✅ 业务活动也延长会话有效期
        self.expires_at = now + timedelta(minutes=120)
    
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
        # 默认配置（优化后的配置，更宽松且合理）
        default_config = {
            'session_timeout_minutes': 120,  # 120分钟总超时（2小时，足够长）
            'inactivity_timeout_minutes': 60,  # 60分钟无活动超时（1小时）
            'heartbeat_timeout_minutes': 10,  # 10分钟活动超时（从5分钟增加，更宽容）
            'cleanup_interval_seconds': 120,  # 120秒清理间隔（2分钟，减少清理频率）
            'deep_validation_interval_seconds': 600,  # 10分钟深度验证
            'enable_auto_cleanup': True,
            'enable_heartbeat_monitoring': True,
            'log_level': 'INFO'
        }
        
        try:
            config = get_global_config()
            # ✅ 如果配置为空（未加载），直接使用默认配置
            if not config:
                self.config = default_config
                return
            
            session_config = config.get('session_management', {})
            
            # 合并配置
            self.config = {**default_config, **session_config}
            
        except Exception as e:
            # ✅ 降低日志级别为 debug，避免启动时显示错误
            # 这是正常情况，因为 StrictSessionManager 在全局配置加载前就初始化了
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
        """执行严格的会话清理（优化版：只清理真正过期的会话）"""
        with self._lock:
            now = datetime.now()
            cleanup_actions = []
            
            self.logger.sess.debug('Starting session cleanup check', 
                          {'total_sessions': len(self.sessions)})
            
            for session_id, session in list(self.sessions.items()):
                # ✅ 关键优化：只清理真正过期的会话
                # 不再使用 is_disconnected() 和 is_inactive()，避免误判
                
                # 1. 检查会话是否已过期（expires_at）
                if session.is_expired():
                    cleanup_actions.append(('expired', session_id, session))
                    self.logger.sess.info('Cleaning up expired session', 
                                  {'session_id': session_id[:8], 
                                   'expired_at': session.expires_at.isoformat(),
                                   'time_since_activity': (now - session.last_activity).total_seconds()/60})
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
                self.logger.sess.debug('No sessions needed cleaning in this round')
    
    def _perform_deep_validation(self):
        """深度验证会话有效性"""
        with self._lock:
            self.logger.sess.info('Performing deep session validation')
            
            invalid_sessions = []
            
            for session_id, session in list(self.sessions.items()):  # 使用list()避免在迭代时修改字典
                # 严格验证条件
                is_valid = (session.is_registered and 
                           not session.is_expired())
                
                if not is_valid:
                    invalid_sessions.append(session_id)
                    self.logger.sess.warn('Found invalid session', 
                                  {'session_id': session_id[:8],
                                   'registered': session.is_registered,
                                   'expired': session.is_expired(),
                                   'function_count': len(session.client_metadata.get('functions', []))})
            
            # 删除无效会话
            removed_count = 0
            for session_id in invalid_sessions:
                if session_id in self.sessions:
                    del self.sessions[session_id]
                    removed_count += 1
            
            if removed_count > 0:
                self.logger.sess.info('Deep validation repair completed', 
                              {'removed_invalid': removed_count,
                               'remaining_valid': len(self.sessions)})
    
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
                           'expires_in': self.session_timeout.total_seconds()/60,
                           'total_sessions': len(self.sessions),
                           'session_ids': list(self.sessions.keys())[:5]})
            
            return session
    
    def validate_session(self, session_id: str) -> Optional[EnhancedClientSession]:
        """严格会话验证（优化版：简化验证逻辑）"""
        with self._lock:
            session = self.sessions.get(session_id)
            
            if not session:
                self.logger.sess.warn('Session does not exist', 
                              {'session_id': session_id[:8]})
                return None
            
            # ✅ 简化验证：只检查是否注册和是否过期
            # 不再检查 connected 和 active，避免误判
            if not session.is_registered or session.is_expired():
                self.logger.sess.warn('Invalid session detected', 
                              {'session_id': session_id[:8],
                               'registered': session.is_registered,
                               'expired': session.is_expired()})
                return None
            
            # 更新活动时间（这会自动延长会话有效期）
            session.update_activity()
            
            self.logger.sess.debug('Session validation passed', 
                          {'session_id': session_id[:8],
                           'remaining_seconds': int((session.expires_at - datetime.now()).total_seconds())})
            
            return session
    
    def get_session(self, session_id: str) -> Optional[EnhancedClientSession]:
        """获取会话（不更新活动时间）"""
        with self._lock:
            session = self.sessions.get(session_id)
            return session
    
    def heartbeat(self, session_id: str) -> bool:
        """心跳更新（优化版：简化逻辑，增强日志）"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                self.logger.sess.warn('Heartbeat update failed - session not found', 
                              {'session_id': session_id[:8]})
                return False
            
            if not session.is_registered:
                self.logger.sess.warn('Heartbeat update failed - session not registered', 
                              {'session_id': session_id[:8]})
                return False
            
            if session.is_expired():
                self.logger.sess.warn('Heartbeat update failed - session expired', 
                              {'session_id': session_id[:8],
                               'expired_at': session.expires_at.isoformat()})
                return False
            
            now = datetime.now()
            time_since_last_heartbeat = (now - session.last_heartbeat).total_seconds()
            
            # 更新心跳（这会同时更新活动时间和延长会话）
            session.update_heartbeat()
            
            # 记录心跳更新（降低日志级别，避免日志风暴）
            if time_since_last_heartbeat >= 10.0:  # 只记录间隔大于10秒的心跳
                self.logger.sess.debug('Heartbeat updated', 
                              {'session_id': session_id[:8], 
                               'interval': f'{time_since_last_heartbeat:.1f}s',
                               'new_expires_at': session.expires_at.isoformat()})
            
            return True
    
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

    def update_session_attributes(
        self,
        session_id: str,
        require_tts: Optional[bool] = None,
        enable_srs: Optional[bool] = None,
        function_calling_op: Optional[str] = None,
        function_calling: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[Dict[str, str]] = None,
        scene_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """按协议更新会话属性（完整版）
        
        Args:
            session_id: 会话ID
            require_tts: TTS 开关
            enable_srs: SRS 开关
            function_calling_op: 函数操作类型（REPLACE/ADD/UPDATE/DELETE）
            function_calling: 函数定义列表
            system_prompt: 系统提示词配置
            scene_context: 场景上下文配置
            
        Returns:
            是否更新成功
        """
        if not function_calling:
            function_calling = []
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                self.logger.sess.warn('Update failed - session not found', 
                              {'session_id': session_id[:8]})
                return False
            
            # 更新 TTS 开关
            if require_tts is not None:
                session.client_metadata["require_tts"] = require_tts
                self.logger.sess.debug('Updated require_tts', 
                              {'session_id': session_id[:8], 'value': require_tts})
            
            # 更新 SRS 开关
            if enable_srs is not None:
                session.client_metadata["enable_srs"] = enable_srs
                self.logger.sess.debug('Updated enable_srs', 
                              {'session_id': session_id[:8], 'value': enable_srs})
            
            # ✅ 新增：更新系统提示词
            if system_prompt is not None:
                current_prompt = session.client_metadata.get("system_prompt", {})
                # 只更新提供的字段
                if "role_description" in system_prompt:
                    current_prompt["role_description"] = system_prompt["role_description"]
                if "response_requirements" in system_prompt:
                    current_prompt["response_requirements"] = system_prompt["response_requirements"]
                
                session.client_metadata["system_prompt"] = current_prompt
                self.logger.sess.info('Updated system_prompt', 
                              {'session_id': session_id[:8], 
                               'has_role': "role_description" in system_prompt,
                               'has_requirements': "response_requirements" in system_prompt})
            
            # ✅ 新增：更新场景上下文
            if scene_context is not None:
                current_scene = session.client_metadata.get("scene_context", {})
                # 只更新提供的字段
                if "current_scene" in scene_context:
                    current_scene["current_scene"] = scene_context["current_scene"]
                if "scene_description" in scene_context:
                    current_scene["scene_description"] = scene_context["scene_description"]
                if "keywords" in scene_context:
                    current_scene["keywords"] = scene_context["keywords"]
                if "scene_specific_prompt" in scene_context:
                    current_scene["scene_specific_prompt"] = scene_context["scene_specific_prompt"]
                
                session.client_metadata["scene_context"] = current_scene
                self.logger.sess.info('Updated scene_context', 
                              {'session_id': session_id[:8],
                               'scene': current_scene.get("current_scene", "unknown")})
            
            # 更新函数调用
            if function_calling_op and function_calling is not None:
                fc = session.client_metadata.get("functions", [])
                names = {f.get("name") for f in fc if isinstance(f, dict) and f.get("name")}
                
                if function_calling_op == "REPLACE":
                    session.client_metadata["functions"] = list(function_calling)
                    session.client_metadata["function_names"] = [f.get("name", "") for f in function_calling if isinstance(f, dict)]
                    self.logger.sess.info('Replaced functions', 
                                  {'session_id': session_id[:8], 
                                   'count': len(function_calling)})
                
                elif function_calling_op == "ADD":
                    session.client_metadata["functions"] = fc + list(function_calling)
                    session.client_metadata["function_names"] = session.client_metadata.get("function_names", []) + [
                        f.get("name", "") for f in function_calling if isinstance(f, dict)
                    ]
                    self.logger.sess.info('Added functions', 
                                  {'session_id': session_id[:8], 
                                   'added': len(function_calling)})
                
                elif function_calling_op == "UPDATE":
                    new_names = {f.get("name") for f in function_calling if isinstance(f, dict) and f.get("name")}
                    fc = [x for x in fc if x.get("name") not in new_names]
                    fc.extend(function_calling)
                    session.client_metadata["functions"] = fc
                    session.client_metadata["function_names"] = [f.get("name", "") for f in fc if isinstance(f, dict) and f.get("name")]
                    self.logger.sess.info('Updated functions', 
                                  {'session_id': session_id[:8], 
                                   'updated': len(new_names)})
                
                elif function_calling_op == "DELETE":
                    del_names = {f.get("name") for f in function_calling if isinstance(f, dict)}
                    fc = [x for x in fc if x.get("name") not in del_names]
                    session.client_metadata["functions"] = fc
                    session.client_metadata["function_names"] = [f.get("name", "") for f in fc if isinstance(f, dict) and f.get("name")]
                    self.logger.sess.info('Deleted functions', 
                                  {'session_id': session_id[:8], 
                                   'deleted': len(del_names)})
            
            return True

    def get_protocol_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """返回协议 SESSION_INFO.session_data 所需格式"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return None
            remaining = max(0, (session.expires_at - datetime.now()).total_seconds())
            return {
                "platform": session.client_metadata.get("platform", session.client_metadata.get("client_type", "WEB")),
                "require_tts": session.client_metadata.get("require_tts", False),
                "enable_srs": session.client_metadata.get("enable_srs", True),
                "function_calling": session.client_metadata.get("functions", []),
                "create_time": int(session.created_at.timestamp() * 1000),
                "remaining_seconds": int(remaining),
            }

    def get_functions_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话支持的函数定义"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                functions = session.client_metadata.get("functions", [])
                return functions
            else:
                self.logger.sess.warn('Functions requested for non-existent session', 
                              {'session_id': session_id[:8] if session_id else None})
        return []

    def get_operation_set_for_session(self, session_id: str) -> List[str]:
        """获取会话的操作集合（兼容旧版API）"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                return session.operation_set or session.client_metadata.get("operation_set", [])
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