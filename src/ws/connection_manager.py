# -*- coding: utf-8 -*-
"""
WebSocket 连接管理器

职责：session_id 与 WebSocket 的双向映射，发送消息。
"""
import asyncio
from typing import Dict, Any, Optional

from src.common.enhanced_logger import get_enhanced_logger


class ConnectionManager:
    """session_id -> WebSocket 映射，线程安全"""

    def __init__(self):
        self._connections: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._logger = get_enhanced_logger()

    @property
    def active_connections(self) -> Dict[str, Any]:
        return dict(self._connections)

    async def connect(self, websocket: Any, session_id: str) -> None:
        async with self._lock:
            self._connections[session_id] = websocket
        self._logger.ws.info("WebSocket connected", {"session_id": session_id[:16] if session_id else ""})

    async def disconnect(self, session_id: str) -> None:
        async with self._lock:
            self._connections.pop(session_id, None)
        self._logger.ws.info("WebSocket disconnected", {"session_id": session_id[:16] if session_id else ""})

    async def send_json(self, session_id: str, message: Dict[str, Any]) -> bool:
        ws = self._connections.get(session_id)
        if not ws:
            return False
        try:
            await ws.send_json(message)
            return True
        except Exception as e:
            self._logger.sys.error("Send message failed", {"session_id": session_id[:16], "error": str(e)})
            await self.disconnect(session_id)
            return False
