# -*- coding: utf-8 -*-
"""
响应工具 - 封装标准化成功/失败响应，保证所有客户端解析一致性
"""
from typing import Any, Optional


def _get_response_config() -> dict:
    """从全局配置获取响应码和提示语"""
    try:
        from src.common.config_utils import get_config_by_key
        return {
            "success_code": get_config_by_key("response", "success_code"),
            "fail_code": get_config_by_key("response", "fail_code"),
            "auth_fail_code": get_config_by_key("response", "auth_fail_code"),
            "data_none_code": get_config_by_key("response", "data_none_code"),
            "success_msg": get_config_by_key("response", "success_msg"),
            "fail_msg": get_config_by_key("response", "fail_msg"),
            "auth_fail_msg": get_config_by_key("response", "auth_fail_msg"),
            "data_none_msg": get_config_by_key("response", "data_none_msg"),
        }
    except Exception:
        return {
            "success_code": 200,
            "fail_code": 400,
            "auth_fail_code": 401,
            "data_none_code": 404,
            "success_msg": "请求处理成功",
            "fail_msg": "请求处理失败",
            "auth_fail_msg": "接口认证失败",
            "data_none_msg": "未查询到相关文物数据",
        }


def success_response(data: Any = None, msg: Optional[str] = None) -> dict:
    """
    成功响应
    
    Args:
        data: 响应数据，默认为None
        msg: 自定义提示语，默认使用配置中的成功提示
    
    Returns:
        标准JSON格式: {"code": 200, "msg": "xxx", "data": xxx}
    """
    config = _get_response_config()
    return {
        "code": config["success_code"],
        "msg": msg or config["success_msg"],
        "data": data
    }


def fail_response(
    msg: Optional[str] = None,
    code: Optional[int] = None,
    data: Any = None
) -> dict:
    """
    通用失败响应
    
    Args:
        msg: 自定义错误提示语
        code: 自定义错误码，默认使用配置中的失败码
        data: 错误详情数据
    
    Returns:
        标准JSON格式: {"code": 400, "msg": "xxx", "data": xxx}
    """
    config = _get_response_config()
    return {
        "code": code if code is not None else config["fail_code"],
        "msg": msg or config["fail_msg"],
        "data": data
    }


def auth_fail_response(msg: Optional[str] = None) -> dict:
    """
    认证失败响应
    
    Args:
        msg: 自定义提示语，默认使用配置中的认证失败提示
    
    Returns:
        标准JSON格式: {"code": 401, "msg": "xxx", "data": null}
    """
    config = _get_response_config()
    return {
        "code": config["auth_fail_code"],
        "msg": msg or config["auth_fail_msg"],
        "data": None
    }


def data_none_response(msg: Optional[str] = None) -> dict:
    """
    数据不存在响应（知识库查询空结果）
    
    Args:
        msg: 自定义提示语，默认使用配置中的数据不存在提示
    
    Returns:
        标准JSON格式: {"code": 404, "msg": "xxx", "data": null}
    """
    config = _get_response_config()
    return {
        "code": config["data_none_code"],
        "msg": msg or config["data_none_msg"],
        "data": None
    }
