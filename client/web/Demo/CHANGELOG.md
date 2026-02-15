# 更新日志

## 2026-02-16 - 重大功能更新

### 新增功能

#### 1. 设置面板
- 在聊天界面右上角添加了设置按钮（⚙️）
- 点击后打开侧边栏配置面板
- 支持实时修改配置，立即生效

#### 2. 客户端基本信息配置
- **Platform**: 客户端平台类型（WEB/APP/MINI_PROGRAM/TV）
- **RequireTTS**: 是否要求服务器用语音回复（默认：true）
- **AutoPlay**: 收到语音消息是否自动播放（默认：true）
- **FunctionCalling**: JSON格式的函数定义，支持实时编辑

#### 3. VAD（语音活动检测）配置
- **EnableVAD**: 是否启用VAD（默认：true）
- **Silence Threshold**: 静音阈值（0-1，默认：0.01）
- **Silence Duration**: 静音持续时长（毫秒，默认：1500）
- **Speech Threshold**: 语音阈值（0-1，默认：0.05）
- **Min Speech Duration**: 最小语音持续时长（毫秒，默认：300）
- **Pre-Speech Padding**: 语音前填充（毫秒，默认：300）
- **Post-Speech Padding**: 语音后填充（毫秒，默认：500）

### 功能优化

#### 1. 消息气泡创建策略
现在三类消息气泡完全独立创建：
- **流式文字消息**: 同批流数据共用一个气泡，实时更新内容
- **流式语音消息**: 同批流数据共用一个气泡，显示语音时长
- **函数调用消息**: 每个函数调用独立创建气泡

#### 2. VAD控制逻辑
- **不启用VAD**: 点击语音按钮后直接进入实时语音采集并发送，停止时结束
- **启用VAD**: 点击语音按钮后实时采集音频，但由VAD模块控制何时开始/停止发送
  - VAD根据配置参数自动检测语音开始和结束
  - 自动添加语音前后填充，确保语音完整性
  - 过滤掉过短的语音片段

#### 3. 语音消息时长显示
- 发送的语音消息显示实际发出的语音总时长
- 接收的语音消息显示服务器返回的语音时长
- 时长格式：MM:SS

### 技术改进

1. **状态管理优化**: 
   - 添加了 `session.autoPlay` 配置
   - 添加了 `recording.vadParams` 详细参数
   - 默认启用 RequireTTS 和 AutoPlay

2. **消息服务重构**:
   - 分离文本、语音、函数调用的回调处理
   - 每种类型的响应创建独立的消息气泡
   - 正确计算和传递语音时长

3. **音频服务增强**:
   - 新增 `startRecordingWithVAD()` 方法
   - 实现完整的VAD检测逻辑
   - 支持语音前后填充和最小时长过滤

4. **WebSocket客户端优化**:
   - 正确传递所有回调函数（onChunk, onVoiceChunk, onFunctionCall）
   - 分离文本流和语音流的处理逻辑

### 文件变更

- 新增: `src/components/SettingsPanel.js` - 设置面板组件
- 修改: `src/components/ChatWindow.js` - 添加设置按钮和VAD支持
- 修改: `src/components/MessageBubble.js` - 优化语音时长显示
- 修改: `src/services/MessageService.js` - 重构消息气泡创建策略
- 修改: `src/services/AudioService.js` - 添加VAD支持
- 修改: `src/core/StateManager.js` - 添加配置参数
- 修改: `src/core/WebSocketClient.js` - 优化回调传递
- 修改: `src/styles.css` - 添加设置面板样式

### 使用说明

1. 启动应用后登录
2. 点击右上角的⚙️按钮打开设置面板
3. 根据需要调整各项配置
4. 配置修改后立即生效，无需重启
5. 使用语音功能时，VAD会自动检测语音开始和结束

