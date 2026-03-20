# 浮动面板尺寸调整功能 — 实施方案

## 一、现有窗口尺寸控制分析

### 当前实现方式
- **窗口模式**：固定尺寸 `80% × 80%`，最大 `800px × 600px`，居中定位 `translate(-50%, -50%)`
- **全屏模式**：`100vw × 100vh`，无约束
- **尺寸控制**：仅通过 `toggleWindowMode()` 在两种预设模式间切换
- **拖拽**：仅支持位置拖拽（header 区域），不支持尺寸调整

### 关键代码位置
- `FloatingPanel.js`：`createElement()` 设置初始尺寸，`toggleWindowMode()` 切换模式
- `styles.css`：`.floating-panel.window-mode` 定义窗口模式样式
- 拖拽逻辑：`enableDrag()` 方法处理位置移动

---

## 二、需求理解与设计

### 核心需求
1. **九宫格操作手柄**：围绕窗口外扩 8 个可拖拽区域
   ```
   [左上] [上] [右上]
   [左] [窗口] [右]
   [左下] [下] [右下]
   ```

2. **手柄功能分类**
   - **四角**（左上、右上、左下、右下）：拖拽时同时调整宽高
   - **四边**（上、下、左、右）：拖拽时仅调整单个方向尺寸

3. **手柄尺寸控制**
   - 统一参数：`resizeHandleWidth`（像素，默认 8px）
   - 手柄区域完全不重叠，环绕窗口外部
   - 手柄 DOM 与窗口内容完全隔离，无交互冲突

4. **视觉反馈**
   - 默认：透明（`opacity: 0`）
   - Hover：半透明可见（`opacity: 0.3~0.5`）
   - 拖拽中：高亮（`opacity: 0.7`）

5. **约束条件**
   - 最小窗口尺寸：`300px × 200px`
   - 最大窗口尺寸：`viewport.width × viewport.height`
   - 窗口始终保持在视口内

---

## 三、实施方案

### 3.1 DOM 结构设计

```
.floating-panel (主容器)
├── .floating-panel-resize-handles (手柄容器，position: absolute)
│   ├── .resize-handle.corner.top-left
│   ├── .resize-handle.edge.top
│   ├── .resize-handle.corner.top-right
│   ├── .resize-handle.edge.left
│   ├── .resize-handle.edge.right
│   ├── .resize-handle.corner.bottom-left
│   ├── .resize-handle.edge.bottom
│   └── .resize-handle.corner.bottom-right
├── .floating-panel-header
├── .floating-panel-content
```

### 3.2 CSS 样式设计

```css
/* 手柄容器 */
.floating-panel-resize-handles {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;  /* 默认不拦截事件 */
}

/* 通用手柄样式 */
.resize-handle {
    position: absolute;
    background: rgba(255, 107, 2, 0.3);  /* 默认透明 */
    opacity: 0;
    transition: opacity 0.2s ease;
    pointer-events: auto;  /* 手柄本身可交互 */
    cursor: default;  /* 由 JS 动态设置 */
}

/* 四角手柄 */
.resize-handle.corner {
    width: var(--handle-width, 8px);
    height: var(--handle-width, 8px);
}

.resize-handle.corner.top-left {
    top: calc(var(--handle-width, 8px) * -1);
    left: calc(var(--handle-width, 8px) * -1);
    cursor: nwse-resize;
}

.resize-handle.corner.top-right {
    top: calc(var(--handle-width, 8px) * -1);
    right: calc(var(--handle-width, 8px) * -1);
    cursor: nesw-resize;
}

.resize-handle.corner.bottom-left {
    bottom: calc(var(--handle-width, 8px) * -1);
    left: calc(var(--handle-width, 8px) * -1);
    cursor: nesw-resize;
}

.resize-handle.corner.bottom-right {
    bottom: calc(var(--handle-width, 8px) * -1);
    right: calc(var(--handle-width, 8px) * -1);
    cursor: nwse-resize;
}

/* 四边手柄 */
.resize-handle.edge {
    background: rgba(255, 107, 2, 0.2);
}

.resize-handle.edge.top {
    top: calc(var(--handle-width, 8px) * -1);
    left: var(--handle-width, 8px);
    right: var(--handle-width, 8px);
    height: var(--handle-width, 8px);
    cursor: ns-resize;
}

.resize-handle.edge.bottom {
    bottom: calc(var(--handle-width, 8px) * -1);
    left: var(--handle-width, 8px);
    right: var(--handle-width, 8px);
    height: var(--handle-width, 8px);
    cursor: ns-resize;
}

.resize-handle.edge.left {
    left: calc(var(--handle-width, 8px) * -1);
    top: var(--handle-width, 8px);
    bottom: var(--handle-width, 8px);
    width: var(--handle-width, 8px);
    cursor: ew-resize;
}

.resize-handle.edge.right {
    right: calc(var(--handle-width, 8px) * -1);
    top: var(--handle-width, 8px);
    bottom: var(--handle-width, 8px);
    width: var(--handle-width, 8px);
    cursor: ew-resize;
}

/* Hover 状态 */
.resize-handle:hover {
    opacity: 0.5;
    background: rgba(255, 107, 2, 0.5);
}

/* 拖拽中状态 */
.resize-handle.resizing {
    opacity: 0.7;
    background: rgba(255, 107, 2, 0.7);
}
```

### 3.3 JavaScript 实现逻辑

#### 3.3.1 初始化手柄
在 `FloatingPanel.createElement()` 中：
1. 创建手柄容器 `.floating-panel-resize-handles`
2. 创建 8 个手柄元素（四角 + 四边）
3. 为每个手柄绑定 `pointerdown` 事件

#### 3.3.2 拖拽逻辑
```javascript
// 伪代码
enableResize() {
    for each handle {
        handle.addEventListener('pointerdown', (e) => {
            // 1. 记录初始状态：窗口尺寸、位置、鼠标位置
            // 2. 设置 handle.classList.add('resizing')
            // 3. 绑定 document.pointermove 和 document.pointerup
            
            // pointermove 中：
            // - 计算鼠标移动距离
            // - 根据手柄类型（角/边）计算新尺寸
            // - 应用约束（最小/最大尺寸、视口边界）
            // - 更新窗口 width/height/left/top
            
            // pointerup 中：
            // - 移除 'resizing' 类
            // - 解绑 pointermove/pointerup
        });
    }
}
```

#### 3.3.3 尺寸计算规则

| 手柄 | 拖拽方向 | 尺寸变化 | 位置变化 |
|------|---------|---------|---------|
| 左上 | 左上 | w↓, h↓ | left↑, top↑ |
| 上 | 上 | h↓ | top↑ |
| 右上 | 右上 | w↑, h↓ | top↑ |
| 左 | 左 | w↓ | left↑ |
| 右 | 右 | w↑ | - |
| 左下 | 左下 | w↓, h↑ | left↑ |
| 下 | 下 | h↑ | - |
| 右下 | 右下 | w↑, h↑ | - |

#### 3.3.4 约束应用
```javascript
// 最小尺寸
newWidth = Math.max(300, newWidth);
newHeight = Math.max(200, newHeight);

// 最大尺寸
newWidth = Math.min(viewport.width, newWidth);
newHeight = Math.min(viewport.height, newHeight);

// 视口边界
newLeft = Math.max(0, Math.min(newLeft, viewport.width - newWidth));
newTop = Math.max(0, Math.min(newTop, viewport.height - newHeight));
```

### 3.4 与现有功能的集成

#### 3.4.1 与拖拽的兼容性
- 现有拖拽：header 区域移动位置
- 新增调整：手柄区域调整尺寸
- **隔离**：两者通过不同的事件源区分，无冲突

#### 3.4.2 与模式切换的兼容性
- **窗口模式**：显示手柄，支持调整
- **全屏模式**：隐藏手柄（`display: none`），禁用调整
- 切换时保存用户调整的尺寸到 `localStorage`

#### 3.4.3 与双击切换的兼容性
- 双击 header 切换模式时，手柄自动隐藏/显示
- 手柄拖拽中不会触发双击

### 3.5 配置参数

在 `FloatingPanel` 构造函数中新增：
```javascript
this.resizeHandleWidth = options.resizeHandleWidth || 8;  // 手柄宽度（像素）
this.minWindowWidth = options.minWindowWidth || 300;      // 最小窗口宽
this.minWindowHeight = options.minWindowHeight || 200;    // 最小窗口高
this.resizable = options.resizable !== false;             // 是否启用调整
```

---

## 四、实施步骤

### Phase 1：基础架构（1-2 小时）
1. 在 `FloatingPanel.js` 中新增 `createResizeHandles()` 方法
2. 在 `createElement()` 中调用 `createResizeHandles()`
3. 在 CSS 中定义手柄样式（8 个手柄 + hover/resizing 状态）
4. 验证 DOM 结构和样式正确渲染

### Phase 2：拖拽逻辑（2-3 小时）
1. 实现 `enableResize()` 方法
2. 为每个手柄绑定 `pointerdown` 事件
3. 实现 `pointermove` 中的尺寸计算
4. 实现约束逻辑（最小/最大尺寸、视口边界）
5. 测试各手柄的拖拽效果

### Phase 3：集成与优化（1-2 小时）
1. 与模式切换集成（全屏时隐藏手柄）
2. 保存/恢复用户调整的尺寸
3. 与现有拖拽逻辑兼容性测试
4. 性能优化（RAF、防抖等）

### Phase 4：测试与打磨（1 小时）
1. 边界情况测试（极小/极大窗口、视口边界）
2. 触屏设备测试
3. 视觉反馈优化（hover/resizing 动画）

---

## 五、风险与注意事项

### 5.1 技术风险
- **事件冲突**：手柄拖拽与 header 拖拽的事件源区分
  - 解决：通过 `e.target` 判断，手柄事件不冒泡到 header
- **性能**：频繁的 DOM 更新和重排
  - 解决：使用 RAF 批量更新，避免频繁重排

### 5.2 UX 风险
- **手柄可发现性**：用户可能不知道手柄存在
  - 解决：默认 hover 时显示，可考虑首次加载时提示
- **误触发**：鼠标靠近边界时误触发调整
  - 解决：手柄宽度适中（8px），且需要明确的 pointerdown

### 5.3 兼容性
- **全屏模式**：手柄应完全隐藏，不占用空间
- **响应式**：手柄宽度在移动端可能需要调整（更大便于触摸）

---

## 六、预期效果

### 用户交互流程
1. 打开聊天/设置窗口（窗口模式）
2. 鼠标靠近窗口边缘 → 手柄显示（半透明）
3. 拖拽手柄 → 窗口尺寸实时调整
4. 释放鼠标 → 尺寸保存到 localStorage
5. 刷新页面 → 恢复用户调整的尺寸

### 视觉效果
- 手柄默认不可见，hover 时显示
- 拖拽中手柄高亮
- 窗口尺寸平滑变化（无闪烁）
- 光标变化提示可调整方向

---

## 七、后续扩展

1. **双击手柄重置尺寸**：双击任意手柄恢复默认尺寸
2. **快捷键调整**：Ctrl+← → 快速调整宽度
3. **吸附对齐**：靠近视口边界时自动对齐
4. **记忆多个尺寸预设**：保存常用尺寸配置

