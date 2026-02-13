# -*- coding: utf-8 -*-
"""
语音通话服务模块
处理实时语音通话功能
同时调用STT和TTS服务实现语音对话
"""
import asyncio
import json
import websockets
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from collections import defaultdict

from src.common.enhanced_logger import get_enhanced_logger
from src.common.config_utils import get_global_config
from src.services.stt_service import STTService
from src.services.tts_service import UnifiedTTSService as TTSService
from src.core.dynamic_llm_client import DynamicLLMClient


class VoiceCallService:
    """语音通话服务"""
    
    def __init__(self):
        """初始化语音通话服务"""
        self.logger = get_enhanced_logger()
        self.config = get_global_config()
        self.stt_service = STTService()
        self.tts_service = TTSService()
        self.llm_client = DynamicLLMClient()
        
        # 存储活跃的通话会话
        self.active_calls = {}
        self.call_locks = defaultdict(asyncio.Lock)
    
    async def start_call(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        启动语音通话
        
        Args:
            request: 通话启动请求
            token: 认证令牌
            
        Returns:
            通话启动结果
        """
        self.logger.info("开始启动语音通话")
        
        try:
            # 生成通话ID
            call_id = request.get("call_id") or f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(request)) % 10000}"
            session_id = request.get("session_id", "")
            
            # 记录客户端消息接收
            self.logger.voice.info('Voice call start request received', 
                                   {'call_id': call_id, 'session_id': session_id})
            
            # 记录处理开始
            self.logger.voice.info('Starting voice call', 
                          {'call_id': call_id})
            
            # 初始化通话上下文
            call_context = {
                "call_id": call_id,
                "session_id": session_id,
                "start_time": datetime.now(),
                "active": True,
                "conversation_history": [],
                "audio_buffer": b"",
                "processing_queue": asyncio.Queue()
            }
            
            # 存储通话上下文
            self.active_calls[call_id] = call_context
            
            # 构建响应
            result = {
                "code": 200,
                "msg": "语音通话启动成功",
                "data": {
                    "call_id": call_id,
                    "session_id": session_id,
                    "start_time": call_context["start_time"].isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.voice.info('Voice call started successfully', 
                          {'call_id': call_id})
            return result
            
        except Exception as e:
            self.logger.sys.error(f"语音通话启动失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"语音通话启动失败: {str(e)}",
                "data": None
            }
    
    async def end_call(self, call_id: str, token: str = None) -> Dict[str, Any]:
        """
        结束语音通话
        
        Args:
            call_id: 通话ID
            token: 认证令牌
            
        Returns:
            通话结束结果
        """
        self.logger.info(f"开始结束语音通话: {call_id}")
        
        try:
            if call_id not in self.active_calls:
                return {
                    "code": 404,
                    "msg": "通话不存在",
                    "data": None
                }
            
            # 获取通话上下文
            call_context = self.active_calls[call_id]
            
            # 标记通话为非活跃
            call_context["active"] = False
            
            # 清理通话上下文
            del self.active_calls[call_id]
            
            # 构建响应
            result = {
                "code": 200,
                "msg": "语音通话结束成功",
                "data": {
                    "call_id": call_id,
                    "end_time": datetime.now().isoformat(),
                    "duration": (datetime.now() - call_context["start_time"]).total_seconds()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.voice.info('Voice call ended', 
                          {'call_id': call_id, 'session_id': session_id})
            return result
            
        except Exception as e:
            self.logger.sys.error(f"语音通话结束失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"语音通话结束失败: {str(e)}",
                "data": None
            }
    
    async def process_voice_stream(self, call_id: str, audio_chunk: bytes) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理语音流数据
        
        Args:
            call_id: 通话ID
            audio_chunk: 音频数据块
            
        Yields:
            处理结果
        """
        if call_id not in self.active_calls:
            yield {
                "type": "error",
                "message": "通话不存在"
            }
            return
        
        call_context = self.active_calls[call_id]
        
        try:
            # 记录接收到的音频块
            self.logger.voice.info('Audio chunk received', 
                                   {'call_id': call_id, 'chunk_size': len(audio_chunk)})
            
            # 将音频块添加到队列进行处理
            await call_context["processing_queue"].put({
                "type": "audio_chunk",
                "data": audio_chunk,
                "timestamp": datetime.now()
            })
            
            # 异步处理音频数据
            async with self.call_locks[call_id]:
                # 执行STT识别
                recognized_text = await self.stt_service.recognize_audio(audio_chunk)
                
                if recognized_text.strip():
                    # 添加到对话历史
                    call_context["conversation_history"].append({
                        "role": "user",
                        "content": recognized_text,
                        "timestamp": datetime.now()
                    })
                    
                    # 调用LLM生成响应
                    llm_response = await self._generate_llm_response(call_context, recognized_text)
                    
                    # 如果有响应内容，执行TTS
                    if llm_response and llm_response.get("content"):
                        tts_audio = await self.tts_service.synthesize_text(llm_response["content"])
                        
                        # 添加到对话历史
                        call_context["conversation_history"].append({
                            "role": "assistant",
                            "content": llm_response["content"],
                            "timestamp": datetime.now()
                        })
                        
                        yield {
                            "type": "tts_audio",
                            "audio_data": tts_audio.hex() if tts_audio else None,
                            "text_content": llm_response["content"],
                            "call_id": call_id
                        }
                
                yield {
                    "type": "stt_result",
                    "recognized_text": recognized_text,
                    "call_id": call_id,
                    "done": False
                }
                
        except Exception as e:
            self.logger.sys.error(f"语音流处理失败: {str(e)}")
            yield {
                "type": "error",
                "message": f"语音流处理失败: {str(e)}"
            }
    
    async def _generate_llm_response(self, call_context: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """生成LLM响应"""
        try:
            # 构建消息历史
            messages = []
            
            # 添加系统消息
            messages.append({
                "role": "system",
                "content": "你是博物馆智能助手，正在进行语音对话。请简洁明了地回答用户问题。"
            })
            
            # 添加历史对话
            for item in call_context["conversation_history"][-10:]:  # 只保留最近10条消息
                messages.append({
                    "role": item["role"],
                    "content": item["content"]
                })
            
            # 添加当前用户输入
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # 构建请求负载
            payload = {
                "model": self.llm_client.model,
                "messages": messages,
                "temperature": self.llm_client.parameters.get("temperature", 0.7),
                "max_tokens": self.llm_client.parameters.get("max_tokens", 512),
                "top_p": self.llm_client.parameters.get("top_p", 0.9),
            }
            
            # 调用LLM
            response = self.llm_client._chat_completions_with_functions(payload)
            
            # 提取内容
            choices = response.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                return {"content": content}
            else:
                return {"content": "抱歉，我没有理解您的意思。"}
                
        except Exception as e:
            self.logger.sys.error(f"LLM响应生成失败: {str(e)}")
            return {"content": "抱歉，我现在无法处理您的请求。"}
    
    async def get_call_status(self, call_id: str, token: str = None) -> Dict[str, Any]:
        """
        获取通话状态
        
        Args:
            call_id: 通话ID
            token: 认证令牌
            
        Returns:
            通话状态
        """
        try:
            if call_id not in self.active_calls:
                return {
                    "code": 404,
                    "msg": "通话不存在",
                    "data": None
                }
            
            call_context = self.active_calls[call_id]
            
            status = {
                "call_id": call_id,
                "active": call_context["active"],
                "start_time": call_context["start_time"].isoformat(),
                "duration": (datetime.now() - call_context["start_time"]).total_seconds(),
                "conversation_count": len(call_context["conversation_history"]),
                "queue_size": call_context["processing_queue"].qsize()
            }
            
            return {
                "code": 200,
                "msg": "获取通话状态成功",
                "data": status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.sys.error(f"获取通话状态失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"获取通话状态失败: {str(e)}",
                "data": None
            }
    
    async def handle_real_time_communication(self, websocket, call_id: str, token: str = None):
        """
        处理实时通信（WebSocket连接）
        
        Args:
            websocket: WebSocket连接
            call_id: 通话ID
            token: 认证令牌
        """
        try:
            # 验证通话是否存在
            if call_id not in self.active_calls:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "通话不存在"
                }))
                return
            
            call_context = self.active_calls[call_id]
            
            # 发送连接成功消息
            await websocket.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "call_id": call_id
            }))
            
            # 消息处理循环
            while call_context["active"]:
                try:
                    # 接收客户端消息
                    data = await websocket.receive_json()
                    message_type = data.get("type")
                    
                    self.logger.voice.info('Real-time message received', 
                                           {'call_id': call_id, 'message_type': data.get('type')})
                    
                    # 处理不同类型的消息
                    if message_type == "voice_data":
                        # 音频数据
                        audio_data = data.get("audio_data", b"")
                        if isinstance(audio_data, str):
                            import base64
                            audio_data = base64.b64decode(audio_data)
                        
                        # 处理语音数据
                        async for result in self.process_voice_stream(call_id, audio_data):
                            await websocket.send(json.dumps(result))
                    
                    elif message_type == "call_end":
                        # 结束通话
                        await self.end_call(call_id, token)
                        await websocket.send(json.dumps({
                            "type": "call_end",
                            "status": "ended",
                            "call_id": call_id
                        }))
                        break
                    
                    elif message_type == "ping":
                        # 心跳
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                    else:
                        # 未知消息类型
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": f"未知的消息类型: {message_type}"
                        }))
                
                except websockets.exceptions.ConnectionClosed:
                    self.logger.voice.info('WebSocket connection disconnected', 
                                  {'call_id': call_id})
                    break
                except Exception as e:
                    self.logger.sys.error(f"处理WebSocket消息异常: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"处理消息异常: {str(e)}"
                    }))
        
        except Exception as e:
            self.logger.sys.error(f"实时通信处理失败: {str(e)}")
            try:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"实时通信处理失败: {str(e)}"
                }))
            except:
                pass