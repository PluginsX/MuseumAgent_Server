# 打断机制全面排查和修复

## 问题现象
用户报告打断机制失败，无法中断正在进行的 LLM 响应。

## 排查步骤

### 1. 检查客户端是否发送打断请求

**客户端逻辑**（MessageService.js）：
```javascript
async interruptCurrentRequest(reason = 'USER_NEW_INPUT') {
    if (!this.currentRequestId || !this.isReceivingResponse) {
        console.log('[MessageService] 无活跃请求需要打断');
        return;
    }
    
    // 1. 停止音频播放
    audioService.stopAllPlayback();
    
    // 2. 发送 INTERRUPT 消息
    await this.wsClient.sendInterrupt(this.currentRequestId, reason);
    
    // 3. 清理客户端状态
    this.isReceivingResponse = false;
    this.currentRequestId = null;
    this.currentMessageId = null;
}
```

**检查点**：
- ✅ `currentRequestId` 是否正确设置
- ✅ `isReceivingResponse` 是否为 true
- ✅ `sendInterrupt` 是否被调用

### 2. 检查 WebSocket 客户端是否发送消息

**WebSocketClient.js**：
```javascript
async sendInterrupt(requestId, reason = 'USER_NEW_INPUT') {
    const message = {
        version: '1.0',
        msg_type: 'INTERRUPT',
        session_id: this.sessionId,
        payload: {
            interrupt_request_id: requestId,
            reason: reason
        },
        timestamp: Date.now()
    };
    
    return new Promise((resolve, reject) => {
        const handler = (data) => {
            this.messageHandlers.delete('INTERRUPT_ACK');
            resolve(data.payload);
        };
        
        this.messageHandlers.set('INTERRUPT_ACK', handler);
        this._send(message);
        
        // 超时处理（5秒）
        setTimeout(() => {
            if (this.messageHandlers.has('INTERRUPT_ACK')) {
                this.messageHandlers.delete('INTERRUPT_ACK');
                reject(new Error('打断请求超时'));
            }
        }, 5000);
    });
}
```

**检查点**：
- ✅ 消息格式是否正确
- ✅ `interrupt_request_id` 是否是 `req_xxx` 格式
- ✅ 是否等待 `INTERRUPT_ACK` 响应

### 3. 检查服务器是否接收到打断请求

**服务器日志应该显示**：
```
[WS] [INFO] Received message | {"msg_type": "INTERRUPT", ...}
[WS] [INFO] Request interrupted | {"request_id": "req_xxx", ...}
```

**如果没有这些日志**：
- 消息可能没有发送到服务器
- 或者服务器没有正确路由 INTERRUPT 消息

### 4. 检查服务器是否设置取消事件

**agent_handler.py**：
```python
async def _handle_interrupt(session_id: str, payload: Dict) -> None:
    interrupt_request_id = payload.get("interrupt_request_id")
    
    if interrupt_request_id in active_requests:
        req_info = active_requests[interrupt_request_id]
        req_info["cancel_event"].set()  # ✅ 设置取消信号
        interrupted_ids.append(interrupt_request_id)
    
    # 发送确认
    await manager.send_json(session_id, build_message("INTERRUPT_ACK", {...}, session_id))
```

**检查点**：
- ✅ `active_requests` 中是否有该请求
- ✅ `cancel_event.set()` 是否被调用
- ✅ `INTERRUPT_ACK` 是否发送

### 5. 检查 LLM 客户端是否检查取消信号

**dynamic_llm_client.py**：
```python
async for line in resp.content:
    # ✅ 检查取消信号
    if cancel_event and cancel_event.is_set():
        self.logger.llm.info('LLM stream cancelled by user')
        resp.close()  # 关闭 HTTP 连接
        return
```

**检查点**：
- ✅ `cancel_event` 是否传递到 LLM 客户端
- ✅ 是否在每次读取数据时检查
- ✅ 是否关闭 HTTP 连接

### 6. 检查请求处理器是否检查取消信号

**request_processor.py**：
```python
async for chunk in generator.stream_generate(...):
    # ✅ 检查取消信号
    if cancel_event and cancel_event.is_set():
        logger.ws.info('Request cancelled during LLM generation')
        yield {
            "request_id": request_id,
            "text_stream_seq": -1,
            "voice_stream_seq": -1,
            "interrupted": True,
            "interrupt_reason": "USER_NEW_INPUT",
            "content": {}
        }
        return
```

**检查点**：
- ✅ 是否在生成过程中检查
- ✅ 是否发送中断标记
- ✅ 是否提前返回

## 可能的问题

### 问题 1：客户端没有触发打断

**原因**：
- `currentRequestId` 为 null
- `isReceivingResponse` 为 false
- 用户输入时机不对（响应已经结束）

**解决方案**：
- 在浏览器控制台检查 `messageService.currentRequestId` 和 `messageService.isReceivingResponse`
- 确保在响应过程中触发打断

### 问题 2：服务器没有收到打断请求

**原因**：
- WebSocket 连接断开
- 消息格式错误
- 服务器没有正确路由 INTERRUPT 消息

**解决方案**：
- 检查 WebSocket 连接状态
- 检查服务器日志是否有 INTERRUPT 消息
- 检查 `agent_handler.py` 中的消息路由

### 问题 3：取消事件没有传播

**原因**：
- `cancel_event` 没有传递到 LLM 客户端
- `cancel_event` 没有传递到请求处理器
- 检查频率太低（只在某些点检查）

**解决方案**：
- 确保 `cancel_event` 在整个调用链中传递
- 在关键位置增加检查点
- 提高检查频率

### 问题 4：HTTP 连接没有关闭

**原因**：
- 只设置了 `cancel_event`，但没有关闭 HTTP 连接
- LLM API 继续发送数据
- 服务器继续处理数据

**解决方案**：
- 在检测到取消时立即调用 `resp.close()`
- 确保 aiohttp 连接被正确关闭

## 测试方法

### 手动测试

1. **打开浏览器控制台**
2. **发送一个长文本请求**（例如："给我讲一个很长很长的故事"）
3. **在响应过程中立即发送新请求**（例如："停止"）
4. **观察控制台日志**：
   ```
   [MessageService] 检测到新输入，打断当前响应
   [MessageService] 发送打断信号 - 请求ID: req_xxx
   [WebSocket] 发送打断请求: req_xxx
   [WebSocket] 收到打断确认: {...}
   [MessageService] 打断信号已发送
   ```

5. **观察服务器日志**：
   ```
   [WS] [INFO] Request interrupted | {"request_id": "req_xxx"}
   [LLM] [INFO] LLM stream cancelled by user
   [WS] [INFO] Request cancelled during LLM generation
   ```

### 自动化测试脚本

创建 `test_interrupt.py`：
```python
import asyncio
import websockets
import json
import time

async def test_interrupt():
    uri = "ws://localhost:8000/ws/agent"
    
    async with websockets.connect(uri) as ws:
        # 1. 注册会话
        register_msg = {
            "version": "1.0",
            "msg_type": "REGISTER",
            "payload": {
                "auth": {"auth_type": "API_KEY", "api_key": "test_key"},
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
        session_id = data["payload"]["session_id"]
        print(f"✅ 会话注册成功: {session_id}")
        
        # 2. 发送长文本请求
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
                "content": {"text": "给我讲一个很长很长的故事"},
                "require_tts": False
            },
            "timestamp": int(time.time() * 1000)
        }
        await ws.send(json.dumps(text_msg))
        print(f"✅ 发送文本请求: {request_id}")
        
        # 3. 等待一小段时间，让 LLM 开始生成
        await asyncio.sleep(0.5)
        
        # 4. 发送打断请求
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
        print(f"✅ 发送打断请求: {request_id}")
        
        # 5. 接收响应
        interrupted = False
        ack_received = False
        
        async for message in ws:
            data = json.loads(message)
            msg_type = data.get("msg_type")
            
            if msg_type == "INTERRUPT_ACK":
                ack_received = True
                print(f"✅ 收到打断确认: {data['payload']}")
            
            elif msg_type == "RESPONSE":
                payload = data.get("payload", {})
                if payload.get("interrupted"):
                    interrupted = True
                    print(f"✅ 收到中断标记")
                    break
                
                # 打印接收到的文本
                content = payload.get("content", {})
                text = content.get("text", "")
                if text:
                    print(f"📝 收到文本: {text}")
        
        # 6. 验证结果
        assert ack_received, "❌ 未收到打断确认"
        assert interrupted, "❌ 未收到中断标记"
        print("✅ 打断机制测试通过")

if __name__ == "__main__":
    asyncio.run(test_interrupt())
```

## 修复建议

### 1. 增加详细日志

在关键位置添加日志：
```python
# agent_handler.py
logger.ws.info("Interrupt request received", {
    "request_id": interrupt_request_id,
    "session_id": session_id,
    "active_requests": list(active_requests.keys())
})

# dynamic_llm_client.py
self.logger.llm.info('Checking cancel event', {
    'is_set': cancel_event.is_set() if cancel_event else False,
    'line_count': line_count
})
```

### 2. 确保取消事件传播

检查所有调用链：
```
agent_handler.py (_handle_request)
  → request_processor.py (process_text_request_with_cancel)
    → command_generator.py (stream_generate)
      → dynamic_llm_client.py (_chat_completions_with_functions_stream)
```

确保每一层都传递 `cancel_event`。

### 3. 提高检查频率

在 LLM 客户端中，每次读取数据时都检查：
```python
async for line in resp.content:
    if cancel_event and cancel_event.is_set():
        resp.close()
        return
    # 处理数据...
```

### 4. 添加超时保护

如果打断失败，添加超时保护：
```python
# 客户端
setTimeout(() => {
    if (this.isReceivingResponse) {
        console.warn('[MessageService] 打断超时，强制清理状态');
        this.isReceivingResponse = false;
        this.currentRequestId = null;
        this.currentMessageId = null;
    }
}, 10000);  // 10秒超时
```

## 下一步

1. **运行测试脚本**，确认打断机制是否工作
2. **检查服务器日志**，查看是否有 INTERRUPT 相关日志
3. **检查浏览器控制台**，查看客户端是否发送打断请求
4. **根据日志定位问题**，进行针对性修复


