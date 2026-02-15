#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的通信架构和功能
"""

import asyncio
import json
import time
import websockets

async def test_new_communication_features():
    """测试新的通信架构特性"""
    print("=== 测试新的通信架构特性 ===")
    
    # WebSocket服务器地址
    ws_url = "ws://localhost:8001/ws/agent/stream"
    
    try:
        # 连接WebSocket服务器
        async with websockets.connect(ws_url) as ws:
            print(f"已连接到: {ws_url}")
            
            # 1. 发送注册请求（包含认证信息）
            print("\n1. 发送注册请求...")
            register_message = {
                "version": "1.0",
                "msg_type": "REGISTER",
                "payload": {
                    "auth": {
                        "type": "ACCOUNT",
                        "username": "test_user",
                        "password": "test_password"
                    },
                    "client_type": "WEB",
                    "function_calling": [],
                    "require_tts": False
                },
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"注册请求: {json.dumps(register_message, indent=2)}")
            await ws.send(json.dumps(register_message))
            
            # 接收注册响应
            register_response = await ws.recv()
            register_data = json.loads(register_response)
            print(f"注册响应: {json.dumps(register_data, indent=2)}")
            
            if register_data.get("msg_type") != "REGISTER_ACK":
                print(f"注册失败: {register_data.get('payload', {}).get('error_msg')}")
                return
            
            session_id = register_data.get("payload", {}).get("session_id")
            if not session_id:
                print("未获取到会话ID")
                return
            
            print(f"注册成功，会话ID: {session_id}")
            
            # 2. 发送文本请求
            print("\n2. 发送文本请求...")
            text_message = {
                "version": "1.0",
                "msg_type": "REQUEST",
                "session_id": session_id,
                "payload": {
                    "data_type": "TEXT",
                    "stream_flag": True,
                    "stream_seq": 0,
                    "require_tts": False,
                    "content": {
                        "text": "你好，测试新的通信架构和二进制语音处理功能"
                    }
                },
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"文本请求: {json.dumps(text_message, indent=2)}")
            await ws.send(json.dumps(text_message))
            
            # 接收文本响应
            print("\n接收文本响应...")
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    print(f"响应: {json.dumps(response_data, indent=2)}")
                    
                    if response_data.get("msg_type") == "RESPONSE":
                        payload = response_data.get("payload", {})
                        if payload.get("data_type") == "TEXT" and payload.get("stream_seq") == -1:
                            print("文本响应完成")
                            break
                except asyncio.TimeoutError:
                    print("接收响应超时")
                    break
            
            # 3. 测试二进制语音流开始
            print("\n3. 测试二进制语音流开始...")
            voice_stream_start_message = {
                "version": "1.0",
                "msg_type": "VOICE_STREAM_START",
                "session_id": session_id,
                "payload": {
                    "require_tts": False
                },
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"语音流开始请求: {json.dumps(voice_stream_start_message, indent=2)}")
            await ws.send(json.dumps(voice_stream_start_message))
            
            # 接收语音流开始确认
            voice_stream_start_response = await ws.recv()
            voice_stream_start_data = json.loads(voice_stream_start_response)
            print(f"语音流开始响应: {json.dumps(voice_stream_start_data, indent=2)}")
            
            if voice_stream_start_data.get("msg_type") != "VOICE_STREAM_START_ACK":
                print(f"语音流开始失败: {voice_stream_start_data.get('payload', {}).get('error_msg')}")
            else:
                print("语音流开始成功")
            
            # 4. 发送关闭会话请求
            print("\n4. 发送关闭会话请求...")
            shutdown_message = {
                "version": "1.0",
                "msg_type": "SHUTDOWN",
                "session_id": session_id,
                "payload": {
                    "reason": "测试完成"
                },
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"关闭请求: {json.dumps(shutdown_message, indent=2)}")
            await ws.send(json.dumps(shutdown_message))
            
            # 接收关闭响应
            shutdown_response = await ws.recv()
            shutdown_data = json.loads(shutdown_response)
            print(f"关闭响应: {json.dumps(shutdown_data, indent=2)}")
            
            print("\n=== 测试完成 ===")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_new_communication_features())
