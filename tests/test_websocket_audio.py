#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket音频功能测试脚本
用于测试语音消息发送和接收功能
"""
import asyncio
import websockets
import json
import base64
import uuid
from src.common.auth_utils import create_access_token
from src.services.session_service import SessionService


async def test_audio_stream():
    """测试音频流功能"""
    print("开始测试WebSocket音频流功能...")
    
    # 创建访问令牌和会话
    session_service = SessionService()
    session_info = await session_service.create_session(user_id=1, username="test_user")
    session_id = session_info['session_id']
    
    token = create_access_token(
        subject="test_user", 
        user_id=1, 
        extra={"session_id": session_id}
    )
    
    print(f"创建会话: {session_id}")
    
    try:
        # 连接到WebSocket服务器
        uri = f"ws://localhost:8002/ws/agent/stream?token={token}&session_id={session_id}"
        async with websockets.connect(uri) as websocket:
            print("WebSocket连接已建立")
            
            # 接收连接确认消息
            connection_msg = await websocket.recv()
            print(f"连接确认: {connection_msg}")
            
            # 发送预录制音频数据
            stream_id = str(uuid.uuid4())
            print(f"发送预录制音频数据: {stream_id}")
            
            # 模拟音频数据
            import base64
            dummy_audio_data = b"dummy_pre_recorded_audio_data_for_testing"
            audio_base64 = base64.b64encode(dummy_audio_data).decode('utf-8')
            
            audio_msg = {
                "type": "audio_data",
                "stream_id": stream_id,
                "enable_tts": True,  # 启用语音播报
                "audio_data": audio_base64
            }
            
            await websocket.send(json.dumps(audio_msg))
            print("发送预录制音频数据消息")
            
            # 等待服务器响应
            print("等待服务器响应...")
            for _ in range(10):  # 最多等待10次响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response) if response.startswith('{') else response
                    print(f"收到响应: {response_data}")
                    
                    # 如果收到完成标记，则退出
                    if isinstance(response_data, dict) and response_data.get('type') == 'text_stream' and response_data.get('done'):
                        print("收到文本流完成标记")
                        break
                    elif isinstance(response_data, dict) and response_data.get('type') == 'audio_stream':
                        print("收到音频流响应 - 语音播报功能正常工作")
                        break
                except asyncio.TimeoutError:
                    print("等待响应超时")
                    break
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理会话
        await session_service.delete_session(session_id)
        print("会话已清理")


async def test_text_stream_with_tts():
    """测试带TTS的文字流功能"""
    print("\n开始测试文字流功能（启用TTS）...")
    
    # 创建访问令牌和会话
    session_service = SessionService()
    session_info = await session_service.create_session(user_id=1, username="test_user")
    session_id = session_info['session_id']
    
    token = create_access_token(
        subject="test_user", 
        user_id=1, 
        extra={"session_id": session_id}
    )
    
    print(f"创建会话: {session_id}")
    
    try:
        # 连接到WebSocket服务器
        uri = f"ws://localhost:8002/ws/agent/stream?token={token}&session_id={session_id}"
        async with websockets.connect(uri) as websocket:
            print("WebSocket连接已建立")
            
            # 接收连接确认消息
            connection_msg = await websocket.recv()
            print(f"连接确认: {connection_msg}")
            
            # 发送带TTS的文字流消息
            stream_id = str(uuid.uuid4())
            text_msg = {
                "type": "text_stream",
                "stream_id": stream_id,
                "content": "你好，这是一条测试消息",
                "enable_tts": True  # 启用语音播报
            }
            
            await websocket.send(json.dumps(text_msg))
            print("发送文字流消息（启用TTS）")
            
            # 等待服务器响应
            print("等待服务器响应...")
            audio_received = False
            for _ in range(10):  # 最多等待10次响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response) if response.startswith('{') else response
                    print(f"收到响应: {response_data}")
                    
                    # 检查是否收到音频流响应
                    if isinstance(response_data, dict) and response_data.get('type') == 'audio_stream':
                        print("收到音频流响应 - TTS功能正常工作")
                        audio_received = True
                        break
                    # 如果收到完成标记，则继续等待音频响应
                    elif isinstance(response_data, dict) and response_data.get('type') == 'text_stream' and response_data.get('done'):
                        print("收到文本流完成标记")
                        continue
                except asyncio.TimeoutError:
                    print("等待响应超时")
                    break
            
            if not audio_received:
                print("警告: 未收到音频流响应，TTS功能可能未正常工作")
    
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理会话
        await session_service.delete_session(session_id)
        print("会话已清理")


if __name__ == "__main__":
    print("开始WebSocket音频功能测试...")
    
    # 运行测试
    asyncio.run(test_audio_stream())
    asyncio.run(test_text_stream_with_tts())
    
    print("\n测试完成!")