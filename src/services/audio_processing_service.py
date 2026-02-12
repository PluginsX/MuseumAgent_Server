# -*- coding: utf-8 -*-
"""
音频处理服务模块
处理预录制音频，执行STT和TTS功能
使用阿里云DashScope SDK进行语音处理
"""
import json
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from src.common.log_utils import get_logger
from src.common.log_formatter import log_step, log_communication
from src.services.stt_service import STTService
from src.services.tts_service import UnifiedTTSService as TTSService


class AudioProcessingService:
    """音频处理服务"""
    
    def __init__(self):
        """初始化音频处理服务"""
        self.logger = get_logger()
        self.stt_service = STTService()
        self.tts_service = TTSService()
    
    async def stt_convert(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        音频转文本
        
        Args:
            request: 音频转文本请求
            token: 认证令牌
            
        Returns:
            转换结果
        """
        self.logger.info("开始音频转文本处理")
        
        try:
            # 获取音频数据
            audio_data = request.get("audio_data", b"")
            if isinstance(audio_data, str):
                # 如果是base64编码的字符串，需要解码
                import base64
                audio_data = base64.b64decode(audio_data)
            
            # 记录客户端消息接收
            print(log_communication('AUDIO_SERVICE', 'RECEIVE', '音频数据', 
                                   {'audio_size': len(audio_data)}))
            
            # 记录处理开始
            print(log_step('AUDIO_SERVICE', 'START', '开始音频转文本', 
                          {'audio_size': len(audio_data)}))
            
            # 执行STT识别
            text_result = await self.stt_service.recognize_audio(audio_data)
            
            # 构建响应
            result = {
                "code": 200,
                "msg": "音频转文本成功",
                "data": {
                    "recognized_text": text_result,
                    "original_audio_size": len(audio_data)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            print(log_step('AUDIO_SERVICE', 'SUCCESS', '音频转文本完成', 
                          {'text_length': len(text_result)}))
            return result
            
        except Exception as e:
            self.logger.error(f"音频转文本失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"音频转文本失败: {str(e)}",
                "data": None
            }
    
    async def tts_convert(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        文本转音频
        
        Args:
            request: 文本转音频请求
            token: 认证令牌
            
        Returns:
            转换结果
        """
        self.logger.info("开始文本转音频处理")
        
        try:
            # 获取文本内容
            text_content = request.get("text", "")
            
            # 记录客户端消息接收
            print(log_communication('AUDIO_SERVICE', 'RECEIVE', '文本内容', 
                                   {'text_preview': text_content[:50]}))
            
            # 记录处理开始
            print(log_step('AUDIO_SERVICE', 'START', '开始文本转音频', 
                          {'text_length': len(text_content)}))
            
            # 执行TTS合成
            audio_result = await self.tts_service.synthesize_text(text_content)
            
            # 构建响应（注意：实际部署时不应返回完整的音频数据，而是返回音频URL或其他引用）
            result = {
                "code": 200,
                "msg": "文本转音频成功",
                "data": {
                    "audio_data": audio_result.hex() if audio_result else None,  # 实际应用中应返回音频URL
                    "audio_size": len(audio_result) if audio_result else 0,
                    "original_text": text_content
                },
                "timestamp": datetime.now().isoformat()
            }
            
            print(log_step('AUDIO_SERVICE', 'SUCCESS', '文本转音频完成', 
                          {'audio_size': len(audio_result) if audio_result else 0}))
            return result
            
        except Exception as e:
            self.logger.error(f"文本转音频失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"文本转音频失败: {str(e)}",
                "data": None
            }
    
    async def process_audio(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        完整的音频处理流程（可选：先STT再TTS）
        
        Args:
            request: 音频处理请求
            token: 认证令牌
            
        Returns:
            处理结果
        """
        self.logger.info("开始完整音频处理流程")
        
        try:
            # 获取请求参数
            audio_data = request.get("audio_data", b"")
            target_text = request.get("target_text", "")
            process_type = request.get("process_type", "stt_then_tts")  # stt, tts, stt_then_tts
            
            result = {
                "code": 200,
                "msg": "音频处理完成",
                "data": {},
                "timestamp": datetime.now().isoformat()
            }
            
            if process_type == "stt":
                # 仅执行STT
                if isinstance(audio_data, str):
                    import base64
                    audio_data = base64.b64decode(audio_data)
                
                recognized_text = await self.stt_service.recognize_audio(audio_data)
                result["data"]["recognized_text"] = recognized_text
                
            elif process_type == "tts":
                # 仅执行TTS
                synthesized_audio = await self.tts_service.synthesize_text(target_text)
                result["data"]["audio_data"] = synthesized_audio.hex() if synthesized_audio else None
                result["data"]["audio_size"] = len(synthesized_audio) if synthesized_audio else 0
                
            elif process_type == "stt_then_tts":
                # 先STT再TTS
                if isinstance(audio_data, str):
                    import base64
                    audio_data = base64.b64decode(audio_data)
                
                recognized_text = await self.stt_service.recognize_audio(audio_data)
                synthesized_audio = await self.tts_service.synthesize_text(recognized_text)
                
                result["data"]["recognized_text"] = recognized_text
                result["data"]["synthesized_audio"] = synthesized_audio.hex() if synthesized_audio else None
                result["data"]["synthesized_audio_size"] = len(synthesized_audio) if synthesized_audio else 0
            
            print(log_step('AUDIO_SERVICE', 'SUCCESS', '完整音频处理完成', 
                          {'process_type': process_type}))
            return result
            
        except Exception as e:
            self.logger.error(f"完整音频处理失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"完整音频处理失败: {str(e)}",
                "data": None
            }
    
    async def stream_process_audio(self, request: Dict[str, Any], token: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式音频处理
        
        Args:
            request: 音频处理请求
            token: 认证令牌
            
        Yields:
            处理结果片段
        """
        try:
            # 获取音频流
            audio_stream = request.get("audio_stream", [])
            
            # 模拟流式处理
            for i, audio_chunk in enumerate(audio_stream):
                # 执行STT识别
                text_result = await self.stt_service.recognize_audio(audio_chunk)
                
                yield {
                    "type": "audio_chunk_processed",
                    "chunk_index": i,
                    "recognized_text": text_result,
                    "done": False
                }
            
            yield {
                "type": "audio_chunk_processed",
                "chunk_index": len(audio_stream),
                "done": True
            }
        except Exception as e:
            self.logger.error(f"流式音频处理失败: {str(e)}")
            yield {
                "type": "error",
                "message": f"流式音频处理失败: {str(e)}"
            }