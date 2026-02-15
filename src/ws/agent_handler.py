# -*- coding: utf-8 -*-
"""
智能体流式 WebSocket 处理器

路径: /ws/agent/stream
严格遵循 docs/CommunicationProtocol_CS.md。
"""
import asyncio
import base64
import json
import uuid
import time
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.ws.protocol import (
    build_message,
    build_error,
    validate_common,
    validate_register_payload,
    validate_request_payload,
    session_data_to_protocol,
)
from src.ws.connection_manager import ConnectionManager
from src.ws.request_processor import process_text_request, process_voice_request
from src.common.enhanced_logger import get_enhanced_logger
from src.db.client_api import ClientLocalAPI
from src.session.strict_session_manager import strict_session_manager
from src.services.registry import service_registry

router = APIRouter(prefix="/ws", tags=["WebSocket"])
manager = ConnectionManager()
logger = get_enhanced_logger()

# 配置
HEARTBEAT_INTERVAL = 30
SESSION_TIMEOUT_SECONDS = 3600
SESSION_WARN_THRESHOLD = 300  # 5 分钟


def _get_client_ip(ws: WebSocket) -> Optional[str]:
    if hasattr(ws, "client") and ws.client:
        return getattr(ws.client, "host", None)
    return None


async def _handle_register(ws: WebSocket, payload: Dict, conn_session_id: Optional[str]) -> Optional[str]:
    """处理 REGISTER，返回 session_id 或 None（失败）"""
    if "platform" not in payload and "client_type" in payload:
        payload["platform"] = payload["client_type"]
    err = validate_register_payload(payload)
    if err:
        await ws.send_json(build_error("MALFORMED_PAYLOAD", err))
        return None
    auth = payload["auth"]
    auth_type = auth.get("type")
    platform = payload["platform"]
    require_tts = payload["require_tts"]
    function_calling = payload.get("function_calling", [])

    client_api = ClientLocalAPI()
    try:
        if auth_type == "API_KEY":
            client_info = client_api.verify_client_auth(
                auth_type="API_KEY",
                auth_value=auth.get("api_key"),
                ip=_get_client_ip(ws),
            )
        else:
            client_info = client_api.verify_client_auth(
                auth_type="ACCOUNT",
                auth_value=auth.get("account"),
                password=auth.get("password"),
                ip=_get_client_ip(ws),
            )
        if not client_info or not client_info.get("is_authenticated"):
            await ws.send_json(build_error("AUTH_FAILED", "认证失败"))
            return None
        client_api.update_client_login_info(client_info["user_id"], _get_client_ip(ws))
    except Exception as e:
        logger.ws.error("Auth failed", {"error": str(e)})
        await ws.send_json(build_error("AUTH_FAILED", "认证失败", str(e)))
        return None

    session_id = f"sess_{uuid.uuid4().hex[:16]}"
    client_metadata = {
        "platform": platform,
        "require_tts": require_tts,
        "user_id": client_info.get("username", "api_user"),
        "client_info": client_info,
    }
    strict_session_manager.register_session_with_functions(
        session_id, client_metadata, function_calling
    )
    await manager.connect(ws, session_id)
    await ws.send_json(build_message("REGISTER_ACK", {
        "status": "SUCCESS",
        "message": "会话创建成功",
        "session_id": session_id,
        "session_timeout_seconds": SESSION_TIMEOUT_SECONDS,
    }, session_id))
    logger.ws.info("Session registered", {"session_id": session_id[:16], "platform": platform})
    return session_id


async def _handle_request(
    ws: WebSocket,
    session_id: str,
    payload: Dict,
    voice_buffer: Dict[str, bytes],
    active_voice_request: Dict[str, Optional[str]],
) -> bool:
    """处理 REQUEST。返回 False 表示应退出循环（如 SHUTDOWN）"""
    err = validate_request_payload(payload)
    if err:
        await ws.send_json(build_error("MALFORMED_PAYLOAD", err, request_id=payload.get("request_id"), session_id=session_id))
        return True

    session_service = service_registry.get_service("session")
    if not session_service:
        await ws.send_json(build_error("SERVER_BUSY", "会话服务不可用", request_id=payload.get("request_id"), session_id=session_id))
        return True

    valid = await session_service.validate_session(session_id)
    if not valid:
        await ws.send_json(build_error("SESSION_INVALID", "会话无效或已超时", request_id=payload.get("request_id"), session_id=session_id))
        return True

    # 更新会话属性
    if "require_tts" in payload:
        strict_session_manager.update_session_attributes(session_id, require_tts=payload["require_tts"])
    if payload.get("function_calling_op") and "function_calling" in payload:
        strict_session_manager.update_session_attributes(
            session_id,
            function_calling_op=payload["function_calling_op"],
            function_calling=payload["function_calling"],
        )

    request_id = payload["request_id"]
    data_type = payload["data_type"]
    stream_flag = payload["stream_flag"]
    stream_seq = int(payload["stream_seq"])
    content = payload.get("content", {})
    require_tts = payload.get("require_tts")
    session = strict_session_manager.get_session(session_id)
    if session:
        require_tts = require_tts if require_tts is not None else session.client_metadata.get("require_tts", False)
    else:
        require_tts = require_tts or False

    # VOICE BINARY：起始/结束帧，中间为二进制
    if data_type == "VOICE" and content.get("voice_mode") == "BINARY":
        if stream_seq == 0:
            active_voice_request[session_id] = request_id
            voice_buffer[request_id] = b""
        elif stream_seq == -1:
            active_voice_request.pop(session_id, None)
            audio = voice_buffer.pop(request_id, b"")
            
            # 🔧 提取音频格式提示（如果客户端提供）
            audio_format_hint = content.get("audio_format")
            
            try:
                async for resp_payload in process_voice_request(session_id, request_id, audio, require_tts, audio_format_hint):
                    msg = build_message("RESPONSE", resp_payload, session_id)
                    if not await manager.send_json(session_id, msg):
                        break
            except Exception as e:
                logger.sys.error("Voice request failed", {"error": str(e)})
                await ws.send_json(build_error("INTERNAL_ERROR", "语音处理失败", str(e), request_id=request_id, session_id=session_id))
        return True

    # VOICE BASE64
    if data_type == "VOICE":
        voice_b64 = content.get("voice", "")
        if not voice_b64:
            await ws.send_json(build_error("MALFORMED_PAYLOAD", "VOICE+BASE64 需 content.voice", request_id=request_id, session_id=session_id))
            return True
        try:
            audio = base64.b64decode(voice_b64)
        except Exception as e:
            await ws.send_json(build_error("MALFORMED_PAYLOAD", "语音 Base64 解码失败", str(e), request_id=request_id, session_id=session_id))
            return True
        
        # 🔧 提取音频格式提示（如果客户端提供）
        audio_format_hint = content.get("audio_format")
        
        try:
            async for resp_payload in process_voice_request(session_id, request_id, audio, require_tts, audio_format_hint):
                msg = build_message("RESPONSE", resp_payload, session_id)
                if not await manager.send_json(session_id, msg):
                    break
        except Exception as e:
            logger.sys.error("Voice request failed", {"error": str(e)})
            await ws.send_json(build_error("INTERNAL_ERROR", "语音处理失败", str(e), request_id=request_id, session_id=session_id))
        return True

    # TEXT（含仅更新属性的空 text）
    text = content.get("text", "")
    if data_type == "TEXT" and not text and not payload.get("require_tts") and not payload.get("function_calling_op"):
        await ws.send_json(build_error("MALFORMED_PAYLOAD", "TEXT 类型需 content.text", request_id=request_id, session_id=session_id))
        return True

    if text:
        try:
            async for resp_payload in process_text_request(session_id, request_id, text, require_tts):
                msg = build_message("RESPONSE", resp_payload, session_id)
                if not await manager.send_json(session_id, msg):
                    break
        except Exception as e:
            logger.sys.error("Text request failed", {"error": str(e)})
            await ws.send_json(build_error("INTERNAL_ERROR", "文本处理失败", str(e), request_id=request_id, session_id=session_id))
    return True


async def _handle_session_query(ws: WebSocket, session_id: str, payload: Dict) -> None:
    session_data = strict_session_manager.get_protocol_session_data(session_id)
    if not session_data:
        await ws.send_json(build_error("SESSION_INVALID", "会话不存在", session_id=session_id))
        return
    qf = payload.get("query_fields") or []
    sd = session_data_to_protocol(session_data, qf if qf else None)
    await ws.send_json(build_message("SESSION_INFO", {
        "status": "SUCCESS",
        "message": "查询成功",
        "session_data": sd,
    }, session_id))


async def _handle_heartbeat_reply(ws: WebSocket, session_id: str, last_heartbeat_reply: Dict[str, float]) -> None:
    """处理心跳回复（带防抖）"""
    now = time.time()
    last_reply_time = last_heartbeat_reply.get(session_id, 0)
    
    # 防抖：如果距离上次心跳回复不到1秒，忽略本次请求
    if now - last_reply_time < 1.0:
        logger.ws.debug("Heartbeat reply ignored (debounced)", {"session_id": session_id[:16]})
        return
    
    last_heartbeat_reply[session_id] = now
    strict_session_manager.heartbeat(session_id)
    
    remaining = int((strict_session_manager.session_timeout.total_seconds()))
    session = strict_session_manager.get_session(session_id)
    if session:
        remaining = max(0, int((session.expires_at.timestamp() - time.time())))
    await ws.send_json(build_message("HEARTBEAT", {"remaining_seconds": remaining}, session_id))


async def _handle_health_check(ws: WebSocket) -> None:
    conn_count = len(manager.active_connections)
    await ws.send_json(build_message("HEALTH_CHECK_ACK", {
        "health_status": {
            "cpu_usage": 0,
            "conn_count": conn_count,
            "status": "HEALTHY",
        }
    }))


@router.websocket("/agent/stream")
async def agent_stream(websocket: WebSocket):
    await websocket.accept()
    session_id: Optional[str] = None
    last_heartbeat = time.time()
    last_heartbeat_reply: Dict[str, float] = {}  # 用于心跳防抖
    voice_buffer: Dict[str, bytes] = {}
    active_voice_request: Dict[str, Optional[str]] = {}

    async def send_json(msg: Dict) -> bool:
        try:
            await websocket.send_json(msg)
            return True
        except Exception:
            return False

    try:
        while True:
            now = time.time()
            if session_id and (now - last_heartbeat) >= HEARTBEAT_INTERVAL:
                remaining = SESSION_TIMEOUT_SECONDS - int(now - last_heartbeat)
                remaining = max(0, remaining)
                await send_json(build_message("HEARTBEAT", {"remaining_seconds": remaining}, session_id))
                last_heartbeat = now
                if remaining <= SESSION_WARN_THRESHOLD:
                    await send_json(build_message("SESSION_WARN", {
                        "warn_type": "EXPIRE_SOON",
                        "remaining_seconds": remaining,
                        "message": f"会话即将在{remaining // 60}分钟后超时，请发送请求刷新",
                    }, session_id))

            try:
                raw = await asyncio.wait_for(websocket.receive(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            if "bytes" in raw:
                data = raw["bytes"]
                if isinstance(data, bytes) and session_id:
                    rid = active_voice_request.get(session_id)
                    if rid:
                        voice_buffer[rid] = voice_buffer.get(rid, b"") + data
                continue

            text = raw.get("text")
            if not text:
                continue

            try:
                msg = json.loads(text)
            except json.JSONDecodeError as e:
                await send_json(build_error("MALFORMED_PAYLOAD", "无效 JSON", str(e), session_id=session_id))
                continue

            err = validate_common(msg)
            if err:
                await send_json(build_error("MALFORMED_PAYLOAD", err, session_id=session_id))
                continue

            msg_type = msg.get("msg_type")
            payload = msg.get("payload", {})

            if session_id:
                last_heartbeat = now

            if msg_type == "REGISTER":
                sid = await _handle_register(websocket, payload, session_id)
                if sid:
                    session_id = sid

            elif msg_type == "REQUEST":
                if not session_id:
                    await send_json(build_error("SESSION_INVALID", "会话不存在或未注册", request_id=payload.get("request_id")))
                    continue
                ok = await _handle_request(websocket, session_id, payload, voice_buffer, active_voice_request)
                if not ok:
                    break

            elif msg_type == "SESSION_QUERY":
                if not session_id:
                    await send_json(build_error("SESSION_INVALID", "会话不存在"))
                    continue
                await _handle_session_query(websocket, session_id, payload)

            elif msg_type == "HEARTBEAT_REPLY":
                if session_id:
                    await _handle_heartbeat_reply(websocket, session_id, last_heartbeat_reply)

            elif msg_type == "HEALTH_CHECK":
                await _handle_health_check(websocket)

            elif msg_type == "SHUTDOWN":
                reason = payload.get("reason", "客户端关闭")
                await send_json(build_message("SHUTDOWN", {"reason": reason}, session_id))
                if session_id:
                    strict_session_manager.unregister_session(session_id)
                    await manager.disconnect(session_id)
                break

            else:
                await send_json(build_error("MALFORMED_PAYLOAD", f"未知 msg_type: {msg_type}", session_id=session_id))

    except WebSocketDisconnect:
        logger.ws.info("WebSocket disconnected", {"session_id": session_id[:16] if session_id else ""})
    except Exception as e:
        logger.sys.error("Agent stream error", {"error": str(e)})
    finally:
        if session_id:
            await manager.disconnect(session_id)
            strict_session_manager.unregister_session(session_id)
