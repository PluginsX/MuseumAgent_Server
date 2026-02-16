# -*- coding: utf-8 -*-
"""
REQUEST 业务处理器

职责：根据 REQUEST 调用 CommandGenerator、STT、TTS，产出协议 RESPONSE 流。
与协议层解耦：接收文本/语音，产出 (request_id, text_stream_seq, voice_stream_seq, function_call, content) 流。
"""
import base64
import json
import re
from typing import AsyncGenerator, Dict, Any, Optional

from src.common.enhanced_logger import get_enhanced_logger
from src.session.strict_session_manager import strict_session_manager


class SentenceBuffer:
    """
    轻量级句子缓冲器 - 用于优化流式TTS
    
    设计原则：
    1. 快速处理，最小化延迟
    2. 以短句子为单位（5-30字）
    3. 简单的正则匹配，避免复杂计算
    """
    
    def __init__(self, min_length: int = 5, max_length: int = 30):
        """
        初始化句子缓冲器
        
        Args:
            min_length: 最小句子长度（默认5字，快速发送）
            max_length: 最大句子长度（默认30字，避免延迟）
        """
        self.buffer = ""
        self.min_length = min_length
        self.max_length = max_length
        
        # 句子结束标记（中英文）- 强制分段
        self.sentence_endings = re.compile(r'[。！？\n.!?]+')
        
        # 次要分隔符（逗号、分号等）- 优先使用，保持短句
        self.minor_breaks = re.compile(r'[，；、,;]')
    
    def add_chunk(self, chunk: str) -> list[str]:
        """
        快速添加文本块，返回可以发送的短句子列表
        
        优化策略：
        1. 优先在逗号等次要分隔符处分段（保持短句）
        2. 遇到句号等强制分段
        3. 超过最大长度立即分段（避免延迟）
        
        Args:
            chunk: LLM输出的文本块
            
        Returns:
            可以发送给TTS的短句子列表
        """
        if not chunk:
            return []
        
        self.buffer += chunk
        sentences = []
        
        # 1. 优先检查次要分隔符（逗号等）- 保持短句，快速发送
        while len(self.buffer) >= self.min_length:
            # 先找次要分隔符
            minor_match = self.minor_breaks.search(self.buffer)
            # 再找句子结束符
            ending_match = self.sentence_endings.search(self.buffer)
            
            # 选择最近的分隔符
            if minor_match and (not ending_match or minor_match.start() < ending_match.start()):
                # 在逗号处分段
                end_pos = minor_match.end()
                sentence = self.buffer[:end_pos].strip()
                if len(sentence) >= self.min_length:
                    sentences.append(sentence)
                    self.buffer = self.buffer[end_pos:]
                else:
                    break
            elif ending_match:
                # 在句号处分段
                end_pos = ending_match.end()
                sentence = self.buffer[:end_pos].strip()
                if len(sentence) >= self.min_length:
                    sentences.append(sentence)
                    self.buffer = self.buffer[end_pos:]
                else:
                    break
            else:
                # 没有分隔符
                break
        
        # 2. 如果缓冲区超过最大长度，强制分段（避免延迟）
        if len(self.buffer) >= self.max_length:
            sentence = self.buffer[:self.max_length].strip()
            if sentence:
                sentences.append(sentence)
                self.buffer = self.buffer[self.max_length:]
        
        return sentences
    
    def flush(self) -> Optional[str]:
        """
        刷新缓冲区，返回剩余的文本（在流结束时调用）
        
        Returns:
            剩余的文本，如果为空则返回None
        """
        if self.buffer.strip():
            sentence = self.buffer.strip()
            self.buffer = ""
            return sentence
        return None


async def process_text_request(
    session_id: str,
    request_id: str,
    text: str,
    require_tts: bool,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    处理文本请求：流式 LLM -> 可选流式 TTS（优化版）
    
    优化策略：
    1. 文本立即流式发送给客户端（保持低延迟）
    2. TTS使用句子级缓冲，按完整句子合成（保证语音连贯）
    
    Yield 协议 RESPONSE payload（不含外层 msg 壳）
    """
    logger = get_enhanced_logger()
    text_seq = 0
    voice_seq = 0
    tts_service = None
    sentence_buffer = None
    
    if require_tts:
        try:
            from src.services.tts_service import UnifiedTTSService
            tts_service = UnifiedTTSService()
            # 创建轻量级句子缓冲器（最小5字，最大30字）- 快速处理，短句输出
            sentence_buffer = SentenceBuffer(min_length=5, max_length=30)
            logger.tts.info("TTS sentence buffer initialized", {
                "min_length": 5,
                "max_length": 30,
                "strategy": "short_sentence_fast"
            })
        except Exception as e:
            logger.tts.error("TTS init failed", {"error": str(e)})

    from src.core.command_generator import CommandGenerator
    generator = CommandGenerator()

    async def send_text(content: str, seq: int):
        payload = {
            "request_id": request_id,
            "text_stream_seq": seq,
            "content": {"text": content} if content else {},
        }
        yield payload

    voice_sent = [False]  # 用列表实现 closure 可变

    async def send_voice(base64_audio: str, seq: int):
        voice_sent[0] = True
        payload = {
            "request_id": request_id,
            "voice_stream_seq": seq,
            "content": {"voice": base64_audio} if base64_audio else {},
        }
        yield payload

    async def send_function_call(name: str, parameters: Dict):
        payload = {
            "request_id": request_id,
            "text_stream_seq": text_seq,
            "function_call": {"name": name, "parameters": parameters},
            "content": {},
        }
        yield payload
    
    async def synthesize_and_send(sentence: str):
        """合成并发送完整句子的语音"""
        nonlocal voice_seq
        if not sentence or not tts_service:
            return
        
        try:
            logger.tts.info("Synthesizing sentence", {
                "text": sentence[:50],
                "length": len(sentence)
            })
            
            async for audio_chunk in tts_service.stream_synthesize(sentence):
                b64 = base64.b64encode(audio_chunk).decode("utf-8")
                async for p in send_voice(b64, voice_seq):
                    yield p
                voice_seq += 1
        except Exception as e:
            logger.tts.error("TTS stream failed", {"error": str(e), "text": sentence[:50]})

    try:
        async for chunk in generator.stream_generate(user_input=text, session_id=session_id):
            if isinstance(chunk, dict):
                t = chunk.get("type")
                if t == "text":
                    c = chunk.get("content", "")
                    
                    # 1. 立即发送文本给客户端（保持低延迟）
                    async for p in send_text(c, text_seq):
                        yield p
                    text_seq += 1
                    
                    # 2. 使用句子缓冲器处理TTS（保证连贯性）
                    if c and require_tts and sentence_buffer:
                        # 将文本块添加到缓冲器
                        complete_sentences = sentence_buffer.add_chunk(c)
                        
                        # 对每个完整句子进行TTS合成
                        for sentence in complete_sentences:
                            async for p in synthesize_and_send(sentence):
                                yield p
                
                elif t == "function_call":
                    name = chunk.get("name", "")
                    args = chunk.get("arguments", "{}")
                    if isinstance(args, str):
                        try:
                            args = json.loads(args) if args else {}
                        except json.JSONDecodeError:
                            args = {}
                    async for p in send_function_call(name, args):
                        yield p
                    text_seq += 1
            
            elif isinstance(chunk, str):
                # 1. 立即发送文本给客户端
                async for p in send_text(chunk, text_seq):
                    yield p
                text_seq += 1
                
                # 2. 使用句子缓冲器处理TTS
                if chunk and require_tts and sentence_buffer:
                    complete_sentences = sentence_buffer.add_chunk(chunk)
                    for sentence in complete_sentences:
                        async for p in synthesize_and_send(sentence):
                            yield p
        
        # 3. 流结束时，刷新缓冲器中剩余的文本
        if require_tts and sentence_buffer:
            remaining = sentence_buffer.flush()
            if remaining:
                logger.tts.info("Flushing remaining text", {
                    "text": remaining[:50],
                    "length": len(remaining)
                })
                async for p in synthesize_and_send(remaining):
                    yield p

        # 文本流结束
        async for p in send_text("", -1):
            yield p
        if voice_sent[0]:
            async for p in send_voice("", -1):
                yield p
    except Exception as e:
        logger.sys.error("Text request process failed", {"error": str(e)})
        raise

