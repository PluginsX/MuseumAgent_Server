# -*- coding: utf-8 -*-
"""
测试WebSocket连接并验证访问日志记录
"""
import asyncio
import json
import websockets

async def test_websocket():
    """测试WebSocket连接"""
    print("测试WebSocket连接...")
    
    try:
        # 连接到WebSocket服务器
        async with websockets.connect("ws://localhost:12301/ws/agent/stream") as websocket:
            print("已连接到WebSocket服务器")
            
            import time
            # 发送REGISTER消息
            register_msg = {
                "version": "1.0",
                "msg_type": "REGISTER",
                "timestamp": int(time.time() * 1000),
                "payload": {
                    "platform": "WEB",
                    "require_tts": False,
                    "enable_srs": False,
                    "function_calling": [],
                    "auth": {
                        "type": "API_KEY",
                        "api_key": "museum_test_api_key"
                    }
                }
            }
            
            print("发送REGISTER消息...")
            await websocket.send(json.dumps(register_msg))
            
            # 接收响应
            response = await websocket.recv()
            print(f"收到响应: {response}")
            
            # 解析响应
            response_data = json.loads(response)
            session_id = response_data.get("payload", {}).get("session_id")
            
            if session_id:
                print(f"获取到会话ID: {session_id}")
                
                # 发送一条TEXT请求
                text_msg = {
                    "version": "1.0",
                    "msg_type": "REQUEST",
                    "timestamp": int(time.time() * 1000),
                    "payload": {
                        "request_id": "test_123",
                        "data_type": "TEXT",
                        "stream_flag": False,
                        "stream_seq": 0,
                        "content": {
                            "text": "测试消息"
                        }
                    }
                }
                
                print("发送TEXT请求...")
                await websocket.send(json.dumps(text_msg))
                
                # 接收响应
                response = await websocket.recv()
                print(f"收到TEXT响应: {response}")
                
                # 发送SHUTDOWN消息
                shutdown_msg = {
                    "version": "1.0",
                    "msg_type": "SHUTDOWN",
                    "timestamp": int(time.time() * 1000),
                    "payload": {
                        "reason": "测试结束"
                    }
                }
                
                print("发送SHUTDOWN消息...")
                await websocket.send(json.dumps(shutdown_msg))
                
                # 接收响应
                response = await websocket.recv()
                print(f"收到SHUTDOWN响应: {response}")
            else:
                print("未获取到会话ID")
                
    except Exception as e:
        print(f"WebSocket测试出错: {e}")

async def main():
    """主函数"""
    await test_websocket()

if __name__ == "__main__":
    asyncio.run(main())
