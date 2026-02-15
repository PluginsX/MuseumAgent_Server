# 语音流式发送修复日志

## 问题描述
1. 客户端发送的语音消息时长显示为 00:00
2. 语音不是流式发送，而是预录制后整体发送
3. 服务器只在客户端结束录音时才收到数据并报STT错误

## 根本原因
原实现中，ChatWindow将所有音频数据收集到数组中，然后在停止录音时才创建ReadableStream并同步读取所有数据。这导致：
- 所有音频数据在停止录音时一次性发送
- 不是真正的流式传输
- 服务器无法实时接收音频数据

## 修复方案

### 1. 改为真正的流式传输
**ChatWindow.js**:
- 在开始录音时立即创建ReadableStream
- 保存stream controller引用
- 录音回调中实时调用`controller.enqueue()`推送数据
- 停止录音时调用`controller.close()`结束流

### 2. 实时发送音频数据
**WebSocketClient.js**:
- 在`sendVoiceRequestStream`中先发送起始帧
- 使用`reader.read()`循环实时读取流数据
- 每读取到一个chunk立即通过`ws.send()`发送
- 添加详细日志记录发送过程
- 最后发送结束帧

### 3. 正确计算和显示时长
**ChatWindow.js**:
- 保存当前语音消息ID
- 在停止录音时计算总时长（根据PCM数据大小）
- 更新消息气泡的duration字段

**MessageService.js**:
- `sendVoiceMessageStream`立即返回消息ID
- 不等待请求完成，允许异步处理响应

## 关键代码变更

### ChatWindow.js
```javascript
// 开始录音时
const stream = new ReadableStream({
    start: (controller) => {
        this.voiceStreamController = controller;
    }
});

// 立即开始发送
this.currentVoiceMessageId = await messageService.sendVoiceMessageStream(stream);

// 录音回调中实时推送
await audioService.startRecording((audioData) => {
    this.audioChunks.push(audioData);
    if (this.voiceStreamController) {
        this.voiceStreamController.enqueue(new Uint8Array(audioData));
    }
});

// 停止录音时
const duration = (totalBytes / 2) / 16000;
stateManager.updateMessage(this.currentVoiceMessageId, { duration });
this.voiceStreamController.close();
```

### WebSocketClient.js
```javascript
// 实时读取并发送
const reader = audioStream.getReader();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    // 立即发送
    if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(value);
        console.log('[WebSocket] 发送音频数据块:', value.byteLength, '字节');
    }
}
```

## 预期效果
1. ✅ 用户按下🎤后，音频数据实时发送到服务器
2. ✅ 服务器可以实时接收音频流并进行STT处理
3. ✅ 语音消息气泡正确显示实际录音时长
4. ✅ 控制台可以看到每个音频块的发送日志
5. ✅ VAD启用时，只有VAD检测到的语音部分会被发送

## 测试建议
1. 打开浏览器控制台
2. 点击🎤开始录音
3. 观察控制台输出：
   - 应该看到"流式传输已准备就绪"
   - 应该看到多条"实时发送音频数据"日志
   - 应该看到WebSocket发送日志
4. 点击⏹️停止录音
5. 检查语音消息气泡是否显示正确时长
6. 检查服务器日志是否实时接收到音频数据

## 服务器端注意事项
服务器端的STT错误 `'ModuleLogger' object has no attribute 'warning'` 是服务器代码的问题，需要在服务器端修复。客户端已经正确实现流式发送。

