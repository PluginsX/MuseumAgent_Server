# -*- coding: utf-8 -*-
"""
配置读取工具 - 加载JSON/INI配置，提供全局配置访问接口
"""
import json
import os
from configparser import ConfigParser
from typing import Any, Optional

# 全局配置变量
GLOBAL_CONFIG: Optional[dict] = None
GLOBAL_INI_CONFIG: Optional[ConfigParser] = None

# 默认配置文件路径（相对于项目根目录）
DEFAULT_JSON_CONFIG_PATH = "./config/config.json"
DEFAULT_INI_CONFIG_PATH = "./config/config.ini"


def load_config(
    json_path: Optional[str] = None,
    ini_path: Optional[str] = None
) -> None:
    """
    加载JSON和INI配置文件，初始化全局配置
    项目启动时仅执行一次，避免重复IO操作
    
    Args:
        json_path: JSON配置文件路径，默认 ./config/config.json
        ini_path: INI配置文件路径，默认 ./config/config.ini
    
    Raises:
        FileNotFoundError: 配置文件不存在
        json.JSONDecodeError: JSON格式错误
        ValueError: 配置项缺失
    """
    global GLOBAL_CONFIG, GLOBAL_INI_CONFIG
    
    json_path = json_path or DEFAULT_JSON_CONFIG_PATH
    ini_path = ini_path or DEFAULT_INI_CONFIG_PATH
    
    # 解析相对路径为绝对路径（相对于项目根目录）
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_full_path = os.path.normpath(os.path.join(base_dir, json_path))
    ini_full_path = os.path.normpath(os.path.join(base_dir, ini_path))
    
    # 加载JSON配置
    if not os.path.exists(json_full_path):
        raise FileNotFoundError(f"JSON配置文件不存在: {json_full_path}")
    
    try:
        with open(json_full_path, "r", encoding="utf-8") as f:
            GLOBAL_CONFIG = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"JSON配置文件格式错误: {e.msg}",
            e.doc, e.pos
        ) from e
    
    # 校验必需配置项
    required_keys = ["server", "llm", "artifact_knowledge_base", "response"]
    for key in required_keys:
        if key not in GLOBAL_CONFIG:
            raise ValueError(f"JSON配置缺少必需项: {key}")
    
    # 加载INI配置
    if not os.path.exists(ini_full_path):
        raise FileNotFoundError(f"INI配置文件不存在: {ini_full_path}")
    
    GLOBAL_INI_CONFIG = ConfigParser()
    GLOBAL_INI_CONFIG.read(ini_full_path, encoding="utf-8")


def get_global_config() -> dict:
    """
    获取JSON全局配置（只读）
    
    Returns:
        全局JSON配置字典
    
    Raises:
        RuntimeError: 配置未加载
    """
    if GLOBAL_CONFIG is None:
        raise RuntimeError("全局配置未加载，请先调用 load_config()")
    return GLOBAL_CONFIG


def get_global_ini_config() -> ConfigParser:
    """
    获取INI全局配置（只读）
    
    Returns:
        全局INI配置对象
    
    Raises:
        RuntimeError: 配置未加载
    """
    if GLOBAL_INI_CONFIG is None:
        raise RuntimeError("INI配置未加载，请先调用 load_config()")
    return GLOBAL_INI_CONFIG


def get_config_by_key(*keys: str) -> Any:
    """
    按层级键获取配置的快捷方法
    
    Args:
        *keys: 层级键，如 get_config_by_key("llm", "provider")
    
    Returns:
        配置值
    
    Example:
        get_config_by_key("llm", "provider") -> "dashscope"
        get_config_by_key("server", "port") -> 8000
    """
    config = get_global_config()
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise KeyError(f"配置项不存在: {' -> '.join(keys)}")
    return value
