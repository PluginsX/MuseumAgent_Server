#!/usr/bin/env python3
"""
打断机制测试脚本

测试场景：
1. 短语音输入后立即打断（STT阶段）
2. 长语音输入中途打断（STT阶段）
3. LLM生成开始后立即打断
4. LLM生成中途打断
5. TTS播放阶段打断
"""

import asyncio
import websockets
import json
import time
import os
from pathlib import Path

# 配置
WS_URL = "ws://localhost:8001/ws/agent/stream"
AUDIO_DIR = Path(__file__).parent / "tests"
SHORT_AUDIO = AUDIO_DIR / "hello.mp3"
LONG_AUDIO = AUDIO_DIR / "hello_1.mp3"

class InterruptTestClient:
    def __init__(self):
        self.ws = None
        self.session_id = None
        self.current_request_id = None
        self.message_handlers = {}
        self.test_results = []
        
    async def connect(self):
        """连接到 WebSocket 服务器"""
        self.ws = await websockets.connect(WS_URL)
        print(f"[OK] 已连接到服务器: {WS_URL}")
        
        # 启动消息接收任务
        asyncio.create_task(self._receive_messages())
        await asyncio.sleep(0.5)
        
    async def _receive_messages(self):
        """接收并处理服务器消息"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("msg_type")
                
                print(f"[MSG] 收到消息: {msg_type}")
                
                # 如果是错误消息，打印详情
                if msg_type == "ERROR":
                    payload = data.get("payload", {})
                    print(f"[ERROR_DETAIL] 错误代码: {payload.get('error_code')}")
                    print(f"[ERROR_DETAIL] 错误消息: {payload.get('error_msg')}")
                
                # 调用对应的处理器
                if msg_type in self.message_handlers:
                    handler = self.message_handlers[msg_type]
                    await handler(data)
                    
                # 特殊处理
                if msg_type == "SESSION_CREATED":
                    self.session_id = data.get("session_id")
                    print(f"[OK] 会话已创建: {self.session_id}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("[ERROR] WebSocket 连接已关闭")
        except Exception as e:
            print(f"[ERROR] 接收消息错误: {e}")
            
    async def send_message(self, msg_type, payload):
        """发送消息到服务器"""
        message = {
            "version": "1.0",
            "msg_type": msg_type,
            "session_id": self.session_id,
            "payload": payload,
            "timestamp": int(time.time() * 1000)
        }
        await self.ws.send(json.dumps(message))
        
    async def create_session(self):
        """创建会话"""
        await self.send_message("SESSION_CREATE", {
            "require_tts": True,
            "enable_srs": False
        })
        await asyncio.sleep(1)
        
    async def send_voice_stream(self, audio_file, request_id):
        """发送语音流"""
        self.current_request_id = request_id
        
        # 读取音频文件
        with open(audio_file, "rb") as f:
            audio_data = f.read()
            
        # 分块发送
        chunk_size = 4096
        seq = 0
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            is_last = (i + chunk_size >= len(audio_data))
            
            await self.send_message("VOICE_REQUEST", {
                "request_id": request_id,
                "data_type": "AUDIO",
                "stream_flag": "END" if is_last else "CONTINUE",
                "stream_seq": seq,
                "content": {
                    "audio_format": "mp3",
                    "audio_data": chunk.hex()
                },
                "require_tts": True
            })
            
            seq += 1
            await asyncio.sleep(0.01)  # 模拟真实流式传输
            
        print(f"[OK] 语音流发送完成: {audio_file.name}, 共 {seq} 个分片")
        
    async def send_interrupt(self, request_id, reason="USER_NEW_INPUT"):
        """发送打断请求"""
        print(f"[INTERRUPT] 发送打断请求: {request_id}, 原因: {reason}")
        
        interrupt_time = time.time()
        
        # 设置一次性处理器
        ack_received = asyncio.Event()
        ack_data = {}
        
        async def handler(data):
            ack_data.update(data)
            ack_received.set()
            
        self.message_handlers["INTERRUPT_ACK"] = handler
        
        # 发送打断请求
        await self.send_message("INTERRUPT", {
            "interrupt_request_id": request_id,
            "reason": reason
        })
        
        # 等待确认（超时5秒）
        try:
            await asyncio.wait_for(ack_received.wait(), timeout=5.0)
            response_time = (time.time() - interrupt_time) * 1000
            
            payload = ack_data.get("payload", {})
            status = payload.get("status")
            interrupted_ids = payload.get("interrupted_request_ids", [])
            
            print(f"[OK] 收到打断确认: 状态={status}, 响应时间={response_time:.2f}ms")
            print(f"   已中断请求: {interrupted_ids}")
            
            return {
                "success": True,
                "response_time": response_time,
                "status": status,
                "interrupted_ids": interrupted_ids
            }
            
        except asyncio.TimeoutError:
            print(f"[ERROR] 打断请求超时（5秒无响应）")
            return {
                "success": False,
                "error": "timeout"
            }
        finally:
            # 清除处理器
            self.message_handlers.pop("INTERRUPT_ACK", None)
            
    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()
            print("[OK] 连接已关闭")
            
    # ========== 测试场景 ==========
    
    async def test_interrupt_during_stt_short(self):
        """测试场景1: 短语音输入后立即打断（STT阶段）"""
        print("\n" + "="*60)
        print("测试场景1: 短语音输入后立即打断（STT阶段）")
        print("="*60)
        
        request_id = f"req_{int(time.time() * 1000)}"
        
        # 发送短语音
        asyncio.create_task(self.send_voice_stream(SHORT_AUDIO, request_id))
        
        # 等待0.5秒后打断
        await asyncio.sleep(0.5)
        result = await self.send_interrupt(request_id, "TEST_STT_SHORT")
        
        self.test_results.append({
            "test": "interrupt_during_stt_short",
            "result": result
        })
        
        await asyncio.sleep(2)
        
    async def test_interrupt_during_stt_long(self):
        """测试场景2: 长语音输入中途打断（STT阶段）"""
        print("\n" + "="*60)
        print("测试场景2: 长语音输入中途打断（STT阶段）")
        print("="*60)
        
        request_id = f"req_{int(time.time() * 1000)}"
        
        # 发送长语音
        asyncio.create_task(self.send_voice_stream(LONG_AUDIO, request_id))
        
        # 等待1秒后打断
        await asyncio.sleep(1.0)
        result = await self.send_interrupt(request_id, "TEST_STT_LONG")
        
        self.test_results.append({
            "test": "interrupt_during_stt_long",
            "result": result
        })
        
        await asyncio.sleep(2)
        
    async def test_interrupt_during_llm_early(self):
        """测试场景3: LLM生成开始后立即打断"""
        print("\n" + "="*60)
        print("测试场景3: LLM生成开始后立即打断")
        print("="*60)
        
        request_id = f"req_{int(time.time() * 1000)}"
        
        # 发送短语音
        asyncio.create_task(self.send_voice_stream(SHORT_AUDIO, request_id))
        
        # 等待2秒（让STT完成，LLM开始生成）
        await asyncio.sleep(2.0)
        result = await self.send_interrupt(request_id, "TEST_LLM_EARLY")
        
        self.test_results.append({
            "test": "interrupt_during_llm_early",
            "result": result
        })
        
        await asyncio.sleep(2)
        
    async def test_interrupt_during_llm_mid(self):
        """测试场景4: LLM生成中途打断"""
        print("\n" + "="*60)
        print("测试场景4: LLM生成中途打断")
        print("="*60)
        
        request_id = f"req_{int(time.time() * 1000)}"
        
        # 发送长语音（触发更长的LLM响应）
        asyncio.create_task(self.send_voice_stream(LONG_AUDIO, request_id))
        
        # 等待3秒（让LLM生成一段时间）
        await asyncio.sleep(3.0)
        result = await self.send_interrupt(request_id, "TEST_LLM_MID")
        
        self.test_results.append({
            "test": "interrupt_during_llm_mid",
            "result": result
        })
        
        await asyncio.sleep(2)
        
    async def test_interrupt_during_tts(self):
        """测试场景5: TTS播放阶段打断"""
        print("\n" + "="*60)
        print("测试场景5: TTS播放阶段打断")
        print("="*60)
        
        request_id = f"req_{int(time.time() * 1000)}"
        
        # 发送短语音
        asyncio.create_task(self.send_voice_stream(SHORT_AUDIO, request_id))
        
        # 等待4秒（让TTS开始播放）
        await asyncio.sleep(4.0)
        result = await self.send_interrupt(request_id, "TEST_TTS")
        
        self.test_results.append({
            "test": "interrupt_during_tts",
            "result": result
        })
        
        await asyncio.sleep(2)
        
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        
        total = len(self.test_results)
        success = sum(1 for r in self.test_results if r["result"].get("success"))
        
        print(f"\n总测试数: {total}")
        print(f"成功: {success}")
        print(f"失败: {total - success}")
        print(f"成功率: {success/total*100:.1f}%\n")
        
        for test_result in self.test_results:
            test_name = test_result["test"]
            result = test_result["result"]
            
            if result.get("success"):
                response_time = result.get("response_time", 0)
                status = result.get("status", "UNKNOWN")
                print(f"[PASS] {test_name}")
                print(f"   响应时间: {response_time:.2f}ms")
                print(f"   状态: {status}")
            else:
                error = result.get("error", "unknown")
                print(f"[FAIL] {test_name}")
                print(f"   错误: {error}")
            print()


async def main():
    """主测试流程"""
    client = InterruptTestClient()
    
    try:
        # 连接并创建会话
        await client.connect()
        await client.create_session()
        
        # 运行所有测试场景
        await client.test_interrupt_during_stt_short()
        await client.test_interrupt_during_stt_long()
        await client.test_interrupt_during_llm_early()
        await client.test_interrupt_during_llm_mid()
        await client.test_interrupt_during_tts()
        
        # 打印总结
        client.print_summary()
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await client.close()


if __name__ == "__main__":
    print("[START] 开始打断机制测试")
    print(f"[DIR] 音频目录: {AUDIO_DIR}")
    print(f"[AUDIO] 短语音: {SHORT_AUDIO}")
    print(f"[AUDIO] 长语音: {LONG_AUDIO}")
    
    # 检查音频文件
    if not SHORT_AUDIO.exists():
        print(f"[ERROR] 短语音文件不存在: {SHORT_AUDIO}")
        exit(1)
    if not LONG_AUDIO.exists():
        print(f"[ERROR] 长语音文件不存在: {LONG_AUDIO}")
        exit(1)
        
    asyncio.run(main())

