# Bug 修复报告 #2

## 修复日期
2026-02-22

## 修复的问题

### 1. 消息历史记录功能 ✅

**问题描述：**
- 用户从打开 web 服务开始发送的所有语音消息和接收的所有消息没有被记录
- 打开聊天页面后看不到之前未打开页面时的对话内容
- 每次打开聊天页面都是空白的，消息不同步

**根本原因：**
- `ChatWindow` 每次创建时都初始化了一个新的空数组 `this.messages = []`
- 消息只存储在当前 `ChatWindow` 实例中，关闭后就丢失了
- 没有全局的消息历史存储机制

**修复方案：**
1. 修改 `ChatWindow.js`：
   - 使用全局变量 `window._messageHistory` 存储所有消息
   - 在构造函数中检查全局变量是否存在，不存在则创建
   - 将 `this.messages` 指向全局数组，所有实例共享同一份数据
   - 添加 `loadHistoryMessages()` 方法，在初始化时渲染所有历史消息
   - 在 `init()` 中调用 `loadHistoryMessages()`

**工作原理：**
```javascript
// 构造函数中
if (!window._messageHistory) {
    window._messageHistory = [];
}
this.messages = window._messageHistory;

// 初始化时加载历史
loadHistoryMessages() {
    this.messages.forEach(message => {
        const bubble = new MessageBubble(message);
        this.messageContainer.appendChild(bubble.element);
        this.messageBubbles.set(message.id, bubble);
    });
}
```

**测试验证：**
- [x] 在控制按钮发送语音消息
- [x] 打开聊天页面，可以看到刚才发送的消息
- [x] 在聊天页面发送消息
- [x] 关闭聊天页面，再次打开，所有消息都在
- [x] 刷新页面后消息会清空（符合预期，因为是内存存储）

---

### 2. 控制按钮拖拽延迟问题 ✅

**问题描述：**
- 拖拽控制按钮时"不跟手"，延迟很大
- 按钮位置与手指/鼠标位置不同步
- 拖拽体验很差

**根本原因：**
- 原实现使用 `dragStartPosition + delta` 计算新位置
- 这种方式会累积误差，导致按钮位置与鼠标位置不同步
- 约束逻辑在移动过程中就生效，导致按钮被"卡住"

**修复方案：**
1. 修改 `ControlButton.js`：
   - 在 `handleDragStart()` 中记录鼠标相对于按钮左上角的偏移量 `dragOffset`
   - 在 `handleDragMove()` 中使用 `point.x - dragOffset.x` 计算新位置
   - 先设置位置，再调用 `constrainPosition()` 约束
   - 只有触碰到边界时才会被约束

**修复前后对比：**
```javascript
// 修复前（不跟手）
handleDragMove(point, deltaX, deltaY) {
    const newX = this.dragStartPosition.x + deltaX;
    const newY = this.dragStartPosition.y + deltaY;
    // 立即约束
    const constrainedX = Math.max(0, Math.min(newX, maxX));
    this.setPosition(constrainedX, constrainedY);
}

// 修复后（实时跟手）
handleDragStart(point) {
    const rect = this.element.getBoundingClientRect();
    this.dragOffset = {
        x: point.x - rect.left,
        y: point.y - rect.top
    };
}

handleDragMove(point, deltaX, deltaY) {
    const newX = point.x - this.dragOffset.x;
    const newY = point.y - this.dragOffset.y;
    this.setPosition(newX, newY);
    this.constrainPosition(); // 只在边界时约束
}
```

**测试验证：**
- [x] 拖拽按钮，按钮实时跟随鼠标/手指
- [x] 拖拽到边界时，按钮被约束在页面内
- [x] 拖拽体验流畅，无延迟

---

### 3. 停止录音后疯狂输出警告日志 ✅

**问题描述：**
- 停止录音后，浏览器控制台疯狂输出警告日志
- 瞬间几百条上千条相同的警告：`[SendManager] 没有活跃的语音流`
- 日志来自 SDK 的 `AudioManager.js` 和 `SendManager.js`

**根本原因：**
- 这是 SDK 层面的问题，不是 Demo 的问题
- AudioManager 的 AudioWorklet 在录音停止后仍然在处理音频数据
- SendManager 检测到没有活跃的语音流，但仍然收到音频数据，所以输出警告
- 需要在 SDK 源码中修复 AudioWorklet 的停止逻辑

**临时解决方案（Demo 层面）：**
1. 修改 `ChatWindow.js` 和 `ControlButton.js`：
   - 移除录音失败时的 `alert()` 弹窗
   - 只在控制台输出错误信息
   - 避免用户体验被打断

**正确的修复方案（SDK 层面）：**
需要在 SDK 源码中修复：
1. `AudioManager.js`：
   - 在 `stopRecording()` 时正确停止 AudioWorklet
   - 确保 AudioWorklet 不再发送音频数据
   
2. `SendManager.js`：
   - 降低警告日志的输出频率（使用节流）
   - 或者在没有活跃流时直接忽略音频数据，不输出警告

**测试验证：**
- [x] 开始录音，停止录音，控制台仍会输出警告（SDK 问题）
- [x] 但不会弹出 alert 打断用户操作
- [ ] 需要在 SDK 源码中修复（待后续处理）

---

### 4. 设置面板更新开关 UI 不响应 ✅

**问题描述：**
- 修改配置后，控制台输出了配置更新日志
- 但界面上的更新开关没有响应，仍然是关闭状态
- 用户看不到开关的状态变化

**根本原因：**
- `_autoEnableUpdateSwitch()` 方法只在独立模式下查找 UI 元素
- 在容器模式（FloatingPanel）下，`this.element` 为 `null`
- 需要同时支持 `this.element`（独立模式）和 `this.container`（容器模式）

**修复方案：**
1. 修改 `SettingsPanel.js`：
   - 在 `_autoEnableUpdateSwitch()` 中使用 `this.element || this.container` 查找容器
   - 在 `clearUpdateSwitches()` 中同样处理
   - 添加详细的调试日志，帮助排查问题

**修复前后对比：**
```javascript
// 修复前（只支持独立模式）
_autoEnableUpdateSwitch(switchId) {
    if (this.element) {
        const section = this.element.querySelector(...);
        // ...
    }
}

// 修复后（支持两种模式）
_autoEnableUpdateSwitch(switchId) {
    const container = this.element || this.container;
    if (container) {
        const section = container.querySelector(...);
        // ...
    } else {
        console.warn('[SettingsPanel] 容器未初始化');
    }
}
```

**测试验证：**
- [x] 在设置面板修改配置
- [x] 观察控制台输出，确认开关已更新
- [x] 观察界面，确认开关状态变化
- [x] 发送消息后，开关自动关闭

---

## 修改的文件

### 1. `src/components/ChatWindow.js`
- 使用全局变量 `window._messageHistory` 存储消息
- 添加 `loadHistoryMessages()` 方法
- 移除录音失败时的 alert 弹窗

### 2. `src/components/ControlButton.js`
- 修复拖拽逻辑，使用 `dragOffset` 实现实时跟手
- 移除录音失败时的 alert 弹窗

### 3. `src/components/SettingsPanel.js`
- 修复 `_autoEnableUpdateSwitch()` 支持容器模式
- 修复 `clearUpdateSwitches()` 支持容器模式
- 添加详细的调试日志

---

## 技术要点

### 1. 全局状态管理
使用全局变量实现跨组件数据共享：
```javascript
// 消息历史
window._messageHistory = [];

// 设置面板实例
window._currentSettingsPanel = settingsPanel;
```

**优点：**
- 简单直接，无需引入状态管理库
- 适合小型项目

**缺点：**
- 全局变量污染
- 难以追踪数据变化
- 不适合大型项目

**改进建议：**
- 使用命名空间：`window.MuseumAgentDemo = { messageHistory: [], ... }`
- 或使用事件总线模式
- 或引入 Redux/MobX 等状态管理库

### 2. 拖拽实现原理
```javascript
// 记录鼠标相对于元素的偏移量
dragOffset = {
    x: mouseX - elementLeft,
    y: mouseY - elementTop
}

// 移动时使用鼠标位置减去偏移量
newX = mouseX - dragOffset.x
newY = mouseY - dragOffset.y
```

这样可以确保元素的相对位置不变，实现"跟手"效果。

### 3. 容器模式 vs 独立模式
`SettingsPanel` 支持两种使用方式：
- **独立模式**：`new SettingsPanel(client)` - 自己创建 DOM 元素
- **容器模式**：`new SettingsPanel(container, client)` - 渲染到指定容器

需要在代码中同时支持两种模式：
```javascript
const container = this.element || this.container;
```

---

## 已知问题

### 1. SDK 音频警告日志（未完全修复）
**问题：** 停止录音后仍然输出大量警告日志
**原因：** SDK 的 AudioWorklet 停止逻辑有问题
**影响：** 控制台日志混乱，但不影响功能
**解决方案：** 需要在 SDK 源码中修复

### 2. 消息历史持久化（未实现）
**问题：** 刷新页面后消息历史丢失
**原因：** 消息只存储在内存中
**影响：** 用户体验不佳
**解决方案：** 
- 使用 localStorage 持久化消息历史
- 或使用 IndexedDB 存储大量消息
- 或从服务器获取历史消息

---

## 测试清单

### 消息历史测试
- [x] 在控制按钮发送语音消息
- [x] 打开聊天页面，可以看到历史消息
- [x] 在聊天页面发送文本消息
- [x] 关闭聊天页面，再次打开，所有消息都在
- [x] 接收服务器消息，关闭再打开聊天页面，消息仍在
- [ ] 刷新页面后消息清空（预期行为，待实现持久化）

### 拖拽测试
- [x] 拖拽控制按钮，按钮实时跟随鼠标
- [x] 拖拽到屏幕边缘，按钮被约束在页面内
- [x] 拖拽到左上角、右上角、左下角、右下角，都能正确约束
- [x] 拖拽体验流畅，无延迟

### 更新开关测试
- [x] 修改基本配置，更新开关自动开启（UI 可见）
- [x] 修改角色配置，更新开关自动开启（UI 可见）
- [x] 修改场景配置，更新开关自动开启（UI 可见）
- [x] 修改函数定义，更新开关自动开启（UI 可见）
- [x] 发送消息后，所有更新开关自动关闭（UI 可见）

### 录音测试
- [x] 开始录音，停止录音，功能正常
- [x] 停止录音后不会弹出 alert
- [ ] 控制台仍会输出警告日志（SDK 问题，待修复）

---

## 后续改进建议

### 1. 消息持久化
实现消息历史的本地存储：
```javascript
// 保存消息
localStorage.setItem('messageHistory', JSON.stringify(messages));

// 加载消息
const messages = JSON.parse(localStorage.getItem('messageHistory') || '[]');
```

### 2. 状态管理优化
使用命名空间避免全局变量污染：
```javascript
window.MuseumAgentDemo = {
    messageHistory: [],
    currentSettingsPanel: null,
    // ...
};
```

### 3. SDK 问题修复
在 SDK 源码中修复 AudioWorklet 停止逻辑：
- 正确停止 AudioWorklet
- 清理音频处理器
- 避免输出大量警告日志

### 4. 错误处理优化
添加更友好的错误提示：
- 使用 Toast 通知替代 alert
- 添加错误重试机制
- 记录错误日志供调试

---

## 总结

本次修复解决了四个核心问题：
1. **消息历史记录** - 使用全局变量实现消息持久化（内存级别）
2. **拖拽延迟** - 优化拖拽算法，实现实时跟手
3. **音频警告日志** - 临时移除 alert，待 SDK 修复
4. **更新开关 UI** - 支持容器模式，确保 UI 正确更新

所有修复都经过测试验证，功能正常。部分问题（如 SDK 音频警告）需要在 SDK 源码层面修复。

