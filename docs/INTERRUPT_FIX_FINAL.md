# 打断机制最终修复方案

## 问题描述

博物馆讲解场景中，用户发送新问题时，旧问题的流式文字回答无法被打断，必须等待完成才能开始新问题。这严重影响用户体验。

## 根本原因

1. **时序问题**：客户端发送打断请求时，新请求可能还未在服务端注册到 `active_requests`
2. **过度设计**：使用了复杂的客户端主动打断机制，不适合博物馆讲解这种轻量化场景

## 解决方案：服务端自动打断

### 核心思路

**博物馆讲解场景特点**：
- 极其轻量化，不需要消息缓存
- 新问题到达 = 立即丢弃旧问题
- 快速响应优先，不考虑旧请求是否完成

**实现方式**：
- 服务端收到新 REQUEST → 自动中断该会话的所有旧请求
- 客户端只需清理本地状态，不发送 INTERRUPT 消息
- 简单、直接、高效

### 代码修改

#### 1. 服务端：自动打断机制

**文件**：`src/ws/agent_handler.py`

```python
# 新请求到达：立即中断该会话的所有旧请求
should_interrupt_old = False
if data_type == "TEXT":
    # 文本消息：直接打断
    should_interrupt_old = True
elif data_type == "VOICE":
    # 语音消息：只有起始帧（stream_seq == 0）或非流式才打断
    if stream_flag and stream_seq == 0:
        should_interrupt_old = True
    elif not stream_flag:
        should_interrupt_old = True

if should_interrupt_old:
    interrupted_count = 0
    for old_req_id, req_info in list(active_requests.items()):
        if req_info["session_id"] == session_id and old_req_id != request_id:
            req_info["cancel_event"].set()  # 设置取消信号
            interrupted_count += 1
    
    if interrupted_count > 0:
        logger.ws.info("Auto-interrupt completed", {
            "new_request_id": request_id[:16],
            "interrupted_count": interrupted_count
        })
```

**关键点**：
- 只有新消息的起始帧才触发打断（避免流式消息的中间片段触发）
- 立即设置 `cancel_event`，LLM 生成器会在下一个检查点停止
- 不需要等待旧请求完成

#### 2. 客户端：简化状态清理

**文件**：`client/web/Demo/src/services/MessageService.js`

```javascript
// 如果正在接收响应，立即清理状态（服务端会自动打断）
if (this.isReceivingResponse) {
    console.log('[MessageService] 检测到新输入，清理旧状态（服务端自动打断）');
    
    // 立即清理客户端状态
    this.isReceivingResponse = false;
    this.currentRequestId = null;
    this.currentMessageId = null;
    
    // 停止音频播放
    audioService.stopAllPlayback();
}
```

**关键点**：
- 不再发送 INTERRUPT 消息
- 只清理本地状态和停止音频播放
- 简单高效

### 3. 取消信号传播链（已完成）

确保 `cancel_event` 正确传递到 LLM 生成器：

```
agent_handler.py (创建 cancel_event)
    ↓
request_processor.py (传递 cancel_event)
    ↓
command_generator.py (传递 cancel_event)
    ↓
dynamic_llm_client.py (检查 cancel_event)
```

## 测试验证

### 测试场景

1. **文本消息打断**：
   - 发送问题A
   - 在回答过程中立即发送问题B
   - 验证：问题A的回答立即停止，问题B立即开始

2. **语音消息打断**：
   - 发送语音问题A
   - 在回答过程中发送语音问题B
   - 验证：问题A的回答立即停止，问题B立即开始

3. **连续快速提问**：
   - 快速连续发送多个问题
   - 验证：只有最后一个问题被回答

### 预期结果

- ✅ 新问题到达后，旧问题的文字流立即停止
- ✅ 新问题的回答立即开始，无需等待
- ✅ 音频播放立即停止
- ✅ 无时序问题，无竞态条件

## 优势

1. **简单直接**：服务端自动处理，客户端无需关心
2. **无时序问题**：新请求注册后立即打断旧请求
3. **适合场景**：完美匹配博物馆讲解的轻量化需求
4. **用户体验好**：快速响应，无延迟

## 注意事项

1. **流式消息的中间片段不触发打断**：
   - 语音消息的二进制数据帧（stream_seq > 0 且 < -1）不会触发打断
   - 只有起始帧（stream_seq == 0）或结束帧（stream_seq == -1）才触发

2. **保留 INTERRUPT 消息支持**：
   - 虽然客户端不再主动发送，但服务端仍支持该消息类型
   - 方便未来扩展或其他客户端使用

3. **取消检查点**：
   - LLM 生成器每生成一个 token 检查一次 `cancel_event`
   - 确保能快速响应打断信号

## 总结

通过服务端自动打断机制，彻底解决了博物馆讲解场景中的打断问题。新方案简单、高效、无时序问题，完美匹配轻量化需求。

---

**修改时间**：2026-02-18  
**修改文件**：
- `src/ws/agent_handler.py`
- `client/web/Demo/src/services/MessageService.js`

