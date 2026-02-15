#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket会话管理系统测试脚本
测试WebSocket连接、会话注册、会话查询等功能
"""

import asyncio
import json
import websockets
import time
import uuid

class WebSocketSessionTest:
    def __init__(self, ws_url="ws://localhost:8001/ws/agent/stream"):
        self.ws_url = ws_url
        self.ws = None
        self.session_id = None
    
    async def connect(self):
        """建立WebSocket连接"""
        print(f"[测试] 连接到WebSocket服务: {self.ws_url}")
        try:
            self.ws = await websockets.connect(self.ws_url)
            print("[测试] WebSocket连接成功")
            return True
        except Exception as e:
            print(f"[测试] WebSocket连接失败: {e}")
            return False
    
    async def register_session(self):
        """测试会话注册"""
        if not self.ws:
            print("[测试] WebSocket连接未建立")
            return False
        
        print("[测试] 开始会话注册...")
        
        # 构建注册消息
        register_message = {
            "version": "1.0",
            "msg_type": "REGISTER",
            "session_id": None,
            "payload": {
                "auth": {
                    "type": "ACCOUNT",
                    "username": "123",
                    "password": "123"
                },
                "client_type": "PYTHON_TEST",
                "function_calling": [],
                "require_tts": False
            },
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            # 发送注册请求
            await self.ws.send(json.dumps(register_message))
            print("[测试] 注册请求已发送")
            
            # 接收注册响应
            response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            response_data = json.loads(response)
            print(f"[测试] 收到注册响应: {response_data['msg_type']}")
            
            if response_data['msg_type'] == "REGISTER_ACK":
                self.session_id = response_data['payload']['session_id']
                print(f"[测试] 会话注册成功，会话ID: {self.session_id}")
                return True
            else:
                print(f"[测试] 会话注册失败: {response_data}")
                return False
        except asyncio.TimeoutError:
            print("[测试] 注册超时")
            return False
        except Exception as e:
            print(f"[测试] 注册过程中发生错误: {e}")
            return False
    
    async def query_session_info(self):
        """测试会话信息查询"""
        if not self.ws or not self.session_id:
            print("[测试] WebSocket连接未建立或会话未注册")
            return False
        
        print("[测试] 开始查询会话信息...")
        
        # 构建会话查询消息
        query_message = {
            "version": "1.0",
            "msg_type": "SESSION_QUERY",
            "session_id": self.session_id,
            "payload": {
                "query_fields": []
            },
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            # 发送查询请求
            await self.ws.send(json.dumps(query_message))
            print("[测试] 会话查询请求已发送")
            
            # 接收查询响应
            response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            response_data = json.loads(response)
            print(f"[测试] 收到会话查询响应: {response_data['msg_type']}")
            
            if response_data['msg_type'] == "SESSION_INFO":
                print(f"[测试] 会话信息查询成功: {response_data['payload']}")
                return True
            else:
                print(f"[测试] 会话信息查询失败: {response_data}")
                return False
        except asyncio.TimeoutError:
            print("[测试] 会话信息查询超时")
            return False
        except Exception as e:
            print(f"[测试] 会话信息查询过程中发生错误: {e}")
            return False
    
    async def send_text_request(self, text="你好，我是测试客户端"):
        """测试发送文本请求"""
        if not self.ws or not self.session_id:
            print("[测试] WebSocket连接未建立或会话未注册")
            return False
        
        print(f"[测试] 发送文本请求: {text}")
        
        # 构建文本请求消息
        request_message = {
            "version": "1.0",
            "msg_type": "REQUEST",
            "session_id": self.session_id,
            "payload": {
                "data_type": "TEXT",
                "stream_flag": True,
                "stream_seq": 0,
                "require_tts": False,
                "content": {
                    "text": text
                }
            },
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            # 发送请求
            await self.ws.send(json.dumps(request_message))
            print("[测试] 文本请求已发送")
            
            # 接收响应（流式数据）
            while True:
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=15.0)
                    response_data = json.loads(response)
                    
                    if response_data['msg_type'] == "RESPONSE":
                        if response_data['payload']['stream_seq'] == -1:
                            print("[测试] 文本响应完成")
                            return True
                        else:
                            text_chunk = response_data['payload']['content'].get('text', '')
                            print(f"[测试] 收到文本响应片段: {text_chunk}")
                    else:
                        print(f"[测试] 收到其他类型消息: {response_data['msg_type']}")
                except asyncio.TimeoutError:
                    print("[测试] 文本响应超时")
                    return False
        except Exception as e:
            print(f"[测试] 文本请求过程中发生错误: {e}")
            return False
    
    async def health_check(self):
        """测试健康检查"""
        print("[测试] 开始健康检查...")
        
        # 建立临时连接进行健康检查
        try:
            temp_ws = await websockets.connect(self.ws_url)
            
            # 构建健康检查消息
            health_message = {
                "version": "1.0",
                "msg_type": "HEALTH_CHECK",
                "session_id": None,
                "payload": {
                    "check_fields": []
                },
                "timestamp": int(time.time() * 1000)
            }
            
            # 发送健康检查请求
            await temp_ws.send(json.dumps(health_message))
            print("[测试] 健康检查请求已发送")
            
            # 接收健康检查响应
            response = await asyncio.wait_for(temp_ws.recv(), timeout=5.0)
            response_data = json.loads(response)
            print(f"[测试] 收到健康检查响应: {response_data['msg_type']}")
            
            if response_data['msg_type'] == "HEALTH_CHECK_ACK":
                print(f"[测试] 健康检查成功: {response_data['payload']}")
                await temp_ws.close()
                return True
            else:
                print(f"[测试] 健康检查失败: {response_data}")
                await temp_ws.close()
                return False
        except Exception as e:
            print(f"[测试] 健康检查过程中发生错误: {e}")
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.ws:
            try:
                await self.ws.close()
                print("[测试] WebSocket连接已关闭")
            except Exception as e:
                print(f"[测试] 关闭WebSocket连接时发生错误: {e}")
            finally:
                self.ws = None
                self.session_id = None

async def main():
    """主测试函数"""
    test = WebSocketSessionTest()
    
    # 连接WebSocket
    if not await test.connect():
        print("[测试] 连接失败，测试结束")
        return
    
    try:
        # 测试会话注册
        if not await test.register_session():
            print("[测试] 会话注册失败，测试结束")
            return
        
        # 测试会话信息查询
        if not await test.query_session_info():
            print("[测试] 会话信息查询失败")
        
        # 测试发送文本请求
        if not await test.send_text_request():
            print("[测试] 文本请求失败")
        
        # 测试健康检查
        if not await test.health_check():
            print("[测试] 健康检查失败")
        
        print("[测试] 所有测试完成")
    finally:
        # 断开连接
        await test.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
