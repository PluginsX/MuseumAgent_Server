# 紧急 Bug 修复清单

## 问题汇总

### 1. 退格键失效（SettingsPanel 和 ChatWindow 输入框）
**原因**：ControlButton 的 Pointer Events 调用了全局 `preventDefault()`，阻止了所有键盘事件

**修复方案**：
- ControlButton 的 `preventDefault()` 只应该在按钮自身上生效
- 不应该影响其他元素的输入

### 2. ChatWindow 按钮无效（语音按钮、发送按钮）
**原因**：
- ChatWindow 可能没有正确初始化
- 事件监听器可能被阻止
- 容器问题导致按钮不可点击

**修复方案**：
- 检查 ChatWindow 的 render 和事件绑定
- 确保按钮在 FloatingPanel 中正确显示

### 3. 消息气泡都在右侧（用户侧）
**原因**：AgentController 中消息类型判断错误，所有消息的 `type` 都是 'sent'

**修复方案**：
- 修复 AgentController 中的消息类型判断
- TEXT_CHUNK、VOICE_CHUNK、FUNCTION_CALL 应该是 'received'
- MESSAGE_SENT 才是 'sent'

### 4. 语音按钮状态不同步
**原因**：
- ControlButton 和 ChatWindow 的语音按钮独立监听 client 事件
- 没有统一的状态管理

**修复方案**：
- 两个按钮都监听相同的 client 事件（RECORDING_START、RECORDING_STOP）
- 确保事件监听器正确绑定

### 5. 历史消息不显示
**原因**：
- ChatWindow 的 `loadExistingMessages()` 可能没有正确执行
- 或者 AgentController 的消息数组为空

**修复方案**：
- 检查 ChatWindow 初始化时是否调用了 `loadExistingMessages()`
- 确保 AgentController 正确记录了历史消息

## 修复优先级

1. **P0**：消息气泡都在右侧 - 这是最严重的问题
2. **P0**：退格键失效 - 影响所有输入
3. **P1**：ChatWindow 按钮无效 - 无法发送消息
4. **P1**：语音按钮状态不同步 - 用户体验问题
5. **P2**：历史消息不显示 - 功能缺失

## 详细修复步骤

### 修复 1：消息类型判断错误

在 `AgentController.js` 中，所有接收的消息应该是 `type: 'received'`：

```javascript
// ❌ 错误
this.addMessage({
    type: 'sent',  // 错误！
    content: data.chunk,
    messageType: 'text'
});

// ✅ 正确
this.addMessage({
    type: 'received',  // 正确！
    content: data.chunk,
    messageType: 'text'
});
```

### 修复 2：ControlButton preventDefault 范围

ControlButton 的事件处理不应该影响全局：

```javascript
// ❌ 当前代码会阻止所有事件
this.element.addEventListener('pointerdown', (e) => {
    e.preventDefault();  // 这会影响全局！
    e.stopPropagation();
});

// ✅ 修复：只在按钮上阻止
this.element.addEventListener('pointerdown', (e) => {
    // 只阻止按钮自身的默认行为，不影响其他元素
    if (e.target === this.element) {
        e.preventDefault();
    }
    e.stopPropagation();
});
```

### 修复 3：ChatWindow 容器问题

FloatingPanel 可能没有正确附加 ChatWindow 的元素：

```javascript
// 检查 FloatingPanel.attachComponent() 方法
// 确保 ChatWindow 的 container 被正确设置
```

### 修复 4：语音按钮状态同步

确保两个按钮都监听相同的事件：

```javascript
// ControlButton.js
this.client.on(Events.RECORDING_START, () => {
    this.setIcon('⏹️');
    this.element.classList.add('recording');
});

// ChatWindow.js
this.client.on(Events.RECORDING_START, () => {
    this.voiceButton.textContent = '⏹️';
    this.voiceButton.classList.add('recording');
});
```

### 修复 5：历史消息加载

确保 ChatWindow 初始化时加载历史消息：

```javascript
init() {
    this.render();
    this.bindEvents();
    this.subscribeToAgentController();
    this.loadExistingMessages();  // 确保调用
}
```

## 测试检查点

修复后需要验证：

- [ ] 输入框可以正常使用退格键删除文字
- [ ] 发送的消息显示在右侧（蓝色背景）
- [ ] 接收的消息显示在左侧（白色背景）
- [ ] ChatWindow 的发送按钮可以点击
- [ ] ChatWindow 的语音按钮可以点击
- [ ] 两个语音按钮状态同步（同时变成录音状态）
- [ ] 打开 ChatWindow 时显示历史消息
- [ ] 三种消息类型（文本、语音、函数调用）都能正确显示

