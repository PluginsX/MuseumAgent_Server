# 打断机制修复文档

## 问题描述

Web Demo 客户端在发送打断请求时出现超时错误：

```
MessageService.js:55 [MessageService] 打断失败: Error: 打断请求超时
WebSocketClient.js:656 [WebSocket] 请求超时: req_1771423141749_c3peh6t9w
```

## 根因分析

### 1. 客户端超时时间过短
- **原始设置**: 5秒超时
- **问题**: 服务端处理打断请求可能需要更长时间（特别是在高负载或网络延迟情况下）
- **位置**: `WebSocketClient.js:333`

### 2. 客户端阻塞式等待
- **原始逻辑**: `await this.wsClient.sendInterrupt()` 阻塞等待服务端确认
- **问题**: 如果服务端响应慢或网络延迟，会导致用户体验卡顿
- **影响**: 用户发送新消息时需要等待打断完成才能继续

### 3. 消息处理优先级问题
- **原始逻辑**: 打断确认与其他消息（如心跳、响应）混在一起处理
- **问题**: 可能被其他消息阻塞，导致处理延迟

### 4. 服务端同步处理
- **原始逻辑**: `await _handle_interrupt()` 同步等待处理完成
- **问题**: 阻塞主消息循环，影响其他消息处理

## 修复方案

### 修复1: 增加客户端超时时间

**文件**: `client/web/Demo/src/core/WebSocketClient.js`

```javascript
// 从 5秒 增加到 15秒
setTimeout(() => {
    if (this.messageHandlers.has('INTERRUPT_ACK')) {
        this.messageHandlers.delete('INTERRUPT_ACK');
        reject(new Error('打断请求超时'));
    }
}, 15000);  // ✅ 从 5000 改为 15000
```

**理由**: 
- 给服务端足够的处理时间
- 适应网络延迟和高负载场景
- 15秒是合理的用户等待时间上限

### 修复2: 客户端乐观更新（非阻塞）

**文件**: `client/web/Demo/src/services/MessageService.js`

```javascript
async interruptCurrentRequest(reason = 'USER_NEW_INPUT') {
    // 1. 立即停止音频播放（不等待服务端确认）
    audioService.stopAllPlayback();
    
    // 2. 立即清理客户端状态（乐观更新）
    const oldRequestId = this.currentRequestId;
    this.isReceivingResponse = false;
    this.currentRequestId = null;
    this.currentMessageId = null;
    
    // 3. 异步发送打断消息（不阻塞）
    this.wsClient.sendInterrupt(oldRequestId, reason)
        .then((ackPayload) => {
            console.log('[MessageService] 打断确认收到:', ackPayload);
        })
        .catch((error) => {
            console.warn('[MessageService] 打断确认超时（已本地处理）:', error.message);
        });
}
```

**理由**:
- **乐观更新**: 立即清理本地状态，不等待服务端确认
- **非阻塞**: 打断请求异步发送，不影响后续操作
- **用户体验**: 用户感觉打断是即时的，无需等待

### 修复3: 优化消息处理优先级

**文件**: `client/web/Demo/src/core/WebSocketClient.js`

```javascript
_handleMessage(event) {
    const data = JSON.parse(event.data);
    
    // 处理心跳
    if (data.msg_type === 'HEARTBEAT') {
        this._handleHeartbeat(data);
        return;
    }

    // ✅ 优先处理打断确认（避免被其他消息阻塞）
    if (data.msg_type === 'INTERRUPT_ACK') {
        const handler = this.messageHandlers.get('INTERRUPT_ACK');
        if (handler) {
            handler(data);
        }
        return;
    }

    // 处理其他消息...
}
```

**理由**:
- 打断确认优先处理，避免被其他消息阻塞
- 确保快速响应用户的打断操作

### 修复4: 服务端异步处理打断

**文件**: `src/ws/agent_handler.py`

```python
elif msg_type == "INTERRUPT":
    if not session_id:
        await send_json(build_error("SESSION_INVALID", "会话不存在或未注册"))
        continue
    # ✅ 使用 asyncio.create_task 异步处理打断，避免阻塞主循环
    asyncio.create_task(_handle_interrupt(session_id, payload))
    # 注意：_handle_interrupt 内部会发送 INTERRUPT_ACK
```

**理由**:
- 不阻塞主消息循环
- 立即处理下一条消息（如新的请求）
- 提高并发处理能力

### 修复5: 增强服务端错误处理

**文件**: `src/ws/agent_handler.py`

```python
async def _handle_interrupt(session_id: str, payload: Dict) -> None:
    # ... 处理逻辑 ...
    
    # ✅ 使用 try-except 确保确认消息一定发送
    try:
        await manager.send_json(session_id, build_message("INTERRUPT_ACK", {
            "interrupted_request_ids": interrupted_ids,
            "status": status,
            "message": message
        }, session_id))
        logger.ws.info("INTERRUPT_ACK sent", {
            "session_id": session_id[:16],
            "interrupted_count": len(interrupted_ids)
        })
    except Exception as e:
        logger.ws.error("Failed to send INTERRUPT_ACK", {
            "session_id": session_id[:16],
            "error": str(e)
        })
```

**理由**:
- 确保即使发生错误也能记录日志
- 避免异常导致连接断开

## 修复效果

### 修复前
1. 打断请求超时（5秒）
2. 用户体验卡顿（需等待打断完成）
3. 消息处理可能被阻塞
4. 服务端同步处理影响性能

### 修复后
1. ✅ 超时时间增加到15秒（更宽容）
2. ✅ 乐观更新，立即响应用户操作
3. ✅ 打断确认优先处理
4. ✅ 服务端异步处理，不阻塞主循环
5. ✅ 增强错误处理和日志记录

## 测试验证

### 测试场景1: 正常打断
1. 发送文本消息，等待AI回复
2. 在AI回复过程中，立即发送新消息
3. **预期**: 旧消息立即停止，新消息开始处理

### 测试场景2: 语音打断
1. 开启话筒，说话触发VAD
2. 在AI语音回复过程中，再次说话
3. **预期**: AI语音立即停止，新语音开始识别

### 测试场景3: 高延迟网络
1. 模拟网络延迟（如使用Chrome DevTools限速）
2. 发送打断请求
3. **预期**: 客户端立即响应，不等待服务端确认

### 测试场景4: 服务端高负载
1. 同时发送多个请求
2. 在处理过程中发送打断
3. **预期**: 打断请求不阻塞其他消息处理

## 监控指标

### 客户端日志
```javascript
[MessageService] 发送打断信号 - 请求ID: req_xxx 消息ID: msg_xxx 原因: USER_NEW_INPUT
[MessageService] 打断信号已发送（本地状态已清理）
[MessageService] 打断确认收到: {interrupted_request_ids: [...], status: "SUCCESS"}
```

### 服务端日志
```python
[WebSocket] Processing interrupt request - session_id: sess_xxx, interrupt_request_id: req_xxx
[WebSocket] Request interrupted - request_id: req_xxx, reason: USER_NEW_INPUT
[WebSocket] INTERRUPT_ACK sent - session_id: sess_xxx, interrupted_count: 1
```

## 注意事项

1. **乐观更新的权衡**: 客户端立即清理状态，即使服务端确认失败，也不会回滚。这是为了用户体验的权衡。
2. **网络异常**: 如果网络完全断开，打断请求会超时，但本地状态已清理，不影响用户继续操作。
3. **并发打断**: 如果用户快速连续发送多个打断请求，只有最后一个会生效（因为前面的请求已完成）。

## 后续优化建议

1. **添加重试机制**: 如果打断确认超时，可以自动重试1-2次
2. **优化取消检查点**: 在LLM生成和TTS合成的更多位置添加取消检查
3. **性能监控**: 添加打断请求的响应时间监控
4. **用户反馈**: 在UI上显示打断状态（如"正在停止..."）

## 相关文件

- `client/web/Demo/src/core/WebSocketClient.js` - WebSocket客户端
- `client/web/Demo/src/services/MessageService.js` - 消息服务
- `src/ws/agent_handler.py` - WebSocket处理器
- `src/ws/request_processor.py` - 请求处理器（支持取消）
- `docs/CommunicationProtocol_CS.md` - 通信协议文档

## 版本信息

- **修复日期**: 2026-02-18
- **修复版本**: v1.1.0
- **影响范围**: Web Demo客户端 + 服务端WebSocket处理

