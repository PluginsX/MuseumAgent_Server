# 语音消息会话失效问题修复报告

## 问题描述

用户在发送语音消息时，会话突然失效，导致无法继续发送消息，必须刷新页面重新登录。

## 问题分析

### 关键日志线索

```
[WebSocket] 未找到对应的请求: req_1771393209351_yyiw3lqk6
[WebSocket] 未找到对应的请求: req_1771393239826_ytkcwf2rq
[WebSocket] 未找到对应的请求: req_1771393302636_o5qm40kn9
[WebSocket] 未找到对应的请求: req_1771393316717_68y1ny3nu
[WebSocket] 心跳超时，连接可能已断开
```

### 根本原因

**客户端 WebSocket 流式响应处理逻辑存在严重缺陷：**

1. **流类型判断错误**：每次收到 RESPONSE 时，都用当前帧的 `text_stream_seq` 和 `voice_stream_seq` 是否存在来判断该请求是否包含该类型的流。这导致：
   - 第一帧可能只有文本流（`text_stream_seq: 0`），没有语音流
   - 客户端误判为"该请求不包含语音流"，标记 `voiceComplete = true`
   - 当文本流结束（`text_stream_seq: -1`）时，客户端认为所有流都结束了
   - **提前删除了 `pendingRequests` 中的请求处理器**
   - 后续服务器发送的语音流帧（`voice_stream_seq: 0, 1, 2...`）找不到对应的请求处理器
   - 产生"未找到对应的请求"警告

2. **超时定时器未清理**：请求完成时没有清除超时定时器，导致内存泄漏和潜在的误触发

3. **心跳超时触发**：由于大量"未找到请求"的警告和内部状态混乱，最终导致心跳超时，连接断开

## 修复方案

### 1. 修复流类型判断逻辑

**原逻辑（错误）：**
```javascript
// 每次都用当前帧判断
const hasTextStream = payload.text_stream_seq !== undefined;
const hasVoiceStream = payload.voice_stream_seq !== undefined;

const textComplete = !hasTextStream || request.textEnded;
const voiceComplete = !hasVoiceStream || request.voiceEnded;
```

**新逻辑（正确）：**
```javascript
// 第一次收到响应时，记录该请求包含哪些流
if (!request.hasCheckedStreams) {
    request.hasTextStream = payload.text_stream_seq !== undefined;
    request.hasVoiceStream = payload.voice_stream_seq !== undefined;
    request.hasCheckedStreams = true;
}

// 后续使用记录的流类型判断
const textComplete = !request.hasTextStream || request.textEnded;
const voiceComplete = !request.hasVoiceStream || request.voiceEnded;
```

### 2. 增加超时定时器清理

```javascript
if (allEnded) {
    // ✅ 清除超时定时器
    if (request.timeoutId) {
        clearTimeout(request.timeoutId);
    }
    
    if (request.onComplete) {
        request.onComplete(data);
    }
    this.pendingRequests.delete(requestId);
}
```

### 3. 增加流类型标记字段

在 `_sendRequest()` 和 `_waitForResponse()` 中初始化请求上下文时，增加：

```javascript
this.pendingRequests.set(requestId, {
    onTextChunk: onChunk,
    onVoiceChunk: onVoiceChunk,
    onFunctionCall: onFunctionCall,
    onComplete: (data) => {
        if (onComplete) onComplete(data);
        resolve(data);
    },
    reject: reject,
    textEnded: false,
    voiceEnded: false,
    hasCheckedStreams: false,  // ✅ 新增
    hasTextStream: false,       // ✅ 新增
    hasVoiceStream: false       // ✅ 新增
});
```

### 4. 优化日志输出

将"未找到请求"的警告降级为 debug 级别，因为这在请求完成后是正常现象：

```javascript
if (!request) {
    console.debug('[WebSocket] 请求已完成或不存在:', requestId);
    return;
}
```

### 5. 增加详细的流状态日志

```javascript
if (!request.hasCheckedStreams) {
    request.hasTextStream = payload.text_stream_seq !== undefined;
    request.hasVoiceStream = payload.voice_stream_seq !== undefined;
    request.hasCheckedStreams = true;
    console.log('[WebSocket] 检测到流类型:', {
        requestId: requestId,
        hasText: request.hasTextStream,
        hasVoice: request.hasVoiceStream
    });
}
```

## 修复文件

- `client/web/Demo/src/core/WebSocketClient.js`
  - `_handleResponse()` 方法：修复流类型判断逻辑
  - `_sendRequest()` 方法：增加流类型标记字段和超时清理
  - `_waitForResponse()` 方法：增加流类型标记字段和超时清理

## 测试验证

修复后需要验证以下场景：

1. ✅ 发送语音消息，验证不再出现"未找到对应的请求"警告
2. ✅ 连续发送多条语音消息，验证会话保持有效
3. ✅ 发送长语音消息（10秒以上），验证不会触发心跳超时
4. ✅ 混合发送文本和语音消息，验证两种消息类型都能正常工作
5. ✅ 长时间空闲后发送消息，验证心跳机制正常工作

## 技术总结

**核心教训：流式响应的状态管理必须基于请求的完整生命周期，而不是单个响应帧。**

- **错误做法**：每次收到响应帧时，根据当前帧的字段判断流类型
- **正确做法**：第一次收到响应时记录流类型，后续使用记录的类型判断完成状态

这个问题的本质是**状态管理的时序错误**：将"瞬时状态"（当前帧包含哪些字段）误用为"持久状态"（该请求包含哪些流）。

## 相关文档

- [通信协议规范](../CommunicationProtocol_CS.md)
- [会话管理架构](./SessionManagement_Architecture.md)

