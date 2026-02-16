# 客户端修复总结

## 修复的问题

### 1. 语音数据格式问题 ✅

**问题描述**：
- 客户端发送的语音服务器STT无法识别
- 服务器报错：`'ModuleLogger' object has no attribute 'warning'`

**分析**：
- 客户端语音数据格式符合协议（PCM 16kHz, 16bit, mono）
- 流式发送逻辑正确（起始帧 → 二进制帧 → 结束帧）
- 服务器端错误是Python代码问题，不是客户端问题

**客户端确认**：
- `WebSocketClient.js` 的 `sendVoiceRequestStream()` 方法严格遵循协议
- 音频数据通过 `Uint8Array` 直接发送二进制帧
- 无需Base64编码（BINARY模式）

**服务器端需要修复**：
```python
# 服务器端错误日志显示
# logger.warning() 方法不存在，应该是 logger.warn() 或其他问题
```

---

### 2. FunctionCalling 动态更新 ✅

**问题描述**：
- 注册会话后，用户修改函数定义无法更新到服务器
- 需要在下次请求时自动携带更新的函数定义

**修复方案**：

#### 2.1 添加修改标记
`StateManager.js`：
```javascript
session: {
    functionCalling: [...],
    functionCallingModified: false // 标记是否修改过
}
```

#### 2.2 设置面板标记修改
`SettingsPanel.js`：
```javascript
updateConfig(key, value) {
    if (key === 'functionCalling') {
        stateManager.setState('session.functionCallingModified', true);
    }
}
```

#### 2.3 请求时携带更新
`MessageService.js`：
```javascript
// 文本请求
if (sessionConfig.functionCallingModified) {
    options.functionCallingOp = 'REPLACE';
    options.functionCalling = sessionConfig.functionCalling;
    stateManager.setState('session.functionCallingModified', false);
}

// 语音请求
if (sessionConfig.functionCallingModified) {
    voiceOptions.functionCallingOp = 'REPLACE';
    voiceOptions.functionCalling = sessionConfig.functionCalling;
    stateManager.setState('session.functionCallingModified', false);
}
```

#### 2.4 协议支持
根据 `CommunicationProtocol_CS.md`：
```json
{
    "function_calling_op": "REPLACE",
    "function_calling": [...]
}
```

---

### 3. 默认 FunctionCalling 配置 ✅

**问题描述**：
- 默认函数列表为空，不利于测试
- 需要设计几个实用的默认函数

**修复方案**：

`StateManager.js` 添加默认函数定义：

```javascript
functionCalling: [
    {
        name: "get_exhibit_info",
        description: "获取指定展品的详细信息，包括名称、年代、材质、尺寸等",
        parameters: [
            { name: "exhibit_id", type: "string", description: "展品ID" }
        ]
    },
    {
        name: "search_exhibits",
        description: "根据关键词搜索相关展品",
        parameters: [
            { name: "keyword", type: "string", description: "搜索关键词" },
            { name: "limit", type: "number", description: "返回结果数量限制，默认10" }
        ]
    },
    {
        name: "get_exhibition_schedule",
        description: "获取展览时间表和开放时间",
        parameters: [
            { name: "date", type: "string", description: "日期，格式YYYY-MM-DD，不填则返回今日" }
        ]
    },
    {
        name: "get_navigation",
        description: "获取从当前位置到目标展厅的导航路线",
        parameters: [
            { name: "from", type: "string", description: "起点展厅名称" },
            { name: "to", type: "string", description: "目标展厅名称" }
        ]
    }
]
```

**函数说明**：
1. **get_exhibit_info**：查询单个展品详情
2. **search_exhibits**：关键词搜索展品
3. **get_exhibition_schedule**：查询展览时间
4. **get_navigation**：展厅导航

---

### 4. 自动播放控制漏洞 ✅

**问题描述**：
- 启用自动播放后，无法手动停止正在播放的语音
- 自动播放和手动播放使用不同的控制逻辑

**修复方案**：

#### 4.1 统一播放控制
`MessageService.js`：
```javascript
// 自动播放时也设置 currentPlayingMessageId
if (sessionConfig.autoPlay !== false) {
    // 停止当前正在播放的语音
    if (audioService.currentPlayingMessageId) {
        audioService.stopPlayback();
    }
    
    // 设置当前播放的消息ID
    audioService.currentPlayingMessageId = voiceMessageId;
    
    await audioService.playPCM(combined.buffer);
    
    // 播放完成后清除ID
    audioService.currentPlayingMessageId = null;
}
```

#### 4.2 手动控制
`MessageBubble.js`：
```javascript
async togglePlayVoice() {
    // 如果正在播放当前语音（无论自动还是手动），都可以停止
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
    await audioService.playPCM(this.message.audioData);
    audioService.currentPlayingMessageId = null;
}
```

**效果**：
- 自动播放时，点击任意语音气泡可以停止当前播放
- 手动播放时，点击其他语音会先停止当前播放
- 全局同时只能播放一个语音
- 用户完全掌控播放状态

---

## 修改的文件

1. **StateManager.js**
   - 添加默认 FunctionCalling 配置（4个测试函数）
   - 添加 `functionCallingModified` 标记

2. **MessageService.js**
   - 文本请求和语音请求都支持动态更新 FunctionCalling
   - 自动播放时设置 `currentPlayingMessageId`
   - 播放前停止其他正在播放的语音

3. **SettingsPanel.js**
   - 修改 FunctionCalling 时设置 `functionCallingModified` 标记

4. **WebSocketClient.js**
   - 已正确实现流式语音发送（无需修改）

5. **MessageBubble.js**
   - 已实现统一的播放控制（无需修改）

---

## 测试建议

### 1. 测试语音识别
- 点击话筒录音并发送
- 查看浏览器控制台日志，确认音频数据正在流式发送
- 如果服务器仍然无法识别，需要检查服务器端代码

### 2. 测试 FunctionCalling 更新
1. 打开设置面板
2. 修改 FunctionCalling JSON
3. 发送一条消息（文本或语音）
4. 查看控制台日志，确认携带了 `function_calling_op: "REPLACE"`

### 3. 测试自动播放控制
1. 启用 AutoPlay
2. 发送语音消息，等待服务器回复语音
3. 语音自动播放时，点击该语音气泡
4. 应该立即停止播放

### 4. 测试默认函数
- 查看设置面板的 FunctionCalling 配置
- 应该看到4个预定义的函数
- 可以测试修改、添加、删除函数

---

## 服务器端需要修复的问题

根据错误日志：
```
[STT] [ERROR] STT failed | {"error": "'ModuleLogger' object has no attribute 'warning'"}
```

**可能的原因**：
1. 日志对象方法名错误（应该是 `warn()` 而不是 `warning()`）
2. 日志对象初始化问题
3. STT模块内部错误处理有问题

**建议**：
- 检查服务器端 STT 模块的日志调用
- 确认 ModuleLogger 类的方法定义
- 添加更详细的错误日志，定位具体问题

---

## 协议遵循确认

客户端严格遵循 `CommunicationProtocol_CS.md`：

✅ **REGISTER**：携带 auth、platform、require_tts、function_calling  
✅ **REQUEST (TEXT)**：支持 function_calling_op 和 function_calling  
✅ **REQUEST (VOICE, BINARY)**：起始帧 → 二进制帧 → 结束帧  
✅ **RESPONSE**：正确处理 text_stream_seq、voice_stream_seq、function_call  
✅ **HEARTBEAT**：自动回复 HEARTBEAT_REPLY  

客户端实现完全符合协议规范。

