# -*- coding: utf-8 -*-
"""
错误处理与容错机制
实现统一的错误处理、熔断、降级等容错策略
"""
import asyncio
import time
import traceback
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable, Union
from datetime import datetime
from dataclasses import dataclass
from functools import wraps
import threading
from contextlib import contextmanager

from src.common.enhanced_logger import get_enhanced_logger


class ErrorType(Enum):
    """错误类型枚举"""
    CLIENT_ERROR = "client_error"           # 客户端错误
    SERVER_ERROR = "server_error"           # 服务端错误
    NETWORK_ERROR = "network_error"         # 网络错误
    TIMEOUT_ERROR = "timeout_error"         # 超时错误
    RESOURCE_ERROR = "resource_error"       # 资源错误
    EXTERNAL_ERROR = "external_error"       # 外部服务错误


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 关闭状态（正常）
    OPEN = "open"           # 开启状态（熔断）
    HALF_OPEN = "half_open" # 半开状态（试探）


@dataclass
class ErrorInfo:
    """错误信息"""
    error_type: ErrorType
    message: str
    timestamp: datetime
    traceback_info: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        """初始化错误处理器"""
        self.logger = get_enhanced_logger()
        self.error_counts = {}  # 错误计数
        self.error_logs = []    # 错误日志
        self.max_log_entries = 1000  # 最大日志条目数
        self.lock = threading.RLock()
    
    def log_error(self, error_type: ErrorType, message: str, 
                  context: Optional[Dict[str, Any]] = None, 
                  exception: Optional[Exception] = None):
        """
        记录错误
        
        Args:
            error_type: 错误类型
            message: 错误消息
            context: 上下文信息
            exception: 异常对象
        """
        with self.lock:
            # 增加错误计数
            key = f"{error_type.value}_{message}"
            self.error_counts[key] = self.error_counts.get(key, 0) + 1
            
            # 记录错误日志
            traceback_info = traceback.format_exc() if exception else None
            error_info = ErrorInfo(
                error_type=error_type,
                message=message,
                timestamp=datetime.now(),
                traceback_info=traceback_info,
                context=context
            )
            
            self.error_logs.append(error_info)
            
            # 限制日志条目数量
            if len(self.error_logs) > self.max_log_entries:
                self.error_logs = self.error_logs[-self.max_log_entries:]
            
            # 记录到日志
            self.logger.err.info(f'{error_type.value}: {message}', {
                'context': context,
                'timestamp': error_info.timestamp.isoformat()
            })
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Returns:
            错误统计信息
        """
        with self.lock:
            total_errors = sum(self.error_counts.values())
            recent_errors = self.error_logs[-10:] if self.error_logs else []
            
            return {
                "total_errors": total_errors,
                "error_types": {k: v for k, v in self.error_counts.items()},
                "recent_errors": [
                    {
                        "type": error.error_type.value,
                        "message": error.message,
                        "timestamp": error.timestamp.isoformat(),
                        "context": error.context
                    }
                    for error in recent_errors
                ],
                "timestamp": datetime.now().isoformat()
            }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理错误并返回标准化错误响应
        
        Args:
            error: 异常对象
            context: 上下文信息
            
        Returns:
            标准化错误响应
        """
        error_type = self._classify_error(error)
        error_msg = str(error)
        
        self.log_error(error_type, error_msg, context, error)
        
        # 根据错误类型返回不同的响应
        if error_type == ErrorType.CLIENT_ERROR:
            status_code = 400
        elif error_type == ErrorType.TIMEOUT_ERROR:
            status_code = 408
        elif error_type == ErrorType.RESOURCE_ERROR:
            status_code = 507
        else:
            status_code = 500  # 默认服务器错误
        
        return {
            "code": status_code,
            "msg": f"请求处理失败: {error_msg}",
            "data": None,
            "error_type": error_type.value,
            "timestamp": datetime.now().isoformat()
        }
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """分类错误类型"""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return ErrorType.TIMEOUT_ERROR
        elif "connection" in error_str or "network" in error_str:
            return ErrorType.NETWORK_ERROR
        elif "memory" in error_str or "disk" in error_str:
            return ErrorType.RESOURCE_ERROR
        elif "400" in error_str or "bad request" in error_str:
            return ErrorType.CLIENT_ERROR
        elif "500" in error_str or "internal server" in error_str:
            return ErrorType.SERVER_ERROR
        else:
            return ErrorType.SERVER_ERROR


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, 
                 half_open_tries: int = 1):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间（秒）
            half_open_tries: 半开状态尝试次数
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_tries = half_open_tries
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        self.lock = threading.RLock()
        
        self.logger = get_enhanced_logger()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        调用受熔断器保护的函数
        
        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                # 检查是否到了恢复时间
                if (self.last_failure_time and 
                    time.time() - self.last_failure_time >= self.recovery_timeout):
                    self.state = CircuitState.HALF_OPEN
                    self.logger.info("熔断器进入半开状态")
                else:
                    raise Exception(f"熔断器开启: {func.__name__} 被拒绝")
            
            try:
                result = func(*args, **kwargs)
                
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= self.half_open_tries:
                        # 恢复到关闭状态
                        self._reset()
                        self.logger.info("熔断器恢复正常状态")
                else:
                    # 重置失败计数
                    self._reset()
                
                return result
                
            except Exception as e:
                self._record_failure()
                raise e
    
    async def acall(self, func: Callable, *args, **kwargs) -> Any:
        """
        异步调用受熔断器保护的函数
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                # 检查是否到了恢复时间
                if (self.last_failure_time and 
                    time.time() - self.last_failure_time >= self.recovery_timeout):
                    self.state = CircuitState.HALF_OPEN
                    self.logger.info("熔断器进入半开状态")
                else:
                    raise Exception(f"熔断器开启: {func.__name__} 被拒绝")
            
            try:
                result = await func(*args, **kwargs)
                
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= self.half_open_tries:
                        # 恢复到关闭状态
                        self._reset()
                        self.logger.info("熔断器恢复正常状态")
                else:
                    # 重置失败计数
                    self._reset()
                
                return result
                
            except Exception as e:
                self._record_failure()
                raise e
    
    def _record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(f"熔断器开启: 达到失败阈值 {self.failure_threshold}")
    
    def _reset(self):
        """重置熔断器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0


class FallbackManager:
    """降级管理器"""
    
    def __init__(self):
        """初始化降级管理器"""
        self.fallback_functions = {}
        self.logger = get_enhanced_logger()
    
    def register_fallback(self, service_name: str, fallback_func: Callable):
        """
        注册降级函数
        
        Args:
            service_name: 服务名称
            fallback_func: 降级函数
        """
        self.fallback_functions[service_name] = fallback_func
        self.logger.info(f"注册降级函数: {service_name}")
    
    def get_fallback(self, service_name: str) -> Optional[Callable]:
        """
        获取降级函数
        
        Args:
            service_name: 服务名称
            
        Returns:
            降级函数
        """
        return self.fallback_functions.get(service_name)
    
    async def execute_with_fallback(self, primary_func: Callable, 
                                   service_name: str, 
                                   *args, **kwargs) -> Any:
        """
        执行主函数，失败时使用降级函数
        
        Args:
            primary_func: 主函数
            service_name: 服务名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
        """
        try:
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*args, **kwargs)
            else:
                return primary_func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"主函数执行失败: {str(e)}，尝试降级")
            
            fallback_func = self.get_fallback(service_name)
            if fallback_func:
                try:
                    if asyncio.iscoroutinefunction(fallback_func):
                        result = await fallback_func(*args, **kwargs)
                    else:
                        result = fallback_func(*args, **kwargs)
                    
                    self.logger.info(f"降级函数执行成功: {service_name}")
                    return result
                except Exception as fallback_error:
                    self.logger.sys.error('Fallback function also failed', {'error': str(fallback_error)})
                    raise e  # 重新抛出原始错误
            else:
                self.logger.warning(f"未找到降级函数: {service_name}")
                raise e


class FaultToleranceManager:
    """容错管理器"""
    
    def __init__(self):
        """初始化容错管理器"""
        self.logger = get_enhanced_logger()
        self.error_handler = ErrorHandler()
        self.circuit_breakers = {}
        self.fallback_manager = FallbackManager()
        self.lock = threading.RLock()
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """
        获取熔断器
        
        Args:
            service_name: 服务名称
            
        Returns:
            熔断器实例
        """
        with self.lock:
            if service_name not in self.circuit_breakers:
                self.circuit_breakers[service_name] = CircuitBreaker()
            return self.circuit_breakers[service_name]
    
    def register_fallback(self, service_name: str, fallback_func: Callable):
        """
        注册降级函数
        
        Args:
            service_name: 服务名称
            fallback_func: 降级函数
        """
        self.fallback_manager.register_fallback(service_name, fallback_func)
    
    def execute_with_fault_tolerance(self, service_name: str, 
                                   primary_func: Callable, 
                                   *args, **kwargs) -> Any:
        """
        执行带容错的函数
        
        Args:
            service_name: 服务名称
            primary_func: 主函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
        """
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        try:
            # 通过熔断器执行
            return circuit_breaker.call(
                self.fallback_manager.execute_with_fallback,
                primary_func, service_name, *args, **kwargs
            )
        except Exception as e:
            # 处理错误
            return self.error_handler.handle_error(e, {
                "service_name": service_name,
                "function_name": primary_func.__name__
            })
    
    async def aexecute_with_fault_tolerance(self, service_name: str, 
                                         primary_func: Callable, 
                                         *args, **kwargs) -> Any:
        """
        异步执行带容错的函数
        """
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        try:
            # 通过熔断器执行
            return await circuit_breaker.acall(
                self.fallback_manager.execute_with_fallback,
                primary_func, service_name, *args, **kwargs
            )
        except Exception as e:
            # 处理错误
            return self.error_handler.handle_error(e, {
                "service_name": service_name,
                "function_name": primary_func.__name__
            })
    
    def retry_with_backoff(self, max_retries: int = 3, 
                          base_delay: float = 1.0, 
                          max_delay: float = 60.0,
                          backoff_factor: float = 2.0,
                          jitter: bool = True):
        """
        带退避的重试装饰器
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟
            max_delay: 最大延迟
            backoff_factor: 退避因子
            jitter: 是否添加抖动
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            # 计算延迟时间
                            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                            if jitter:
                                import random
                                delay *= (0.5 + random.random() * 0.5)  # 添加抖动
                        
                            self.logger.info(f"第 {attempt + 1} 次重试，延迟 {delay:.2f}s: {str(e)}")
                            await asyncio.sleep(delay)
                        else:
                            self.logger.sys.error('Retry failed', {'error': str(e), 'attempts': max_retries + 1})
                
                raise last_exception
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            # 计算延迟时间
                            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                            if jitter:
                                import random
                                delay *= (0.5 + random.random() * 0.5)  # 添加抖动
                        
                            self.logger.info(f"第 {attempt + 1} 次重试，延迟 {delay:.2f}s: {str(e)}")
                            time.sleep(delay)
                        else:
                            self.logger.sys.error('Retry failed', {'error': str(e), 'attempts': max_retries + 1})
                
                raise last_exception
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态
        
        Returns:
            健康状态信息
        """
        with self.lock:
            circuit_states = {
                name: cb.state.value for name, cb in self.circuit_breakers.items()
            }
            
            return {
                "circuit_breakers": circuit_states,
                "error_stats": self.error_handler.get_error_stats(),
                "timestamp": datetime.now().isoformat()
            }


# 全局容错管理器实例
_fault_tolerance_manager = None
_fault_tolerance_manager_lock = threading.Lock()


def get_fault_tolerance_manager() -> FaultToleranceManager:
    """获取容错管理器单例"""
    global _fault_tolerance_manager
    if _fault_tolerance_manager is None:
        with _fault_tolerance_manager_lock:
            if _fault_tolerance_manager is None:
                _fault_tolerance_manager = FaultToleranceManager()
    return _fault_tolerance_manager


def execute_with_fault_tolerance(service_name: str, primary_func: Callable, 
                               *args, **kwargs) -> Any:
    """执行带容错的函数"""
    manager = get_fault_tolerance_manager()
    return manager.execute_with_fault_tolerance(service_name, primary_func, 
                                             *args, **kwargs)


def aexecute_with_fault_tolerance(service_name: str, primary_func: Callable, 
                                *args, **kwargs) -> Any:
    """异步执行带容错的函数"""
    manager = get_fault_tolerance_manager()
    return manager.aexecute_with_fault_tolerance(service_name, primary_func, 
                                              *args, **kwargs)


def register_fallback(service_name: str, fallback_func: Callable):
    """注册降级函数"""
    manager = get_fault_tolerance_manager()
    manager.register_fallback(service_name, fallback_func)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                      max_delay: float = 60.0, backoff_factor: float = 2.0, 
                      jitter: bool = True):
    """带退避的重试装饰器"""
    manager = get_fault_tolerance_manager()
    return manager.retry_with_backoff(max_retries, base_delay, max_delay, 
                                    backoff_factor, jitter)


def get_health_status() -> Dict[str, Any]:
    """获取健康状态"""
    manager = get_fault_tolerance_manager()
    return manager.get_health_status()