# -*- coding: utf-8 -*-
"""
增强型日志系统
提供统一、简洁、结构化的日志输出
"""
import logging
import json
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
from functools import wraps

# 默认配置
DEFAULT_LOG_PATH = "./logs/"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_MAX_SIZE = 10485760  # 10MB
DEFAULT_LOG_BACKUP_COUNT = 7
DEFAULT_LOGGER_NAME = "enhanced_museum_agent"

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class Module(Enum):
    """模块枚举"""
    VOICE = "VOICE"    # 语音处理 (TTS/STT)
    WS = "WS"          # WebSocket通信
    API = "API"        # API请求处理
    AUTH = "AUTH"      # 认证授权
    SESS = "SESS"      # 会话管理
    AUDIO = "AUDIO"    # 音频处理
    LLM = "LLM"        # 语言模型
    RAG = "RAG"        # 检索增强生成
    FUNC = "FUNC"      # 函数调用
    CLI = "CLI"        # 客户端交互
    SYS = "SYS"        # 系统操作
    DB = "DB"          # 数据库操作
    CACHE = "CACHE"    # 缓存操作
    NET = "NET"        # 网络通信
    ERR = "ERR"        # 错误处理
    TTS = "TTS"        # 文本转语音
    STT = "STT"        # 语音转文本

class LogLevel(Enum):
    """日志级别枚举"""
    TRACE = "DEBUG"  # 映射到DEBUG级别，但标记为TRACE
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARNING"
    ERROR = "ERROR"
    FATAL = "CRITICAL"

class EnhancedLogFormatter:
    """增强型日志格式化器"""
    
    def __init__(self, use_color: bool = True):
        self.use_color = use_color
        self.colors = {
            'TRACE': '\033[37m',  # 白色
            'DEBUG': '\033[36m',  # 青色
            'INFO': '\033[32m',   # 绿色
            'WARN': '\033[33m',   # 黄色
            'ERROR': '\033[31m',  # 红色
            'FATAL': '\033[35m',  # 紫色
            'RESET': '\033[0m'    # 重置
        } if use_color and sys.stdout.isatty() else {}
    
    def format(self, module: Module, level: LogLevel, message: str, 
               data: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化日志消息
        
        Args:
            module: 模块标识
            level: 日志级别
            message: 日志消息
            data: 结构化数据
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 添加颜色
        color = self.colors.get(level.value, '')
        reset = self.colors.get('RESET', '')
        
        # 格式化数据
        data_str = ""
        if data:
            data_str = f" | {json.dumps(data, ensure_ascii=False)}"
        
        # 构建日志消息
        log_msg = f"[{timestamp}] [{module.value}] [{level.value}] {color}{message}{reset}{data_str}"
        
        return log_msg

class EnhancedLogger:
    """增强型日志记录器"""
    
    def __init__(self, name: str = DEFAULT_LOGGER_NAME, 
                 log_path: str = DEFAULT_LOG_PATH,
                 log_level: str = DEFAULT_LOG_LEVEL,
                 use_color: bool = True):
        """
        初始化增强型日志记录器
        
        Args:
            name: 记录器名称
            log_path: 日志文件路径
            log_level: 日志级别
            use_color: 是否使用颜色
        """
        self.name = name
        self.log_formatter = EnhancedLogFormatter(use_color)
        
        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # 清除已有处理器
        self.logger.handlers.clear()
        
        # 解析路径为绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.normpath(os.path.join(base_dir, log_path))
        
        # 自动创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        log_file_path = os.path.join(log_dir, f"{name}.log")
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=DEFAULT_LOG_MAX_SIZE,
            backupCount=DEFAULT_LOG_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.addHandler(file_handler)
        
        # 创建各模块的便捷访问器
        self.voice = ModuleLogger(self, Module.VOICE)
        self.ws = ModuleLogger(self, Module.WS)
        self.api = ModuleLogger(self, Module.API)
        self.auth = ModuleLogger(self, Module.AUTH)
        self.sess = ModuleLogger(self, Module.SESS)
        self.audio = ModuleLogger(self, Module.AUDIO)
        self.llm = ModuleLogger(self, Module.LLM)
        self.rag = ModuleLogger(self, Module.RAG)
        self.func = ModuleLogger(self, Module.FUNC)
        self.cli = ModuleLogger(self, Module.CLI)
        self.sys = ModuleLogger(self, Module.SYS)
        self.db = ModuleLogger(self, Module.DB)
        self.cache = ModuleLogger(self, Module.CACHE)
        self.net = ModuleLogger(self, Module.NET)
        self.err = ModuleLogger(self, Module.ERR)
        self.tts = ModuleLogger(self, Module.TTS)
        self.stt = ModuleLogger(self, Module.STT)
    
    def _log(self, module: Module, level: LogLevel, message: str, 
             data: Optional[Dict[str, Any]] = None):
        """内部日志记录方法"""
        # 如果传入的是ModuleLogger实例，则提取其模块
        if hasattr(module, 'module'):
            actual_module = module.module
        else:
            actual_module = module
        formatted_msg = self.log_formatter.format(actual_module, level, message, data)
        log_level = getattr(logging, level.value)
        self.logger.log(log_level, formatted_msg)
    
    def trace(self, module: Module, message: str, 
              data: Optional[Dict[str, Any]] = None):
        """TRACE级别日志"""
        self._log(module, LogLevel.TRACE, message, data)
    
    def debug(self, module: Module, message: str, 
              data: Optional[Dict[str, Any]] = None):
        """DEBUG级别日志"""
        self._log(module, LogLevel.DEBUG, message, data)
    
    def info(self, module: Module, message: str, 
             data: Optional[Dict[str, Any]] = None):
        """INFO级别日志"""
        self._log(module, LogLevel.INFO, message, data)
    
    def warn(self, module: Module, message: str, 
             data: Optional[Dict[str, Any]] = None):
        """WARN级别日志"""
        self._log(module, LogLevel.WARN, message, data)
    
    def error(self, module: Module, message: str, 
              data: Optional[Dict[str, Any]] = None):
        """ERROR级别日志"""
        self._log(module, LogLevel.ERROR, message, data)
    
    def fatal(self, module: Module, message: str, 
              data: Optional[Dict[str, Any]] = None):
        """FATAL级别日志"""
        self._log(module, LogLevel.FATAL, message, data)

class ModuleLogger:
    """模块日志记录器 - 提供便捷的模块级日志记录"""
    
    def __init__(self, parent_logger: EnhancedLogger, module: Module):
        self.parent = parent_logger
        self.module = module
    
    def trace(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.trace(self.module, message, data)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.debug(self.module, message, data)
    
    def info(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.info(self.module, message, data)
    
    def warn(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.warn(self.module, message, data)
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.error(self.module, message, data)
    
    def fatal(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.fatal(self.module, message, data)

def log_api_call(module: Module, operation: str = ""):
    """API调用日志装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = get_enhanced_logger()
            
            # 记录请求开始
            logger.info(
                module,
                f"{operation} request started" if operation else "API request started",
                {
                    "function": func.__name__,
                    "start_time": start_time.isoformat()
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录请求完成
                duration = (datetime.now() - start_time).total_seconds() * 1000  # 毫秒
                logger.info(
                    module,
                    f"{operation} request completed" if operation else "API request completed",
                    {
                        "function": func.__name__,
                        "duration_ms": round(duration, 2),
                        "success": True
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000  # 毫秒
                logger.sys.error(
                    module,
                    f"{operation} request failed" if operation else "API request failed",
                    {
                        "function": func.__name__,
                        "duration_ms": round(duration, 2),
                        "error": str(e),
                        "success": False
                    }
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = get_enhanced_logger()
            
            # 记录请求开始
            logger.info(
                module,
                f"{operation} request started" if operation else "API request started",
                {
                    "function": func.__name__,
                    "start_time": start_time.isoformat()
                }
            )
            
            try:
                result = func(*args, **kwargs)
                
                # 记录请求完成
                duration = (datetime.now() - start_time).total_seconds() * 1000  # 毫秒
                logger.info(
                    module,
                    f"{operation} request completed" if operation else "API request completed",
                    {
                        "function": func.__name__,
                        "duration_ms": round(duration, 2),
                        "success": True
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000  # 毫秒
                logger.sys.error(
                    module,
                    f"{operation} request failed" if operation else "API request failed",
                    {
                        "function": func.__name__,
                        "duration_ms": round(duration, 2),
                        "error": str(e),
                        "success": False
                    }
                )
                raise
        
        # 根据函数是否为协程选择适当的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

# 全局日志记录器实例
_enhanced_logger: Optional[EnhancedLogger] = None

def init_enhanced_logger(name: str = DEFAULT_LOGGER_NAME,
                        log_path: str = DEFAULT_LOG_PATH,
                        log_level: str = DEFAULT_LOG_LEVEL,
                        use_color: bool = True) -> EnhancedLogger:
    """初始化增强型日志记录器"""
    global _enhanced_logger
    _enhanced_logger = EnhancedLogger(name, log_path, log_level, use_color)
    return _enhanced_logger

def get_enhanced_logger() -> EnhancedLogger:
    """获取增强型日志记录器实例"""
    global _enhanced_logger
    if _enhanced_logger is None:
        _enhanced_logger = init_enhanced_logger()
    return _enhanced_logger

# 导入asyncio用于装饰器判断
import asyncio