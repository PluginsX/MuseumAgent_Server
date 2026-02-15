# -*- coding: utf-8 -*-
"""
REQUEST 业务处理器

职责：根据 REQUEST 调用 CommandGenerator、STT、TTS，产出协议 RESPONSE 流。
与协议层解耦：接收文本/语音，产出 (request_id, text_stream_seq, voice_stream_seq, function_call, content) 流。
"""
import base64
import json
from typing import AsyncGenerator, Dict, Any, Optional

from src.common.enhanced_logger import get_enhanced_logger
from src.session.strict_session_manager import strict_session_manager


async def process_text_request(
    session_id: str,
    request_id: str,
    text: str,
    require_tts: bool,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    处理文本请求：流式 LLM -> 可选流式 TTS
    Yield 协议 RESPONSE payload（不含外层 msg 壳）
    """
    logger = get_enhanced_logger()
    text_seq = 0
    voice_seq = 0
    tts_service = None
    if require_tts:
        try:
            from src.services.tts_service import UnifiedTTSService
            tts_service = UnifiedTTSService()
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

    try:
        async for chunk in generator.stream_generate(user_input=text, session_id=session_id):
            if isinstance(chunk, dict):
                t = chunk.get("type")
                if t == "text":
                    c = chunk.get("content", "")
                    async for p in send_text(c, text_seq):
                        yield p
                    text_seq += 1
                    if c and require_tts and tts_service:
                        try:
                            async for audio_chunk in tts_service.stream_synthesize(c):
                                b64 = base64.b64encode(audio_chunk).decode("utf-8")
                                async for p in send_voice(b64, voice_seq):
                                    yield p
                                voice_seq += 1
                        except Exception as e:
                            logger.tts.error("TTS stream failed", {"error": str(e)})
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
                async for p in send_text(chunk, text_seq):
                    yield p
                text_seq += 1
                if chunk and require_tts and tts_service:
                    try:
                        async for audio_chunk in tts_service.stream_synthesize(chunk):
                            b64 = base64.b64encode(audio_chunk).decode("utf-8")
                            async for p in send_voice(b64, voice_seq):
                                yield p
                            voice_seq += 1
                    except Exception as e:
                        logger.tts.error("TTS stream failed", {"error": str(e)})

        # 文本流结束
        async for p in send_text("", -1):
            yield p
        if voice_sent[0]:
            async for p in send_voice("", -1):
                yield p
    except Exception as e:
        logger.sys.error("Text request process failed", {"error": str(e)})
        raise


async def process_voice_request(
    session_id: str,
    request_id: str,
    audio_bytes: bytes,
    require_tts: bool,
    audio_format_hint: str = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    处理语音请求：STT -> 文本 -> 同 process_text_request
    
    Args:
        session_id: 会话ID
        request_id: 请求ID
        audio_bytes: 音频数据
        require_tts: 是否需要TTS
        audio_format_hint: 音频格式提示（可选）
    """
    logger = get_enhanced_logger()
    from src.services.stt_service import UnifiedSTTService
    stt = UnifiedSTTService()
    try:
        # 🔧 传递音频格式提示给STT服务
        text = await stt.recognize_audio(audio_bytes, audio_format_hint)
    except Exception as e:
        logger.stt.error("STT failed", {"error": str(e)})
        text = ""
    if not (text and text.strip()):
        # 空识别结果
        payload = {
            "request_id": request_id,
            "text_stream_seq": 0,
            "content": {"text": "抱歉，我没有听清楚您说什么。"},
        }
        yield payload
        payload_end = {"request_id": request_id, "text_stream_seq": -1, "content": {}}
        yield payload_end
        if require_tts:
            yield {"request_id": request_id, "voice_stream_seq": -1, "content": {}}
        return
    async for p in process_text_request(session_id, request_id, text.strip(), require_tts):
        yield p
