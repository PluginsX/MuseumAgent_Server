# -*- coding: utf-8 -*-
"""
性能优化策略
实现缓存、异步处理、连接池等性能优化功能
"""
import asyncio
import time
import hashlib
import pickle
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from functools import wraps
import threading
from collections import OrderedDict
import aioredis

from src.common.enhanced_logger import get_enhanced_logger


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """
        初始化LRU缓存
        
        Args:
            max_size: 最大缓存大小
            ttl_seconds: TTL（生存时间）秒数
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.lock = threading.RLock()
    
    def _clean_expired(self):
        """清理过期项"""
        current_time = time.time()
        expired_keys = []
        
        for key, (value, expiry_time) in self.cache.items():
            if current_time > expiry_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        with self.lock:
            self._clean_expired()
            
            if key in self.cache:
                value, expiry_time = self.cache[key]
                current_time = time.time()
                
                if current_time <= expiry_time:
                    # 移动到末尾（最近使用）
                    del self.cache[key]
                    self.cache[key] = (value, expiry_time)
                    return value
                else:
                    # 过期，删除
                    del self.cache[key]
        
        return None
    
    def set(self, key: str, value: Any):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self.lock:
            self._clean_expired()
            
            current_time = time.time()
            expiry_time = current_time + self.ttl_seconds
            
            if key in self.cache:
                # 更新现有项
                del self.cache[key]
            elif len(self.cache) >= self.max_size:
                # 删除最久未使用的项
                self.cache.popitem(last=False)
            
            self.cache[key] = (value, expiry_time)
    
    def delete(self, key: str):
        """
        删除缓存项
        
        Args:
            key: 缓存键
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        """初始化性能优化器"""
        self.logger = get_enhanced_logger()
        
        # L1缓存（内存缓存）
        self.l1_cache = LRUCache(max_size=1000, ttl_seconds=300)
        
        # L2缓存（Redis缓存）- 如果可用
        self.l2_cache = None
        self._init_redis_cache()
        
        # 连接池
        self.connection_pools = {}
        
        # 任务队列
        self.task_queues = {}
        
        self.logger.sys.info('Performance optimizer initialized')
    
    def _init_redis_cache(self):
        """初始化Redis缓存"""
        try:
            # 这里可以连接到Redis服务器
            # self.l2_cache = aioredis.from_url("redis://localhost:6379", decode_responses=True)
            self.logger.sys.info('Redis cache not enabled (Redis server configuration required)')
        except Exception as e:
            self.logger.sys.warn(f'Redis cache initialization failed: {str(e)}')
    
    def cache_result(self, ttl_seconds: int = 300, max_size: int = 1000):
        """
        缓存装饰器
        
        Args:
            ttl_seconds: 缓存TTL（秒）
            max_size: 最大缓存大小
        """
        def decorator(func: Callable) -> Callable:
            cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # 尝试从缓存获取
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    self.logger.sys.info('Cache hit', {'function': func.__name__, 'key': cache_key})
                    return cached_result
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 存入缓存
                cache.set(cache_key, result)
                self.logger.sys.info('Cache miss, stored', {'function': func.__name__, 'key': cache_key})
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # 尝试从缓存获取
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    self.logger.sys.info('Cache hit', {'function': func.__name__, 'key': cache_key})
                    return cached_result
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 存入缓存
                cache.set(cache_key, result)
                self.logger.sys.info('Cache miss, stored', {'function': func.__name__, 'key': cache_key})
                
                return result
            
            # 根据函数是否为异步来选择包装器
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 将参数序列化为字符串
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def execute_with_retry(self, func: Callable, max_retries: int = 3, 
                                delay: float = 1.0, backoff: float = 2.0) -> Any:
        """
        带重试的函数执行
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            delay: 初始延迟时间
            backoff: 延迟倍数
            
        Returns:
            函数执行结果
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    sleep_time = delay * (backoff ** attempt)
                    self.logger.sys.info('Retry attempt', 
                                  {'attempt': attempt + 1, 'function': func.__name__, 'sleep': sleep_time, 'error': str(e)})
                    await asyncio.sleep(sleep_time)
                else:
                    self.logger.sys.error('Retry failed', 
                                  {'attempts': max_retries + 1, 'function': func.__name__, 'error': str(e)})
        
        raise last_exception
    
    def rate_limit(self, max_calls: int, time_window: int):
        """
        速率限制装饰器
        
        Args:
            max_calls: 时间窗口内的最大调用次数
            time_window: 时间窗口（秒）
        """
        def decorator(func: Callable) -> Callable:
            calls = []
            lock = threading.Lock()
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                nonlocal calls
                current_time = time.time()
                
                with lock:
                    # 清理过期的调用记录
                    calls = [call_time for call_time in calls if current_time - call_time < time_window]
                    
                    if len(calls) >= max_calls:
                        raise Exception(f"速率限制超出: {max_calls} 次/{time_window}秒")
                    
                    calls.append(current_time)
                
                return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                nonlocal calls
                current_time = time.time()
                
                with lock:
                    # 清理过期的调用记录
                    calls = [call_time for call_time in calls if current_time - call_time < time_window]
                    
                    if len(calls) >= max_calls:
                        raise Exception(f"速率限制超出: {max_calls} 次/{time_window}秒")
                    
                    calls.append(current_time)
                
                return func(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def bulk_execute(self, tasks: list, concurrency: int = 10) -> list:
        """
        批量并发执行任务
        
        Args:
            tasks: 任务列表
            concurrency: 并发数
            
        Returns:
            执行结果列表
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_task(task):
            async with semaphore:
                if asyncio.iscoroutinefunction(task):
                    return await task()
                else:
                    return task()
        
        coroutines = [limited_task(task) for task in tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        return results
    
    def measure_performance(self, name: str = None):
        """
        性能测量装饰器
        
        Args:
            name: 操作名称
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                start_cpu = time.process_time()
                
                try:
                    result = await func(*args, **kwargs)
                    success = True
                except Exception as e:
                    result = e
                    success = False
                
                end_time = time.perf_counter()
                end_cpu = time.process_time()
                
                duration = end_time - start_time
                cpu_time = end_cpu - start_cpu
                
                op_name = name or func.__name__
                self.logger.sys.info('Performance measurement', {
                    'operation': op_name,
                    'duration_ms': round(duration * 1000, 2),
                    'cpu_time_ms': round(cpu_time * 1000, 2),
                    'success': success
                })
                
                if not success:
                    raise result
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                start_cpu = time.process_time()
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    result = e
                    success = False
                
                end_time = time.perf_counter()
                end_cpu = time.process_time()
                
                duration = end_time - start_time
                cpu_time = end_cpu - start_cpu
                
                op_name = name or func.__name__
                self.logger.sys.info('Performance measurement', {
                    'operation': op_name,
                    'duration_ms': round(duration * 1000, 2),
                    'cpu_time_ms': round(cpu_time * 1000, 2),
                    'success': success
                })
                
                if not success:
                    raise result
                
                return result
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def warmup_cache(self, func: Callable, args_list: list):
        """
        预热缓存
        
        Args:
            func: 带缓存装饰器的函数
            args_list: 参数列表
        """
        self.logger.sys.info('Starting cache warmup', {'function': func.__name__, 'count': len(args_list)})
        
        for args in args_list:
            if isinstance(args, tuple):
                await func(*args)
            else:
                await func(args)
        
        self.logger.sys.info('Cache warmup completed', {'function': func.__name__})


# 全局性能优化器实例
_performance_optimizer = None
_performance_optimizer_lock = threading.Lock()


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取性能优化器单例"""
    global _performance_optimizer
    if _performance_optimizer is None:
        with _performance_optimizer_lock:
            if _performance_optimizer is None:
                _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def cache_result(ttl_seconds: int = 300, max_size: int = 1000):
    """缓存装饰器"""
    optimizer = get_performance_optimizer()
    return optimizer.cache_result(ttl_seconds, max_size)


def execute_with_retry(func: Callable, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """带重试的函数执行"""
    optimizer = get_performance_optimizer()
    return optimizer.execute_with_retry(func, max_retries, delay, backoff)


def rate_limit(max_calls: int, time_window: int):
    """速率限制装饰器"""
    optimizer = get_performance_optimizer()
    return optimizer.rate_limit(max_calls, time_window)


def measure_performance(name: str = None):
    """性能测量装饰器"""
    optimizer = get_performance_optimizer()
    return optimizer.measure_performance(name)