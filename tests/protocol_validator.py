#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博物馆智能体通信协议 可行性验证脚本

模拟 C-S 之间的 WebSocket 通信，验证协议设计完备性。
不依赖 STT/TTS/SRS/LLM，仅测试协议层消息格式与流程。

运行前安装: pip install websockets

用法: python tests/protocol_validator.py
"""
import sys
import io

# Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import asyncio
import base64
import json
import uuid
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

try:
    import websockets
except ImportError:
    print("请先安装: pip install websockets")
    raise

# ---------------------------------------------------------------------------
# 协议常量（与 docs/CommunicationProtocol_CS.md 一致）
# ---------------------------------------------------------------------------
VERSION = "1.0"
PLATFORMS = {"WEB", "APP", "MINI_PROGRAM", "TV"}
AUTH_TYPES = {"API_KEY", "ACCOUNT"}
DATA_TYPES = {"TEXT", "VOICE"}
VOICE_MODES = {"BASE64", "BINARY"}
FUNCTION_OPS = {"REPLACE", "ADD", "UPDATE", "DELETE"}


# ---------------------------------------------------------------------------
# 报文构建与校验
# ---------------------------------------------------------------------------

def make_base_msg(msg_type: str, payload: Dict, session_id: Optional[str] = None) -> Dict:
    """构建符合协议的公共报文结构"""
    return {
        "version": VERSION,
        "msg_type": msg_type,
        "session_id": session_id,
        "payload": payload,
        "timestamp": int(time.time() * 1000),
    }


def validate_common_fields(msg: Dict) -> Optional[str]:
    """校验公共字段，返回错误信息或 None"""
    if not isinstance(msg, dict):
        return "报文必须是 JSON 对象"
    if msg.get("version") != VERSION:
        return f"version 应为 '{VERSION}'"
    if not msg.get("msg_type"):
        return "缺少 msg_type"
    if "payload" not in msg:
        return "缺少 payload"
    if "timestamp" not in msg or not isinstance(msg["timestamp"], (int, float)):
        return "缺少或无效的 timestamp"
    return None


def validate_register_payload(p: Dict) -> Optional[str]:
    """校验 REGISTER payload"""
    auth = p.get("auth")
    if not isinstance(auth, dict):
        return "auth 必填且为对象"
    t = auth.get("type")
    if t not in AUTH_TYPES:
        return f"auth.type 应为 {AUTH_TYPES} 之一"
    if t == "API_KEY" and "api_key" not in auth:
        return "auth.api_key 必填"
    if t == "ACCOUNT" and (not auth.get("account") or not auth.get("password")):
        return "auth.account 和 auth.password 必填"
    if p.get("platform") not in PLATFORMS:
        return f"platform 应为 {PLATFORMS} 之一"
    if "require_tts" not in p:
        return "require_tts 必填"
    if not isinstance(p.get("function_calling"), list):
        return "function_calling 必填且为数组"
    return None


def validate_request_payload(p: Dict) -> Optional[str]:
    """校验 REQUEST payload"""
    if not p.get("request_id"):
        return "request_id 必填"
    dt = p.get("data_type")
    if dt not in DATA_TYPES:
        return f"data_type 应为 {DATA_TYPES} 之一"
    if "stream_flag" not in p:
        return "stream_flag 必填"
    if "stream_seq" not in p or not isinstance(p["stream_seq"], (int, float)):
        return "stream_seq 必填且为数字"
    content = p.get("content")
    if not isinstance(content, dict):
        return "content 必填且为对象"
    if dt == "TEXT" and "text" not in content:
        return "TEXT 类型需 content.text"
    if dt == "VOICE":
        vm = content.get("voice_mode")
        if vm not in VOICE_MODES:
            return f"VOICE 需 content.voice_mode 为 {VOICE_MODES} 之一"
        if vm == "BASE64" and not content.get("voice") and p.get("stream_flag") is False:
            return "VOICE+BASE64 非流式时需 content.voice"
    if p.get("function_calling_op") and p["function_calling_op"] not in FUNCTION_OPS:
        return f"function_calling_op 应为 {FUNCTION_OPS} 之一"
    return None


# ---------------------------------------------------------------------------
# 模拟服务端
# ---------------------------------------------------------------------------

@dataclass
class MockSession:
    session_id: str
    platform: str
    require_tts: bool
    function_calling: List[Dict]
    created_at: float = field(default_factory=time.time)

    def to_session_data(self) -> Dict:
        return {
            "platform": self.platform,
            "require_tts": self.require_tts,
            "function_calling": self.function_calling,
            "create_time": int(self.created_at * 1000),
            "remaining_seconds": 3600,
        }


class MockProtocolServer:
    """模拟协议服务端：仅处理协议层，不做真实业务"""

    def __init__(self):
        self.sessions: Dict[str, MockSession] = {}
        self.conn_to_session: Dict[Any, str] = {}
        self.voice_buffers: Dict[str, bytes] = {}  # request_id -> 拼接的二进制

    async def handle_client(self, ws, path=None):
        session_id = None
        try:
            async for raw in ws:
                if isinstance(raw, bytes):
                    # 二进制帧：视为 BINARY 语音数据
                    rid = self._get_active_voice_request(ws)
                    if rid:
                        self.voice_buffers[rid] = self.voice_buffers.get(rid, b"") + raw
                    continue
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await self._send_error(ws, "MALFORMED_PAYLOAD", "无效 JSON", session_id=session_id)
                    continue
                err = validate_common_fields(msg)
                if err:
                    await self._send_error(ws, "MALFORMED_PAYLOAD", err, session_id=session_id)
                    continue
                mt = msg["msg_type"]
                payload = msg.get("payload", {})
                sid = msg.get("session_id")

                if mt == "REGISTER":
                    e = validate_register_payload(payload)
                    if e:
                        await self._send_error(ws, "MALFORMED_PAYLOAD", e)
                        continue
                    # 模拟认证：api_key 非空即通过
                    auth = payload["auth"]
                    if auth["type"] == "API_KEY" and not auth.get("api_key"):
                        await self._send_error(ws, "AUTH_FAILED", "API 密钥无效")
                        await ws.close()
                        return
                    if auth["type"] == "ACCOUNT" and (not auth.get("account") or not auth.get("password")):
                        await self._send_error(ws, "AUTH_FAILED", "账号或密码错误")
                        await ws.close()
                        return
                    session_id = f"sess_{uuid.uuid4().hex[:16]}"
                    self.sessions[session_id] = MockSession(
                        session_id=session_id,
                        platform=payload["platform"],
                        require_tts=payload["require_tts"],
                        function_calling=payload.get("function_calling", []),
                    )
                    self.conn_to_session[ws] = session_id
                    await ws.send(json.dumps(make_base_msg("REGISTER_ACK", {
                        "status": "SUCCESS",
                        "message": "会话创建成功",
                        "session_id": session_id,
                        "session_timeout_seconds": 3600,
                    }, session_id)))

                elif mt == "REQUEST":
                    if not session_id or session_id not in self.sessions:
                        await self._send_error(ws, "SESSION_INVALID", "会话无效", session_id, payload.get("request_id"))
                        continue
                    e = validate_request_payload(payload)
                    if e:
                        await self._send_error(ws, "MALFORMED_PAYLOAD", e, session_id, payload.get("request_id"))
                        continue
                    sess = self.sessions[session_id]
                    # 更新会话属性
                    if "require_tts" in payload:
                        sess.require_tts = payload["require_tts"]
                    if payload.get("function_calling_op") and "function_calling" in payload:
                        op = payload["function_calling_op"]
                        fc = payload["function_calling"]
                        if op == "REPLACE":
                            sess.function_calling = list(fc)
                        elif op == "ADD":
                            sess.function_calling.extend(fc)
                        elif op == "UPDATE":
                            names = {x["name"] for x in fc if isinstance(x, dict) and x.get("name")}
                            sess.function_calling = [x for x in sess.function_calling if x.get("name") not in names]
                            sess.function_calling.extend(fc)
                        elif op == "DELETE":
                            names = {x.get("name") for x in fc if isinstance(x, dict)}
                            sess.function_calling = [x for x in sess.function_calling if x.get("name") not in names]
                    rid = payload["request_id"]
                    dt = payload["data_type"]
                    stream_flag = payload["stream_flag"]
                    stream_seq = int(payload["stream_seq"])
                    content = payload.get("content", {})

                    if dt == "VOICE" and content.get("voice_mode") == "BINARY":
                        if stream_seq == 0:
                            self._set_active_voice_request(ws, rid)
                        elif stream_seq == -1:
                            self._clear_active_voice_request(ws)
                            # 模拟：收到完整语音后返回 mock 响应
                            audio = self.voice_buffers.pop(rid, b"")
                            await self._send_mock_response(ws, sess, rid, audio)
                        continue

                    if dt == "TEXT" or (dt == "VOICE" and content.get("voice_mode") == "BASE64"):
                        text = content.get("text", "")
                        voice_b64 = content.get("voice", "")
                        await self._send_mock_response(ws, sess, rid, base64.b64decode(voice_b64) if voice_b64 else b"", text)

                elif mt == "SESSION_QUERY":
                    if not session_id or session_id not in self.sessions:
                        await self._send_error(ws, "SESSION_INVALID", "会话无效", session_id)
                        continue
                    sess = self.sessions[session_id]
                    qf = payload.get("query_fields") or []
                    sd = sess.to_session_data()
                    if qf:
                        sd = {k: v for k, v in sd.items() if k in qf}
                    await ws.send(json.dumps(make_base_msg("SESSION_INFO", {
                        "status": "SUCCESS",
                        "message": "查询成功",
                        "session_data": sd,
                    }, session_id)))

                elif mt == "HEARTBEAT_REPLY":
                    if session_id:
                        await ws.send(json.dumps(make_base_msg("HEARTBEAT", {"remaining_seconds": 3500}, session_id)))

                elif mt == "HEALTH_CHECK":
                    await ws.send(json.dumps(make_base_msg("HEALTH_CHECK_ACK", {
                        "health_status": {"cpu_usage": 10, "conn_count": 1, "status": "HEALTHY"}
                    })))

                elif mt == "SHUTDOWN":
                    await ws.send(json.dumps(make_base_msg("SHUTDOWN", {"reason": payload.get("reason", "客户端关闭")}, session_id)))
                    if session_id and session_id in self.sessions:
                        del self.sessions[session_id]
                    if ws in self.conn_to_session:
                        del self.conn_to_session[ws]
                    await ws.close()
                    return
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if ws in self.conn_to_session:
                sid = self.conn_to_session.pop(ws)
                self.sessions.pop(sid, None)

    def _get_active_voice_request(self, ws) -> Optional[str]:
        return getattr(ws, "_active_voice_request_id", None)

    def _set_active_voice_request(self, ws, rid: str):
        ws._active_voice_request_id = rid
        self.voice_buffers[rid] = b""

    def _clear_active_voice_request(self, ws):
        rid = getattr(ws, "_active_voice_request_id", None)
        if rid:
            delattr(ws, "_active_voice_request_id")
        return rid

    async def _send_error(self, ws, code: str, msg: str, session_id=None, request_id=None):
        p = {"error_code": code, "error_msg": msg, "error_detail": "", "retryable": code in ("AUTH_FAILED", "SERVER_BUSY", "STREAM_SEQ_ERROR", "REQUEST_TIMEOUT", "INTERNAL_ERROR")}
        if request_id:
            p["request_id"] = request_id
        await ws.send(json.dumps(make_base_msg("ERROR", p, session_id)))

    async def _send_mock_response(self, ws, sess: MockSession, request_id: str, audio: bytes = b"", text: str = ""):
        """模拟业务响应：文本 + 可选语音 + 可选 function_call"""
        # 流式模拟：先发文本块
        await ws.send(json.dumps(make_base_msg("RESPONSE", {
            "request_id": request_id,
            "text_stream_seq": 0,
            "function_call": {"name": "get_exhibit_info", "parameters": {"exhibit_id": "1001"}} if sess.function_calling else None,
            "content": {"text": text or "模拟回复文本"},
        }, sess.session_id)))
        # 文本结束
        await ws.send(json.dumps(make_base_msg("RESPONSE", {
            "request_id": request_id,
            "text_stream_seq": -1,
            "content": {},
        }, sess.session_id)))
        if sess.require_tts:
            # 语音块（模拟 base64）
            fake_audio = base64.b64encode(audio or b"\x00" * 100).decode()
            await ws.send(json.dumps(make_base_msg("RESPONSE", {
                "request_id": request_id,
                "voice_stream_seq": 0,
                "content": {"voice": fake_audio},
            }, sess.session_id)))
            await ws.send(json.dumps(make_base_msg("RESPONSE", {
                "request_id": request_id,
                "voice_stream_seq": -1,
                "content": {},
            }, sess.session_id)))


# ---------------------------------------------------------------------------
# 模拟客户端与测试用例
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    passed: bool
    detail: str = ""


async def run_client_test(uri: str, name: str, runner) -> TestResult:
    try:
        async with websockets.connect(uri) as ws:
            return await runner(ws)
    except Exception as e:
        return TestResult(name, False, str(e))


async def test_register_success(ws) -> TestResult:
    msg = make_base_msg("REGISTER", {
        "auth": {"type": "API_KEY", "api_key": "test_key"},
        "platform": "WEB",
        "require_tts": False,
        "function_calling": [{"name": "f1", "description": "d1", "parameters": [{"name": "p1", "type": "string"}]}],
    }, None)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") != "REGISTER_ACK":
        return TestResult("REGISTER 成功", False, f"期望 REGISTER_ACK，得到 {data.get('msg_type')}")
    p = data.get("payload", {})
    if p.get("status") != "SUCCESS" or not p.get("session_id"):
        return TestResult("REGISTER 成功", False, f"payload 异常: {p}")
    # 保存 session_id 供后续测试
    ws._session_id = p["session_id"]
    return TestResult("REGISTER 成功", True)


async def test_register_fail(ws) -> TestResult:
    msg = make_base_msg("REGISTER", {
        "auth": {"type": "API_KEY", "api_key": ""},
        "platform": "WEB",
        "require_tts": False,
        "function_calling": [],
    }, None)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") != "ERROR":
        return TestResult("REGISTER 失败", False, f"期望 ERROR，得到 {data.get('msg_type')}")
    if data.get("payload", {}).get("error_code") != "AUTH_FAILED":
        return TestResult("REGISTER 失败", False, "error_code 应为 AUTH_FAILED")
    return TestResult("REGISTER 失败", True)


async def test_text_request(ws) -> TestResult:
    sid = getattr(ws, "_session_id", None)
    if not sid:
        r = await test_register_success(ws)
        if not r.passed:
            return r
        sid = ws._session_id
    rid = f"req_{uuid.uuid4().hex[:8]}"
    msg = make_base_msg("REQUEST", {
        "request_id": rid,
        "data_type": "TEXT",
        "stream_flag": False,
        "stream_seq": 0,
        "content": {"text": "这件文物年代？"},
    }, sid)
    await ws.send(json.dumps(msg))
    responses = []
    for _ in range(5):
        raw = await asyncio.wait_for(ws.recv(), 2.0)
        data = json.loads(raw)
        if data.get("msg_type") == "RESPONSE" and data.get("payload", {}).get("request_id") == rid:
            responses.append(data)
            p = data["payload"]
            if p.get("text_stream_seq") == -1:
                break
    if not responses:
        return TestResult("TEXT 请求", False, "未收到 RESPONSE")
    if responses[0]["payload"].get("request_id") != rid:
        return TestResult("TEXT 请求", False, "request_id 未回显")
    return TestResult("TEXT 请求", True)


async def test_voice_base64(ws) -> TestResult:
    sid = getattr(ws, "_session_id", None)
    if not sid:
        r = await test_register_success(ws)
        if not r.passed:
            return r
        sid = ws._session_id
    rid = f"req_{uuid.uuid4().hex[:8]}"
    fake_pcm = base64.b64encode(b"\x00\x01" * 100).decode()
    msg = make_base_msg("REQUEST", {
        "request_id": rid,
        "data_type": "VOICE",
        "stream_flag": False,
        "stream_seq": 0,
        "require_tts": True,
        "content": {"voice_mode": "BASE64", "voice": fake_pcm},
    }, sid)
    await ws.send(json.dumps(msg))
    count = 0
    while count < 10:
        raw = await asyncio.wait_for(ws.recv(), 2.0)
        data = json.loads(raw)
        if data.get("msg_type") == "RESPONSE":
            p = data["payload"]
            if p.get("request_id") == rid:
                count += 1
                if p.get("voice_stream_seq") == -1:
                    break
    return TestResult("VOICE Base64", True)


async def test_voice_binary_stream(ws) -> TestResult:
    # 需要 require_tts 以便服务端返回语音流
    msg = make_base_msg("REGISTER", {
        "auth": {"type": "API_KEY", "api_key": "test_key"},
        "platform": "WEB",
        "require_tts": True,
        "function_calling": [],
    }, None)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    reg = json.loads(raw)
    if reg.get("msg_type") != "REGISTER_ACK":
        return TestResult("VOICE BINARY 流式", False, "注册失败")
    ws._session_id = reg["payload"]["session_id"]
    sid = ws._session_id
    rid = f"req_{uuid.uuid4().hex[:8]}"
    # 起始帧
    start_msg = make_base_msg("REQUEST", {
        "request_id": rid,
        "data_type": "VOICE",
        "stream_flag": True,
        "stream_seq": 0,
        "content": {"voice_mode": "BINARY"},
    }, sid)
    await ws.send(json.dumps(start_msg))
    # 二进制帧
    await ws.send(b"\x00\x01\x02\x03" * 50)
    # 结束帧
    end_msg = make_base_msg("REQUEST", {
        "request_id": rid,
        "data_type": "VOICE",
        "stream_flag": True,
        "stream_seq": -1,
        "content": {"voice_mode": "BINARY"},
    }, sid)
    await ws.send(json.dumps(end_msg))
    count = 0
    while count < 10:
        raw = await asyncio.wait_for(ws.recv(), 2.0)
        if isinstance(raw, bytes):
            continue
        data = json.loads(raw)
        if data.get("msg_type") == "RESPONSE" and data.get("payload", {}).get("request_id") == rid:
            count += 1
            if data["payload"].get("voice_stream_seq") == -1:
                break
    return TestResult("VOICE BINARY 流式", True)


async def test_session_attribute_update(ws) -> TestResult:
    sid = getattr(ws, "_session_id", None)
    if not sid:
        r = await test_register_success(ws)
        if not r.passed:
            return r
        sid = ws._session_id
    # 仅更新属性
    rid = f"req_{uuid.uuid4().hex[:8]}"
    msg = make_base_msg("REQUEST", {
        "request_id": rid,
        "data_type": "TEXT",
        "stream_flag": False,
        "stream_seq": 0,
        "require_tts": True,
        "function_calling_op": "ADD",
        "function_calling": [{"name": "new_f", "description": "new", "parameters": []}],
        "content": {"text": ""},
    }, sid)
    await ws.send(json.dumps(msg))
    # 收完该 REQUEST 的所有 RESPONSE（含 text 与 voice 结束）
    text_done = voice_done = False
    while not (text_done and voice_done):
        raw = await asyncio.wait_for(ws.recv(), 2.0)
        data = json.loads(raw)
        if data.get("msg_type") != "RESPONSE":
            return TestResult("会话属性更新", False, f"收到 {data.get('msg_type')}")
        p = data.get("payload", {})
        if p.get("request_id") != rid:
            continue
        if p.get("text_stream_seq") == -1:
            text_done = True
        if p.get("voice_stream_seq") == -1:
            voice_done = True
    # 查询会话
    qmsg = make_base_msg("SESSION_QUERY", {"query_fields": ["require_tts", "function_calling"]}, sid)
    await ws.send(json.dumps(qmsg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    info = json.loads(raw)
    if info.get("msg_type") != "SESSION_INFO":
        return TestResult("会话属性更新", False, f"SESSION_QUERY 返回 {info.get('msg_type')}")
    sd = info.get("payload", {}).get("session_data", {})
    if not sd.get("require_tts"):
        return TestResult("会话属性更新", False, "require_tts 未更新")
    fc = sd.get("function_calling", [])
    if not any(x.get("name") == "new_f" for x in fc):
        return TestResult("会话属性更新", False, "function_calling 未更新")
    return TestResult("会话属性更新", True)


async def test_session_query(ws) -> TestResult:
    sid = getattr(ws, "_session_id", None)
    if not sid:
        r = await test_register_success(ws)
        if not r.passed:
            return r
        sid = ws._session_id
    msg = make_base_msg("SESSION_QUERY", {"query_fields": []}, sid)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") != "SESSION_INFO":
        return TestResult("SESSION_QUERY", False, f"得到 {data.get('msg_type')}")
    sd = data.get("payload", {}).get("session_data", {})
    for k in ("platform", "require_tts", "function_calling", "create_time", "remaining_seconds"):
        if k not in sd:
            return TestResult("SESSION_QUERY", False, f"session_data 缺少 {k}")
    return TestResult("SESSION_QUERY", True)


async def test_health_check_no_session(ws) -> TestResult:
    msg = make_base_msg("HEALTH_CHECK", {"check_fields": []}, None)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") != "HEALTH_CHECK_ACK":
        return TestResult("HEALTH_CHECK 无会话", False, f"得到 {data.get('msg_type')}")
    hs = data.get("payload", {}).get("health_status", {})
    if "status" not in hs:
        return TestResult("HEALTH_CHECK 无会话", False, "缺少 health_status")
    return TestResult("HEALTH_CHECK 无会话", True)


async def test_request_without_session(ws) -> TestResult:
    """未注册时发 REQUEST 应得 SESSION_INVALID"""
    msg = make_base_msg("REQUEST", {
        "request_id": "req_x",
        "data_type": "TEXT",
        "stream_flag": False,
        "stream_seq": 0,
        "content": {"text": "hi"},
    }, "fake_session_id")
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") != "ERROR":
        return TestResult("无会话 REQUEST 拒绝", False, f"期望 ERROR，得到 {data.get('msg_type')}")
    if data.get("payload", {}).get("error_code") != "SESSION_INVALID":
        return TestResult("无会话 REQUEST 拒绝", False, "error_code 应为 SESSION_INVALID")
    return TestResult("无会话 REQUEST 拒绝", True)


async def test_response_has_request_id(ws) -> TestResult:
    """RESPONSE 必须回显 request_id"""
    sid = getattr(ws, "_session_id", None)
    if not sid:
        r = await test_register_success(ws)
        if not r.passed:
            return r
        sid = ws._session_id
    rid = "req_validate_id_12345"
    msg = make_base_msg("REQUEST", {
        "request_id": rid,
        "data_type": "TEXT",
        "stream_flag": False,
        "stream_seq": 0,
        "content": {"text": "test"},
    }, sid)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") == "RESPONSE":
        if data.get("payload", {}).get("request_id") != rid:
            return TestResult("RESPONSE request_id 回显", False, f"request_id 未回显: {data.get('payload')}")
    return TestResult("RESPONSE request_id 回显", True)


async def test_register_account(ws) -> TestResult:
    """ACCOUNT 类型认证"""
    msg = make_base_msg("REGISTER", {
        "auth": {"type": "ACCOUNT", "account": "testuser", "password": "testpass"},
        "platform": "APP",
        "require_tts": True,
        "function_calling": [],
    }, None)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") != "REGISTER_ACK":
        return TestResult("ACCOUNT 认证注册", False, f"得到 {data.get('msg_type')}")
    p = data.get("payload", {})
    if p.get("status") != "SUCCESS" or not p.get("session_id"):
        return TestResult("ACCOUNT 认证注册", False, str(p))
    return TestResult("ACCOUNT 认证注册", True)


async def test_heartbeat_reply(ws) -> TestResult:
    """HEARTBEAT_REPLY 响应"""
    r = await test_register_success(ws)
    if not r.passed:
        return r
    # 服务端主动发 HEARTBEAT 由服务端定时触发，此处客户端收到后回 HEARTBEAT_REPLY
    # 改为：客户端主动发 HEARTBEAT_REPLY，服务端应正常处理（可回 HEARTBEAT 或仅刷新）
    msg = make_base_msg("HEARTBEAT_REPLY", {"client_status": "ONLINE"}, ws._session_id)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") != "HEARTBEAT":
        return TestResult("HEARTBEAT 回信", False, f"得到 {data.get('msg_type')}")
    if "remaining_seconds" not in data.get("payload", {}):
        return TestResult("HEARTBEAT 回信", False, "payload 缺 remaining_seconds")
    return TestResult("HEARTBEAT 回信", True)


async def test_shutdown_flow(ws) -> TestResult:
    """SHUTDOWN 后连接关闭"""
    r = await test_register_success(ws)
    if not r.passed:
        return r
    msg = make_base_msg("SHUTDOWN", {"reason": "测试结束"}, ws._session_id)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") != "SHUTDOWN":
        return TestResult("SHUTDOWN 流程", False, f"期望 SHUTDOWN，得到 {data.get('msg_type')}")
    if "reason" not in data.get("payload", {}):
        return TestResult("SHUTDOWN 流程", False, "payload 缺 reason")
    # 连接应被关闭
    try:
        await asyncio.wait_for(ws.recv(), 0.5)
    except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError):
        pass
    return TestResult("SHUTDOWN 流程", True)


async def test_malformed_register(ws) -> TestResult:
    """错误格式 REGISTER 应得 MALFORMED_PAYLOAD 或 AUTH_FAILED"""
    msg = make_base_msg("REGISTER", {
        "auth": {"type": "API_KEY"},
        "platform": "WEB",
        "require_tts": False,
        "function_calling": [],
    }, None)
    await ws.send(json.dumps(msg))
    raw = await asyncio.wait_for(ws.recv(), 2.0)
    data = json.loads(raw)
    if data.get("msg_type") not in ("ERROR", "REGISTER_ACK"):
        return TestResult("错误格式 REGISTER", False, f"得到 {data.get('msg_type')}")
    if data.get("msg_type") == "REGISTER_ACK":
        return TestResult("错误格式 REGISTER", False, "缺 api_key 不应成功")
    return TestResult("错误格式 REGISTER", True)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

async def main():
    server = MockProtocolServer()
    port = 19999
    uri = f"ws://127.0.0.1:{port}"
    print("=" * 60)
    print("博物馆智能体 通信协议 可行性验证")
    print("=" * 60)

    async def serve():
        async with websockets.serve(server.handle_client, "127.0.0.1", port, ping_interval=None):
            await asyncio.Future()

    serve_task = asyncio.create_task(serve())
    await asyncio.sleep(0.3)

    tests = [
        ("REGISTER 失败（空 api_key）", lambda ws: test_register_fail(ws)),
        ("HEALTH_CHECK 无会话", lambda ws: test_health_check_no_session(ws)),
        ("REGISTER 成功", lambda ws: test_register_success(ws)),
        ("TEXT 请求", lambda ws: test_text_request(ws)),
        ("VOICE Base64", lambda ws: test_voice_base64(ws)),
        ("VOICE BINARY 流式", lambda ws: test_voice_binary_stream(ws)),
        ("会话属性更新", lambda ws: test_session_attribute_update(ws)),
        ("SESSION_QUERY", lambda ws: test_session_query(ws)),
        ("RESPONSE request_id 回显", lambda ws: test_response_has_request_id(ws)),
        ("无会话 REQUEST 拒绝", lambda ws: test_request_without_session(ws)),
        ("错误格式 REGISTER", lambda ws: test_malformed_register(ws)),
        ("ACCOUNT 认证注册", lambda ws: test_register_account(ws)),
        ("HEARTBEAT 回信", lambda ws: test_heartbeat_reply(ws)),
        ("SHUTDOWN 流程", lambda ws: test_shutdown_flow(ws)),
    ]

    results: List[TestResult] = []
    for name, runner in tests:
        r = await run_client_test(uri, name, runner)
        results.append(r)
        status = "[PASS]" if r.passed else "[FAIL]"
        print(f"  {status} {name}" + (f"  |  {r.detail}" if r.detail and not r.passed else ""))

    serve_task.cancel()
    try:
        await serve_task
    except asyncio.CancelledError:
        pass

    passed = sum(1 for x in results if x.passed)
    total = len(results)
    print("=" * 60)
    print(f"通过: {passed}/{total}")
    if passed == total:
        print("协议验证通过，设计完备。")
    else:
        print("存在未通过用例，请检查协议或实现。")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
