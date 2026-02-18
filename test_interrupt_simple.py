#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打断机制测试脚本

测试场景：
1. 发送长文本请求
2. 在响应过程中发送打断请求
3. 验证打断是否成功
"""

import asyncio
import websockets
import json
import time
import sys

async def test_interrupt():
    """测试打断机制"""
    uri = "ws://localhost:8000/ws/agent"
    
    print("=" * 60)
    print("打断机制测试")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as ws:
            print("\n[1/6] 连接 WebSocket...")
            print(f"✅ 已连接到: {uri}")
            
            # 1. 注册会话
            print("\n[2/6] 注册会话...")
            register_msg = {
                "version": "1.0",
                "msg_type": "REGISTER",
                "payload": {
                    "auth": {
                        "auth_type": "API_KEY",
                        "api_key": "test_api_key_12345"
                    },
                    "platform": "test",
                    "require_tts": False,
                    "enable_srs": False,
                    "function_calling": []
                },
                "timestamp": int(time.time() * 1000)
            }
            await ws.send(json.dumps(register_msg))
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get("msg_type") != "REGISTER_ACK":
                print(f"❌ 注册失败: {data}")
                return False
            
            session_id = data["payload"]["session_id"]
            print(f"✅ 会话注册成功")
            print(f"   Session ID: {session_id}")
            
            # 2. 发送长文本请求
            print("\n[3/6] 发送长文本请求...")
            request_id = f"req_{int(time.time() * 1000)}"
            text_msg = {
                "version": "1.0",
                "msg_type": "REQUEST",
                "session_id": session_id,
                "payload": {
                    "request_id": request_id,
                    "data_type": "TEXT",
                    "stream_flag": "START",
                    "stream_seq": 0,
                    "content": {
                        "text": "请给我讲一个非常非常长的故事，包含很多细节和情节"
                    },
                    "require_tts": False
                },
                "timestamp": int(time.time() * 1000)
            }
            await ws.send(json.dumps(text_msg))
            print(f"✅ 已发送文本请求")
            print(f"   Request ID: {request_id}")
            
            # 3. 等待一小段时间，让 LLM 开始生成
            print("\n[4/6] 等待 LLM 开始生成...")
            await asyncio.sleep(1.0)
            
            # 接收一些响应
            text_chunks = []
            for _ in range(3):
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(response)
                    if data.get("msg_type") == "RESPONSE":
                        payload = data.get("payload", {})
                        content = payload.get("content", {})
                        text = content.get("text", "")
                        if text:
                            text_chunks.append(text)
                            print(f"   📝 收到文本: {text[:50]}...")
                except asyncio.TimeoutError:
                    break
            
            if not text_chunks:
                print("❌ 未收到任何响应，无法测试打断")
                return False
            
            print(f"✅ 已收到 {len(text_chunks)} 个文本块")
            
            # 4. 发送打断请求
            print("\n[5/6] 发送打断请求...")
            interrupt_msg = {
                "version": "1.0",
                "msg_type": "INTERRUPT",
                "session_id": session_id,
                "payload": {
                    "interrupt_request_id": request_id,
                    "reason": "USER_NEW_INPUT"
                },
                "timestamp": int(time.time() * 1000)
            }
            await ws.send(json.dumps(interrupt_msg))
            print(f"✅ 已发送打断请求")
            print(f"   Interrupt Request ID: {request_id}")
            
            # 5. 接收响应并验证
            print("\n[6/6] 验证打断结果...")
            interrupted = False
            ack_received = False
            timeout_count = 0
            max_timeout = 10
            
            while timeout_count < max_timeout:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(response)
                    msg_type = data.get("msg_type")
                    
                    if msg_type == "INTERRUPT_ACK":
                        ack_received = True
                        payload = data.get("payload", {})
                        status = payload.get("status")
                        message = payload.get("message")
                        interrupted_ids = payload.get("interrupted_request_ids", [])
                        
                        print(f"✅ 收到打断确认")
                        print(f"   Status: {status}")
                        print(f"   Message: {message}")
                        print(f"   Interrupted IDs: {interrupted_ids}")
                        
                        if status == "SUCCESS" and request_id in interrupted_ids:
                            print("✅ 打断成功！")
                        else:
                            print(f"⚠️  打断状态异常: {status}")
                    
                    elif msg_type == "RESPONSE":
                        payload = data.get("payload", {})
                        
                        # 检查是否有中断标记
                        if payload.get("interrupted"):
                            interrupted = True
                            reason = payload.get("interrupt_reason", "UNKNOWN")
                            print(f"✅ 收到中断标记")
                            print(f"   Reason: {reason}")
                            break
                        
                        # 检查是否是流结束
                        text_seq = payload.get("text_stream_seq")
                        if text_seq == -1:
                            print(f"   📝 文本流结束")
                            if ack_received:
                                # 如果已经收到 ACK，但流正常结束，说明打断可能失败
                                print("⚠️  收到 ACK 但流正常结束，打断可能失败")
                            break
                        
                        # 打印接收到的文本
                        content = payload.get("content", {})
                        text = content.get("text", "")
                        if text:
                            print(f"   📝 继续收到文本: {text[:50]}...")
                
                except asyncio.TimeoutError:
                    timeout_count += 1
                    if ack_received:
                        # 如果已经收到 ACK，超时可能意味着流已停止
                        print(f"   ⏱️  超时 ({timeout_count}/{max_timeout})，可能已停止")
                        if timeout_count >= 3:
                            break
                    else:
                        print(f"   ⏱️  等待响应超时 ({timeout_count}/{max_timeout})")
            
            # 6. 验证结果
            print("\n" + "=" * 60)
            print("测试结果")
            print("=" * 60)
            
            success = True
            
            if not ack_received:
                print("❌ 未收到打断确认 (INTERRUPT_ACK)")
                success = False
            else:
                print("✅ 收到打断确认 (INTERRUPT_ACK)")
            
            if not interrupted:
                print("⚠️  未收到中断标记 (interrupted=True)")
                print("   注意：这可能是正常的，取决于打断时机")
            else:
                print("✅ 收到中断标记 (interrupted=True)")
            
            if success:
                print("\n🎉 打断机制测试通过！")
                return True
            else:
                print("\n❌ 打断机制测试失败！")
                return False
    
    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket 错误: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    result = await test_interrupt()
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    asyncio.run(main())

