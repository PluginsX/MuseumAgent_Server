# -*- coding: utf-8 -*-
"""
WebSocket API - 支持实时流式通信
用于语音对话、长文本流式生成、实时状态推送
"""
import json
import uuid
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import JSONResponse

from src.common.log_utils import get_logger
from src.common.log_formatter import log_step, log_communication
from src.common.auth_utils import decode_access_token

router = APIRouter(prefix="/ws", tags=["WebSocket"])

logger = get_logger()


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
            print(log_step('WS', 'CONNECT', 'WebSocket连接建立', {'session_id': session_id}))
    
    async def disconnect(self, session_id: str):
        """断开连接"""
        if self._lock is None:
            import asyncio
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
                print(log_step('WS', 'DISCONNECT', 'WebSocket连接断开', {'session_id': session_id}))
    
    async def send_personal_message(self, session_id: str, message: Dict[str, Any]):
        """发送消息给指定会话"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
                print(log_communication('WS', 'SEND', '发送消息', message, {'session_id': session_id}))
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                await self.disconnect(session_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有连接"""
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                await self.disconnect(session_id)


manager = ConnectionManager()


@router.websocket("/agent/stream")
async def agent_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌")
):
    """
    智能体流式通信WebSocket端点
    
    支持的消息类型：
    - text_stream: 文本流式生成
    - session_heartbeat: 会话心跳
    """
    await websocket.accept()
    
    session_id = None
    stream_id = None
    
    try:
        # 验证JWT Token
        try:
            payload = decode_access_token(token)
            if not payload:
                print(log_step('WS', 'AUTH_FAIL', 'Token验证失败', {'error': '无效或过期的令牌'}))
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            session_id = payload.get("session_id") or str(uuid.uuid4())
            print(log_step('WS', 'AUTH', 'Token验证成功', {'session_id': session_id}))
        except Exception as e:
            print(log_step('WS', 'AUTH_FAIL', 'Token验证失败', {'error': str(e)}))
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
                
                print(log_communication('WS', 'RECEIVE', '收到客户端消息', data, {'session_id': session_id}))
                
                # 处理不同类型的消息
                if message_type == "text_stream":
                    # 文本流式生成请求
                    stream_id = data.get("stream_id", str(uuid.uuid4()))
                    user_input = data.get("content", "")
                    
                    print(log_step('WS', 'STREAM_START', '开始流式生成', 
                                  {'stream_id': stream_id, 'input': user_input[:50]}))
                    
                    # 调用流式生成器
                    from src.core.command_generator import CommandGenerator
                    generator = CommandGenerator()
                    
                    try:
                        # 流式生成文本
                        async for chunk in generator.stream_generate(
                            user_input=user_input,
                            session_id=session_id
                        ):
                            await manager.send_personal_message(session_id, {
                                "type": "text_stream",
                                "stream_id": stream_id,
                                "chunk": chunk,
                                "done": False
                            })
                        
                        # 发送完成标记
                        await manager.send_personal_message(session_id, {
                            "type": "text_stream",
                            "stream_id": stream_id,
                            "done": True
                        })
                        
                        print(log_step('WS', 'STREAM_COMPLETE', '流式生成完成', {'stream_id': stream_id}))
                        
                    except Exception as e:
                        logger.error(f"流式生成失败: {e}")
                        await manager.send_personal_message(session_id, {
                            "type": "error",
                            "stream_id": stream_id,
                            "message": f"生成失败: {str(e)}"
                        })
                
                elif message_type == "session_heartbeat":
                    # 会话心跳
                    print(log_step('WS', 'HEARTBEAT', '收到心跳', {'session_id': session_id}))
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
                print(log_step('WS', 'DISCONNECT', '客户端主动断开', {'session_id': session_id}))
                break
            
            except Exception as e:
                logger.error(f"处理消息异常: {e}")
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
                print(log_step('WS', 'AUTH_FAIL', 'Token验证失败', {'error': '无效或过期的令牌'}))
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            session_id = payload.get("session_id") or str(uuid.uuid4())
            print(log_step('WS', 'AUTH', 'Token验证成功', {'session_id': session_id}))
        except Exception as e:
            print(log_step('WS', 'AUTH_FAIL', 'Token验证失败', {'error': str(e)}))
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
                
                print(log_communication('WS', 'RECEIVE', '收到音频请求', data, {'session_id': session_id}))
                
                if message_type == "tts_request":
                    # TTS请求
                    text = data.get("text", "")
                    
                    print(log_step('WS', 'TTS_START', '开始语音合成', 
                                  {'text': text[:50]}))
                    
                    # 调用统一TTS流式服务
                    from src.services.tts_service import UnifiedTTSService
                    tts_service = UnifiedTTSService()
                    
                    try:
                        # 流式生成音频
                        async for audio_chunk in tts_service.stream_synthesize(text):
                            # 发送音频数据块（二进制）
                            await websocket.send_bytes(audio_chunk)
                        
                        print(log_step('WS', 'TTS_COMPLETE', '语音合成完成', {}))
                        
                    except Exception as e:
                        logger.error(f"TTS合成失败: {e}")
                        await manager.send_personal_message(session_id, {
                            "type": "error",
                            "message": f"语音合成失败: {str(e)}"
                        })
                
                elif message_type == "session_heartbeat":
                    # 会话心跳
                    print(log_step('WS', 'HEARTBEAT', '收到心跳', {'session_id': session_id}))
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
                print(log_step('WS', 'DISCONNECT', '客户端主动断开', {'session_id': session_id}))
                break
            
            except Exception as e:
                logger.error(f"处理消息异常: {e}")
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
