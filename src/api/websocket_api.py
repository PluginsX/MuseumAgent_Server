# -*- coding: utf-8 -*-
"""
WebSocket API - 支持实时流式通信
用于语音对话、长文本流式生成、实时状态推送
"""
import asyncio
import json
import uuid
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import JSONResponse

from src.common.enhanced_logger import get_enhanced_logger
from src.common.auth_utils import decode_access_token
from src.services.registry import service_registry

router = APIRouter(prefix="/ws", tags=["WebSocket"])

logger = get_enhanced_logger()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = None
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """建立连接"""
        if self._lock is None:
            import asyncio
            self._lock = asyncio.Lock()
        
        async with self._lock:
            self.active_connections[session_id] = websocket
            logger.ws.info("WebSocket connection established", {'session_id': session_id})
    
    async def disconnect(self, session_id: str):
        """断开连接"""
        if self._lock is None:
            import asyncio
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
                logger.ws.info("WebSocket connection disconnected", {'session_id': session_id})
    
    async def send_personal_message(self, session_id: str, message: Dict[str, Any]):
        """发送消息给指定会话"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
                logger.ws.debug("Sending message", {'session_id': session_id, 'message_type': message.get('type'), 'message_size': len(str(message))})
            except Exception as e:
                logger.sys.error(f"发送消息失败: {e}")
                await self.disconnect(session_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有连接"""
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.sys.error(f"广播消息失败: {e}")
                await self.disconnect(session_id)


manager = ConnectionManager()


@router.websocket("/agent/stream")
async def agent_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
    session_id: str = Query(None, description="会话ID")
):
    """
    智能体流式通信WebSocket端点
    
    支持的消息类型：
    - text_stream: 文本流式生成
    - session_heartbeat: 会话心跳
    """
    await websocket.accept()
    
    stream_id = None
    
    try:
        # 验证JWT Token
        try:
            payload = decode_access_token(token)
            if not payload:
                logger.ws.error("Token validation failed", {'error': 'Invalid or expired token'})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            logger.ws.info("Token validation successful", {'user': payload.get('sub')})
        except Exception as e:
            logger.ws.error("Token validation failed", {'error': str(e)})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # 必须提供session_id参数 - 不再自动生成
        if not session_id:
            logger.ws.error("Session ID not provided", {'error': 'Session ID required, please register session at /api/session/register'})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # 验证会话是否已注册
        session_service = service_registry.get_service("session")
        
        if not session_service:
            logger.ws.error("Session service unavailable", {})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        try:
            is_valid = await session_service.validate_session(session_id)
            logger.ws.debug("Session validation result", {'session_id': session_id, 'is_valid': is_valid, 'active_sessions_count': len(list(session_service.active_sessions.keys()))})
            
            if not is_valid:
                logger.ws.error("Session validation failed", {'session_id': session_id, 'error': 'Invalid or unregistered session, please register at /api/session/register'})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            logger.ws.info("Session validation successful", {'session_id': session_id})
        except Exception as e:
            logger.ws.error("Session validation exception", {'error': str(e)})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # 建立连接
        await manager.connect(websocket, session_id)
        
        # 发送连接成功消息
        await manager.send_personal_message(session_id, {
            "type": "connection",
            "status": "connected",
            "session_id": session_id
        })
        
        # 消息处理循环 - 使用正确的WebSocket接收方法处理不同类型的消息
        # 存储音频数据的缓冲区
        audio_buffer = {}
        current_streams = {}
        # 当前活跃的流ID（用于二进制数据关联）
        active_stream_for_session = {}
        
        # WebSocket连接处理循环 - 使用异步任务处理文本和二进制消息
        import asyncio
        try:
            # 创建一个异步任务来处理消息
            async def handle_messages():
                while True:
                    try:
                        # 尝试接收文本消息（带超时）
                        text_task = asyncio.create_task(websocket.receive_text())
                        # 尝试接收二进制消息（带超时）
                        bytes_task = asyncio.create_task(websocket.receive_bytes())
                        
                        # 等待最先完成的任务
                        done, pending = await asyncio.wait(
                            [text_task, bytes_task],
                            return_when=asyncio.FIRST_COMPLETED,
                            timeout=1.0  # 1秒超时
                        )
                        
                        # 取消未完成的任务
                        for task in pending:
                            task.cancel()
                        
                        if done:
                            # 获取完成的任务结果
                            msg_task = done.pop()
                            try:
                                data = msg_task.result()
                                
                                if isinstance(data, str):
                                    # 文本消息（通常是JSON）
                                    try:
                                        message_data = json.loads(data)
                                        message_type = message_data.get("type")
                                        
                                        # 使用传入的session_id
                                        current_session_id = session_id
                                        
                                        if message_type == "text_stream":
                                            # 文本流式生成请求
                                            stream_id = message_data.get("stream_id", str(uuid.uuid4()))
                                            user_input = message_data.get("content", "")
                                            enable_tts = message_data.get("enable_tts", False)
                                            
                                            logger.ws.info("Starting streaming generation", {'stream_id': stream_id, 'input_preview': user_input[:50], 'enable_tts': enable_tts})
                                            
                                            # 调用流式生成器
                                            from src.core.command_generator import CommandGenerator
                                            generator = CommandGenerator()
                                            
                                            try:
                                                # 流式生成文本
                                                full_response = ""
                                                async for chunk in generator.stream_generate(
                                                    user_input=user_input,
                                                    session_id=current_session_id
                                                ):
                                                    full_response += chunk
                                                    await manager.send_personal_message(current_session_id, {
                                                        "type": "text_stream",
                                                        "stream_id": stream_id,
                                                        "chunk": chunk,
                                                        "done": False
                                                    })
                                                
                                                # 发送完成标记
                                                await manager.send_personal_message(current_session_id, {
                                                    "type": "text_stream",
                                                    "stream_id": stream_id,
                                                    "done": True
                                                })
                                                
                                                # 检查是否需要语音回复
                                                if enable_tts and full_response:
                                                    logger.ws.info('Starting text-to-speech conversion', 
                                                                {'stream_id': stream_id, 'text_length': len(full_response)})
                                                    
                                                    # 调用TTS服务进行语音合成
                                                    from src.services.tts_service import UnifiedTTSService
                                                    import base64
                                                    tts_service = UnifiedTTSService()
                                                    
                                                    try:
                                                        # 生成语音
                                                        audio_data = await tts_service.synthesize_text(full_response)
                                                        
                                                        if audio_data:
                                                            logger.tts.info('Speech synthesis completed', 
                                                                      {'stream_id': stream_id, 'audio_size': len(audio_data)})
                                                            
                                                            # 将音频数据转换为Base64编码
                                                            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                                                            
                                                            # 发送语音数据给客户端
                                                            await manager.send_personal_message(current_session_id, {
                                                                "type": "audio_stream",
                                                                "stream_id": stream_id,
                                                                "audio_data": audio_base64,
                                                                "done": True
                                                            })
                                                        else:
                                                            logger.tts.warn('Empty speech synthesis result', {'stream_id': stream_id})
                                                    except Exception as tts_error:
                                                        logger.tts.error('Speech synthesis failed', {'error': str(tts_error)})
                                                else:
                                                    logger.ws.debug('TTS disabled or empty response', 
                                                                  {'enable_tts': enable_tts, 'response_length': len(full_response)})
                                                
                                                logger.ws.info("Streaming generation completed", {'session_id': current_session_id})
                                                
                                            except Exception as e:
                                                logger.sys.error(f"流式生成失败: {e}")
                                                await manager.send_personal_message(current_session_id, {
                                                    "type": "error",
                                                    "stream_id": stream_id,
                                                    "message": f"生成失败: {str(e)}"
                                                })
                                        
                                        elif message_type == "audio_stream_start":
                                            stream_id = message_data.get("stream_id", str(uuid.uuid4()))
                                            enable_tts = message_data.get("enable_tts", False)
                                            
                                            logger.ws.info("Starting audio stream processing", {
                                                'stream_id': stream_id,
                                                'session_id': current_session_id,
                                                'enable_tts': enable_tts
                                            })
                                            
                                            # 初始化此流的音频缓冲区
                                            if stream_id not in audio_buffer:
                                                audio_buffer[stream_id] = []
                                            
                                            # 存储当前流的信息
                                            current_streams[stream_id] = {
                                                "stream_id": stream_id,
                                                "enable_tts": enable_tts
                                            }
                                            
                                            # 标记此流为当前活跃流
                                            active_stream_for_session[current_session_id] = stream_id
                                            
                                        elif message_type == "audio_stream_end":
                                            # 音频流结束 - 完成STT处理并将结果发送给文本生成服务
                                            # 优先使用客户端发送的stream_id，如果不存在则使用当前活跃的流ID
                                            client_stream_id = message_data.get("stream_id", str(uuid.uuid4()))
                                            current_active_stream_id = active_stream_for_session.get(current_session_id)
                                            
                                            # 确定要使用的流ID
                                            stream_id = client_stream_id
                                            if not stream_id or stream_id not in audio_buffer:
                                                stream_id = current_active_stream_id or client_stream_id
                                            
                                            logger.ws.info("Ending audio stream processing", {'client_stream_id': client_stream_id, 'current_active_stream_id': current_active_stream_id, 'final_stream_id': stream_id, 'session_id': current_session_id})
                                            
                                            try:
                                                # 从对应流的缓冲区获取音频数据
                                                if stream_id in audio_buffer and audio_buffer[stream_id]:
                                                    # 合并音频数据
                                                    audio_data = b''.join(audio_buffer[stream_id])
                                                    logger.ws.info('Starting speech recognition', 
                                                                  {'stream_id': stream_id, 'audio_size': len(audio_data)})
                                                    
                                                    # 调用STT服务进行语音识别
                                                    from src.services.stt_service import UnifiedTTSService
                                                    stt_service = UnifiedSTTService()
                                                    
                                                    # 进行语音识别
                                                    recognized_text = await stt_service.recognize_audio(audio_data)
                                                    
                                                    logger.stt.info("Speech recognition result", {'stream_id': stream_id, 'recognized_text': recognized_text[:100]})
                                                    
                                                    if not recognized_text.strip():
                                                        logger.stt.warn("Empty speech recognition result", {'stream_id': stream_id})
                                                        # 发送提示信息给客户端
                                                        await manager.send_personal_message(current_session_id, {
                                                            "type": "text_stream",
                                                            "stream_id": stream_id,
                                                            "chunk": "抱歉，我没有听清楚您说什么。",
                                                            "done": False
                                                        })
                                                        await manager.send_personal_message(current_session_id, {
                                                            "type": "text_stream",
                                                            "stream_id": stream_id,
                                                            "done": True
                                                        })
                                                    else:
                                                        # 使用识别的文本调用文本生成服务
                                                        from src.core.command_generator import CommandGenerator
                                                        generator = CommandGenerator()
                                                        
                                                        # 流式生成文本响应
                                                        full_response = ""
                                                        async for chunk in generator.stream_generate(
                                                            user_input=recognized_text,
                                                            session_id=current_session_id
                                                        ):
                                                            full_response += chunk
                                                            await manager.send_personal_message(current_session_id, {
                                                                "type": "text_stream",
                                                                "stream_id": stream_id,
                                                                "chunk": chunk,
                                                                "done": False
                                                            })
                                                        
                                                        # 发送完成标记
                                                        await manager.send_personal_message(current_session_id, {
                                                            "type": "text_stream",
                                                            "stream_id": stream_id,
                                                            "done": True
                                                        })
                                                        
                                                        # 检查是否需要语音回复
                                                        enable_tts = current_streams.get(stream_id, {}).get("enable_tts", False)
                                                        if enable_tts and full_response:
                                                            logger.ws.info('Starting text-to-speech conversion', 
                                                                        {'stream_id': stream_id, 'text_length': len(full_response)})
                                                            
                                                            # 调用TTS服务进行语音合成
                                                            from src.services.tts_service import UnifiedTTSService
                                                            tts_service = UnifiedTTSService()
                                                            
                                                            try:
                                                                # 生成语音
                                                                audio_data = await tts_service.synthesize_text(full_response)
                                                                
                                                                if audio_data:
                                                                    logger.tts.info('Speech synthesis completed', 
                                                                                  {'stream_id': stream_id, 'audio_size': len(audio_data)})
                                                                    
                                                                    # 将音频数据转换为Base64编码
                                                                    import base64
                                                                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                                                                    
                                                                    # 发送语音数据给客户端
                                                                    await manager.send_personal_message(current_session_id, {
                                                                        "type": "audio_stream",
                                                                        "stream_id": stream_id,
                                                                        "audio_data": audio_base64,
                                                                        "done": True
                                                                    })
                                                                else:
                                                                    logger.tts.warn('Empty speech synthesis result', {'stream_id': stream_id})
                                                            except Exception as tts_error:
                                                                logger.tts.error('Speech synthesis failed', {'error': str(tts_error)})
                                                        else:
                                                            logger.ws.debug('TTS disabled or empty response', 
                                                                          {'enable_tts': enable_tts, 'response_length': len(full_response)})
                                                        
                                                        logger.audio.info("Audio processing completed", {'stream_id': stream_id, 'recognized_text': recognized_text[:50]})
                                                        
                                                        # 清理缓冲区
                                                        if stream_id in audio_buffer:
                                                            del audio_buffer[stream_id]
                                                        if stream_id in current_streams:
                                                            del current_streams[stream_id]
                                                        # 清理活跃流标记
                                                        if current_session_id in active_stream_for_session and active_stream_for_session[current_session_id] == stream_id:
                                                            del active_stream_for_session[current_session_id]
                                                        
                                                else:
                                                    logger.audio.warn("Audio buffer is empty", {'stream_id': stream_id})
                                                    # 发送错误信息给客户端
                                                    await manager.send_personal_message(current_session_id, {
                                                        "type": "error",
                                                        "message": "音频数据为空"
                                                    })
                                                
                                            except Exception as e:
                                                logger.sys.error(f"音频流结束处理失败: {e}")
                                                import traceback
                                                print(f"音频处理异常详情: {traceback.format_exc()}")
                                                await manager.send_personal_message(current_session_id, {
                                                    "type": "error",
                                                    "message": f"音频流处理结束失败: {str(e)}"
                                                })
                                        
                                        elif message_type == "session_heartbeat":
                                            # 会话心跳
                                            logger.ws.debug("Heartbeat received", {'session_id': current_session_id})
                                            await manager.send_personal_message(current_session_id, {
                                                "type": "session_heartbeat",
                                                "timestamp": message_data.get("timestamp", 0)
                                            })
                                        
                                        else:
                                            # 未知消息类型
                                            logger.warning(f"未知的消息类型: {message_type}")
                                            await manager.send_personal_message(current_session_id, {
                                                "type": "error",
                                                "message": f"未知的消息类型: {message_type}"
                                            })
                                    
                                    except json.JSONDecodeError:
                                        logger.ws.error("Failed to decode JSON message", {'session_id': session_id, 'raw_data_preview': data[:100]})
                                
                                elif isinstance(data, bytes):
                                    # 二进制消息（音频数据）
                                    logger.ws.info('Received binary audio data', 
                                                  {'size': len(data), 'streams_count': len(audio_buffer), 'session_id': session_id})
                                    
                                    # 将音频数据添加到当前活跃的流的缓冲区
                                    # 使用活跃流标记来确定音频数据应该归属哪个流
                                    current_active_stream_id = active_stream_for_session.get(session_id)
                                    if current_active_stream_id and current_active_stream_id in audio_buffer:
                                        # 添加到当前活跃的流
                                        audio_buffer[current_active_stream_id].append(data)
                                        logger.ws.info('Audio data added to buffer', 
                                                      {'stream_id': current_active_stream_id, 'buffer_size': len(audio_buffer[current_active_stream_id]), 'session_id': session_id})
                                    elif audio_buffer:
                                        # 如果没有当前活跃流，尝试使用最近的流
                                        recent_stream_id = list(audio_buffer.keys())[-1] if audio_buffer else None
                                        if recent_stream_id:
                                            audio_buffer[recent_stream_id].append(data)
                                            logger.ws.info('Audio data added to recent buffer', 
                                                          {'stream_id': recent_stream_id, 'buffer_size': len(audio_buffer[recent_stream_id]), 'session_id': session_id})
                                        else:
                                            logger.ws.warn("No active audio stream found", {'session_id': session_id})
                                    else:
                                        logger.ws.warn("No active audio stream to receive data", {'session_id': session_id, 'current_streams': list(current_streams.keys())})
                                
                                else:
                                    # 其他类型的数据
                                    logger.ws.warn('Received unknown data type', {'session_id': session_id, 'data_type': str(type(data))})
                            
                            except asyncio.CancelledError:
                                # 任务被取消，继续循环
                                continue
                            except Exception as e:
                                # 如果是WebSocket断开连接，则退出
                                if isinstance(e, WebSocketDisconnect):
                                    break
                                logger.sys.error(f"处理消息异常: {e}")
                                continue
                        else:
                            # 超时，继续循环
                            continue
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        if isinstance(e, asyncio.TimeoutError):
                            # 超时，继续循环
                            continue
                        else:
                            logger.sys.error(f"接收消息异常: {e}")
                            break
            
            # 启动消息处理任务
            await handle_messages()
            
        except WebSocketDisconnect:
            logger.ws.info("Client disconnected", {'session_id': session_id})
        
        except Exception as e:
            logger.sys.error(f"处理消息异常: {e}")
            await manager.send_personal_message(session_id, {
                "type": "error",
                "message": f"处理失败: {str(e)}"
            })
    
    except Exception as e:
        logger.exception(f"WebSocket连接异常: {e}")
    
    finally:
        # 清理连接
        if session_id:
            await manager.disconnect(session_id)


@router.websocket("/audio/tts")
async def audio_tts_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌")
):
    """
    音频TTS流式传输WebSocket端点
    
    用于实时语音合成和音频流式传输
    """
    await websocket.accept()
    
    session_id = None
    
    try:
        # 验证JWT Token
        try:
            payload = decode_access_token(token)
            if not payload:
                logger.ws.error("Token validation failed", {'error': 'Invalid or expired token'})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            session_id = payload.get("session_id") or str(uuid.uuid4())
            logger.ws.info("Token validation successful", {'session_id': session_id})
        except Exception as e:
            logger.ws.error("Token validation failed", {'error': str(e)})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # 建立连接
        await manager.connect(websocket, session_id)
        
        # 发送连接成功消息
        await manager.send_personal_message(session_id, {
            "type": "connection",
            "status": "connected",
            "session_id": session_id
        })
        
        # 消息处理循环
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                logger.ws.debug("Received audio request", {'session_id': session_id, 'request_type': data.get('type'), 'request_size': len(str(data))})
                
                if message_type == "tts_request":
                    # TTS请求
                    text = data.get("text", "")
                    
                    logger.tts.info("Starting speech synthesis", {'session_id': session_id, 'text_length': len(text)})
                    
                    # 调用统一TTS流式服务
                    from src.services.tts_service import UnifiedTTSService
                    tts_service = UnifiedTTSService()
                    
                    try:
                        # 流式生成音频
                        async for audio_chunk in tts_service.stream_synthesize(text):
                            # 发送音频数据块（二进制）
                            await websocket.send_bytes(audio_chunk)
                        
                        logger.tts.info("Speech synthesis completed", {'session_id': session_id})
                        
                    except Exception as e:
                        logger.sys.error(f"TTS合成失败: {e}")
                        await manager.send_personal_message(session_id, {
                            "type": "error",
                            "message": f"语音合成失败: {str(e)}"
                        })
                
                elif message_type == "session_heartbeat":
                    # 会话心跳
                    logger.ws.debug("Heartbeat received", {'session_id': session_id})
                    await manager.send_personal_message(session_id, {
                        "type": "session_heartbeat",
                        "timestamp": payload.get("timestamp", 0)
                    })
                
                else:
                    # 未知消息类型
                    logger.warning(f"未知的消息类型: {message_type}")
                    await manager.send_personal_message(session_id, {
                        "type": "error",
                        "message": f"未知的消息类型: {message_type}"
                    })
            
            except WebSocketDisconnect:
                logger.ws.info("Client disconnected", {'session_id': session_id})
                break
            
            except Exception as e:
                logger.sys.error(f"处理消息异常: {e}")
                await manager.send_personal_message(session_id, {
                    "type": "error",
                    "message": f"处理失败: {str(e)}"
                })
    
    except Exception as e:
        logger.exception(f"WebSocket连接异常: {e}")
    
    finally:
        # 清理连接
        if session_id:
            await manager.disconnect(session_id)


@router.get("/connections")
async def get_connections():
    """获取当前活跃的WebSocket连接数（用于监控）"""
    return {
        "active_connections": len(manager.active_connections),
        "sessions": list(manager.active_connections.keys())
    }
