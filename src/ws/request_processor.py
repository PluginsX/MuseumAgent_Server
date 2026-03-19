# -*- coding: utf-8 -*-
"""
REQUEST 业务处理器

职责：根据 REQUEST 调用 CommandGenerator、STT、TTS，产出协议 RESPONSE 流。
与协议层解耦：接收文本/语音，产出 (request_id, text_stream_seq, voice_stream_seq, function_call, content) 流。

支持打断机制：通过 asyncio.Event 实现协作式取消。
"""
import asyncio
import base64
import json
import re
from typing import AsyncGenerator, Dict, Any, Optional

from src.common.enhanced_logger import get_enhanced_logger
from src.session.strict_session_manager import strict_session_manager


class SentenceBuffer:
    """
    语义感知分句缓冲器 v2.0 - 用于优化流式TTS
    
    分句策略（优先级从高到低）：
    1. 强边界：。！？\n .!?  → 无论长度，立即分段
    2. 弱边界：，；、,;    → 仅当已积累 >= weak_break_min_length 字时在此分段
    3. 硬截断：超过 max_length 字时强制截断（防止超长句拖延TTS）
    
    原则：
    - 宁可稍等（积累到弱边界），绝不硬切句子中间
    - 弱边界分出来的片段语调完整，TTS 合成自然
    - 强边界后立即触发，保证句末停顿感
    """
    
    def __init__(self,
                 weak_break_min_length: int = 15,
                 max_length: int = 60):
        self.buffer = ""
        self.weak_break_min_length = weak_break_min_length
        self.max_length = max_length
        self.strong_endings = re.compile(r'[。！？\n.!?]+')
        self.weak_breaks = re.compile(r'[，；、,;]')
    
    def add_chunk(self, chunk: str) -> list:
        if not chunk:
            return []
        self.buffer += chunk
        sentences = []
        while self.buffer:
            strong_match = self.strong_endings.search(self.buffer)
            if strong_match:
                end_pos = strong_match.end()
                sentence = self.buffer[:end_pos].strip()
                if sentence:
                    sentences.append(sentence)
                self.buffer = self.buffer[end_pos:]
                continue
            if len(self.buffer) >= self.weak_break_min_length:
                weak_match = self.weak_breaks.search(self.buffer)
                if weak_match:
                    end_pos = weak_match.end()
                    sentence = self.buffer[:end_pos].strip()
                    if sentence:
                        sentences.append(sentence)
                    self.buffer = self.buffer[end_pos:]
                    continue
            if len(self.buffer) >= self.max_length:
                cut_pos = self.buffer[:self.max_length].rfind(' ')
                if cut_pos < self.max_length // 2:
                    cut_pos = self.max_length
                sentence = self.buffer[:cut_pos].strip()
                if sentence:
                    sentences.append(sentence)
                self.buffer = self.buffer[cut_pos:]
                continue
            break
        return sentences
    
    def flush(self) -> str | None:
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
    async for payload in process_text_request_with_cancel(session_id, request_id, text, require_tts, None):
        yield payload


async def process_text_request_with_cancel(
    session_id: str,
    request_id: str,
    text: str,
    require_tts: bool,
    cancel_event: Optional[asyncio.Event] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    处理文本请求：真正的流式架构

    架构说明：
    - LLM chunk 收到后立即 yield text payload 给客户端（零缓存，真正流式）
    - tts_worker 作为独立 Task 与 LLM 并行运行，消费 tts_queue 合成语音
    - LLM 完成后主协程等待 voice_queue 的 None 结束标记，消费所有语音块
    - 文本流结束帧在所有文本 yield 后发送
    - 语音流结束帧在所有语音 yield 后发送
    """
    logger = get_enhanced_logger()

    text_seq  = [0]
    voice_seq = [0]
    voice_sent = [False]

    def make_text_payload(content: str, seq: int) -> dict:
        return {
            "request_id": request_id,
            "text_stream_seq": seq,
            "content": {"text": content} if content else {},
        }

    def make_voice_payload(b64_audio: str, seq: int) -> dict:
        voice_sent[0] = True
        return {
            "request_id": request_id,
            "voice_stream_seq": seq,
            "content": {"voice": b64_audio} if b64_audio else {},
        }

    def make_function_payload(name: str, parameters: Dict) -> dict:
        return {
            "request_id": request_id,
            "text_stream_seq": text_seq[0],
            "function_call": {"name": name, "parameters": parameters},
            "content": {},
        }

    def make_interrupted_payload() -> dict:
        return {
            "request_id": request_id,
            "text_stream_seq": -1,
            "voice_stream_seq": -1 if require_tts else None,
            "interrupted": True,
            "interrupt_reason": "USER_NEW_INPUT",
            "content": {}
        }

    # ── TTS 初始化 ────────────────────────────────────────────────
    tts_service     = None
    sentence_buffer = None
    tts_queue   = asyncio.Queue()  # str 句子 | None
    voice_queue = asyncio.Queue()  # (b64_str, seq) | None

    if require_tts:
        try:
            from src.services.tts_service import UnifiedTTSService
            tts_service     = UnifiedTTSService()
            sentence_buffer = SentenceBuffer(weak_break_min_length=15, max_length=60)
            logger.tts.info("TTS pipeline initialized", {
                "weak_break_min_length": 15,
                "max_length": 60,
                "strategy": "parallel_pipeline"
            })
        except Exception as e:
            logger.tts.error("TTS init failed, voice disabled", {"error": str(e)})
            require_tts = False

    # ── TTS Worker ────────────────────────────────────────────────
    async def tts_worker():
        """从 tts_queue 取句子，合成后把音频块 put 进 voice_queue。"""
        try:
            while True:
                sentence = await tts_queue.get()
                if sentence is None:
                    break
                if cancel_event and cancel_event.is_set():
                    break
                try:
                    logger.tts.info("TTS synthesizing", {"text": sentence[:50], "len": len(sentence)})
                    chunk_count = 0
                    async for audio_chunk in tts_service.stream_synthesize(
                        sentence, session_id=session_id, cancel_event=cancel_event
                    ):
                        if cancel_event and cancel_event.is_set():
                            return
                        b64 = base64.b64encode(audio_chunk).decode("utf-8")
                        await voice_queue.put((b64, voice_seq[0]))
                        chunk_count += 1
                        voice_seq[0] += 1
                    logger.tts.info("TTS sentence done, put to voice_queue", {"text": sentence[:20], "chunks": chunk_count})
                except Exception as e:
                    logger.tts.error("TTS synthesis error", {"error": str(e), "text": sentence[:50]})
        finally:
            logger.tts.info("tts_worker finishing, putting None to voice_queue")
            # 无论正常结束还是异常，都发送结束标记
            await voice_queue.put(None)

    # ── 提前启动 TTS worker ───────────────────────────────────────
    worker_task = None
    if require_tts and tts_service:
        worker_task = asyncio.create_task(tts_worker())

    # ── LLM 流式消费：chunk 到即 yield，同时投句子入 tts_queue ────
    from src.core.command_generator import CommandGenerator
    generator = CommandGenerator()

    llm_cancelled = False
    try:
        async for chunk in generator.stream_generate(
            user_input=text,
            session_id=session_id,
            cancel_event=cancel_event
        ):
            if cancel_event and cancel_event.is_set():
                llm_cancelled = True
                break

            if isinstance(chunk, dict):
                t = chunk.get("type")
                if t == "text":
                    c = chunk.get("content", "")
                    if c:
                        # 立即 yield 给客户端（真正流式，零缓存）
                        yield make_text_payload(c, text_seq[0])
                        text_seq[0] += 1
                        # 同时投入 TTS 分句缓冲
                        if require_tts and sentence_buffer:
                            for sent in sentence_buffer.add_chunk(c):
                                await tts_queue.put(sent)
                        # 非阻塞 drain：把已合成好的语音帧交错 yield 出去
                        if require_tts:
                            while True:
                                try:
                                    item = voice_queue.get_nowait()
                                    if item is None:
                                        # 收到结束标记，先放回去，等后面 drain 处理
                                        await voice_queue.put(None)
                                        break
                                    b64, seq = item
                                    logger.tts.info("Yielding voice chunk (interleaved)", {"seq": seq})
                                    yield make_voice_payload(b64, seq)
                                except asyncio.QueueEmpty:
                                    break

                elif t == "function_call":
                    name = chunk.get("name", "")
                    args = chunk.get("arguments", "{}")
                    if isinstance(args, str):
                        try:
                            args = json.loads(args) if args else {}
                        except json.JSONDecodeError:
                            args = {}
                    yield make_function_payload(name, args)

            elif isinstance(chunk, str) and chunk:
                yield make_text_payload(chunk, text_seq[0])
                text_seq[0] += 1
                if require_tts and sentence_buffer:
                    for sent in sentence_buffer.add_chunk(chunk):
                        await tts_queue.put(sent)
                # 非阻塞 drain（纯字符串 chunk 分支）
                if require_tts:
                    while True:
                        try:
                            item = voice_queue.get_nowait()
                            if item is None:
                                await voice_queue.put(None)
                                break
                            b64, seq = item
                            yield make_voice_payload(b64, seq)
                        except asyncio.QueueEmpty:
                            break

    except Exception as e:
        logger.sys.error("LLM stream error", {"error": str(e)})
        raise
    finally:
        # 刷新 sentence_buffer 剩余内容，发送 tts_queue 结束标记
        if require_tts and sentence_buffer:
            remaining = sentence_buffer.flush()
            if remaining:
                await tts_queue.put(remaining)
        if require_tts:
            await tts_queue.put(None)

    # ── 处理取消 ──────────────────────────────────────────────────
    if llm_cancelled or (cancel_event and cancel_event.is_set()):
        logger.ws.info("Request cancelled", {"request_id": request_id[:16]})
        if worker_task and not worker_task.done():
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        yield make_interrupted_payload()
        return

    # ── 文本流结束帧 ──────────────────────────────────────────────
    yield make_text_payload("", -1)

    # ── 消费 voice_queue，yield 所有语音块 ────────────────────────
    # 必须等到 None 结束标记才能退出，不能用 worker_task.done() 提前判断
    if require_tts and tts_service and worker_task:
        logger.tts.info("Entering voice_queue drain loop", {"worker_done": worker_task.done()})
        try:
            voice_chunk_count = 0
            while True:
                if cancel_event and cancel_event.is_set():
                    if not worker_task.done():
                        worker_task.cancel()
                    break

                try:
                    item = await asyncio.wait_for(voice_queue.get(), timeout=60.0)
                except asyncio.TimeoutError:
                    logger.tts.error("Voice queue timeout (60s), aborting", {"chunks_sent": voice_chunk_count})
                    break

                if item is None:  # tts_worker finally 发来的结束标记
                    logger.tts.info("Voice queue drain complete", {"chunks_sent": voice_chunk_count})
                    break

                b64, seq = item
                voice_chunk_count += 1
                logger.tts.info("Yielding voice chunk", {"seq": seq, "b64_len": len(b64)})
                yield make_voice_payload(b64, seq)

        except Exception as e:
            logger.tts.error("Voice queue error", {"error": str(e)})
        finally:
            if not worker_task.done():
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass

        # 语音流结束帧
        if voice_sent[0]:
            logger.tts.info("Sending voice end frame")
            yield make_voice_payload("", -1)
