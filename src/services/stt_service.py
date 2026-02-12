# -*- coding: utf-8 -*-
"""
统一STT服务模块
用于处理语音转文本功能
使用阿里云DashScope SDK进行语音识别
"""
import json
import asyncio
import websockets
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import base64

from src.common.log_utils import get_logger
from src.common.log_formatter import log_step, log_communication
from src.common.config_utils import get_global_config


class UnifiedSTTService:
    """统一STT服务 - 集成流式和非流式STT功能"""
    
    def __init__(self):
        """初始化STT服务"""
        self.logger = get_logger()
        # 延迟加载配置，直到实际使用时
        self._config = None
        self._stt_config = None
        self.stt_base_url = None
        self.stt_api_key = None
        self.stt_model = None

    def _ensure_config_loaded(self):
        """确保配置已加载"""
        if self._config is None:
            self._config = get_global_config()
            self._stt_config = self._config.get("stt", {})
            
            # STT客户端配置
            self.stt_base_url = self._stt_config.get("base_url", "wss://dashscope.aliyuncs.com/api-ws/v1/inference")
            self.stt_api_key = self._stt_config.get("api_key", "")
            self.stt_model = self._stt_config.get("model", "paraformer-realtime-v2")
            
            if not self.stt_api_key:
                raise RuntimeError("STT 未配置 api_key，请在 config.json 中设置")
    
    async def recognize_audio(self, audio_data: bytes) -> str:
        """
        识别音频为文本（非流式）
        
        Args:
            audio_data: 音频数据
            
        Returns:
            识别出的文本
        """
        if not audio_data:
            return ""
            
        self.logger.info(f"开始STT识别: 音频大小 {len(audio_data)} bytes")
        
        # 确保配置已加载
        self._ensure_config_loaded()
        
        try:
            # 编码音频数据为Base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 构建请求payload
            payload = {
                "model": self.stt_model,
                "audio": {
                    "content": audio_b64,
                    "mime_type": "audio/wav"  # 根据实际情况调整
                },
                "parameters": {
                    "language": "zh-CN",
                    "accent": "mandarin"
                }
            }
            
            # 记录客户端消息发送
            print(log_communication('STT', 'SEND', 'STT识别请求', 
                                  {'audio_size': len(audio_data), 'model': self.stt_model}))
            
            # 使用WebSocket连接阿里云STT服务
            full_text = ""
            async with websockets.connect(self.stt_base_url) as websocket:
                # 发送认证和配置信息
                auth_payload = {
                    "header": {
                        "action": "connect",
                        "namespace": "SpeechRecognizer",
                        "name": "StartRequest",
                        "message_id": f"auth_{hash(str(audio_data)[:10]) % 10000}",
                        "client_cfg": {
                            "api_key": self.stt_api_key
                        }
                    },
                    "payload": {
                        "audio": {
                            "format": "wav",
                            "rate": 16000,
                            "bits": 16,
                            "channels": 1
                        }
                    }
                }
                
                await websocket.send(json.dumps(auth_payload, ensure_ascii=False))
                
                # 发送音频数据
                audio_payload = {
                    "header": {
                        "action": "send_audio",
                        "namespace": "SpeechRecognizer",
                        "name": "AudioData",
                        "message_id": f"audio_{hash(str(audio_data)[:10]) % 10000}"
                    },
                    "payload": {
                        "audio": audio_b64
                    }
                }
                
                await websocket.send(json.dumps(audio_payload, ensure_ascii=False))
                
                # 发送结束标志
                end_payload = {
                    "header": {
                        "action": "finish",
                        "namespace": "SpeechRecognizer",
                        "name": "FinishRequest",
                        "message_id": f"end_{hash(str(audio_data)[:10]) % 10000}"
                    }
                }
                
                await websocket.send(json.dumps(end_payload, ensure_ascii=False))
                
                # 接收识别结果
                while True:
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    
                    if response_data.get("header", {}).get("status") == "end":
                        break
                    
                    if "payload" in response_data:
                        text_result = response_data["payload"].get("text", "")
                        if text_result:
                            full_text += text_result
                
                # 记录客户端消息接收
                print(log_communication('STT', 'RECEIVE', 'STT识别响应', 
                                      {'recognized_text': full_text[:100]}))
            
            self.logger.info(f"STT识别完成: {full_text[:50]}...")
            return full_text
            
        except Exception as e:
            self.logger.error(f"STT识别失败: {str(e)}")
            print(log_step('STT', 'ERROR', f'STT识别失败', {'error': str(e)}))
            return ""
    
    async def stream_recognize(self, audio_generator) -> AsyncGenerator[str, None]:
        """
        流式语音识别
        
        Args:
            audio_generator: 音频数据生成器
        
        Yields:
            识别出的文本片段
        """
        # 确保配置已加载
        self._ensure_config_loaded()
        
        print(log_step('STT', 'SEND', '开始流式语音识别', {}))
        
        try:
            # 记录客户端消息发送
            print(log_communication('STT', 'SEND', '流式STT请求', 
                                  {'model': self.stt_model}))
            
            # 使用WebSocket连接阿里云STT服务
            async with websockets.connect(self.stt_base_url) as websocket:
                # 发送认证头部
                auth_header = {
                    "action": "connect",
                    "namespace": "SpeechRecognizer",
                    "name": "StartRequest",
                    "message_id": f"auth_{hash(str(datetime.now())) % 10000}",
                    "client_cfg": {
                        "api_key": self.stt_api_key
                    }
                }
                
                await websocket.send(json.dumps({
                    "header": auth_header,
                    "payload": {
                        "audio": {
                            "format": "pcm",  # 或根据输入格式调整
                            "rate": 16000,
                            "bits": 16,
                            "channels": 1
                        }
                    }
                }, ensure_ascii=False))
                
                # 处理流式音频数据
                async for audio_chunk in audio_generator:
                    # 将音频块编码为Base64
                    audio_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                    
                    # 发送音频数据块
                    audio_header = {
                        "action": "send_audio",
                        "namespace": "SpeechRecognizer",
                        "name": "AudioData",
                        "message_id": f"audio_{hash(str(audio_chunk)[:10]) % 10000}"
                    }
                    
                    await websocket.send(json.dumps({
                        "header": audio_header,
                        "payload": {
                            "audio": audio_b64
                        }
                    }, ensure_ascii=False))
                    
                    # 接收中间识别结果
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        response_data = json.loads(response)
                        
                        if "payload" in response_data:
                            text_result = response_data["payload"].get("text", "")
                            if text_result:
                                # 发送文本片段
                                yield text_result
                                
                                print(log_step('STT', 'STREAM', '识别文本片段', 
                                              {'text': text_result[:50]}))
                    except asyncio.TimeoutError:
                        # 没有立即响应是正常的
                        pass
                
                # 发送结束标志
                end_header = {
                    "action": "finish",
                    "namespace": "SpeechRecognizer",
                    "name": "FinishRequest",
                    "message_id": f"end_{hash(str(datetime.now())) % 10000}"
                }
                
                await websocket.send(json.dumps({
                    "header": end_header
                }, ensure_ascii=False))
                
                # 接收最终结果
                final_response = await websocket.recv()
                final_data = json.loads(final_response)
                
                if "payload" in final_data:
                    final_text = final_data["payload"].get("text", "")
                    if final_text:
                        yield final_text
                        print(log_step('STT', 'COMPLETE', '流式语音识别完成', 
                                      {'final_text': final_text[:50]}))
                
        except Exception as e:
            self.logger.error(f"流式STT识别失败: {str(e)}")
            print(log_step('STT', 'ERROR', f'流式STT识别失败', {'error': str(e)}))
            raise e


# 保留向后兼容的别名
STTService = UnifiedSTTService