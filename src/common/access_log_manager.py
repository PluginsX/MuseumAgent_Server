# -*- coding: utf-8 -*-
"""
访问日志管理器

高性能的访问记录登记机制，采用异步队列和批量处理方案，
确保不阻塞主通信线程，同时保证所有访问记录都能被正确写入数据库。
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
import queue
import threading
from datetime import datetime

from src.common.enhanced_logger import get_enhanced_logger
from src.db.database import get_engine
from src.db.models import ServerAccessLog


class AccessLogManager:
    """访问日志管理器"""
    
    def __init__(self):
        """初始化访问日志管理器"""
        self.logger = get_enhanced_logger()
        self.log_queue = queue.Queue(maxsize=20000)  # 增大队列大小，适应高吞吐
        self.batch_size = 100  # 增大批量处理大小，提高写入效率
        self.batch_timeout = 1.0  # 减少批量处理超时时间，确保日志及时写入
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
                # 尝试从队列中获取日志记录，设置超时
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
                time.sleep(1)  # 避免无限循环
        
        # 退出前处理剩余的日志记录
        if batch:
            self._write_batch(batch)
    
    def _write_batch(self, batch: List[Dict[str, Any]]):
        """批量写入日志记录到数据库"""
        if not batch:
            return
        
        try:
            engine = get_engine()
            with engine.connect() as connection:
                # 构建批量插入语句
                values_list = []
                for record in batch:
                    values = {
                        'admin_user_id': record.get('admin_user_id'),
                        'client_user_id': record.get('client_user_id'),
                        'request_type': record.get('request_type'),
                        'endpoint': record.get('endpoint'),
                        'ip_address': record.get('ip_address'),
                        'user_agent': record.get('user_agent'),
                        'status_code': record.get('status_code'),
                        'response_time': record.get('response_time'),
                        'details': record.get('details'),
                        'created_at': record.get('created_at', datetime.now())
                    }
                    values_list.append(values)
                
                # 执行批量插入
                if values_list:
                    # 使用SQLAlchemy的批量插入 - 优化版本
                    from sqlalchemy import text
                    
                    # 构建插入语句
                    columns = ', '.join(values_list[0].keys())
                    
                    # 构建VALUES子句 - 使用更简洁的方式
                    values_clauses = []
                    params = {}
                    
                    for i, values in enumerate(values_list):
                        # 为每条记录构建占位符
                        placeholders = []
                        for k, v in values.items():
                            # 使用更唯一的参数名，避免冲突
                            param_name = f"{k}_{i}"
                            placeholders.append(f":{param_name}")
                            params[param_name] = v
                        
                        # 构建一条记录的VALUES子句
                        values_clauses.append(f"({', '.join(placeholders)})")
                    
                    # 构建完整的SQL语句
                    values_part = ', '.join(values_clauses)
                    sql = f"INSERT INTO server_access_logs ({columns}) VALUES {values_part}"
                    
                    # 执行插入
                    connection.execute(text(sql), params)
                    connection.commit()
                    
                    self.logger.sys.debug(f"Batch wrote {len(batch)} access log records")
                    
        except Exception as e:
            self.logger.sys.error(f"Error writing access log batch: {str(e)}")
            # 可以在这里添加重试机制
            # 重试一次
            try:
                time.sleep(0.1)
                engine = get_engine()
                with engine.connect() as connection:
                    # 简化版本：逐条插入，确保至少部分记录能写入
                    for record in batch:
                        try:
                            values = {
                                'admin_user_id': record.get('admin_user_id'),
                                'client_user_id': record.get('client_user_id'),
                                'request_type': record.get('request_type'),
                                'endpoint': record.get('endpoint'),
                                'ip_address': record.get('ip_address'),
                                'user_agent': record.get('user_agent'),
                                'status_code': record.get('status_code'),
                                'response_time': record.get('response_time'),
                                'details': record.get('details'),
                                'created_at': record.get('created_at', datetime.now())
                            }
                            
                            # 构建单条插入语句
                            columns = ', '.join(values.keys())
                            placeholders = ', '.join([f":{k}" for k in values.keys()])
                            sql = f"INSERT INTO server_access_logs ({columns}) VALUES ({placeholders})"
                            
                            connection.execute(text(sql), values)
                        except Exception as e2:
                            self.logger.sys.error(f"Error writing single access log record: {str(e2)}")
                    connection.commit()
                    self.logger.sys.debug(f"Retry: Wrote access log records one by one")
            except Exception as e3:
                self.logger.sys.error(f"Retry failed: {str(e3)}")
    
    def add_log(self, log_record: Dict[str, Any]):
        """添加日志记录到队列
        
        Args:
            log_record: 日志记录字典，包含以下字段：
                - admin_user_id: 管理员用户ID（可选）
                - client_user_id: 客户用户ID（可选）
                - request_type: 请求类型
                - endpoint: 请求端点
                - ip_address: IP地址（可选）
                - user_agent: 用户代理（可选）
                - status_code: 状态码
                - response_time: 响应时间（可选）
                - details: 详细信息（可选）
                - created_at: 创建时间（可选，默认为当前时间）
        """
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
                # 可以在这里添加备用存储机制，如文件存储
                
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
    """访问日志上下文管理器
    
    用于自动记录请求的开始和结束时间，计算响应时间并记录。
    """
    
    def __init__(self, log_record: Dict[str, Any]):
        """初始化访问日志上下文管理器
        
        Args:
            log_record: 日志记录字典，包含请求的基本信息
        """
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
        return False  # 不抑制异常


def access_log_decorator(endpoint: str, request_type: str = "HTTP"):
    """访问日志装饰器
    
    用于HTTP API路由，自动记录API调用。
    
    Args:
        endpoint: API端点
        request_type: 请求类型
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从请求中获取信息
            # 注意：这里需要根据实际情况调整，获取请求的IP地址、用户代理等信息
            # 由于FastAPI的依赖注入机制，可能需要从request对象中获取这些信息
            
            # 构建日志记录
            log_record = {
                'request_type': request_type,
                'endpoint': endpoint,
                'status_code': 200,  # 默认状态码
                # 其他字段需要根据实际情况填充
            }
            
            # 使用上下文管理器记录访问
            with AccessLogContext(log_record):
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
