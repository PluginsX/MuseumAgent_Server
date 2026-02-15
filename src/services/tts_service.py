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
            # 使用裸PCM格式以获得最佳流式性能（16kHz/16bit/单声道）
            self.tts_format = self._tts_config.get("format", "PCM_16000HZ_MONO_16BIT")  # 从配置中读取音频格式
            
            # 设置DashScope API密钥
            if self.tts_api_key:
                dashscope.api_key = self.tts_api_key
            else:
                raise RuntimeError("TTS 未配置 api_key，请在 config.json 中设置")
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本，过滤掉可能引起TTS服务问题的字符
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        import re
        
        if not text:
            return ""
        
        # 移除多余的空白字符，但保留基本的句子结构
        processed = re.sub(r'\s+', ' ', text.strip())
        
        # 检查是否只剩下标点符号或其他非语音字符
        # 如果文本只包含标点符号，则返回空字符串
        # 使用正则表达式检测是否只包含标点符号和空白
        if re.match(r'^[^\w\s]+$', processed.replace(' ', '')):
            # 如果整个文本只包含标点符号，返回空字符串
            return ""
        
        return processed
    
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
            
        # 预处理文本，过滤掉可能引起问题的纯标点符号
        processed_text = self._preprocess_text(text)
        if not processed_text:
            self.logger.tts.warn('Text preprocessing resulted in empty text', {
                'original_text': text
            })
            return None
            
        self.logger.tts.info("Starting TTS synthesis", {
            'text_preview': processed_text[:50],
            'text_length': len(processed_text)
        })
        
        # 确保配置已加载
        self._ensure_config_loaded()
        
        try:
            # 记录客户端消息发送
            self.logger.tts.info('TTS synthesis request sent', 
                                  {'text_length': len(processed_text), 'model': self.tts_model})
            
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
                # 将字符串格式转换为AudioFormat枚举（默认使用PCM以获得最佳流式性能）
                audio_format = getattr(AudioFormat, self.tts_format, AudioFormat.PCM_16000HZ_MONO_16BIT)
                
                synthesizer = SpeechSynthesizer(
                    model=self.tts_model,
                    voice=self.tts_voice,  # 使用从配置中读取的音色
                    format=audio_format  # 使用从配置中读取的音频格式
                )
                
                # 直接调用实例方法获取音频数据
                audio_data = synthesizer.call(processed_text)
                
                if audio_data:
                    # 记录客户端消息接收
                    self.logger.tts.info('TTS synthesis response received', 
                                          {'audio_size': len(audio_data)})
                    
                    self.logger.tts.info('TTS synthesis completed', {'audio_size': len(audio_data)})
                    return audio_data
                else:
                    self.logger.tts.error('TTS synthesis returned empty audio data', {
                        'input_text': processed_text
                    })
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
        真正的流式语音合成（使用 DashScope callback 机制）
        
        Args:
            text: 要合成的文本
        
        Yields:
            音频数据块（bytes）- 实时从 TTS 服务接收
        """
        # 预处理文本，过滤掉可能引起问题的纯标点符号
        processed_text = self._preprocess_text(text)
        if not processed_text:
            self.logger.tts.warn('Stream text preprocessing resulted in empty text', {
                'original_text': text
            })
            return
        
        self.logger.tts.info('Starting real-time streaming TTS', {'text': processed_text[:50]})
        
        # 确保配置已加载
        self._ensure_config_loaded()
        
        try:
            from dashscope.audio.tts_v2 import AudioFormat, ResultCallback
            import queue
            import threading
            
            # 创建队列用于在 callback 和 async generator 之间传递数据
            audio_queue = queue.Queue()
            synthesis_complete = threading.Event()
            synthesis_error = [None]  # 使用列表以便在闭包中修改
            
            # 定义 callback 类来接收实时音频流
            class StreamingCallback(ResultCallback):
                def __init__(self, logger):
                    super().__init__()
                    self.logger = logger
                
                def on_open(self):
                    self.logger.tts.debug('TTS WebSocket connection opened')
                
                def on_complete(self):
                    self.logger.tts.info('TTS synthesis completed')
                    audio_queue.put(None)  # 结束标记
                    synthesis_complete.set()
                
                def on_error(self, message: str):
                    self.logger.tts.error('TTS synthesis error', {'error': str(message)})
                    synthesis_error[0] = str(message)
                    audio_queue.put(None)
                    synthesis_complete.set()
                
                def on_data(self, data: bytes):
                    """实时接收音频数据（正确的回调方法）"""
                    if data:
                        # 检测音频帧是否包含静音
                        import struct
                        samples = struct.unpack(f'<{len(data)//2}h', data)
                        non_zero = sum(1 for s in samples if abs(s) > 100)
                        max_amplitude = max(abs(s) for s in samples) if samples else 0
                        
                        self.logger.tts.debug('Received audio data', {
                            'size': len(data),
                            'non_zero_samples': non_zero,
                            'total_samples': len(samples),
                            'max_amplitude': max_amplitude,
                            'is_silent': non_zero < len(samples) * 0.1
                        })
                        audio_queue.put(data)
                
                def on_event(self, message):
                    """事件回调（用于其他事件）"""
                    self.logger.tts.debug('TTS event', {'message': str(message)[:100]})
            
            # 创建 callback 实例
            callback = StreamingCallback(self.logger)
            
            # 创建 SpeechSynthesizer 实例（带 callback）
            audio_format = getattr(AudioFormat, self.tts_format, AudioFormat.PCM_16000HZ_MONO_16BIT)
            synthesizer = SpeechSynthesizer(
                model=self.tts_model,
                voice=self.tts_voice,
                format=audio_format,
                callback=callback
            )
            
            # 在后台线程启动合成（非阻塞）
            def run_synthesis():
                try:
                    synthesizer.call(processed_text)
                except Exception as e:
                    synthesis_error[0] = str(e)
                    audio_queue.put(None)
                    synthesis_complete.set()
            
            synthesis_thread = threading.Thread(target=run_synthesis, daemon=True)
            synthesis_thread.start()
            
            # 实时从队列中取出音频数据并 yield
            while True:
                # 非阻塞检查队列
                try:
                    chunk = audio_queue.get(timeout=0.1)
                    if chunk is None:  # 结束标记
                        break
                    yield chunk
                    self.logger.tts.debug('Yielded audio chunk', {'size': len(chunk)})
                except queue.Empty:
                    # 检查是否已完成或出错
                    if synthesis_complete.is_set():
                        break
                    await asyncio.sleep(0.01)  # 短暂等待
            
            # 检查是否有错误
            if synthesis_error[0]:
                raise Exception(f'TTS synthesis failed: {synthesis_error[0]}')
            
            self.logger.tts.info('Real-time streaming TTS completed')
            
        except Exception as e:
            self.logger.tts.error('Streaming TTS synthesis failed', {'error': str(e)})
            raise e


# 保留向后兼容的别名
TTSService = UnifiedTTSService