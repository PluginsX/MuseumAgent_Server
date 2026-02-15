# -*- coding: utf-8 -*-
"""
WebSocket 通信模块

严格遵循 docs/CommunicationProtocol_CS.md 协议规范。
职责：协议层消息校验、构建、连接管理、消息路由。
"""
from src.ws.protocol import (
    PROTOCOL_VERSION,
    build_message,
    build_error,
    validate_common,
    validate_register_payload,
    validate_request_payload,
)
from src.ws.connection_manager import ConnectionManager
from src.ws.agent_handler import router as agent_stream_router

# 协议文档禁止修改，本模块与 docs/CommunicationProtocol_CS.md 严格一致
__all__ = [
    "PROTOCOL_VERSION",
    "build_message",
    "build_error",
    "validate_common",
    "validate_register_payload",
    "validate_request_payload",
    "ConnectionManager",
    "agent_stream_router",
]
