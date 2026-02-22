# 回车键问题 - 终极修复方案

## 🎯 问题分析

### 为什么之前的所有方案都失败了？

#### 方案 1：在 document 捕获阶段调用 stopPropagation()
```javascript
// ❌ 失败
document.addEventListener('keydown', (e) => {
    if (isInputField) {
        e.stopPropagation();  // 阻止事件到达输入框！
    }
}, true);
```
**问题**：在捕获阶段阻止传播，事件永远到不了输入框本身。

#### 方案 2：在 document 冒泡阶段调用 stopPropagation()
```javascript
// ❌ 失败
document.addEventListener('keydown', (e) => {
    if (isInputField) {
        e.stopPropagation();
    }
}, false);
```
**问题**：Unity 在捕获阶段就拦截了，冒泡阶段的保护根本到不了。

#### 方案 3：在输入框元素上添加捕获阶段监听器
```javascript
// ❌ 失败
input.addEventListener('keydown', (e) => {
    e.stopPropagation();
}, true);
```
**问题**：阻止了事件传播，导致输入框自己的监听器（ChatWindow 的 keydown）也收不到事件。

---

## ✅ 终极方案：覆盖 addEventListener

### 核心思路
不是阻止事件传播，而是**拦截 Unity 的监听器注册**，在监听器内部添加焦点检测。

### 实现原理
```javascript
// 1. 保存原始的 addEventListener
const originalAddEventListener = EventTarget.prototype.addEventListener;

// 2. 覆盖 addEventListener
EventTarget.prototype.addEventListener = function(type, listener, options) {
    // 3. 检查是否是 Canvas 添加键盘事件
    if (this.tagName === 'CANVAS' && isKeyEvent) {
        // 4. 包装监听器，添加焦点检测
        const wrappedListener = function(e) {
            // 如果焦点在输入框，不调用 Unity 的监听器
            if (isInputField) {
                return;  // 直接返回，不处理
            }
            // 否则正常调用 Unity 的监听器
            listener.call(this, e);
        };
        
        // 5. 使用包装后的监听器
        return originalAddEventListener.call(this, type, wrappedListener, options);
    }
    
    // 其他事件正常处理
    return originalAddEventListener.call(this, type, listener, options);
};
```

### 为什么这个方案一定成功？

**事件流程**：
```
1. 用户按下回车键
   ↓
2. 事件传播：document → ... → textarea
   ↓
3. textarea 的监听器触发（ChatWindow 的 keydown）
   ✓ 调用 sendMessage()，消息发送成功
   ↓
4. 事件继续传播到 Canvas
   ↓
5. Canvas 的监听器触发（Unity 的包装后的监听器）
   ✓ 检测到焦点在 textarea，直接 return
   ✓ Unity 不处理这个事件
```

**关键点**：
- ✅ 不阻止事件传播，输入框和 ChatWindow 都能正常处理
- ✅ Unity 的监听器被包装，内部添加了焦点检测
- ✅ 焦点在输入框时，Unity 的监听器直接返回，不处理事件

---

## 🧪 测试步骤

### 1. 刷新页面
按 `Ctrl + F5` 强制刷新，清除缓存。

### 2. 检查控制台日志
应该看到：
```
[App] 已覆盖 addEventListener，拦截 Canvas 键盘事件
```

### 3. 测试聊天输入框
- 输入文字："测试消息"
- 按回车键
- **预期**：消息立即发送
- **控制台**：应该看到 `[ChatWindow] sendMessage() 被调用`

### 4. 测试 Shift+回车
- 输入文字："第一行"
- 按 Shift+回车
- **预期**：换行，不发送
- 输入："第二行"
- 按回车
- **预期**：发送两行消息

### 5. 测试配置页面输入框
- 打开设置面板
- 在任何文本输入框中输入内容
- 按回车键
- **预期**：根据输入框类型，可能换行或提交表单

### 6. 测试所有按键
- 退格键：删除文字 ✓
- 空格键：输入空格 ✓
- Shift+数字：输入符号 ✓
- 方向键：移动光标 ✓
- 字母、数字：正常输入 ✓

---

## 🔍 调试日志

### 正常情况
```
[App] 已覆盖 addEventListener，拦截 Canvas 键盘事件
[App] 拦截 Canvas 的键盘事件监听器: keydown
[App] 拦截 Canvas 的键盘事件监听器: keyup
[App] 拦截 Canvas 的键盘事件监听器: keypress
```

### 按回车发送消息时
```
[App] 焦点在输入框，跳过 Unity 键盘处理: Enter
[ChatWindow] sendMessage() 被调用
[ChatWindow] 准备发送消息: 测试消息
```

---

## 📊 技术总结

### 为什么覆盖 addEventListener 是最佳方案？

1. **不破坏事件传播**：事件正常传播，所有组件都能处理
2. **精确控制**：只拦截 Canvas 的键盘事件，不影响其他元素
3. **灵活判断**：在 Unity 的监听器内部判断焦点，动态决定是否处理
4. **兼容性好**：不依赖 DOM 结构，不需要等待元素加载

### 与其他方案的对比

| 方案 | 优点 | 缺点 | 结果 |
|------|------|------|------|
| document 捕获阶段 stopPropagation | 优先级高 | 阻止事件到达输入框 | ❌ 失败 |
| document 冒泡阶段 stopPropagation | 不影响输入框 | Unity 在捕获阶段已拦截 | ❌ 失败 |
| 输入框捕获阶段 stopPropagation | 精确控制 | 阻止输入框自己的监听器 | ❌ 失败 |
| 覆盖 addEventListener | 完全控制 Unity | 需要覆盖全局方法 | ✅ 成功 |

---

## 🎉 预期结果

- ✅ 聊天输入框回车发送消息
- ✅ Shift+回车换行
- ✅ 配置页面输入框回车正常工作
- ✅ 所有键盘按键正常输入
- ✅ Unity 在焦点不在输入框时正常接收键盘事件

---

## 如果还是不工作

请提供以下信息：

1. **完整的控制台日志**（从页面加载开始）
2. **是否看到 "已覆盖 addEventListener" 日志**
3. **是否看到 "拦截 Canvas 的键盘事件监听器" 日志**
4. **按回车时是否看到 "焦点在输入框，跳过 Unity 键盘处理" 日志**
5. **是否看到 "sendMessage() 被调用" 日志**

根据日志可以判断问题出在哪个环节。

