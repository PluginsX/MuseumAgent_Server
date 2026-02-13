# -*- coding: utf-8 -*-
"""
语音回复功能测试脚本
测试当客户端请求启用"启用语音播报"时，服务器是否会用语音回复
"""

import asyncio
import websockets
import json
import base64
import time
from datetime import datetime

async def test_voice_reply():
    """测试语音回复功能"""
    # 测试步骤1: 登录获取token
    print("=" * 60)
    print("测试步骤1: 登录获取token")
    print("=" * 60)
    
    import httpx
    
    login_data = {
        "username": "123",
        "password": "123"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/api/auth/login",
            json=login_data
        )
        
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get("data", {}).get("access_token")
            print(f"登录成功，获取到token: {token[:20]}...")
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return
    
    # 测试步骤2: 注册会话
    print("\n" + "=" * 60)
    print("测试步骤2: 注册会话")
    print("=" * 60)
    
    session_data = {
        "client_type": "test_client",
        "functions": [],
        "device_info": {
            "platform": "windows",
            "browser": "test"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/api/session/register",
            json=session_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            session_result = response.json()
            session_id = session_result.get("data", {}).get("session_id")
            print(f"会话注册成功，获取到session_id: {session_id}")
        else:
            print(f"会话注册失败: {response.status_code} - {response.text}")
            return
    
    # 测试步骤3: 测试文本消息 + 语音回复
    print("\n" + "=" * 60)
    print("测试步骤3: 测试文本消息 + 语音回复")
    print("=" * 60)
    
    ws_url = f"ws://localhost:8002/ws/agent/stream?token={token}&session_id={session_id}"
    
    async with websockets.connect(ws_url) as websocket:
        print(f"WebSocket连接成功: {ws_url}")
        
        # 发送文本消息，启用语音回复
        text_message = {
            "type": "text_stream",
            "content": "你好，今天天气怎么样？",
            "enable_tts": True  # 启用语音回复
        }
        
        print("发送文本消息，启用语音回复...")
        await websocket.send(json.dumps(text_message))
        
        # 接收响应
        print("等待服务器响应...")
        while True:
            try:
                response = await websocket.recv()
                message = json.loads(response)
                
                if message.get("type") == "text_stream":
                    chunk = message.get("chunk", "")
                    done = message.get("done", False)
                    print(f"收到文本回复: {chunk}")
                    if done:
                        print("文本回复完成")
                
                elif message.get("type") == "audio_stream":
                    audio_data = message.get("audio_data")
                    done = message.get("done", False)
                    if audio_data:
                        print(f"收到语音回复: 音频数据大小 {len(audio_data)} 字节")
                    if done:
                        print("语音回复完成")
                        break
                
                elif message.get("type") == "error":
                    error_message = message.get("message", "")
                    print(f"收到错误: {error_message}")
                    break
                
                elif message.get("type") == "connection":
                    status = message.get("status", "")
                    print(f"连接状态: {status}")
                    
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket连接已关闭")
                break
            except Exception as e:
                print(f"接收消息时发生错误: {e}")
                break
    
    # 测试步骤4: 测试语音消息 + 语音回复
    print("\n" + "=" * 60)
    print("测试步骤4: 测试语音消息 + 语音回复")
    print("=" * 60)
    
    # 读取音频文件
    try:
        with open("e:/Project/Python/MuseumAgent_Server/tests/audio.mp3", "rb") as f:
            audio_data = f.read()
        print(f"音频文件读取成功，大小: {len(audio_data)} 字节")
    except Exception as e:
        print(f"读取音频文件失败: {e}")
        return
    
    ws_url = f"ws://localhost:8002/ws/agent/stream?token={token}&session_id={session_id}"
    
    async with websockets.connect(ws_url) as websocket:
        print(f"WebSocket连接成功: {ws_url}")
        
        # 发送预录制音频数据，启用语音回复
        stream_id = f"test_stream_{int(time.time())}"
        import base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        audio_message = {
            "type": "audio_data",
            "stream_id": stream_id,
            "enable_tts": True,  # 启用语音回复
            "audio_data": audio_base64
        }
        
        print("发送预录制音频数据...")
        await websocket.send(json.dumps(audio_message))
        
        # 接收响应
        print("等待服务器响应...")
        while True:
            try:
                response = await websocket.recv()
                
                # 区分二进制数据和文本数据
                if isinstance(response, bytes):
                    print(f"收到二进制数据: 大小 {len(response)} 字节")
                else:
                    message = json.loads(response)
                    
                    if message.get("type") == "text_stream":
                        chunk = message.get("chunk", "")
                        done = message.get("done", False)
                        print(f"收到文本回复: {chunk}")
                        if done:
                            print("文本回复完成")
                    
                    elif message.get("type") == "audio_stream":
                        audio_data = message.get("audio_data")
                        done = message.get("done", False)
                        if audio_data:
                            print(f"收到语音回复: 音频数据大小 {len(audio_data)} 字节")
                        if done:
                            print("语音回复完成")
                            break
                    
                    elif message.get("type") == "error":
                        error_message = message.get("message", "")
                        print(f"收到错误: {error_message}")
                        break
                    
                    elif message.get("type") == "connection":
                        status = message.get("status", "")
                        print(f"连接状态: {status}")
                        
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket连接已关闭")
                break
            except Exception as e:
                print(f"接收消息时发生错误: {e}")
                break
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_voice_reply())