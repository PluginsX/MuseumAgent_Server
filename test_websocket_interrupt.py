# -*- coding: utf-8 -*-
"""
测试打断机制 - WebSocket 客户端
"""
import asyncio
import websockets
import json
import time

async def test_interrupt():
    uri = "ws://localhost:8001/ws/agent/stream"
    
    async with websockets.connect(uri) as websocket:
        print("[OK] WebSocket connected")
        
        # 1. 注册会话
        register_msg = {
            "version": "1.0",
            "msg_type": "REGISTER",
            "session_id": None,
            "payload": {
                "auth": {
                    "type": "API_KEY",
                    "api_key": "test_api_key_001"
                },
                "platform": "TEST",
                "require_tts": False,
                "enable_srs": False,
                "function_calling": []
            },
            "timestamp": int(time.time() * 1000)
        }
        
        await websocket.send(json.dumps(register_msg))
        response = await websocket.recv()
        data = json.loads(response)
        
        if data["msg_type"] != "REGISTER_ACK":
            print(f"❌ 注册失败: {data}")
            return
        
        session_id = data["payload"]["session_id"]
        print(f"✅ 会话注册成功: {session_id}")
        
        # 2. 发送第一个请求（长问题）
        request_id_1 = f"req_test_{int(time.time() * 1000)}_1"
        request_msg_1 = {
            "version": "1.0",
            "msg_type": "REQUEST",
            "session_id": session_id,
            "payload": {
                "request_id": request_id_1,
                "data_type": "TEXT",
                "stream_flag": False,
                "stream_seq": 0,
                "require_tts": False,
                "content": {
                    "text": "请详细讲解凡人修仙传这部小说的完整故事情节，包括主角韩立的成长历程、重要的转折点、主要角色关系、修仙体系设定等等"
                }
            },
            "timestamp": int(time.time() * 1000)
        }
        
        await websocket.send(json.dumps(request_msg_1))
        print(f"✅ 发送第一个请求: {request_id_1}")
        
        # 3. 等待一小段时间，让第一个请求开始处理
        await asyncio.sleep(0.5)
        
        # 4. 立即发送第二个请求（应该触发自动打断）
        request_id_2 = f"req_test_{int(time.time() * 1000)}_2"
        request_msg_2 = {
            "version": "1.0",
            "msg_type": "REQUEST",
            "session_id": session_id,
            "payload": {
                "request_id": request_id_2,
                "data_type": "TEXT",
                "stream_flag": False,
                "stream_seq": 0,
                "require_tts": False,
                "content": {
                    "text": "1"
                }
            },
            "timestamp": int(time.time() * 1000)
        }
        
        await websocket.send(json.dumps(request_msg_2))
        print(f"✅ 发送第二个请求: {request_id_2}")
        print("⏳ 等待响应...")
        
        # 5. 接收响应
        interrupted_received = False
        response_count = 0
        
        try:
            while response_count < 50:  # 最多接收50条消息
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                response_count += 1
                
                if data["msg_type"] == "RESPONSE":
                    payload = data["payload"]
                    request_id = payload.get("request_id")
                    interrupted = payload.get("interrupted", False)
                    text = payload.get("content", {}).get("text", "")
                    
                    if interrupted:
                        print(f"🎯 收到打断通知! request_id={request_id}, reason={payload.get('interrupt_reason')}")
                        interrupted_received = True
                    
                    if text:
                        print(f"📝 [{request_id}] {text[:50]}...")
                    
                    # 检查是否结束
                    if payload.get("text_stream_seq") == -1:
                        print(f"✅ 请求完成: {request_id}")
                        if request_id == request_id_2:
                            break
                
                elif data["msg_type"] == "HEARTBEAT":
                    # 回复心跳
                    heartbeat_reply = {
                        "version": "1.0",
                        "msg_type": "HEARTBEAT_REPLY",
                        "session_id": session_id,
                        "payload": {"client_status": "ONLINE"},
                        "timestamp": int(time.time() * 1000)
                    }
                    await websocket.send(json.dumps(heartbeat_reply))
                
        except asyncio.TimeoutError:
            print("⏱️ 接收超时")
        
        # 6. 结果
        print("\n" + "="*60)
        if interrupted_received:
            print("✅ 测试通过：收到了打断通知")
        else:
            print("❌ 测试失败：没有收到打断通知")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_interrupt())

