import asyncio
import websockets
import json
import base64
import time
import os

class DuplexVoiceTestClient:
    def __init__(self):
        self.ws_url = "ws://localhost:8001/ws/agent/stream"
        self.ws = None
        self.session_id = None
        self.auth_data = {
            "type": "ACCOUNT",
            "username": "123",
            "password": "123"
        }
    
    async def connect(self):
        """连接到WebSocket服务器"""
        print("[测试] 连接到WebSocket服务:", self.ws_url)
        try:
            self.ws = await websockets.connect(self.ws_url)
            print("[测试] WebSocket连接成功")
            return True
        except Exception as e:
            print(f"[测试] WebSocket连接失败: {e}")
            return False
    
    async def register_session(self):
        """注册会话"""
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
                "auth": self.auth_data,
                "client_type": "PYTHON_TEST",
                "function_calling": [],
                "require_tts": True
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
    
    def _read_audio_file(self, file_path):
        """读取音频文件"""
        try:
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            print(f"[测试] 读取音频文件成功: {file_path}, 大小: {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            print(f"[测试] 读取音频文件失败: {e}")
            return None
    
    async def test_duplex_voice(self, audio_file_path):
        """测试双向流式语音"""
        if not self.ws or not self.session_id:
            print("[测试] WebSocket连接未建立或会话未注册")
            return False
        
        # 读取音频文件
        audio_data = self._read_audio_file(audio_file_path)
        if not audio_data:
            return False
        
        print("[测试] 开始测试双向流式语音...")
        
        # 构建控制帧
        control_message = {
            "version": "1.0",
            "msg_type": "VOICE_STREAM_START",
            "session_id": self.session_id,
            "payload": {
                "require_tts": True
            },
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            # 发送控制帧
            await self.ws.send(json.dumps(control_message))
            print("[测试] 发送语音流开始控制帧")
            
            # 等待服务器的VOICE_STREAM_START_ACK响应
            print("[测试] 等待服务器响应...")
            start_ack_received = False
            while not start_ack_received:
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                    if isinstance(response, str):
                        try:
                            response_data = json.loads(response)
                            if response_data['msg_type'] == "VOICE_STREAM_START_ACK":
                                print(f"[测试] 收到语音流开始确认: {response_data['payload']}")
                                start_ack_received = True
                            elif response_data['msg_type'] == "ERROR":
                                print(f"[测试] 服务器错误: {response_data['payload']}")
                                return False
                        except json.JSONDecodeError:
                            print(f"[测试] 收到非JSON响应: {response[:100]}...")
                except asyncio.TimeoutError:
                    print("[测试] 等待服务器响应超时")
                    return False
            
            # 分片发送音频数据
            chunk_size = 4096
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                await self.ws.send(chunk)
                print(f"[测试] 发送语音数据分片 {i//chunk_size + 1}/{(len(audio_data)+chunk_size-1)//chunk_size}")
                await asyncio.sleep(0.01)  # 避免发送过快
            
            # 发送结束帧
            end_message = {
                "version": "1.0",
                "msg_type": "VOICE_STREAM_END",
                "session_id": self.session_id,
                "payload": {},
                "timestamp": int(time.time() * 1000)
            }
            await self.ws.send(json.dumps(end_message))
            print("[测试] 发送语音流结束控制帧")
            
            # 接收服务器的响应
            print("[测试] 接收服务器响应...")
            response_complete = False
            while not response_complete:
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=30.0)
                    if isinstance(response, str):
                        try:
                            response_data = json.loads(response)
                            if response_data['msg_type'] == "RESPONSE":
                                if response_data['payload']['stream_seq'] == -1:
                                    print("[测试] 响应完成")
                                    response_complete = True
                                else:
                                    text_chunk = response_data['payload']['content'].get('text', '')
                                    if text_chunk:
                                        print(f"[测试] 收到文本响应片段: {text_chunk}")
                                    # 检查是否有语音数据
                                    if response_data['payload']['data_type'] == "VOICE":
                                        print("[测试] 收到语音响应数据")
                            elif response_data['msg_type'] == "ERROR":
                                print(f"[测试] 服务器错误: {response_data['payload']}")
                                return False
                        except json.JSONDecodeError:
                            print(f"[测试] 收到非JSON响应: {response[:100]}...")
                    else:
                        # 二进制响应
                        print(f"[测试] 收到二进制响应，大小: {len(response)} bytes")
                except asyncio.TimeoutError:
                    print("[测试] 接收响应超时")
                    return False
            
            return True
        except Exception as e:
            print(f"[测试] 测试双向流式语音失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.ws:
            try:
                await self.ws.close()
                print("[测试] WebSocket连接已关闭")
            except Exception as e:
                print(f"[测试] 关闭连接失败: {e}")

async def main():
    """主测试函数"""
    client = DuplexVoiceTestClient()
    
    try:
        # 连接到服务器
        if not await client.connect():
            return
        
        # 注册会话
        if not await client.register_session():
            await client.disconnect()
            return
        
        # 测试短语音
        short_audio_path = r"E:\Project\Python\MuseumAgent_Server\tests\hello.mp3"
        if os.path.exists(short_audio_path):
            print("\n=== 测试双向流式语音 (短语音) ===")
            await client.test_duplex_voice(short_audio_path)
        else:
            print(f"[测试] 短语音文件不存在: {short_audio_path}")
        
    finally:
        # 断开连接
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
