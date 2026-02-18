# 打断机制完整修复方案

## 当前状态

根据用户反馈，打断机制依然失败。需要进行全面排查和修复。

## 问题诊断清单

### 1. 服务器端检查

#### 检查点 1：服务器是否在运行
```bash
# 检查服务器进程
ps aux | grep python | grep main.py

# 或者尝试连接
curl http://localhost:8000/health
```

#### 检查点 2：INTERRUPT 消息路由
在 `src/ws/agent_handler.py` 中检查：
```python
# 确保 INTERRUPT 消息被正确路由
if msg_type == "INTERRUPT":
    await _handle_interrupt(session_id, payload)
    return True
```

#### 检查点 3：active_requests 管理
```python
# 在 _handle_request 中，确保请求被注册
cancel_event = asyncio.Event()
active_requests[request_id] = {
    "session_id": session_id,
    "cancel_event": cancel_event,
    "timestamp": time.time()
}

# 在请求结束时，确保请求被清理
finally:
    if request_id in active_requests:
        del active_requests[request_id]
```

#### 检查点 4：cancel_event 传播
确保 cancel_event 在整个调用链中传递：
```
_handle_request
  → process_text_request_with_cancel(cancel_event)
    → generator.stream_generate(cancel_event)
      → llm_client._chat_completions_with_functions_stream(cancel_event)
```

### 2. 客户端检查

#### 检查点 1：currentRequestId 设置
在浏览器控制台执行：
```javascript
// 检查当前状态
console.log('currentRequestId:', messageService.currentRequestId);
console.log('isReceivingResponse:', messageService.isReceivingResponse);
```

#### 检查点 2：打断触发时机
```javascript
// 在 MessageService.js 中添加日志
async sendTextMessage(text) {
    if (this.isReceivingResponse) {
        console.log('[DEBUG] 触发打断 - currentRequestId:', this.currentRequestId);
        await this.interruptCurrentRequest('USER_NEW_INPUT');
    }
}
```

#### 检查点 3：WebSocket 消息发送
```javascript
// 在 WebSocketClient.js 中添加日志
async sendInterrupt(requestId, reason) {
    console.log('[DEBUG] 发送 INTERRUPT 消息:', {
        requestId,
        reason,
        sessionId: this.sessionId
    });
    // ...
}
```

### 3. 网络层检查

#### 检查点 1：WebSocket 连接状态
```javascript
// 在浏览器控制台
console.log('WebSocket 状态:', messageService.wsClient.ws.readyState);
// 0: CONNECTING, 1: OPEN, 2: CLOSING, 3: CLOSED
```

#### 检查点 2：消息是否发送
在浏览器开发者工具的 Network 标签中：
1. 找到 WebSocket 连接
2. 查看 Messages 标签
3. 确认是否有 INTERRUPT 消息发送

## 已知问题和修复

### 问题 1：函数名被空字符串覆盖（已修复）

**文件**：`src/core/dynamic_llm_client.py`

**修复**：
```python
# 只在有值时更新函数名
if 'name' in function_call and function_call['name']:
    function_call_name = function_call['name']
```

### 问题 2：INTERRUPT_ACK 使用错误的发送方法（已修复）

**文件**：`src/ws/agent_handler.py`

**修复**：
```python
# 使用 manager.send_json 而不是 ws.send_json
await manager.send_json(session_id, build_message("INTERRUPT_ACK", {...}, session_id))
```

### 问题 3：客户端 ID 跟踪错误（已修复）

**文件**：`client/web/Demo/src/services/MessageService.js`

**修复**：
```javascript
// 正确跟踪 requestId 和 messageId
const { requestId, promise } = this.wsClient.sendTextRequest(text, options);
this.currentRequestId = requestId;  // req_xxx
this.currentMessageId = messageId;  // msg_xxx
```

## 可能的新问题

### 问题 A：cancel_event 检查频率不够

**症状**：打断请求发送了，但 LLM 继续生成

**原因**：只在某些点检查 cancel_event，检查间隔太长

**修复**：在 `dynamic_llm_client.py` 中增加检查点
```python
async for line in resp.content:
    # ✅ 每次读取数据时都检查
    if cancel_event and cancel_event.is_set():
        self.logger.llm.info('LLM stream cancelled')
        resp.close()
        return
    
    # 处理数据...
```

### 问题 B：HTTP 连接没有立即关闭

**症状**：设置了 cancel_event，但数据继续流入

**原因**：只设置了标志，没有关闭底层连接

**修复**：立即关闭 HTTP 响应
```python
if cancel_event and cancel_event.is_set():
    resp.close()  # ✅ 立即关闭连接
    return
```

### 问题 C：请求已经完成，无法打断

**症状**：用户点击打断时，请求已经结束

**原因**：响应太快，或者用户操作太慢

**解决方案**：
1. 在客户端检查 `isReceivingResponse`
2. 如果为 false，提示用户"没有正在进行的请求"
3. 不发送 INTERRUPT 消息

### 问题 D：请求 ID 不匹配

**症状**：服务器收到 INTERRUPT，但找不到对应的请求

**原因**：
- 客户端发送的 request_id 格式错误
- 服务器端 active_requests 中没有该请求
- 请求已经完成并被清理

**修复**：添加详细日志
```python
# agent_handler.py
logger.ws.info("Interrupt request details", {
    "interrupt_request_id": interrupt_request_id,
    "active_requests": list(active_requests.keys()),
    "found": interrupt_request_id in active_requests
})
```

## 完整测试流程

### 步骤 1：启动服务器
```bash
cd E:\Project\Python\MuseumAgent_Server
python main.py
```

### 步骤 2：打开浏览器控制台
按 F12 打开开发者工具

### 步骤 3：发送长文本请求
在聊天界面输入："给我讲一个很长很长的故事"

### 步骤 4：观察控制台
应该看到：
```
[MessageService] 开始接收响应 - 请求ID: req_xxx
[WebSocket] 收到响应: {...}
```

### 步骤 5：立即发送新请求
在响应过程中输入："停止"

### 步骤 6：观察打断日志
**客户端应该显示**：
```
[MessageService] 检测到新输入，打断当前响应
[MessageService] 发送打断信号 - 请求ID: req_xxx
[WebSocket] 发送打断请求: req_xxx
[WebSocket] 收到打断确认: {status: "SUCCESS", ...}
```

**服务器应该显示**：
```
[WS] [INFO] Received message | {"msg_type": "INTERRUPT", ...}
[WS] [INFO] Request interrupted | {"request_id": "req_xxx", ...}
[LLM] [INFO] LLM stream cancelled by user
```

### 步骤 7：验证结果
- ✅ 旧的响应停止
- ✅ 新的请求开始处理
- ✅ 没有错误日志

## 紧急修复建议

如果打断机制完全不工作，可以采用以下临时方案：

### 方案 1：客户端强制清理
```javascript
// 在 MessageService.js 中
async interruptCurrentRequest(reason) {
    // 1. 立即清理客户端状态
    this.isReceivingResponse = false;
    this.currentRequestId = null;
    this.currentMessageId = null;
    
    // 2. 停止音频播放
    audioService.stopAllPlayback();
    
    // 3. 尝试发送 INTERRUPT（不等待响应）
    try {
        this.wsClient.sendInterrupt(oldRequestId, reason).catch(() => {});
    } catch (e) {}
    
    // 4. 立即允许新请求
    return;
}
```

### 方案 2：服务器端超时清理
```python
# 在 agent_handler.py 中添加定时清理
async def cleanup_old_requests():
    while True:
        await asyncio.sleep(60)  # 每分钟清理一次
        now = time.time()
        to_remove = []
        for req_id, req_info in active_requests.items():
            if now - req_info["timestamp"] > 300:  # 5分钟超时
                req_info["cancel_event"].set()
                to_remove.append(req_id)
        
        for req_id in to_remove:
            del active_requests[req_id]
            logger.ws.info("Cleaned up old request", {"request_id": req_id})
```

## 下一步行动

1. **确认服务器正在运行**
2. **在浏览器中测试打断**
3. **检查浏览器控制台日志**
4. **检查服务器日志**
5. **根据日志定位具体问题**
6. **应用相应的修复方案**

## 联系信息

如果问题持续存在，请提供：
1. 浏览器控制台完整日志
2. 服务器完整日志（包含 INTERRUPT 相关）
3. 打断操作的详细步骤
4. 预期行为 vs 实际行为

这将帮助我们更快地定位和解决问题。

