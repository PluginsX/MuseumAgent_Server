# -*- coding: utf-8 -*-
"""
统一TTS服务模块
用于处理文本转语音功能
使用阿里云DashScope SDK进行语音合成
"""
import json
import asyncio
import websockets
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from src.common.log_utils import get_logger
from src.common.log_formatter import log_step, log_communication
from src.common.config_utils import get_global_config


class UnifiedTTSService:
    """统一TTS服务 - 集成流式和非流式TTS功能"""
    
    def __init__(self):
        """初始化TTS服务"""
        self.logger = get_logger()
        # 延迟加载配置，直到实际使用时
        self._config = None
        self._tts_config = None
        self.tts_base_url = None
        self.tts_api_key = None
        self.tts_model = None
    
    def _ensure_config_loaded(self):
        """确保配置已加载"""
        if self._config is None:
            self._config = get_global_config()
            self._tts_config = self._config.get("tts", {})
            
            # TTS客户端配置
            self.tts_base_url = self._tts_config.get("base_url", "wss://dashscope.aliyuncs.com/api-ws/v1/inference")
            self.tts_api_key = self._tts_config.get("api_key", "")
            self.tts_model = self._tts_config.get("model", "cosyvoice-v3-plus")
            
            if not self.tts_api_key:
                raise RuntimeError("TTS 未配置 api_key，请在 config.json 中设置")
    
    async def synthesize_text(self, text: str) -> Optional[bytes]:
        """
        合成文本为语音（非流式）
        
        Args:
            text: 要合成的文本
            
        Returns:
            音频数据
        """
        if not text:
            return None
            
        self.logger.info(f"开始TTS合成: {text[:50]}...")
        
        # 确保配置已加载
        self._ensure_config_loaded()
        
        try:
            # 构建请求payload
            payload = {
                "header": {
                    "app_id": "museum-agent",
                    "task_id": f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text) % 10000}",
                    "create_timestamp": int(datetime.now().timestamp())
                },
                "parameter": {
                    "chat": {
                        "domain": "general",
                        "channel": 0,
                        "audio_format": "mp3"
                    }
                },
                "payload": {
                    "input": {
                        "text": text
                    },
                    "output": {
                        "audio_format": "mp3",
                        "sample_rate": 24000
                    }
                }
            }
            
            # 记录客户端消息发送
            print(log_communication('TTS', 'SEND', 'TTS合成请求', 
                                  {'text_length': len(text), 'model': self.tts_model}))
            
            # 使用WebSocket连接阿里云TTS服务
            full_audio_data = b""
            async with websockets.connect(self.tts_base_url) as websocket:
                # 发送认证和配置信息
                auth_payload = {
                    "header": {
                        "action": "connect",
                        "namespace": "SpeechSynthesizer",
                        "name": "StartRequest",
                        "message_id": f"auth_{hash(text) % 10000}",
                        "client_cfg": {
                            "api_key": self.tts_api_key
                        }
                    },
                    "payload": payload["payload"]
                }
                
                await websocket.send(json.dumps(auth_payload, ensure_ascii=False))
                
                # 发送合成请求
                synthesis_payload = {
                    "header": {
                        "action": "synthesize",
                        "namespace": "SpeechSynthesizer",
                        "name": "SynthesisRequest",
                        "message_id": f"synth_{hash(text) % 10000}"
                    },
                    "payload": payload["payload"]
                }
                
                await websocket.send(json.dumps(synthesis_payload, ensure_ascii=False))
                
                # 接收音频数据
                while True:
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    
                    if response_data.get("header", {}).get("status") == "end":
                        break
                    
                    if "payload" in response_data:
                        audio_chunk = response_data["payload"].get("audio", "")
                        if audio_chunk:
                            # 解码Base64音频数据
                            import base64
                            decoded_audio = base64.b64decode(audio_chunk)
                            full_audio_data += decoded_audio
                
                # 记录客户端消息接收
                print(log_communication('TTS', 'RECEIVE', 'TTS合成响应', 
                                      {'audio_size': len(full_audio_data)}))
            
            self.logger.info(f"TTS合成完成，音频大小: {len(full_audio_data)} bytes")
            return full_audio_data
            
        except Exception as e:
            self.logger.error(f"TTS合成失败: {str(e)}")
            print(log_step('TTS', 'ERROR', f'TTS合成失败', {'error': str(e)}))
            return None
    
    async def stream_synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        流式语音合成
        
        Args:
            text: 要合成的文本
        
        Yields:
            音频数据块（bytes）
        """
        # 确保配置已加载
        self._ensure_config_loaded()
        
        print(log_step('TTS', 'SEND', '开始流式语音合成', {'text': text[:50]}))
        
        try:
            # 构建请求payload
            payload = {
                "model": self.tts_model,
                "input": {
                    "text": text
                },
                "parameters": {
                    "text_type": "PlainText",
                    "audio_format": "mp3",
                    "sample_rate": 24000
                }
            }
            
            # 记录客户端消息发送
            print(log_communication('TTS', 'SEND', '流式TTS请求', 
                                  {'text_length': len(text), 'model': self.tts_model}))
            
            # 使用WebSocket连接阿里云TTS服务
            async with websockets.connect(self.tts_base_url) as websocket:
                # 发送认证头部
                auth_header = {
                    "action": "connect",
                    "namespace": "SpeechSynthesizer",
                    "name": "StartRequest",
                    "message_id": f"auth_{hash(text) % 10000}",
                    "client_cfg": {
                        "api_key": self.tts_api_key
                    }
                }
                
                await websocket.send(json.dumps({
                    "header": auth_header,
                    "payload": {
                        "input": {
                            "text": text
                        }
                    }
                }, ensure_ascii=False))
                
                # 发送合成请求
                synthesis_header = {
                    "action": "synthesize",
                    "namespace": "SpeechSynthesizer",
                    "name": "SynthesisRequest",
                    "message_id": f"synth_{hash(text) % 10000}"
                }
                
                await websocket.send(json.dumps({
                    "header": synthesis_header,
                    "payload": {
                        "input": {
                            "text": text
                        }
                    }
                }, ensure_ascii=False))
                
                # 流式接收音频数据
                while True:
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    
                    if response_data.get("header", {}).get("status") == "end":
                        break
                    
                    if "payload" in response_data:
                        audio_chunk = response_data["payload"].get("audio", "")
                        if audio_chunk:
                            # 解码Base64音频数据
                            import base64
                            decoded_audio = base64.b64decode(audio_chunk)
                            
                            # 发送音频数据块
                            yield decoded_audio
                            
                            print(log_step('TTS', 'STREAM', '发送音频块', 
                                          {'chunk_size': len(decoded_audio)}))
                
                print(log_step('TTS', 'COMPLETE', '流式语音合成完成', {}))
                
        except Exception as e:
            self.logger.error(f"流式TTS合成失败: {str(e)}")
            print(log_step('TTS', 'ERROR', f'流式TTS合成失败', {'error': str(e)}))
            raise e


# 保留向后兼容的别名
TTSService = UnifiedTTSService