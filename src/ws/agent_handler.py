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
from src.ws.request_processor import process_text_request, process_text_request_with_cancel
from src.common.enhanced_logger import get_enhanced_logger
from src.db.client_api import ClientLocalAPI
from src.session.strict_session_manager import strict_session_manager
from src.services.registry import service_registry
from src.services.interrupt_manager import get_interrupt_manager

router = APIRouter(prefix="/ws", tags=["WebSocket"])
manager = ConnectionManager()
logger = get_enhanced_logger()
interrupt_manager = get_interrupt_manager()

# 配置（优化心跳间隔）
HEARTBEAT_INTERVAL = 60  # 60秒发送一次心跳（从30秒增加）
SESSION_TIMEOUT_SECONDS = 3600
SESSION_WARN_THRESHOLD = 300  # 5 分钟

# ✅ 活跃任务管理（用于打断机制 - 直接取消 asyncio.Task）
active_tasks: Dict[str, asyncio.Task] = {}
# 结构：{session_id: task}

# ✅ 追踪每个会话的当前请求ID和TTS状态（用于发送正确的结束帧）
active_request_info: Dict[str, Dict[str, Any]] = {}
# 结构：{session_id: {"request_id": str, "require_tts": bool}}


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
    enable_srs = payload.get("enable_srs", True)  # 默认启用 SRS
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
        "enable_srs": enable_srs,
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
    voice_buffer: Dict[str, Dict[str, Any]],
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
    if "enable_srs" in payload:
        strict_session_manager.update_session_attributes(session_id, enable_srs=payload["enable_srs"])
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

    # ✅ 新请求到达：立即中断该会话的所有旧任务
    should_interrupt_old = False
    if data_type == "TEXT":
        should_interrupt_old = True
    elif data_type == "VOICE":
        if stream_flag and stream_seq == 0:
            should_interrupt_old = True
        elif not stream_flag:
            should_interrupt_old = True
    
    # ✅ 调用统一中断管理器，中断所有流程
    if should_interrupt_old:
        # 获取旧请求信息
        old_request_info = active_request_info.get(session_id, {})
        old_request_id = old_request_info.get("request_id", "unknown")
        old_require_tts = old_request_info.get("require_tts", False)
        
        logger.ws.info("New request arrived, interrupting old processes", {
            "session_id": session_id[:16],
            "old_request_id": old_request_id[:16] if old_request_id != "unknown" else "unknown",
            "new_request_id": request_id[:16]
        })
        
        # 1. ✅ 关闭所有连接（STT/SRS/LLM/TTS）
        interrupt_results = await interrupt_manager.interrupt_all(session_id)
        
        # 2. ✅ 立即发送终包（连接已关闭，旧任务无法再发送数据）
        if old_request_id != "unknown":
            try:
                # 发送文本流结束帧
                await manager.send_json(session_id, build_message("RESPONSE", {
                    "request_id": old_request_id,
                    "text_stream_seq": -1,
                    "content": {}
                }, session_id))
                
                # 如果旧请求需要TTS，发送语音流结束帧
                if old_require_tts:
                    await manager.send_json(session_id, build_message("RESPONSE", {
                        "request_id": old_request_id,
                        "voice_stream_seq": -1,
                        "content": {}
                    }, session_id))
                
                logger.ws.info("Sent end frames for interrupted request", {
                    "session_id": session_id[:16],
                    "old_request_id": old_request_id[:16],
                    "interrupt_results": interrupt_results
                })
            except Exception as e:
                logger.ws.error("Failed to send end frames", {"error": str(e)})
        
        # 3. ✅ 取消旧的 asyncio 任务（让它自然退出）
        if session_id in active_tasks:
            old_task = active_tasks[session_id]
            if not old_task.done():
                old_task.cancel()
                logger.ws.info("Cancelled old asyncio task", {
                    "session_id": session_id[:16]
                })
    
    # ✅ 记录当前请求信息（用于打断时发送正确的结束帧）
    active_request_info[session_id] = {
        "request_id": request_id,
        "require_tts": require_tts
    }
    
    # ✅ 创建处理任务（后台运行，不阻塞主循环）
    async def process_request():
        try:
            # 注册会话到中断管理器
            interrupt_manager.register_session(session_id, request_id)
            
            # VOICE BINARY
            if data_type == "VOICE" and content.get("voice_mode") == "BINARY":
                if stream_seq == 0:
                    audio_format_hint = content.get("audio_format", "pcm")
                    active_voice_request[session_id] = request_id
                    voice_buffer[request_id] = {
                        "audio_format": audio_format_hint,
                        "chunks": []
                    }
                    logger.ws.info("Voice stream started", {"request_id": request_id[:16]})
                    
                elif stream_seq == -1:
                    active_voice_request.pop(session_id, None)
                    buffer_data = voice_buffer.pop(request_id, {})
                    audio_chunks = buffer_data.get("chunks", [])
                    audio_format_hint = buffer_data.get("audio_format", "pcm")
                    
                    logger.ws.info("Voice stream ended", {"request_id": request_id[:16]})
                    
                    try:
                        from src.services.stt_service import UnifiedSTTService
                        stt_service = UnifiedSTTService()
                        
                        async def audio_generator():
                            for chunk in audio_chunks:
                                yield chunk
                        
                        recognized_text = await stt_service.stream_recognize(audio_generator(), audio_format_hint, session_id=session_id)
                        
                        if not recognized_text or not recognized_text.strip():
                            await manager.send_json(session_id, build_message("RESPONSE", {
                                "request_id": request_id,
                                "text_stream_seq": 0,
                                "content": {"text": "抱歉，我没有听清楚您说什么。"}
                            }, session_id))
                            await manager.send_json(session_id, build_message("RESPONSE", {
                                "request_id": request_id,
                                "text_stream_seq": -1,
                                "content": {}
                            }, session_id))
                            if require_tts:
                                await manager.send_json(session_id, build_message("RESPONSE", {
                                    "request_id": request_id,
                                    "voice_stream_seq": -1,
                                    "content": {}
                                }, session_id))
                        else:
                            async for resp_payload in process_text_request(session_id, request_id, recognized_text.strip(), require_tts):
                                if not await manager.send_json(session_id, build_message("RESPONSE", resp_payload, session_id)):
                                    break
                    except Exception as e:
                        logger.sys.error("STT failed", {"error": str(e)})
                        await ws.send_json(build_error("INTERNAL_ERROR", "语音识别失败", str(e), request_id=request_id, session_id=session_id))
                return

            # VOICE BASE64
            if data_type == "VOICE":
                voice_b64 = content.get("voice", "")
                if not voice_b64:
                    await ws.send_json(build_error("MALFORMED_PAYLOAD", "VOICE+BASE64 需 content.voice", request_id=request_id, session_id=session_id))
                    return
                try:
                    audio = base64.b64decode(voice_b64)
                except Exception as e:
                    await ws.send_json(build_error("MALFORMED_PAYLOAD", "语音 Base64 解码失败", str(e), request_id=request_id, session_id=session_id))
                    return
                
                audio_format_hint = content.get("audio_format", "pcm")
                
                try:
                    from src.services.stt_service import UnifiedSTTService
                    stt_service = UnifiedSTTService()
                    
                    async def audio_generator():
                        yield audio
                    
                    recognized_text = await stt_service.stream_recognize(audio_generator(), audio_format_hint, session_id=session_id)
                    
                    if not recognized_text or not recognized_text.strip():
                        await manager.send_json(session_id, build_message("RESPONSE", {
                            "request_id": request_id,
                            "text_stream_seq": 0,
                            "content": {"text": "抱歉，我没有听清楚您说什么。"}
                        }, session_id))
                        await manager.send_json(session_id, build_message("RESPONSE", {
                            "request_id": request_id,
                            "text_stream_seq": -1,
                            "content": {}
                        }, session_id))
                        if require_tts:
                            await manager.send_json(session_id, build_message("RESPONSE", {
                                "request_id": request_id,
                                "voice_stream_seq": -1,
                                "content": {}
                            }, session_id))
                    else:
                        async for resp_payload in process_text_request(session_id, request_id, recognized_text.strip(), require_tts):
                            if not await manager.send_json(session_id, build_message("RESPONSE", resp_payload, session_id)):
                                break
                except Exception as e:
                    logger.sys.error("Voice request failed", {"error": str(e)})
                    await ws.send_json(build_error("INTERNAL_ERROR", "语音处理失败", str(e), request_id=request_id, session_id=session_id))
                return

            # TEXT
            text = content.get("text", "")
            if data_type == "TEXT" and not text and not payload.get("require_tts") and not payload.get("function_calling_op"):
                await ws.send_json(build_error("MALFORMED_PAYLOAD", "TEXT 类型需 content.text", request_id=request_id, session_id=session_id))
                return

            if text:
                try:
                    async for resp_payload in process_text_request(session_id, request_id, text, require_tts):
                        if not await manager.send_json(session_id, build_message("RESPONSE", resp_payload, session_id)):
                            break
                except Exception as e:
                    logger.sys.error("Text request failed", {"error": str(e)})
                    await ws.send_json(build_error("INTERNAL_ERROR", "文本处理失败", str(e), request_id=request_id, session_id=session_id))
        except asyncio.CancelledError:
            logger.ws.info("Request task cancelled (end frames already sent by interrupt handler)", {
                "request_id": request_id[:16], 
                "session_id": session_id[:16]
            })
            # ✅ 不再发送终包，因为打断处理器已经发送过了
            # 避免重复发送导致客户端混乱
        except Exception as e:
            logger.sys.error("Request processing failed", {"error": str(e)})
        finally:
            # 清理任务引用
            if active_tasks.get(session_id) == asyncio.current_task():
                active_tasks.pop(session_id, None)
            # 清理请求信息
            if active_request_info.get(session_id, {}).get("request_id") == request_id:
                active_request_info.pop(session_id, None)
            # 清理中断管理器中的会话
            interrupt_manager.cleanup_session(session_id)
            logger.ws.debug("Request task cleaned up", {"request_id": request_id[:16], "session_id": session_id[:16]})
    
    # ✅ 创建任务并注册（不等待，让任务在后台运行）
    task = asyncio.create_task(process_request())
    active_tasks[session_id] = task
    
    # ✅ 立即返回 True，不阻塞主循环，让主循环可以立即接收下一条消息
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
    
    # 更新心跳（这会延长会话有效期）
    success = strict_session_manager.heartbeat(session_id)
    
    if not success:
        logger.ws.warn("Heartbeat update failed - session may be invalid", {"session_id": session_id[:16]})
        await ws.send_json(build_error("SESSION_INVALID", "会话不存在或已过期", session_id=session_id))
        return
    
    # 获取会话实际剩余时间
    session = strict_session_manager.get_session(session_id)
    if session:
        remaining = max(0, int((session.expires_at.timestamp() - time.time())))
    else:
        remaining = 0
    
    logger.ws.debug("Heartbeat reply processed", {
        "session_id": session_id[:16],
        "remaining_seconds": remaining
    })
    
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
    last_heartbeat_reply: Dict[str, float] = {}  # 用于心跳防抖
    voice_buffer: Dict[str, Dict[str, Any]] = {}  # 存储 {request_id: {"audio_format": str, "chunks": [bytes]}}
    active_voice_request: Dict[str, Optional[str]] = {}
    heartbeat_task: Optional[asyncio.Task] = None
    should_stop = False

    async def send_json(msg: Dict) -> bool:
        try:
            await websocket.send_json(msg)
            return True
        except Exception:
            return False

    async def heartbeat_loop():
        """独立的心跳发送任务，不阻塞主循环"""
        nonlocal session_id, should_stop
        while not should_stop:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                
                if not session_id or should_stop:
                    continue
                
                # 从会话对象获取实际剩余时间
                session = strict_session_manager.get_session(session_id)
                if session:
                    remaining = max(0, int((session.expires_at.timestamp() - time.time())))
                else:
                    remaining = 0
                
                logger.ws.debug("Sending heartbeat", {
                    "session_id": session_id[:16],
                    "remaining_seconds": remaining
                })
                
                await send_json(build_message("HEARTBEAT", {"remaining_seconds": remaining}, session_id))
                
                if remaining <= SESSION_WARN_THRESHOLD:
                    await send_json(build_message("SESSION_WARN", {
                        "warn_type": "EXPIRE_SOON",
                        "remaining_seconds": remaining,
                        "message": f"会话即将在{remaining // 60}分钟后超时，请发送请求刷新",
                    }, session_id))
            except Exception as e:
                logger.ws.error("Heartbeat loop error", {"error": str(e)})
                break

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            if "bytes" in raw:
                data = raw["bytes"]
                if isinstance(data, bytes) and session_id:
                    rid = active_voice_request.get(session_id)
                    if rid and rid in voice_buffer:
                        # 将音频块添加到列表中（用于流式 STT）
                        voice_buffer[rid]["chunks"].append(data)
                        total_size = sum(len(chunk) for chunk in voice_buffer[rid]["chunks"])
                        logger.ws.debug("Received audio chunk", {
                            "request_id": rid[:16],
                            "chunk_size": len(data),
                            "total_size": total_size,
                            "chunk_count": len(voice_buffer[rid]["chunks"])
                        })
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

            if msg_type == "REGISTER":
                sid = await _handle_register(websocket, payload, session_id)
                if sid:
                    session_id = sid
                    # ✅ 启动心跳任务
                    if heartbeat_task is None or heartbeat_task.done():
                        heartbeat_task = asyncio.create_task(heartbeat_loop())
                        logger.ws.info("Heartbeat task started", {"session_id": session_id[:16]})

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
        # ✅ 停止心跳任务
        should_stop = True
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if session_id:
            await manager.disconnect(session_id)
            strict_session_manager.unregister_session(session_id)
