# -*- coding: utf-8 -*-
"""
通信协议层 - 纯逻辑，无 I/O

严格遵循 docs/CommunicationProtocol_CS.md，不可修改协议文档时本模块同步冻结。
"""
import time
from typing import Dict, Any, Optional

PROTOCOL_VERSION = "1.0"

# 协议枚举
PLATFORMS = {"WEB", "APP", "MINI_PROGRAM", "TV"}
AUTH_TYPES = {"API_KEY", "ACCOUNT"}
DATA_TYPES = {"TEXT", "VOICE"}
VOICE_MODES = {"BASE64", "BINARY"}
FUNCTION_OPS = {"REPLACE", "ADD", "UPDATE", "DELETE"}

# 错误码与 retryable 映射
ERROR_RETRYABLE = {
    "AUTH_FAILED": True,
    "SESSION_INVALID": False,
    "STREAM_SEQ_ERROR": True,
    "PAYLOAD_TOO_LARGE": False,
    "SERVER_BUSY": True,
    "MALFORMED_PAYLOAD": False,
    "INTERNAL_ERROR": True,
    "REQUEST_TIMEOUT": True,
}


def _ts() -> int:
    return int(time.time() * 1000)


def build_message(msg_type: str, payload: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """构建符合协议的 S→C 报文"""
    return {
        "version": PROTOCOL_VERSION,
        "msg_type": msg_type,
        "session_id": session_id,
        "payload": payload,
        "timestamp": _ts(),
    }


def build_error(
    error_code: str,
    error_msg: str,
    error_detail: str = "",
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """构建 ERROR 报文"""
    retryable = ERROR_RETRYABLE.get(error_code, False)
    payload = {
        "error_code": error_code,
        "error_msg": error_msg,
        "error_detail": error_detail,
        "retryable": retryable,
    }
    if request_id:
        payload["request_id"] = request_id
    return build_message("ERROR", payload, session_id)


def validate_common(msg: Dict[str, Any]) -> Optional[str]:
    """校验公共字段，返回错误描述或 None"""
    if not isinstance(msg, dict):
        return "报文必须是 JSON 对象"
    if msg.get("version") != PROTOCOL_VERSION:
        return f"version 应为 '{PROTOCOL_VERSION}'"
    if not msg.get("msg_type"):
        return "缺少 msg_type"
    if "payload" not in msg:
        return "缺少 payload"
    if "timestamp" not in msg or not isinstance(msg.get("timestamp"), (int, float)):
        return "缺少或无效的 timestamp"
    return None


def validate_register_payload(p: Dict[str, Any]) -> Optional[str]:
    """校验 REGISTER payload"""
    auth = p.get("auth")
    if not isinstance(auth, dict):
        return "auth 必填且为对象"
    t = auth.get("type")
    if t not in AUTH_TYPES:
        return f"auth.type 应为 {AUTH_TYPES} 之一"
    if t == "API_KEY" and "api_key" not in auth:
        return "auth.api_key 必填"
    if t == "ACCOUNT" and (not auth.get("account") or not auth.get("password")):
        return "auth.account 和 auth.password 必填"
    if p.get("platform") not in PLATFORMS:
        return f"platform 应为 {PLATFORMS} 之一"
    if "require_tts" not in p:
        return "require_tts 必填"
    if not isinstance(p.get("function_calling"), list):
        return "function_calling 必填且为数组"
    return None


def validate_request_payload(p: Dict[str, Any]) -> Optional[str]:
    """校验 REQUEST payload"""
    if not p.get("request_id"):
        return "request_id 必填"
    dt = p.get("data_type")
    if dt not in DATA_TYPES:
        return f"data_type 应为 {DATA_TYPES} 之一"
    if "stream_flag" not in p:
        return "stream_flag 必填"
    if "stream_seq" not in p or not isinstance(p.get("stream_seq"), (int, float)):
        return "stream_seq 必填且为数字"
    content = p.get("content")
    if not isinstance(content, dict):
        return "content 必填且为对象"
    if dt == "TEXT" and "text" not in content:
        return "TEXT 类型需 content.text"
    if dt == "VOICE":
        vm = content.get("voice_mode")
        if vm not in VOICE_MODES:
            return f"VOICE 需 content.voice_mode 为 {VOICE_MODES} 之一"
        if vm == "BASE64" and not content.get("voice") and p.get("stream_flag") is False:
            return "VOICE+BASE64 非流式时需 content.voice"
    if p.get("function_calling_op") and p["function_calling_op"] not in FUNCTION_OPS:
        return f"function_calling_op 应为 {FUNCTION_OPS} 之一"
    return None


def session_data_to_protocol(session_data: Dict[str, Any], query_fields: Optional[list] = None) -> Dict[str, Any]:
    """
    将会话数据转为协议 SESSION_INFO.session_data 格式。
    session_data 需包含: platform, require_tts, function_calling, create_time, remaining_seconds
    """
    full = {
        "platform": session_data.get("platform", "WEB"),
        "require_tts": session_data.get("require_tts", False),
        "function_calling": session_data.get("function_calling", []),
        "create_time": session_data.get("create_time", 0),
        "remaining_seconds": session_data.get("remaining_seconds", 0),
    }
    if query_fields:
        return {k: v for k, v in full.items() if k in query_fields}
    return full
