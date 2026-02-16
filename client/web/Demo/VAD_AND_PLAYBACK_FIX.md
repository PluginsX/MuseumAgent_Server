# VAD模式和语音播放功能修复

## 修复的问题

### 1. VAD模式下气泡创建时机错误
**问题描述**：
- 启用VAD时，点击话筒按钮后立即创建气泡
- 应该等VAD检测到人声活性后才创建气泡

**修复方案**：
- 修改 `ChatWindow.js` 的 `toggleVoiceRecording()` 方法
- VAD模式：点击按钮后只启动录音监听，不创建气泡
- 当VAD检测到语音开始时，触发 `onSpeechStart` 回调创建气泡并开始流式发送
- 当VAD检测到语音结束时，触发 `onSpeechEnd` 回调自动停止录音

### 2. VAD自动停止录音
**问题描述**：
- VAD检测到静音持续时长后应自动停止录音
- 之前只是重置VAD状态，没有真正停止录音

**修复方案**：
- 修改 `AudioService.js` 的 `_processVAD()` 方法
- 添加 `speechEndCallback` 回调参数
- 检测到语音结束时调用回调，触发自动停止录音

### 3. 语音播放功能完全失效
**问题描述**：
- 发送的语音消息没有保存音频数据，无法播放
- 接收的语音消息也无法点击播放
- 缺少全局播放控制，无法实现"同时只播放一个语音"

**修复方案**：

#### 3.1 保存发送的语音数据
- 修改 `ChatWindow.js`：在停止录音时合并所有音频块
- 更新消息时同时保存 `duration` 和 `audioData`

#### 3.2 修复播放控制逻辑
- 修改 `MessageBubble.js`：
  - 将 `playVoice()` 改为 `togglePlayVoice()`
  - 所有语音消息（发送和接收）都可点击播放
  - 点击正在播放的语音时停止播放
  - 点击其他语音时先停止当前播放

#### 3.3 全局播放状态管理
- 修改 `AudioService.js`：
  - 添加 `currentPlayingMessageId` 属性
  - 播放时记录消息ID
  - 停止时清除消息ID
  - 发送 `AUDIO_PLAY_END` 事件通知所有气泡更新状态

#### 3.4 播放状态显示
- 修改 `MessageBubble.js`：
  - 添加 `updatePlayingState()` 方法
  - 播放时图标显示为 ⏸️
  - 停止时图标显示为 🎤
  - 监听全局播放结束事件更新状态

## 修改的文件

### 1. ChatWindow.js
```javascript
// VAD模式：等检测到语音后才创建气泡
if (vadEnabled) {
    await audioService.startRecordingWithVAD(
        vadParams,
        // onSpeechStart: 创建气泡
        async () => {
            const stream = new ReadableStream({...});
            this.currentVoiceMessageId = await messageService.sendVoiceMessageStream(stream);
        },
        // onAudioData: 实时发送
        (audioData) => {...},
        // onSpeechEnd: 自动停止
        () => {
            setTimeout(() => this.toggleVoiceRecording(), 100);
        }
    );
}

// 停止录音时保存音频数据
const combinedAudioData = ...; // 合并所有音频块
stateManager.updateMessage(this.currentVoiceMessageId, {
    duration: duration,
    audioData: combinedAudioData
});
```

### 2. AudioService.js
```javascript
// 添加当前播放消息ID
this.currentPlayingMessageId = null;

// VAD方法签名改为接收三个回调
async startRecordingWithVAD(vadParams, onSpeechStart, onAudioData, onSpeechEnd)

// VAD处理逻辑
_processVAD(floatData, pcmBuffer) {
    if (检测到语音开始) {
        this.vadState.speechStartCallback(); // 创建气泡
    }
    if (检测到语音结束) {
        this.vadState.speechEndCallback(); // 自动停止
    }
}

// 停止播放时清除ID
stopPlayback() {
    this.currentPlayingMessageId = null;
    eventBus.emit(Events.AUDIO_PLAY_END);
}
```

### 3. MessageBubble.js
```javascript
// 所有语音都可点击播放
renderVoiceContent() {
    voiceElement.addEventListener('click', () => {
        this.togglePlayVoice();
    });
}

// 切换播放/停止
async togglePlayVoice() {
    // 如果正在播放当前语音，停止
    if (audioService.currentPlayingMessageId === this.message.id) {
        audioService.stopPlayback();
        return;
    }
    
    // 停止其他正在播放的语音
    if (audioService.currentPlayingMessageId) {
        audioService.stopPlayback();
    }
    
    // 播放当前语音
    audioService.currentPlayingMessageId = this.message.id;
    this.updatePlayingState(true);
    await audioService.playPCM(this.message.audioData);
    audioService.currentPlayingMessageId = null;
    this.updatePlayingState(false);
}

// 更新播放状态图标
updatePlayingState(isPlaying) {
    icon.textContent = isPlaying ? '⏸️' : '🎤';
}
```

## 功能说明

### 不启用VAD模式
1. 点击话筒按钮 → 立即创建语音气泡
2. 开始录音并实时流式发送
3. 再次点击按钮 → 停止录音，更新时长和音频数据

### 启用VAD模式
1. 点击话筒按钮 → 开始监听，不创建气泡
2. VAD检测到人声 → 创建气泡并开始流式发送
3. VAD检测到静音持续时长 → 自动停止录音

### 语音播放
1. 点击任意语音气泡 → 开始播放，图标变为 ⏸️
2. 播放时点击同一气泡 → 停止播放
3. 播放时点击其他气泡 → 停止当前播放，播放新的语音
4. 全局同时只能播放一个语音

## 测试建议

1. **测试VAD模式**：
   - 启用VAD，点击话筒，保持安静 → 不应创建气泡
   - 开始说话 → 应立即创建气泡
   - 停止说话1.5秒 → 应自动停止录音

2. **测试非VAD模式**：
   - 不启用VAD，点击话筒 → 立即创建气泡
   - 再次点击 → 停止录音

3. **测试语音播放**：
   - 点击发送的语音 → 应能播放
   - 点击接收的语音 → 应能播放
   - 播放时点击其他语音 → 应停止当前播放
   - 播放时图标应显示为 ⏸️

