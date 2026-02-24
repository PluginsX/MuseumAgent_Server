# -*- coding: utf-8 -*-
"""
访问日志管理器

高性能的访问记录登记机制，采用异步队列和批量处理方案，
确保不阻塞主通信线程，同时保证所有访问记录都能被正确写入数据库。
"""
import time
from typing import Dict, Any, List
import queue
import threading
from datetime import datetime

from src.common.enhanced_logger import get_enhanced_logger
from src.services import database_service


class AccessLogManager:
    """访问日志管理器"""
    
    def __init__(self):
        """初始化访问日志管理器"""
        self.logger = get_enhanced_logger()
        self.log_queue = queue.Queue(maxsize=20000)
        self.batch_size = 100
        self.batch_timeout = 1.0
        self.running = False
        self.worker_thread = None
        self._start_worker()
    
    def _start_worker(self):
        """启动工作线程"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            self.logger.sys.info("Access log worker thread started")
    
    def _process_queue(self):
        """处理队列中的日志记录"""
        batch: List[Dict[str, Any]] = []
        last_batch_time = time.time()
        
        while self.running:
            try:
                # 尝试从队列中获取日志记录
                try:
                    log_record = self.log_queue.get(timeout=0.5)
                    batch.append(log_record)
                except queue.Empty:
                    pass
                
                # 检查是否需要批量处理
                current_time = time.time()
                if len(batch) >= self.batch_size or (batch and current_time - last_batch_time >= self.batch_timeout):
                    self._write_batch(batch)
                    batch = []
                    last_batch_time = current_time
                    
            except Exception as e:
                self.logger.sys.error(f"Error processing access log queue: {str(e)}")
                time.sleep(1)
        
        # 退出前处理剩余的日志记录
        if batch:
            self._write_batch(batch)
    
    def _write_batch(self, batch: List[Dict[str, Any]]):
        """批量写入日志记录到数据库"""
        if not batch:
            return
        
        try:
            # 使用数据库服务层批量写入
            count = database_service.batch_create_access_logs(batch)
            self.logger.sys.debug(f"Batch wrote {count} access log records")
        except Exception as e:
            self.logger.sys.error(f"Error writing access log batch: {str(e)}")
    
    def add_log(self, log_record: Dict[str, Any]):
        """添加日志记录到队列"""
        try:
            # 确保必填字段存在
            required_fields = ['request_type', 'endpoint', 'status_code']
            for field in required_fields:
                if field not in log_record:
                    self.logger.sys.error(f"Missing required field {field} in access log record")
                    return
            
            # 添加默认值
            if 'created_at' not in log_record:
                log_record['created_at'] = datetime.now()
            
            # 添加到队列
            try:
                self.log_queue.put(log_record, block=False)
            except queue.Full:
                self.logger.sys.warning("Access log queue is full, dropping log record")
                
        except Exception as e:
            self.logger.sys.error(f"Error adding access log record: {str(e)}")
    
    def shutdown(self):
        """关闭访问日志管理器"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
            self.logger.sys.info("Access log worker thread stopped")


# 创建全局访问日志管理器实例
access_log_manager = AccessLogManager()


class AccessLogContext:
    """访问日志上下文管理器"""
    
    def __init__(self, log_record: Dict[str, Any]):
        """初始化访问日志上下文管理器"""
        self.log_record = log_record
        self.start_time = None
    
    def __enter__(self):
        """进入上下文"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.start_time:
            # 计算响应时间（毫秒）
            response_time = int((time.time() - self.start_time) * 1000)
            self.log_record['response_time'] = response_time
        
        # 处理异常
        if exc_type:
            self.log_record['status_code'] = 500
            if 'details' not in self.log_record:
                self.log_record['details'] = f"Error: {str(exc_val)}"
        
        # 添加到日志队列
        access_log_manager.add_log(self.log_record)
        return False


def access_log_decorator(endpoint: str, request_type: str = "HTTP"):
    """访问日志装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            log_record = {
                'request_type': request_type,
                'endpoint': endpoint,
                'status_code': 200,
            }
            
            with AccessLogContext(log_record):
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
