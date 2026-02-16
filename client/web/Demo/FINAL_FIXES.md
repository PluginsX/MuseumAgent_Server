# 最终修复总结

## 修复的问题

### 1. FunctionCalling 默认配置 ✅

**问题**：
- 默认函数列表为空或使用博物馆相关函数
- 需要改为桌面智能宠物相关的函数

**修复方案**：

在 `StateManager.js` 中设置默认的桌面宠物函数：

```javascript
functionCalling: [
    {
        name: "play_animation",
        description: "播放指定的动画效果，让桌面宠物做出相应动作",
        parameters: [
            { name: "animation_name", type: "string", description: "动画名称，如：wave(挥手)、jump(跳跃)、dance(跳舞)、sleep(睡觉)、happy(开心)" }
        ]
    },
    {
        name: "change_expression",
        description: "改变桌面宠物的表情",
        parameters: [
            { name: "expression", type: "string", description: "表情类型，如：smile(微笑)、sad(伤心)、angry(生气)、surprised(惊讶)、love(爱心)" }
        ]
    },
    {
        name: "move_to_position",
        description: "移动桌面宠物到屏幕指定位置",
        parameters: [
            { name: "x", type: "number", description: "X坐标（像素）" },
            { name: "y", type: "number", description: "Y坐标（像素）" }
        ]
    },
    {
        name: "set_mood",
        description: "设置桌面宠物的心情状态",
        parameters: [
            { name: "mood", type: "string", description: "心情状态，如：happy(开心)、normal(正常)、tired(疲惫)、excited(兴奋)" },
            { name: "duration", type: "number", description: "持续时间（秒），默认60" }
        ]
    },
    {
        name: "speak_text",
        description: "让桌面宠物说出指定文字（显示气泡对话框）",
        parameters: [
            { name: "text", type: "string", description: "要说的文字内容" },
            { name: "duration", type: "number", description: "显示时长（秒），默认3" }
        ]
    }
]
```

**函数说明**：

1. **play_animation**：播放动画
   - 参数：animation_name（动画名称）
   - 示例：wave(挥手)、jump(跳跃)、dance(跳舞)、sleep(睡觉)、happy(开心)

2. **change_expression**：改变表情
   - 参数：expression（表情类型）
   - 示例：smile(微笑)、sad(伤心)、angry(生气)、surprised(惊讶)、love(爱心)

3. **move_to_position**：移动位置
   - 参数：x（X坐标）、y（Y坐标）
   - 示例：移动到屏幕指定位置

4. **set_mood**：设置心情
   - 参数：mood（心情状态）、duration（持续时间）
   - 示例：happy(开心)、normal(正常)、tired(疲惫)、excited(兴奋)

5. **speak_text**：说话
   - 参数：text（文字内容）、duration（显示时长）
   - 示例：显示气泡对话框

### 2. FunctionCalling 动态更新 ✅

**问题**：
- 用户在设置面板修改函数定义后，没有发送到服务器

**修复方案**：

#### 2.1 标记修改
`SettingsPanel.js` 已实现：
```javascript
updateConfig(key, value) {
    if (key === 'functionCalling') {
        stateManager.setState('session.functionCallingModified', true);
        console.log('FunctionCalling已修改，将在下次请求时更新到服务器');
    }
}
```

#### 2.2 发送更新
`MessageService.js` 已实现：
```javascript
// 文本请求
const options = { ... };

// 检查是否需要更新 FunctionCalling
if (sessionConfig.functionCallingModified) {
    options.functionCallingOp = 'REPLACE';
    options.functionCalling = sessionConfig.functionCalling;
    // 重置修改标记
    stateManager.setState('session.functionCallingModified', false);
}

await this.wsClient.sendTextRequest(text, options);

// 语音请求同理
```

**工作流程**：
```
用户修改函数定义
    ↓
设置 functionCallingModified = true
    ↓
用户发送消息（文本或语音）
    ↓
检测到 functionCallingModified = true
    ↓
在请求中添加：
  - function_calling_op: "REPLACE"
  - function_calling: [新的函数列表]
    ↓
发送到服务器
    ↓
重置 functionCallingModified = false
```

### 3. 流式语音播放修复 ✅

**问题**：
- `MessageService.js` 中有一处代码错误
- 使用了已废弃的 API：`audioService.streamingPlayers.get(voiceMessageId)`

**修复方案**：

修改 `sendVoiceMessageStream` 的 `onComplete` 回调：

```javascript
// 错误代码（已修复）
if (sessionConfig.autoPlay !== false) {
    const player = audioService.streamingPlayers.get(voiceMessageId);  // ❌ 错误
    if (player) {
        player.end();
    }
}

// 正确代码
if (sessionConfig.autoPlay !== false) {
    audioService.endStreamingMessage(voiceMessageId);  // ✅ 正确
}
```

**原因**：
- 之前将播放器改为单例模式
- `streamingPlayers` Map 已被移除
- 应该使用新的 API：`endStreamingMessage()`

## 验证流式播放

### 当前实现确认

#### MessageService.js - 文本请求
```javascript
onVoiceChunk: async (audioData, seq) => {
    if (!voiceMessageId) {
        voiceMessageId = this._generateMessageId();
        // 创建语音气泡
        stateManager.addMessage({ ... });
        
        // 如果启用自动播放，开始流式播放
        if (sessionConfig.autoPlay !== false) {
            await audioService.startStreamingMessage(voiceMessageId);  // ✅ 开始播放
        }
    }
    
    // 保存音频数据
    voiceChunks.push(audioData);
    
    // 如果启用自动播放，实时播放音频块
    if (sessionConfig.autoPlay !== false) {
        audioService.addStreamingChunk(voiceMessageId, audioData);  // ✅ 实时播放
    }
},

onComplete: async (data) => {
    // 合并所有数据（用于保存）
    const combined = combineAllChunks(voiceChunks);
    
    // 更新消息
    stateManager.updateMessage(voiceMessageId, {
        audioData: combined.buffer,
        duration: duration,
        isStreaming: false
    });
    
    // 通知播放器结束
    if (sessionConfig.autoPlay !== false) {
        audioService.endStreamingMessage(voiceMessageId);  // ✅ 结束播放
    }
}
```

#### MessageService.js - 语音请求
```javascript
// 完全相同的实现
onVoiceChunk: async (audioData, seq) => {
    // ... 同上
    if (sessionConfig.autoPlay !== false) {
        await audioService.startStreamingMessage(voiceMessageId);
        audioService.addStreamingChunk(voiceMessageId, audioData);
    }
},

onComplete: async (data) => {
    // ... 同上
    if (sessionConfig.autoPlay !== false) {
        audioService.endStreamingMessage(voiceMessageId);  // ✅ 已修复
    }
}
```

### 流式播放流程

```
服务器发送语音块1
    ↓
onVoiceChunk 回调
    ↓
第一次：startStreamingMessage(messageId)  ← 创建播放会话
    ↓
addStreamingChunk(messageId, audioData)  ← 立即播放
    ↓
服务器发送语音块2
    ↓
onVoiceChunk 回调
    ↓
addStreamingChunk(messageId, audioData)  ← 立即播放（无缝衔接）
    ↓
服务器发送语音块3
    ↓
onVoiceChunk 回调
    ↓
addStreamingChunk(messageId, audioData)  ← 立即播放（无缝衔接）
    ↓
...
    ↓
服务器发送完成
    ↓
onComplete 回调
    ↓
endStreamingMessage(messageId)  ← 结束播放会话
```

## 修改的文件

1. **src/core/StateManager.js**
   - 修改默认 `functionCalling` 为桌面宠物相关函数
   - 保留 `functionCallingModified` 标记

2. **src/services/MessageService.js**
   - 修复 `sendVoiceMessageStream` 的 `onComplete` 回调
   - 使用正确的 API：`audioService.endStreamingMessage()`

3. **src/components/SettingsPanel.js**
   - 已实现：修改函数时设置 `functionCallingModified` 标记

## 测试建议

### 测试1：默认函数
1. 打开设置面板
2. 查看 FunctionCalling 配置
3. 应该看到5个桌面宠物相关的函数

### 测试2：函数动态更新
1. 修改 FunctionCalling JSON
2. 发送一条消息
3. 查看控制台日志，应该看到携带 `function_calling_op: "REPLACE"`

### 测试3：流式播放
1. 启用自动播放
2. 发送消息
3. 应该在 < 300ms 内听到声音
4. 查看控制台日志：
   - "开始流式播放: msg_xxx"
   - "接收音频块: xxx 字节"
   - "播放音频块，时长: xxx 秒"
   - "流式消息结束: msg_xxx"

## 总结

✅ **FunctionCalling 默认配置**：设置了5个桌面宠物相关的函数
✅ **FunctionCalling 动态更新**：修改后下次请求自动发送到服务器
✅ **流式语音播放**：修复了API调用错误，确保实时播放

所有功能现在都已正确实现！

