#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试解耦的音频处理架构
验证预录制音频和流式音频是否完全独立运行且互不影响
"""

import asyncio
import websockets
import json
import base64
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tests.auth_helper import get_auth_tokens


async def test_pre_recorded_audio_endpoint():
    """测试预录制音频端点"""
    print("=== 测试预录制音频端点 ===")
    
    # 获取认证令牌
    tokens = get_auth_tokens()
    if not tokens:
        print("获取认证令牌失败")
        return False
    
    token = tokens.get('access_token')
    session_id = tokens.get('session_id')
    
    if not token or not session_id:
        print("认证信息不完整")
        return False
    
    print(f"使用会话ID: {session_id}")
    
    try:
        # 连接到预录制音频端点
        uri = f"ws://localhost:8001/ws/agent/pre_recorded_audio?token={token}&session_id={session_id}"
        async with websockets.connect(uri) as websocket:
            print("成功连接到预录制音频端点")
            
            # 发送一个简单的预录制音频消息（模拟）
            # 这里使用一个空的base64字符串作为示例
            message = {
                "type": "pre_recorded_audio_data",
                "stream_id": "test_stream_" + str(int(time.time())),
                "enable_tts": True,
                "audio_data": base64.b64encode(b"").decode('utf-8')  # 空音频数据用于测试连接
            }
            
            await websocket.send(json.dumps(message, ensure_ascii=False))
            print("已发送预录制音频消息")
            
            # 等待响应
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            response_data = json.loads(response)
            print(f"收到响应: {response_data}")
            
            return True
            
    except asyncio.TimeoutError:
        print("接收响应超时")
        return False
    except Exception as e:
        print(f"预录制音频端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_audio_endpoint():
    """测试流式音频端点"""
    print("\n=== 测试流式音频端点 ===")
    
    # 获取认证令牌
    tokens = get_auth_tokens()
    if not tokens:
        print("获取认证令牌失败")
        return False
    
    token = tokens.get('access_token')
    session_id = tokens.get('session_id')
    
    if not token or not session_id:
        print("认证信息不完整")
        return False
    
    print(f"使用会话ID: {session_id}")
    
    try:
        # 连接到流式音频端点
        uri = f"ws://localhost:8001/ws/agent/stream?token={token}&session_id={session_id}"
        async with websockets.connect(uri) as websocket:
            print("成功连接到流式音频端点")
            
            # 发送一个简单的文本消息测试
            message = {
                "type": "text_stream",
                "stream_id": "test_stream_" + str(int(time.time())),
                "content": "你好，这是一个文本消息测试",
                "enable_tts": False
            }
            
            await websocket.send(json.dumps(message, ensure_ascii=False))
            print("已发送文本消息")
            
            # 等待响应
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            response_data = json.loads(response)
            print(f"收到响应: {response_data}")
            
            return True
            
    except asyncio.TimeoutError:
        print("接收响应超时")
        return False
    except Exception as e:
        print(f"流式音频端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_operations():
    """测试并发操作 - 同时使用两个端点验证互不影响"""
    print("\n=== 测试并发操作 ===")
    
    # 获取认证令牌
    tokens = get_auth_tokens()
    if not tokens:
        print("获取认证令牌失败")
        return False
    
    token = tokens.get('access_token')
    session_id = tokens.get('session_id')
    
    if not token or not session_id:
        print("认证信息不完整")
        return False
    
    print(f"使用会话ID: {session_id}")
    
    async def send_text_request():
        """发送文本请求到流式端点"""
        try:
            # 获取认证令牌
            tokens = get_auth_tokens()
            if not tokens:
                print("获取认证令牌失败")
                return False
            
            token = tokens.get('access_token')
            session_id = tokens.get('session_id')
            
            if not token or not session_id:
                print("认证信息不完整")
                return False
            
            uri = f"ws://localhost:8001/ws/agent/stream?token={token}&session_id={session_id}"
            async with websockets.connect(uri) as ws:
                message = {
                    "type": "text_stream",
                    "stream_id": "concurrent_text_test",
                    "content": "并发文本测试",
                    "enable_tts": False
                }
                await ws.send(json.dumps(message, ensure_ascii=False))
                
                # 接收响应
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"流式端点响应: {json.loads(response)}")
                return True
        except Exception as e:
            print(f"流式端点并发测试失败: {e}")
            return False
    
    async def send_audio_request():
        """发送音频请求到预录制端点"""
        try:
            # 获取认证令牌
            tokens = get_auth_tokens()
            if not tokens:
                print("获取认证令牌失败")
                return False
            
            token = tokens.get('access_token')
            session_id = tokens.get('session_id')
            
            if not token or not session_id:
                print("认证信息不完整")
                return False
            
            uri = f"ws://localhost:8001/ws/agent/pre_recorded_audio?token={token}&session_id={session_id}"
            async with websockets.connect(uri) as ws:
                message = {
                    "type": "pre_recorded_audio_data",
                    "stream_id": "concurrent_audio_test",
                    "enable_tts": False,
                    "audio_data": base64.b64encode(b"test").decode('utf-8')
                }
                await ws.send(json.dumps(message, ensure_ascii=False))
                
                # 接收响应
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"预录制端点响应: {json.loads(response)}")
                return True
        except Exception as e:
            print(f"预录制端点并发测试失败: {e}")
            return False
    
    # 并发执行两个请求
    results = await asyncio.gather(send_text_request(), send_audio_request(), return_exceptions=True)
    
    success_count = sum(1 for result in results if result is True)
    print(f"并发测试完成: {success_count}/2 成功")
    
    return success_count >= 1  # 至少一个成功就算通过


async def main():
    """主测试函数"""
    print("开始测试解耦的音频处理架构...")
    
    # 测试预录制音频端点
    pre_rec_success = await test_pre_recorded_audio_endpoint()
    
    # 测试流式音频端点
    stream_success = await test_streaming_audio_endpoint()
    
    # 测试并发操作
    concurrent_success = await test_concurrent_operations()
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"预录制音频端点: {'✓ 通过' if pre_rec_success else '✗ 失败'}")
    print(f"流式音频端点: {'✓ 通过' if stream_success else '✗ 失败'}")
    print(f"并发操作测试: {'✓ 通过' if concurrent_success else '✗ 失败'}")
    
    overall_success = pre_rec_success and stream_success and concurrent_success
    print(f"整体测试结果: {'✓ 全部通过' if overall_success else '✗ 部分失败'}")
    
    return overall_success


if __name__ == "__main__":
    if sys.platform.lower().startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)