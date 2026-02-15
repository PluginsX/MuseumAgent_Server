import asyncio
import websockets
import json
import base64
import time
import os

class VoiceTestClient:
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
    
    async def send_voice_request_base64(self, audio_file_path):
        """使用BASE64模式发送语音请求"""
        if not self.ws or not self.session_id:
            print("[测试] WebSocket连接未建立或会话未注册")
            return False
        
        # 读取音频文件
        audio_data = self._read_audio_file(audio_file_path)
        if not audio_data:
            return False
        
        print("[测试] 开始发送BASE64语音请求...")
        
        # 将音频数据转换为BASE64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        print(f"[测试] 音频数据Base64编码完成，长度: {len(audio_base64)} characters")
        
        # 构建语音请求消息
        request_message = {
            "version": "1.0",
            "msg_type": "REQUEST",
            "session_id": self.session_id,
            "payload": {
                "data_type": "VOICE",
                "stream_flag": True,
                "stream_seq": 0,
                "require_tts": True,
                "content": {
                    "voice_mode": "BASE64",
                    "voice": audio_base64
                }
            },
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            # 发送请求
            await self.ws.send(json.dumps(request_message))
            print("[测试] BASE64语音请求已发送")
            
            # 接收响应
            while True:
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    
                    if response_data['msg_type'] == "RESPONSE":
                        if response_data['payload']['stream_seq'] == -1:
                            print("[测试] 语音响应完成")
                            return True
                        else:
                            text_chunk = response_data['payload']['content'].get('text', '')
                            if text_chunk:
                                print(f"[测试] 收到文本响应片段: {text_chunk}")
                            # 检查是否有语音数据
                            if response_data['payload']['data_type'] == "VOICE":
                                print("[测试] 收到语音响应数据")
                    elif response_data['msg_type'] == "ERROR":
                        print(f"[测试] 语音请求失败: {response_data['payload']}")
                        return False
                except asyncio.TimeoutError:
                    print("[测试] 语音响应超时")
                    return False
        except Exception as e:
            print(f"[测试] 语音请求过程中发生错误: {e}")
            return False
    
    async def send_voice_request_binary(self, audio_file_path):
        """使用BINARY模式发送语音请求"""
        if not self.ws or not self.session_id:
            print("[测试] WebSocket连接未建立或会话未注册")
            return False
        
        # 读取音频文件
        audio_data = self._read_audio_file(audio_file_path)
        if not audio_data:
            return False
        
        print("[测试] 开始发送BINARY语音请求...")
        
        # 构建控制帧
        control_message = {
            "version": "1.0",
            "msg_type": "REQUEST",
            "session_id": self.session_id,
            "payload": {
                "data_type": "VOICE",
                "stream_flag": True,
                "stream_seq": 0,
                "require_tts": True,
                "content": {
                    "voice_mode": "BINARY"
                }
            },
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            # 发送控制帧
            await self.ws.send(json.dumps(control_message))
            print("[测试] BINARY语音控制帧已发送")
            
            # 发送二进制数据
            await self.ws.send(audio_data)
            print(f"[测试] 二进制语音数据已发送，大小: {len(audio_data)} bytes")
            
            # 发送结束标志
            end_message = {
                "version": "1.0",
                "msg_type": "REQUEST",
                "session_id": self.session_id,
                "payload": {
                    "data_type": "VOICE",
                    "stream_flag": True,
                    "stream_seq": -1,
                    "require_tts": True,
                    "content": {
                        "voice_mode": "BINARY"
                    }
                },
                "timestamp": int(time.time() * 1000)
            }
            await self.ws.send(json.dumps(end_message))
            print("[测试] BINARY语音结束标志已发送")
            
            # 接收响应
            while True:
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    
                    if response_data['msg_type'] == "RESPONSE":
                        if response_data['payload']['stream_seq'] == -1:
                            print("[测试] 语音响应完成")
                            return True
                        else:
                            text_chunk = response_data['payload']['content'].get('text', '')
                            if text_chunk:
                                print(f"[测试] 收到文本响应片段: {text_chunk}")
                            # 检查是否有语音数据
                            if response_data['payload']['data_type'] == "VOICE":
                                print("[测试] 收到语音响应数据")
                    elif response_data['msg_type'] == "ERROR":
                        print(f"[测试] 语音请求失败: {response_data['payload']}")
                        return False
                except asyncio.TimeoutError:
                    print("[测试] 语音响应超时")
                    return False
        except Exception as e:
            print(f"[测试] 语音请求过程中发生错误: {e}")
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
    client = VoiceTestClient()
    
    try:
        # 连接到服务器
        if not await client.connect():
            return
        
        # 注册会话
        if not await client.register_session():
            await client.disconnect()
            return
        
        # 测试短语音 - BASE64模式
        print("\n=== 测试短语音 (BASE64模式) ===")
        short_audio_path = r"E:\Project\Python\MuseumAgent_Server\tests\hello.mp3"
        if os.path.exists(short_audio_path):
            await client.send_voice_request_base64(short_audio_path)
        else:
            print(f"[测试] 短语音文件不存在: {short_audio_path}")
        
        # 测试短语音 - BINARY模式
        print("\n=== 测试短语音 (BINARY模式) ===")
        if os.path.exists(short_audio_path):
            await client.send_voice_request_binary(short_audio_path)
        else:
            print(f"[测试] 短语音文件不存在: {short_audio_path}")
        
        # 测试长语音 - BASE64模式
        print("\n=== 测试长语音 (BASE64模式) ===")
        long_audio_path = r"E:\Project\Python\MuseumAgent_Server\tests\hello_1.mp3"
        if os.path.exists(long_audio_path):
            await client.send_voice_request_base64(long_audio_path)
        else:
            print(f"[测试] 长语音文件不存在: {long_audio_path}")
        
        # 测试长语音 - BINARY模式
        print("\n=== 测试长语音 (BINARY模式) ===")
        if os.path.exists(long_audio_path):
            await client.send_voice_request_binary(long_audio_path)
        else:
            print(f"[测试] 长语音文件不存在: {long_audio_path}")
        
    finally:
        # 断开连接
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
