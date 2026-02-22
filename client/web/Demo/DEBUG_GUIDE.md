# 调试指南 - 如何使用控制台日志排查问题

## 本次修复概述

已修复 **ChatWindow 按钮无响应** 的核心问题，并添加了详细的调试日志系统。

### 核心问题
ChatWindow 的 `show()` 方法会调用 `render()` 重新创建 DOM 元素，但事件监听器只在初始化时绑定一次，导致新创建的按钮没有事件处理器。

### 解决方案
- 将事件绑定拆分为两部分：
  - `bindUIEvents()`: 每次渲染后绑定按钮和输入框事件
  - `bindClientEvents()`: 只在初始化时订阅一次客户端事件
- 在 `render()` 末尾自动调用 `bindUIEvents()`

## 测试步骤

### 1. 准备工作
1. 刷新页面（Ctrl+F5 强制刷新）
2. 打开浏览器开发者工具（F12）
3. 切换到 Console（控制台）标签

### 2. 测试聊天窗口按钮

#### 测试发送按钮
1. 长按控制按钮，选择"聊天"打开聊天窗口
2. 在输入框输入任意文字
3. 点击"发送"按钮
4. **预期日志**：
   ```
   [ChatWindow] 发送按钮被点击
   [ChatWindow] sendMessage() 被调用
   [ChatWindow] 准备发送消息: xxx
   [ChatWindow] 配置更新: {}
   [ChatWindow] 消息发送成功
   [AgentController] 消息发送: {id: "...", text: "...", type: "text"}
   [AgentController] 创建发送消息: {id: "...", type: "sent", ...}
   [ChatWindow] 创建消息气泡: {id: "...", type: "sent", messageType: "text", ...}
   [MessageBubble] 渲染气泡: {id: "...", type: "sent", isSent: true, ...}
   ```

#### 测试语音按钮
1. 点击语音按钮（🎤）
2. **预期日志**：
   ```
   [ChatWindow] 语音按钮被点击，当前录音状态: false
   [ChatWindow] toggleVoiceRecording() 被调用，当前状态: false
   [ChatWindow] 开始录音
   [ChatWindow] 录音配置更新: {}
   [ChatWindow] 录音已开始
   [ChatWindow] 录音开始，更新按钮状态
   [ControlButton] 录音开始，更新按钮状态  // ControlButton 也会同步
   ```
3. 再次点击停止录音
4. **预期日志**：
   ```
   [ChatWindow] 语音按钮被点击，当前录音状态: true
   [ChatWindow] toggleVoiceRecording() 被调用，当前状态: true
   [ChatWindow] 停止录音
   [ChatWindow] 录音停止，更新按钮状态
   [ControlButton] 录音停止，更新按钮状态  // ControlButton 也会同步
   ```

### 3. 测试消息气泡位置

#### 发送的消息（应在右侧）
1. 发送一条文本消息
2. 查看控制台日志中的 `[MessageBubble] 渲染气泡`
3. **预期**：`type: "sent", isSent: true`
4. **视觉检查**：消息气泡应该在右侧，蓝色背景

#### 接收的消息（应在左侧）
1. 等待服务器回复
2. 查看控制台日志
3. **预期日志**：
   ```
   [AgentController] 文本块: {messageId: "...", chunk: "..."}
   [AgentController] 创建接收消息（文本）: {id: "...", type: "received", ...}
   [ChatWindow] 创建消息气泡: {id: "...", type: "received", messageType: "text", ...}
   [MessageBubble] 渲染气泡: {id: "...", type: "received", isSent: false, ...}
   ```
4. **视觉检查**：消息气泡应该在左侧，白色背景

### 4. 测试退格键

#### ChatWindow 输入框
1. 在聊天输入框输入一些文字
2. 按 Backspace 键删除
3. **预期**：文字可以正常删除

#### SettingsPanel 文本框
1. 长按控制按钮，选择"设置"
2. 展开任意配置区域（如"智能体角色配置"）
3. 在文本框中输入或修改文字
4. 按 Backspace 键删除
5. **预期**：文字可以正常删除

### 5. 测试语音按钮同步

1. 打开聊天窗口
2. 点击聊天窗口的语音按钮开始录音
3. **预期**：
   - 聊天窗口的语音按钮变为 ⏹️
   - 控制按钮（如果可见）也应变为 ⏹️
   - 控制台显示两个组件都收到 RECORDING_START 事件
4. 关闭聊天窗口
5. 点击控制按钮开始录音
6. 再次打开聊天窗口
7. **预期**：聊天窗口的语音按钮应显示为 ⏹️（录音中状态）

## 日志前缀说明

- `[ChatWindow]`: 聊天窗口组件
- `[MessageBubble]`: 消息气泡组件
- `[AgentController]`: 智能体控制器（消息管理）
- `[ControlButton]`: 控制按钮组件
- `[SettingsPanel]`: 设置面板组件
- `[FloatingPanel]`: 浮动面板容器
- `[UnityContainer]`: Unity 容器组件

## 常见问题排查

### 问题：点击按钮没有反应

**检查日志**：
- 如果没有看到 `[ChatWindow] 发送按钮被点击` 或 `[ChatWindow] 语音按钮被点击`
- 说明事件监听器没有绑定成功

**可能原因**：
1. `render()` 后没有调用 `bindUIEvents()`
2. 按钮元素被其他元素遮挡（检查 z-index）
3. 按钮的 pointer-events 被禁用

**解决方法**：
- 检查 `[ChatWindow] 界面渲染完成，按钮已绑定事件` 日志是否出现
- 在浏览器开发者工具中检查按钮元素的事件监听器

### 问题：消息气泡全在右侧

**检查日志**：
- 查看 `[MessageBubble] 渲染气泡` 日志中的 `type` 和 `isSent` 字段
- 如果接收的消息显示 `isSent: true`，说明 `type` 传递错误

**可能原因**：
1. `AgentController` 创建消息时 `type` 字段设置错误
2. `ChatWindow.createMessageBubble()` 传递数据时丢失了 `type` 字段

**解决方法**：
- 检查 `[AgentController] 创建接收消息` 日志，确认 `type: "received"`
- 检查 `[ChatWindow] 创建消息气泡` 日志，确认 `type` 正确传递

### 问题：退格键无效

**检查**：
1. 点击输入框，确保输入框获得焦点（有光标闪烁）
2. 检查是否有其他元素捕获了键盘事件

**可能原因**：
1. ControlButton 的 pointer capture 影响（已修复）
2. Unity Canvas 捕获键盘事件
3. 某个父元素的 keydown 监听器调用了 preventDefault

**解决方法**：
- 在控制台运行：`document.activeElement` 查看当前焦点元素
- 检查是否是输入框元素

## 提交问题报告

如果问题仍然存在，请提供以下信息：

1. **完整的控制台日志**（从页面加载到问题出现）
2. **具体操作步骤**（一步一步描述如何重现问题）
3. **预期行为** vs **实际行为**
4. **浏览器信息**（Chrome/Edge/Firefox 版本）
5. **截图或录屏**（如果可能）

将这些信息整理后反馈，我会根据日志进行进一步分析和修复。

