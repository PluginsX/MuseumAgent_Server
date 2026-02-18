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

router = APIRouter(prefix="/ws", tags=["WebSocket"])
manager = ConnectionManager()
logger = get_enhanced_logger()

# 配置（优化心跳间隔）
HEARTBEAT_INTERVAL = 60  # 60秒发送一次心跳（从30秒增加）
SESSION_TIMEOUT_SECONDS = 3600
SESSION_WARN_THRESHOLD = 300  # 5 分钟

# ✅ 活跃请求管理（用于打断机制）
active_requests: Dict[str, Dict[str, Any]] = {}
# 结构：{
#   "req_xxx": {
#       "session_id": "sess_xxx",
#       "cancel_event": asyncio.Event(),
#       "start_time": timestamp,
#       "type": "TEXT" | "VOICE"
#   }
# }


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

    # ✅ 创建取消事件并注册活跃请求
    cancel_event = asyncio.Event()
    active_requests[request_id] = {
        "session_id": session_id,
        "cancel_event": cancel_event,
        "start_time": time.time(),
        "type": data_type
    }
    
    try:
        # VOICE BINARY：流式接收语音数据
        if data_type == "VOICE" and content.get("voice_mode") == "BINARY":
            if stream_seq == 0:
                # 起始帧：初始化流式 STT
                audio_format_hint = content.get("audio_format", "pcm")  # 默认 PCM
                active_voice_request[session_id] = request_id
                voice_buffer[request_id] = {
                    "audio_format": audio_format_hint,
                    "chunks": []  # 存储音频块，用于流式发送给 STT
                }
                
                logger.ws.info("Voice stream started", {
                    "request_id": request_id[:16],
                    "audio_format": audio_format_hint
                })
                
            elif stream_seq == -1:
                # 结束帧：流式调用 STT，等待完整文本结果
                active_voice_request.pop(session_id, None)
                buffer_data = voice_buffer.pop(request_id, {})
                audio_chunks = buffer_data.get("chunks", [])
                audio_format_hint = buffer_data.get("audio_format", "pcm")
                
                total_size = sum(len(chunk) for chunk in audio_chunks)
                
                logger.ws.info("Voice stream ended, starting streaming STT", {
                    "request_id": request_id[:16],
                    "audio_size": total_size,
                    "audio_format": audio_format_hint,
                    "chunk_count": len(audio_chunks)
                })
                
                try:
                    # 使用流式 STT 处理（输入流式，输出完整文本）
                    from src.services.stt_service import UnifiedSTTService
                    stt_service = UnifiedSTTService()
                    
                    # 创建异步生成器，流式发送音频块
                    async def audio_generator():
                        for chunk in audio_chunks:
                            # ✅ 检查取消信号
                            if cancel_event.is_set():
                                logger.ws.info("STT cancelled", {"request_id": request_id[:16]})
                                break
                            yield chunk
                    
                    # 流式调用 STT，等待完整文本结果
                    recognized_text = await stt_service.stream_recognize(audio_generator(), audio_format_hint)
                    
                    # ✅ 检查是否在 STT 过程中被取消
                    if cancel_event.is_set():
                        logger.ws.info("Request cancelled after STT", {"request_id": request_id[:16]})
                        await manager.send_json(session_id, build_message("RESPONSE", {
                            "request_id": request_id,
                            "text_stream_seq": -1,
                            "voice_stream_seq": -1 if require_tts else None,
                            "interrupted": True,
                            "interrupt_reason": "USER_NEW_INPUT",
                            "content": {}
                        }, session_id))
                        return True
                    
                    logger.ws.info("Streaming STT completed", {
                        "request_id": request_id[:16],
                        "recognized_text": recognized_text[:100] if recognized_text else "(empty)"
                    })
                    
                    # 使用完整文本进行后续处理（SRS + LLM）
                    if not recognized_text or not recognized_text.strip():
                        # 空识别结果
                        payload = {
                            "request_id": request_id,
                            "text_stream_seq": 0,
                            "content": {"text": "抱歉，我没有听清楚您说什么。"},
                        }
                        await manager.send_json(session_id, build_message("RESPONSE", payload, session_id))
                        payload_end = {"request_id": request_id, "text_stream_seq": -1, "content": {}}
                        await manager.send_json(session_id, build_message("RESPONSE", payload_end, session_id))
                        if require_tts:
                            await manager.send_json(session_id, build_message("RESPONSE", {"request_id": request_id, "voice_stream_seq": -1, "content": {}}, session_id))
                    else:
                        # ✅ 使用支持取消的文本处理
                        async for resp_payload in process_text_request_with_cancel(session_id, request_id, recognized_text.strip(), require_tts, cancel_event):
                            msg = build_message("RESPONSE", resp_payload, session_id)
                            if not await manager.send_json(session_id, msg):
                                break
                            # 如果响应被标记为中断，提前退出
                            if resp_payload.get("interrupted"):
                                break
                                
                except Exception as e:
                    logger.sys.error("Streaming STT failed", {"error": str(e)})
                    await ws.send_json(build_error("INTERNAL_ERROR", "语音识别失败", str(e), request_id=request_id, session_id=session_id))
            return True

        # VOICE BASE64（兼容旧协议，但仍使用流式 STT）
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
            
            # 提取音频格式提示
            audio_format_hint = content.get("audio_format", "pcm")
            
            logger.ws.info("Voice BASE64 received, using streaming STT", {
                "request_id": request_id[:16],
                "audio_size": len(audio),
                "audio_format": audio_format_hint
            })
            
            try:
                # 使用流式 STT 处理（即使是一次性接收的数据）
                from src.services.stt_service import UnifiedSTTService
                stt_service = UnifiedSTTService()
                
                # 创建异步生成器，一次性发送所有数据
                async def audio_generator():
                    # ✅ 检查取消信号
                    if not cancel_event.is_set():
                        yield audio
                
                # 流式调用 STT，等待完整文本结果
                recognized_text = await stt_service.stream_recognize(audio_generator(), audio_format_hint)
                
                # ✅ 检查是否在 STT 过程中被取消
                if cancel_event.is_set():
                    logger.ws.info("Request cancelled after STT", {"request_id": request_id[:16]})
                    await manager.send_json(session_id, build_message("RESPONSE", {
                        "request_id": request_id,
                        "text_stream_seq": -1,
                        "voice_stream_seq": -1 if require_tts else None,
                        "interrupted": True,
                        "interrupt_reason": "USER_NEW_INPUT",
                        "content": {}
                    }, session_id))
                    return True
                
                logger.ws.info("Streaming STT completed (BASE64)", {
                    "request_id": request_id[:16],
                    "recognized_text": recognized_text[:100] if recognized_text else "(empty)"
                })
                
                # 使用完整文本进行后续处理（SRS + LLM）
                if not recognized_text or not recognized_text.strip():
                    # 空识别结果
                    payload = {
                        "request_id": request_id,
                        "text_stream_seq": 0,
                        "content": {"text": "抱歉，我没有听清楚您说什么。"},
                    }
                    await manager.send_json(session_id, build_message("RESPONSE", payload, session_id))
                    payload_end = {"request_id": request_id, "text_stream_seq": -1, "content": {}}
                    await manager.send_json(session_id, build_message("RESPONSE", payload_end, session_id))
                    if require_tts:
                        await manager.send_json(session_id, build_message("RESPONSE", {"request_id": request_id, "voice_stream_seq": -1, "content": {}}, session_id))
                else:
                    # ✅ 使用支持取消的文本处理
                    async for resp_payload in process_text_request_with_cancel(session_id, request_id, recognized_text.strip(), require_tts, cancel_event):
                        msg = build_message("RESPONSE", resp_payload, session_id)
                        if not await manager.send_json(session_id, msg):
                            break
                        # 如果响应被标记为中断，提前退出
                        if resp_payload.get("interrupted"):
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
                # ✅ 使用支持取消的文本处理
                async for resp_payload in process_text_request_with_cancel(session_id, request_id, text, require_tts, cancel_event):
                    msg = build_message("RESPONSE", resp_payload, session_id)
                    if not await manager.send_json(session_id, msg):
                        break
                    # 如果响应被标记为中断，提前退出
                    if resp_payload.get("interrupted"):
                        break
            except Exception as e:
                logger.sys.error("Text request failed", {"error": str(e)})
                await ws.send_json(build_error("INTERNAL_ERROR", "文本处理失败", str(e), request_id=request_id, session_id=session_id))
        return True
    
    finally:
        # ✅ 清理活跃请求
        active_requests.pop(request_id, None)
        logger.ws.debug("Request completed and cleaned up", {
            "request_id": request_id[:16],
            "session_id": session_id[:16]
        })


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


async def _handle_interrupt(ws: WebSocket, session_id: str, payload: Dict) -> None:
    """
    处理打断请求（INTERRUPT）
    
    功能：
    1. 中断指定请求或该会话的所有请求
    2. 设置取消信号（asyncio.Event）
    3. 返回 INTERRUPT_ACK 确认
    """
    interrupt_request_id = payload.get("interrupt_request_id")
    reason = payload.get("reason", "USER_NEW_INPUT")
    
    interrupted_ids = []
    
    if interrupt_request_id:
        # 中断指定请求
        if interrupt_request_id in active_requests:
            req_info = active_requests[interrupt_request_id]
            if req_info["session_id"] == session_id:
                req_info["cancel_event"].set()
                interrupted_ids.append(interrupt_request_id)
                logger.ws.info("Request interrupted", {
                    "request_id": interrupt_request_id[:16],
                    "reason": reason,
                    "session_id": session_id[:16]
                })
            else:
                logger.ws.warn("Request belongs to different session", {
                    "request_id": interrupt_request_id[:16],
                    "expected_session": session_id[:16],
                    "actual_session": req_info["session_id"][:16]
                })
        else:
            logger.ws.warn("Request not found or already completed", {
                "request_id": interrupt_request_id[:16],
                "session_id": session_id[:16]
            })
    else:
        # 中断该会话的所有请求
        for req_id, req_info in list(active_requests.items()):
            if req_info["session_id"] == session_id:
                req_info["cancel_event"].set()
                interrupted_ids.append(req_id)
        logger.ws.info("All session requests interrupted", {
            "session_id": session_id[:16],
            "count": len(interrupted_ids),
            "reason": reason
        })
    
    # 发送确认
    status = "SUCCESS" if interrupted_ids else "FAILED"
    message = f"已中断 {len(interrupted_ids)} 个请求" if interrupted_ids else "无活跃请求可中断"
    
    await ws.send_json(build_message("INTERRUPT_ACK", {
        "interrupted_request_ids": interrupted_ids,
        "status": status,
        "message": message
    }, session_id))


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

            elif msg_type == "INTERRUPT":
                if not session_id:
                    await send_json(build_error("SESSION_INVALID", "会话不存在或未注册"))
                    continue
                await _handle_interrupt(websocket, session_id, payload)

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
