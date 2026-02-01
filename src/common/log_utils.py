# -*- coding: utf-8 -*-
"""
日志工具 - 初始化日志配置，定义统一日志格式、存储路径、分割规则
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

# 默认日志配置
DEFAULT_LOG_PATH = "./logs/"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_MAX_SIZE = 10485760  # 10MB
DEFAULT_LOG_BACKUP_COUNT = 7

# 日志格式：时间、模块名、函数名、行号、日志级别、内容
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d %(funcName)s] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志器名称
LOGGER_NAME = "museum_agent"

# 日志文件名
LOG_FILE_NAME = "museum_agent.log"
ERROR_LOG_FILE_NAME = "museum_agent_error.log"


def init_logger(
    log_path: Optional[str] = None,
    log_level: Optional[str] = None,
    log_max_size: Optional[int] = None,
    log_backup_count: Optional[int] = None
) -> logging.Logger:
    """
    初始化日志配置，从INI配置中读取日志参数
    
    Args:
        log_path: 日志存储路径
        log_level: 日志级别 DEBUG/INFO/WARNING/ERROR/CRITICAL
        log_max_size: 单个日志文件最大大小（字节）
        log_backup_count: 日志备份文件数量
    
    Returns:
        配置好的Logger实例
    """
    try:
        from src.common.config_utils import get_global_ini_config
        ini_config = get_global_ini_config()
        
        log_path = log_path or ini_config.get("log", "log_path", fallback=DEFAULT_LOG_PATH)
        log_level = log_level or ini_config.get("log", "log_level", fallback=DEFAULT_LOG_LEVEL)
        log_max_size = log_max_size or ini_config.getint("log", "log_max_size", fallback=DEFAULT_LOG_MAX_SIZE)
        log_backup_count = log_backup_count or ini_config.getint("log", "log_backup_count", fallback=DEFAULT_LOG_BACKUP_COUNT)
    except Exception:
        log_path = log_path or DEFAULT_LOG_PATH
        log_level = log_level or DEFAULT_LOG_LEVEL
        log_max_size = log_max_size or DEFAULT_LOG_MAX_SIZE
        log_backup_count = log_backup_count or DEFAULT_LOG_BACKUP_COUNT
    
    # 解析路径为绝对路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.normpath(os.path.join(base_dir, log_path))
    
    # 自动创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 获取或创建logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 清除已有处理器，避免重复添加
    logger.handlers.clear()
    
    # 日志格式器
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # 1. 控制台处理器（开发调试）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. 普通文件处理器（所有运行日志）
    log_file_path = os.path.join(log_dir, LOG_FILE_NAME)
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=log_max_size,
        backupCount=log_backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 3. 错误文件处理器（仅ERROR/CRITICAL）
    error_log_path = os.path.join(log_dir, ERROR_LOG_FILE_NAME)
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=log_max_size,
        backupCount=log_backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


def get_logger() -> logging.Logger:
    """
    获取museum_agent日志器，若未初始化则使用默认配置初始化
    
    Returns:
        Logger实例
    """
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        return init_logger()
    return logger
