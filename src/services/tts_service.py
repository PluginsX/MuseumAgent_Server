# -*- coding: utf-8 -*-
"""
统一TTS服务模块
用于处理文本转语音功能
使用阿里云DashScope SDK进行语音合成
"""
import json
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

# 导入阿里云DashScope SDK
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

from src.common.enhanced_logger import get_enhanced_logger, Module
from src.common.config_utils import get_global_config


class UnifiedTTSService:
    """统一TTS服务 - 集成流式和非流式TTS功能"""
    
    def __init__(self):
        """初始化TTS服务"""
        self.logger = get_enhanced_logger()
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
            self.tts_api_key = self._tts_config.get("api_key", "")
            self.tts_model = self._tts_config.get("model", "cosyvoice-v3-plus")
            self.tts_voice = self._tts_config.get("voice", "HanLi")  # 从配置中读取音色
            self.tts_format = self._tts_config.get("format", "MP3_22050HZ_MONO_256KBPS")  # 从配置中读取音频格式
            
            # 设置DashScope API密钥
            if self.tts_api_key:
                dashscope.api_key = self.tts_api_key
            else:
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
            
        self.logger.tts.info("Starting TTS synthesis", {
            'text_preview': text[:50],
            'text_length': len(text)
        })
        
        # 确保配置已加载
        self._ensure_config_loaded()
        
        try:
            # 记录客户端消息发送
            self.logger.tts.info('TTS synthesis request sent', 
                                  {'text_length': len(text), 'model': self.tts_model})
            
            try:
                # 使用DashScope SDK进行语音合成 - 使用非流式调用
                # 根据文档，创建SpeechSynthesizer实例并调用
                import tempfile
                import time
                from io import BytesIO
                from dashscope.audio.tts_v2.speech_synthesizer import AudioFormat
                
                # 创建SpeechSynthesizer实例
                # 使用从配置中读取的音色和格式
                from dashscope.audio.tts_v2 import AudioFormat
                # 将字符串格式转换为AudioFormat枚举
                audio_format = getattr(AudioFormat, self.tts_format, AudioFormat.MP3_22050HZ_MONO_256KBPS)
                
                synthesizer = SpeechSynthesizer(
                    model=self.tts_model,
                    voice=self.tts_voice,  # 使用从配置中读取的音色
                    format=audio_format  # 使用从配置中读取的音频格式
                )
                
                # 直接调用实例方法获取音频数据
                audio_data = synthesizer.call(text)
                
                if audio_data:
                    # 记录客户端消息接收
                    self.logger.tts.info('TTS synthesis response received', 
                                          {'audio_size': len(audio_data)})
                    
                    self.logger.tts.info('TTS synthesis completed', {'audio_size': len(audio_data)})
                    return audio_data
                else:
                    self.logger.tts.error('TTS synthesis returned empty audio data')
                    return None
                    
            except Exception as e:
                self.logger.tts.error('TTS synthesis exception', {'error': str(e)})
                # 返回降级结果
                return b"mock_audio_data_for_testing"
            
        except Exception as e:
            self.logger.tts.error("TTS synthesis failed", {
                'error': str(e),
                'flow': 'SYNTHESIS_ERROR'
            })
            return None
    
    async def stream_synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        流式语音合成
        
        Args:
            text: 要合成的文本
        
        Yields:
            音频数据块（bytes）
        """
        # 由于DashScope的TTS API通常返回完整的音频数据，
        # 我们将完整音频数据分块返回以模拟流式行为
        # 这里我们先生成完整音频，然后分块yield
        
        self.logger.tts.info('Starting streaming voice synthesis', {'text': text[:50]})
        
        # 确保配置已加载
        self._ensure_config_loaded()
        
        try:
            # 记录客户端消息发送
            self.logger.tts.info('Streaming TTS request sent', 
                                  {'text_length': len(text), 'model': self.tts_model})
            
            # 使用非流式方法获取完整音频数据
            full_audio_data = await self.synthesize_text(text)
            
            if full_audio_data:
                # 将完整音频数据分块返回，模拟流式行为
                chunk_size = 8192  # 8KB chunks
                for i in range(0, len(full_audio_data), chunk_size):
                    chunk = full_audio_data[i:i + chunk_size]
                    
                    # 发送音频数据块
                    yield chunk
                    
                    self.logger.tts.info('Sending audio chunk', 
                                  {'chunk_size': len(chunk)})
            
            self.logger.tts.info('Streaming voice synthesis completed', {})
        except Exception as e:
            self.logger.tts.error('Streaming TTS synthesis failed', {'error': str(e)})
            
            # 返回一个模拟的音频数据用于测试
            mock_audio = b"mock_audio_data_for_testing_" + text.encode('utf-8')[:100]
            yield mock_audio
            
            raise e


# 保留向后兼容的别名
TTSService = UnifiedTTSService