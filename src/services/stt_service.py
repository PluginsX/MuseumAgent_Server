# -*- coding: utf-8 -*-
"""
统一STT服务模块
用于处理语音转文本功能
使用阿里云DashScope SDK进行语音识别
"""
import json
import asyncio
import base64
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

# 导入阿里云DashScope SDK
import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback

# 创建一个简单的回调类
class SimpleRecognitionCallback(RecognitionCallback):
    def __init__(self):
        super().__init__()
        self.results = []

    def on_open(self):
        pass

    def on_error(self, message=None):
        pass

    def on_close(self):
        pass

    def on_event(self, message):
        self.results.append(message)

from src.common.enhanced_logger import get_enhanced_logger, Module
from src.common.config_utils import get_global_config, register_config_listener
from src.services.interrupt_manager import get_interrupt_manager


class UnifiedSTTService:
    """统一STT服务 - 集成流式和非流式STT功能"""
    
    def __init__(self):
        """初始化STT服务"""
        self.logger = get_enhanced_logger()
        self.interrupt_manager = get_interrupt_manager()
        # 延迟加载配置，直到实际使用时
        self._config = None
        self._stt_config = None
        self.stt_base_url = None
        self.stt_api_key = None
        self.stt_model = None
        
        # 注册配置变更监听器
        register_config_listener("stt", self.reload_config)
    
    def reload_config(self, new_config: dict) -> None:
        """重新加载配置"""
        self.logger.sys.info("STT配置变更，正在重新加载...")
        self._stt_config = new_config
        
        # STT客户端配置
        self.stt_api_key = self._stt_config.get("api_key", "")
        self.stt_model = self._stt_config.get("model", "paraformer-realtime-v2")
        
        # 设置DashScope API密钥
        if self.stt_api_key:
            dashscope.api_key = self.stt_api_key
        
        self.logger.sys.info("STT配置重新加载完成")

    def _ensure_config_loaded(self):
        """确保配置已加载"""
        if self._config is None:
            self._config = get_global_config()
            self._stt_config = self._config.get("stt", {})
            
            # STT客户端配置
            self.stt_api_key = self._stt_config.get("api_key", "")
            self.stt_model = self._stt_config.get("model", "paraformer-realtime-v2")
            
            # 设置DashScope API密钥
            if self.stt_api_key:
                dashscope.api_key = self.stt_api_key
            else:
                raise RuntimeError("STT 未配置 api_key，请在 config.json 中设置")
    
    def _detect_audio_format(self, audio_data: bytes) -> tuple:
        """
        自动检测音频格式
        
        Args:
            audio_data: 音频二进制数据
            
        Returns:
            (format_name, file_suffix) 元组
        """
        if len(audio_data) < 4:
            # 数据太短，默认为mp3
            return ('mp3', '.mp3')
        
        # 检查文件头魔数
        header = audio_data[:4]
        
        # WebM格式 (EBML header: 0x1A 0x45 0xDF 0xA3)
        if header == b'\x1a\x45\xdf\xa3':
            self.logger.stt.info("Detected WebM format")
            return ('webm', '.webm')
        
        # MP3格式 (ID3 tag: 'ID3' or MPEG frame sync: 0xFF 0xFB/0xFA)
        if header[:3] == b'ID3' or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
            self.logger.stt.info("Detected MP3 format")
            return ('mp3', '.mp3')
        
        # WAV格式 (RIFF header: 'RIFF')
        if header[:4] == b'RIFF':
            self.logger.stt.info("Detected WAV format")
            return ('wav', '.wav')
        
        # OGG格式 (OggS header)
        if header[:4] == b'OggS':
            self.logger.stt.info("Detected OGG format")
            return ('ogg', '.ogg')
        
        # M4A/AAC格式 (ftyp box)
        if len(audio_data) >= 8 and audio_data[4:8] == b'ftyp':
            self.logger.stt.info("Detected M4A/AAC format")
            return ('m4a', '.m4a')
        
        # 默认为mp3
        self.logger.stt.warn(f"Unknown audio format, header: {header.hex()}, defaulting to mp3")
        return ('mp3', '.mp3')
    
    def _convert_pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """
        将裸PCM数据转换为WAV格式
        
        Args:
            pcm_data: 裸PCM数据（16bit, 16kHz, 单声道）
            
        Returns:
            WAV格式的音频数据
        """
        import struct
        
        # WAV文件参数
        sample_rate = 16000
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_data)
        file_size = 36 + data_size
        
        # 构建WAV文件头（44字节）
        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',           # ChunkID
            file_size,         # ChunkSize
            b'WAVE',           # Format
            b'fmt ',           # Subchunk1ID
            16,                # Subchunk1Size (PCM)
            1,                 # AudioFormat (PCM)
            num_channels,      # NumChannels
            sample_rate,       # SampleRate
            byte_rate,         # ByteRate
            block_align,       # BlockAlign
            bits_per_sample,   # BitsPerSample
            b'data',           # Subchunk2ID
            data_size          # Subchunk2Size
        )
        
        self.logger.stt.info(f"Converted PCM to WAV: {len(pcm_data)} bytes PCM -> {len(wav_header) + len(pcm_data)} bytes WAV")
        
        return wav_header + pcm_data
    

    async def stream_recognize(self, audio_generator, audio_format: str = 'pcm', session_id: str = None) -> str:
        """
        真正的流式语音识别（输入流式，输出完整文本）
        
        Args:
            audio_generator: 音频数据生成器（异步迭代器）
            audio_format: 音频格式（'pcm', 'wav', 'opus'等）
        
        Returns:
            完整的识别文本（用于后续的语义检索）
        """
        self.logger.stt.info('Starting real-time streaming STT', {'format': audio_format})
        
        # 确保配置已加载
        self._ensure_config_loaded()
        
        try:
            import queue
            import threading
            
            # 创建队列用于收集识别结果
            result_queue = queue.Queue()
            recognition_complete = threading.Event()
            recognition_error = [None]
            
            # 定义 callback 类来接收实时识别结果
            class StreamingRecognitionCallback(RecognitionCallback):
                def __init__(self, logger):
                    super().__init__()
                    self.logger = logger
                    self.partial_results = []
                    self.final_result = ""
                
                def on_open(self):
                    self.logger.stt.debug('STT WebSocket connection opened')
                
                def on_complete(self):
                    self.logger.stt.info('STT recognition completed', {'final_text': self.final_result[:100]})
                    result_queue.put(('complete', self.final_result))
                    recognition_complete.set()
                
                def on_error(self, message=None):
                    error_msg = str(message) if message else 'Unknown error'
                    self.logger.stt.error('STT recognition error', {'error': error_msg})
                    recognition_error[0] = error_msg
                    result_queue.put(('error', error_msg))
                    recognition_complete.set()
                
                def on_close(self):
                    self.logger.stt.debug('STT WebSocket connection closed')
                
                def on_event(self, result):
                    """实时接收识别结果"""
                    if result:
                        # 获取识别文本
                        sentence = result.get_sentence()
                        if sentence:
                            text = sentence.get('text', '')
                            if text:
                                # 判断是部分结果还是最终结果
                                # end_time 可能为 None，需要安全处理
                                end_time = sentence.get('end_time')
                                is_final = end_time is not None and end_time > 0
                                
                                if is_final:
                                    self.final_result = text
                                    self.logger.stt.info('STT final result', {'text': text[:100]})
                                else:
                                    self.partial_results.append(text)
                                    self.logger.stt.debug('STT partial result', {'text': text[:50]})
                                
                                result_queue.put(('partial' if not is_final else 'final', text))
            
            # 创建 callback 实例
            callback = StreamingRecognitionCallback(self.logger)
            
            # 创建 Recognition 实例
            recognition = Recognition(
                model=self.stt_model,
                format=audio_format,
                sample_rate=16000,
                callback=callback
            )
                
            # 启动流式识别
            recognition.start()
            self.logger.stt.info('STT streaming started')
            
            # ✅ 注册到中断管理器
            if session_id:
                self.interrupt_manager.register_stt(session_id, recognition)
            
            # 在后台线程发送音频数据
            async def send_audio_frames():
                try:
                    frame_count = 0
                    async for audio_chunk in audio_generator:
                        if audio_chunk:
                            # 发送音频帧（同步调用，但很快）
                            recognition.send_audio_frame(audio_chunk)
                            frame_count += 1
                            self.logger.stt.debug('Sent audio frame', {
                                'frame_num': frame_count,
                                'size': len(audio_chunk)
                            })
                    
                    self.logger.stt.info('All audio frames sent', {'total_frames': frame_count})
                    
                    # 所有音频发送完毕，停止识别（阻塞调用，需要在线程中执行）
                    self.logger.stt.info('Calling recognition.stop() (blocking call)...')
                    await asyncio.to_thread(recognition.stop)
                    self.logger.stt.info('STT streaming stopped')
                    
                except Exception as e:
                    recognition_error[0] = str(e)
                    self.logger.stt.error('Error sending audio frames', {'error': str(e)})
                    recognition_complete.set()
            
            # 启动音频发送任务
            send_task = asyncio.create_task(send_audio_frames())
            
            # 等待识别完成（通过回调触发）
            while not recognition_complete.is_set():
                await asyncio.sleep(0.1)
            
            # 等待发送任务完成
            try:
                await send_task
            except Exception as e:
                self.logger.stt.error('Send task failed', {'error': str(e)})
            
            # 检查是否有错误
            if recognition_error[0]:
                raise Exception(f'STT recognition failed: {recognition_error[0]}')
            
            # 返回完整的识别文本
            final_text = callback.final_result
            self.logger.stt.info('Real-time streaming STT completed', {'final_text': final_text[:100]})
            
            return final_text
        
        except Exception as e:
            self.logger.stt.error('Streaming STT recognition failed', {'error': str(e)})
            raise e


# 保留向后兼容的别名
STTService = UnifiedSTTService