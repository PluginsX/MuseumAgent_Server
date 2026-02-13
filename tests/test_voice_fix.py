#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务器语音消息处理功能
"""
import asyncio
import websockets
import json
import base64
import uuid

async def test_voice_message():
    """
    测试语音消息处理流程
    """
    uri = "ws://localhost:8002/ws/agent/stream?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwibmFtZSI6IlRlc3QiLCJpYXQiOjE1MTYyMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c&session_id=sess_test123"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 成功连接到服务器")
            
            # 发送预录制音频数据消息
            stream_id = str(uuid.uuid4())
            import base64
            # 使用模拟音频数据进行测试
            dummy_audio_data = b'dummy_audio_data_for_test'
            audio_base64 = base64.b64encode(dummy_audio_data).decode('utf-8')
            
            audio_msg = {
                "type": "audio_data",
                "stream_id": stream_id,
                "enable_tts": True,
                "audio_data": audio_base64
            }
            
            await websocket.send(json.dumps(audio_msg))
            print(f"✅ 发送预录制音频数据消息: {stream_id}")
            
            # 监听响应
            print("\n⏳ 等待服务器响应...")
            response_count = 0
            max_responses = 5  # 最多接收5个响应
            
            while response_count < max_responses:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response) if isinstance(response, str) else response
                    print(f"📥 接收到响应 #{response_count + 1}: {response_data}")
                    
                    response_count += 1
                    
                    # 如果收到错误消息，提前退出
                    if response_data.get('type') == 'error':
                        print(f"❌ 服务器返回错误: {response_data.get('message')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ 等待响应超时")
                    break
            
            print(f"\n✅ 测试完成，共收到 {response_count} 条响应")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🧪 开始测试语音消息处理功能...")
    asyncio.run(test_voice_message())