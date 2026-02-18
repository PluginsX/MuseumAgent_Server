# 用户优先对话打断机制 - 设计方案

## 一、现状分析

### 1.1 现有通信流程

#### C→S 流程
1. **REGISTER** → 建立会话
2. **REQUEST** → 发送请求（TEXT/VOICE）
3. **HEARTBEAT_REPLY** → 心跳回复
4. **SHUTDOWN** → 主动断开

#### S→C 流程
1. **REGISTER_ACK** → 注册确认
2. **RESPONSE** → 流式响应（文本流 + 语音流 + 函数调用）
3. **HEARTBEAT** → 心跳
4. **ERROR** → 错误

#### 业务流程
```
用户输入 → STT(语音) → SRS检索 → LLM生成 → TTS(可选) → 流式返回
         ↓                                              ↓
    REQUEST(C→S)                                  RESPONSE(S→C)
                                                   (text_seq: 0,1,2...,-1)
                                                   (voice_seq: 0,1,2...,-1)
```

### 1.2 问题识别

**核心问题：缺乏打断机制**

1. **服务端无法感知打断**：用户发送新请求时，服务端仍在处理旧请求
2. **客户端无法停止播放**：新请求发出后，旧响应的语音仍在播放
3. **资源浪费**：LLM、TTS 继续生成用户不再需要的内容
4. **用户体验差**：无法实现自然的对话打断

---

## 二、设计目标

### 2.1 用户体验目标

1. **即时打断**：用户发送新消息时，立即停止当前回复
2. **资源释放**：停止 LLM 生成、TTS 合成、音频播放
3. **状态清理**：清除旧请求的所有中间状态
4. **无缝切换**：立即开始处理新请求

### 2.2 技术目标

1. **协议扩展**：新增 INTERRUPT 消息类型
2. **服务端支持**：取消正在进行的异步任务
3. **客户端支持**：停止音频播放、清理 UI 状态
4. **向后兼容**：不影响现有功能

---

## 三、方案设计

### 3.1 协议扩展

#### 3.1.1 新增消息类型：INTERRUPT（C→S）

**用途**：客户端通知服务端中断当前正在处理的请求

**时机**：用户在智能体回复过程中发送新消息时

**payload：**

```json
{
  "interrupt_request_id": "req_xxx",  // 要中断的请求ID（可选，为空则中断所有）
  "reason": "USER_NEW_INPUT"          // 中断原因
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| interrupt_request_id | string | 否 | 要中断的请求ID，为空则中断该会话的所有进行中请求 |
| reason | string | 是 | 中断原因：`USER_NEW_INPUT`（用户新输入）/ `USER_STOP`（用户主动停止）/ `CLIENT_ERROR`（客户端错误） |

#### 3.1.2 新增消息类型：INTERRUPT_ACK（S→C）

**用途**：服务端确认中断操作完成

**payload：**

```json
{
  "interrupted_request_ids": ["req_xxx", "req_yyy"],
  "status": "SUCCESS",
  "message": "已中断 2 个请求"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| interrupted_request_ids | array | 被中断的请求ID列表 |
| status | string | `SUCCESS` / `PARTIAL`（部分成功）/ `FAILED` |
| message | string | 描述信息 |

#### 3.1.3 扩展 RESPONSE：增加中断标记

当请求被中断时，服务端发送最后一帧 RESPONSE，标记为中断：

```json
{
  "request_id": "req_xxx",
  "text_stream_seq": -1,
  "voice_stream_seq": -1,
  "interrupted": true,           // ✅ 新增字段
  "interrupt_reason": "USER_NEW_INPUT",
  "content": {}
}
```

---

### 3.2 通信流程设计

#### 3.2.1 正常流程（无打断）

```
Client                          Server
  |                               |
  |------ REQUEST(req_1) -------->|
  |                               | [STT → SRS → LLM → TTS]
  |<----- RESPONSE(seq:0) --------|
  |<----- RESPONSE(seq:1) --------|
  |<----- RESPONSE(seq:2) --------|
  |<----- RESPONSE(seq:-1) -------|
  |                               |
```

#### 3.2.2 打断流程（用户发送新消息）

```
Client                          Server
  |                               |
  |------ REQUEST(req_1) -------->|
  |                               | [STT → SRS → LLM → TTS]
  |<----- RESPONSE(seq:0) --------|
  |<----- RESPONSE(seq:1) --------|
  |                               |
  | [用户发送新消息]               |
  |                               |
  |------ INTERRUPT(req_1) ------>| [取消 LLM/TTS 任务]
  | [停止音频播放]                 |
  | [清理 UI 状态]                 |
  |                               |
  |<--- INTERRUPT_ACK ------------|
  |<--- RESPONSE(seq:-1,          |
  |     interrupted:true) --------|
  |                               |
  |------ REQUEST(req_2) -------->| [开始处理新请求]
  |<----- RESPONSE(seq:0) --------|
  |                               |
```

#### 3.2.3 打断流程（用户主动停止）

```
Client                          Server
  |                               |
  |------ REQUEST(req_1) -------->|
  |<----- RESPONSE(seq:0) --------|
  |                               |
  | [用户点击停止按钮]             |
  |                               |
  |------ INTERRUPT(req_1,        |
  |       reason:USER_STOP) ----->| [取消任务]
  |                               |
  |<--- INTERRUPT_ACK ------------|
  |<--- RESPONSE(seq:-1,          |
  |     interrupted:true) --------|
  |                               |
```

---

### 3.3 服务端实现

#### 3.3.1 请求状态管理

在 `agent_handler.py` 中维护活跃请求状态：

```python
# 全局活跃请求管理
active_requests: Dict[str, Dict[str, Any]] = {}
# 结构：{
#   "req_xxx": {
#       "session_id": "sess_xxx",
#       "cancel_event": asyncio.Event(),
#       "start_time": timestamp,
#       "type": "TEXT" | "VOICE"
#   }
# }
```

#### 3.3.2 取消机制

使用 `asyncio.Event` 实现协作式取消：

```python
async def process_text_request_with_cancel(
    session_id: str,
    request_id: str,
    text: str,
    require_tts: bool,
    cancel_event: asyncio.Event
) -> AsyncGenerator[Dict[str, Any], None]:
    """支持取消的文本请求处理"""
    
    try:
        async for chunk in generator.stream_generate(user_input=text, session_id=session_id):
            # 检查取消信号
            if cancel_event.is_set():
                logger.ws.info("Request cancelled", {"request_id": request_id[:16]})
                # 发送中断标记的最后一帧
                yield {
                    "request_id": request_id,
                    "text_stream_seq": -1,
                    "voice_stream_seq": -1 if require_tts else None,
                    "interrupted": True,
                    "interrupt_reason": "USER_NEW_INPUT",
                    "content": {}
                }
                return
            
            # 正常处理
            # ... 现有逻辑 ...
    finally:
        # 清理资源
        pass
```

#### 3.3.3 INTERRUPT 处理器

```python
async def _handle_interrupt(ws: WebSocket, session_id: str, payload: Dict) -> None:
    """处理打断请求"""
    interrupt_request_id = payload.get("interrupt_request_id")
    reason = payload.get("reason", "USER_NEW_INPUT")
    
    interrupted_ids = []
    
    if interrupt_request_id:
        # 中断指定请求
        if interrupt_request_id in active_requests:
            req_info = active_requests[interrupt_request_id]
            if req_info["session_id"] == session_id:
                req_info["cancel_event"].set()
                interrupted_ids.append(interrupt_request_id)
                logger.ws.info("Request interrupted", {
                    "request_id": interrupt_request_id[:16],
                    "reason": reason
                })
    else:
        # 中断该会话的所有请求
        for req_id, req_info in list(active_requests.items()):
            if req_info["session_id"] == session_id:
                req_info["cancel_event"].set()
                interrupted_ids.append(req_id)
        logger.ws.info("All requests interrupted", {
            "session_id": session_id[:16],
            "count": len(interrupted_ids),
            "reason": reason
        })
    
    # 发送确认
    await ws.send_json(build_message("INTERRUPT_ACK", {
        "interrupted_request_ids": interrupted_ids,
        "status": "SUCCESS" if interrupted_ids else "FAILED",
        "message": f"已中断 {len(interrupted_ids)} 个请求" if interrupted_ids else "无活跃请求"
    }, session_id))
```

#### 3.3.4 REQUEST 处理器修改

```python
async def _handle_request(
    ws: WebSocket,
    session_id: str,
    payload: Dict,
    voice_buffer: Dict[str, Dict[str, Any]],
    active_voice_request: Dict[str, Optional[str]],
) -> bool:
    # ... 现有验证逻辑 ...
    
    request_id = payload["request_id"]
    
    # ✅ 创建取消事件
    cancel_event = asyncio.Event()
    active_requests[request_id] = {
        "session_id": session_id,
        "cancel_event": cancel_event,
        "start_time": time.time(),
        "type": payload["data_type"]
    }
    
    try:
        # 处理请求（传入 cancel_event）
        async for resp_payload in process_text_request_with_cancel(
            session_id, request_id, text, require_tts, cancel_event
        ):
            msg = build_message("RESPONSE", resp_payload, session_id)
            if not await manager.send_json(session_id, msg):
                break
    finally:
        # ✅ 清理活跃请求
        active_requests.pop(request_id, None)
    
    return True
```

---

### 3.4 客户端实现

#### 3.4.1 MessageService 扩展

```javascript
class MessageService {
    constructor() {
        this.wsClient = null;
        this.currentRequestId = null;  // 当前正在处理的请求ID
        this.isReceivingResponse = false;  // 是否正在接收响应
    }
    
    /**
     * 发送打断信号
     */
    async interruptCurrentRequest(reason = 'USER_NEW_INPUT') {
        if (!this.currentRequestId || !this.isReceivingResponse) {
            return;
        }
        
        console.log('[MessageService] 发送打断信号:', this.currentRequestId);
        
        try {
            // 1. 停止音频播放
            audioService.stopAllPlayback();
            
            // 2. 发送 INTERRUPT 消息
            await this.wsClient.sendInterrupt(this.currentRequestId, reason);
            
            // 3. 清理客户端状态
            this.isReceivingResponse = false;
            
            // 4. 触发事件
            eventBus.emit(Events.REQUEST_INTERRUPTED, {
                requestId: this.currentRequestId,
                reason: reason
            });
            
        } catch (error) {
            console.error('[MessageService] 打断失败:', error);
        }
    }
    
    /**
     * 发送文本消息（带自动打断）
     */
    async sendTextMessage(text) {
        // ✅ 如果正在接收响应，先打断
        if (this.isReceivingResponse) {
            await this.interruptCurrentRequest('USER_NEW_INPUT');
            // 等待一小段时间确保打断完成
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // ... 现有发送逻辑 ...
        
        const messageId = this._generateMessageId();
        this.currentRequestId = messageId;
        this.isReceivingResponse = true;
        
        // ... 发送请求 ...
    }
    
    /**
     * 发送语音消息（带自动打断）
     */
    async sendVoiceMessageStream(audioStream) {
        // ✅ 如果正在接收响应，先打断
        if (this.isReceivingResponse) {
            await this.interruptCurrentRequest('USER_NEW_INPUT');
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // ... 现有发送逻辑 ...
    }
}
```

#### 3.4.2 WebSocketClient 扩展

```javascript
class WebSocketClient {
    /**
     * 发送打断请求
     */
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
            // 设置处理器
            const handler = (data) => {
                this.messageHandlers.delete('INTERRUPT_ACK');
                resolve(data.payload);
            };
            
            this.messageHandlers.set('INTERRUPT_ACK', handler);
            this._send(message);
            
            // 超时处理
            setTimeout(() => {
                if (this.messageHandlers.has('INTERRUPT_ACK')) {
                    this.messageHandlers.delete('INTERRUPT_ACK');
                    reject(new Error('打断请求超时'));
                }
            }, 5000);
        });
    }
    
    /**
     * 处理接收到的消息（扩展）
     */
    _handleMessage(event) {
        const data = JSON.parse(event.data);
        console.log('[WebSocket] 收到消息:', data.msg_type);
        
        // ✅ 处理打断确认
        if (data.msg_type === 'INTERRUPT_ACK') {
            const handler = this.messageHandlers.get('INTERRUPT_ACK');
            if (handler) {
                handler(data);
            }
            return;
        }
        
        // 处理响应（检查中断标记）
        if (data.msg_type === 'RESPONSE') {
            const payload = data.payload;
            
            // ✅ 如果响应被中断，清理状态
            if (payload.interrupted) {
                console.log('[WebSocket] 请求被中断:', payload.request_id);
                const request = this.pendingRequests.get(payload.request_id);
                if (request) {
                    // 清除超时定时器
                    if (request.timeoutId) {
                        clearTimeout(request.timeoutId);
                    }
                    // 调用完成回调（标记为中断）
                    if (request.onComplete) {
                        request.onComplete({
                            ...data,
                            interrupted: true
                        });
                    }
                    this.pendingRequests.delete(payload.request_id);
                }
                return;
            }
            
            this._handleResponse(data);
            return;
        }
        
        // ... 其他消息处理 ...
    }
}
```

#### 3.4.3 AudioService 扩展

```javascript
class AudioService {
    /**
     * 停止所有音频播放
     */
    stopAllPlayback() {
        console.log('[AudioService] 停止所有音频播放');
        
        // 停止流式播放器
        if (this.streamingPlayer) {
            this.streamingPlayer.stop();
        }
        
        // 停止当前播放
        if (this.currentPlayingMessageId) {
            this.stopPlayback();
        }
        
        // 停止 AudioContext
        if (this.audioContext && this.audioContext.state === 'running') {
            this.audioContext.suspend();
        }
    }
}
```

#### 3.4.4 UI 交互

在 ChatWindow 中添加打断逻辑：

```javascript
class ChatWindow {
    /**
     * 用户开始输入时自动打断
     */
    onUserStartInput() {
        // 如果正在接收响应，自动打断
        if (messageService.isReceivingResponse) {
            console.log('[ChatWindow] 用户开始输入，自动打断当前响应');
            messageService.interruptCurrentRequest('USER_NEW_INPUT');
        }
    }
    
    /**
     * VAD 检测到语音开始时自动打断
     */
    onVADSpeechStart() {
        // 如果正在接收响应，自动打断
        if (messageService.isReceivingResponse) {
            console.log('[ChatWindow] VAD检测到语音，自动打断当前响应');
            messageService.interruptCurrentRequest('USER_NEW_INPUT');
        }
        
        // ... 创建新的语音消息 ...
    }
}
```

---

## 四、实现细节

### 4.1 取消传播

#### 4.1.1 LLM 生成取消

```python
async def stream_generate(self, user_input: str, session_id: str, cancel_event: asyncio.Event = None):
    """支持取消的流式生成"""
    
    async for chunk in self.llm_client.stream_chat(...):
        # 检查取消信号
        if cancel_event and cancel_event.is_set():
            logger.llm.info("LLM generation cancelled")
            break
        
        yield chunk
```

#### 4.1.2 TTS 合成取消

```python
async def stream_synthesize(self, text: str, cancel_event: asyncio.Event = None):
    """支持取消的流式合成"""
    
    async for audio_chunk in self.tts_client.synthesize_stream(text):
        # 检查取消信号
        if cancel_event and cancel_event.is_set():
            logger.tts.info("TTS synthesis cancelled")
            break
        
        yield audio_chunk
```

### 4.2 资源清理

#### 4.2.1 服务端清理

```python
finally:
    # 清理活跃请求
    active_requests.pop(request_id, None)
    
    # 清理语音缓冲
    voice_buffer.pop(request_id, None)
    
    # 释放 LLM/TTS 资源
    # ...
```

#### 4.2.2 客户端清理

```javascript
// 清理 pending requests
this.pendingRequests.delete(requestId);

// 清理音频缓冲
this.audioChunks = [];

// 重置状态
this.isReceivingResponse = false;
this.currentRequestId = null;
```

### 4.3 边界情况处理

#### 4.3.1 请求已完成

如果打断信号到达时请求已完成，服务端返回：

```json
{
  "interrupted_request_ids": [],
  "status": "FAILED",
  "message": "请求已完成，无法中断"
}
```

#### 4.3.2 网络延迟

客户端发送打断信号后，可能仍会收到几帧旧响应：

```javascript
// 客户端忽略已打断请求的响应
if (this.interruptedRequests.has(payload.request_id)) {
    console.debug('[WebSocket] 忽略已打断请求的响应');
    return;
}
```

#### 4.3.3 并发请求

如果允许并发请求，打断时需要指定 `interrupt_request_id`：

```javascript
// 打断特定请求
await this.wsClient.sendInterrupt(specificRequestId, 'USER_NEW_INPUT');

// 打断所有请求
await this.wsClient.sendInterrupt(null, 'USER_NEW_INPUT');
```

---

## 五、协议更新

### 5.1 更新 CommunicationProtocol_CS.md

#### 5.1.1 新增 C→S 消息类型

在 4.1 节增加：

| msg_type | 说明 |
|----------|------|
| INTERRUPT | 中断当前请求 |

#### 5.1.2 新增 S→C 消息类型

在 5.1 节增加：

| msg_type | 说明 |
|----------|------|
| INTERRUPT_ACK | 中断确认 |

#### 5.1.3 扩展 RESPONSE payload

在 5.3 节增加字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| interrupted | boolean | 否 | 是否被中断 |
| interrupt_reason | string | 否 | 中断原因 |

---

## 六、实施计划

### 6.1 阶段一：协议扩展（1天）

- [ ] 更新 `CommunicationProtocol_CS.md`
- [ ] 定义 INTERRUPT 和 INTERRUPT_ACK 消息格式
- [ ] 扩展 RESPONSE 增加中断标记

### 6.2 阶段二：服务端实现（2-3天）

- [ ] 实现活跃请求管理（`active_requests`）
- [ ] 实现 `_handle_interrupt()` 处理器
- [ ] 修改 `process_text_request()` 支持取消
- [ ] 修改 `CommandGenerator.stream_generate()` 支持取消
- [ ] 修改 `UnifiedTTSService.stream_synthesize()` 支持取消
- [ ] 添加资源清理逻辑
- [ ] 单元测试

### 6.3 阶段三：客户端实现（2-3天）

- [ ] 扩展 `WebSocketClient.sendInterrupt()`
- [ ] 扩展 `MessageService.interruptCurrentRequest()`
- [ ] 扩展 `AudioService.stopAllPlayback()`
- [ ] 修改 `ChatWindow` 添加自动打断逻辑
- [ ] 处理中断响应和状态清理
- [ ] UI 测试

### 6.4 阶段四：集成测试（1-2天）

- [ ] 文本消息打断测试
- [ ] 语音消息打断测试
- [ ] 并发请求打断测试
- [ ] 边界情况测试
- [ ] 性能测试

### 6.5 阶段五：文档和优化（1天）

- [ ] 更新 API 文档
- [ ] 添加使用示例
- [ ] 性能优化
- [ ] 代码审查

**总计：7-10 天**

---

## 七、优势与风险

### 7.1 优势

1. **用户体验提升**：实现自然的对话打断，符合人类对话习惯
2. **资源节约**：及时停止不需要的计算，节省 LLM/TTS 成本
3. **响应速度**：用户新输入能立即得到处理
4. **向后兼容**：不影响现有功能，可选启用

### 7.2 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 取消不及时 | 仍产生部分无用计算 | 在关键点检查取消信号 |
| 状态不一致 | 客户端和服务端状态不同步 | 使用确认机制（INTERRUPT_ACK） |
| 网络延迟 | 打断信号延迟到达 | 客户端忽略已打断请求的响应 |
| 资源泄漏 | 未正确清理资源 | 使用 try-finally 确保清理 |

---

## 八、后续优化

### 8.1 智能打断

- 检测用户输入意图，判断是否需要打断
- 例如：用户说"等等"、"停"时自动打断

### 8.2 打断恢复

- 保存被打断的上下文
- 用户可以选择"继续上一个话题"

### 8.3 优先级队列

- 支持请求优先级
- 高优先级请求可以抢占低优先级请求

### 8.4 部分打断

- 只打断语音流，保留文本流
- 或只打断 TTS，保留 LLM 生成

---

## 九、总结

本方案通过引入 **INTERRUPT** 消息类型和 **协作式取消机制**，实现了用户优先的对话打断功能。核心设计包括：

1. **协议层**：新增 INTERRUPT/INTERRUPT_ACK 消息，扩展 RESPONSE 增加中断标记
2. **服务端**：活跃请求管理 + asyncio.Event 取消传播
3. **客户端**：自动打断检测 + 音频停止 + 状态清理

该方案在保持向后兼容的同时，显著提升了用户体验，使对话交互更加自然流畅。

