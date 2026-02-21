# MuseumAgent Demo 升级计划

## 一、需求概述

### 1.1 升级目标
将当前的纯聊天窗口 Demo 升级为 Unity WebGL 主体 + 智能体辅助功能的混合应用。

### 1.2 核心变化
- **登录界面**：保持不变
- **主界面**：从聊天窗口改为全屏 Unity WebGL 应用
- **智能体功能**：从主界面降级为悬浮辅助功能
- **交互入口**：通过悬浮"控制按钮"访问智能体功能

---

## 二、功能需求

### 2.1 Unity WebGL 集成

#### 2.1.1 Unity 项目结构
- **源目录**：`E:\Project\Python\MuseumAgent_Server\client\web\Unity\build`
- **核心文件**：
  - `Build/` - Unity 构建产物（.data, .framework.js, .loader.js, .wasm）
  - `StreamingAssets/` - 流媒体资源（音频、视频）
  - `TemplateData/` - 模板资源（图标、样式、加载动画）
  - `index.html` - Unity 模板页面（需要抽离）
  - `main.js` - Unity 初始化脚本
  - `ServiceWorker.js` - PWA 服务工作线程
  - `manifest.webmanifest` - PWA 清单

#### 2.1.2 集成方案
1. **文件提取**：创建 `extract-unity.bat` 脚本，自动提取必要文件到 Demo 项目
2. **目标位置**：`Demo/unity/` 目录
3. **页面集成**：登录成功后加载 Unity Canvas，全屏显示
4. **层级关系**：Unity Canvas 作为底层，控制按钮覆盖在最上层

### 2.2 控制按钮（悬浮交互入口）

#### 2.2.1 视觉设计
- **形状**：正方形
- **尺寸**：边长 = min(vw, vh) 的比例，范围 30px - 100px
- **默认位置**：屏幕右下角
- **默认图标**：麦克风 🎤
- **层级**：z-index 最高，覆盖 Unity Canvas

#### 2.2.2 交互事件

##### 单击（Click）
- **功能**：开始/停止语音录制
- **逻辑**：与当前聊天窗口的语音按钮一致
- **VAD**：根据客户端配置决定是否启用
- **视觉反馈**：录制时图标变为 ⏹️，添加 `recording` 样式类

##### 拖拽（Drag）
- **功能**：移动控制按钮位置
- **约束**：按钮的 DOM Rect 边界必须在页面可视区域内
- **支持**：鼠标事件 + 触控事件
- **实现**：
  - `mousedown` / `touchstart` - 开始拖拽
  - `mousemove` / `touchmove` - 移动位置
  - `mouseup` / `touchend` - 结束拖拽

##### 长按（Long Press）
- **触发条件**：按下超过 500ms 且未移动
- **功能**：弹出菜单
- **菜单项**：
  - **设置** - 打开客户端配置页面
  - **聊天** - 打开聊天窗口页面
- **菜单方向**：根据按钮位置自动选择（上方/下方），选择空间最大的方向

#### 2.2.3 状态管理
- **默认状态**：显示，可交互
- **隐藏状态**：打开设置/聊天页面时自动隐藏
- **恢复显示**：关闭设置/聊天页面时自动显示

### 2.3 功能子页面

#### 2.3.1 设置页面
- **内容**：复用当前的 `SettingsPanel` 组件
- **显示方式**：全屏覆盖
- **头部按钮**：
  - 全屏按钮（保留）
  - **关闭按钮**（新增）- 位于全屏按钮右侧
- **关闭行为**：移除页面 + 显示控制按钮

#### 2.3.2 聊天页面
- **内容**：复用当前的 `ChatWindow` 组件
- **显示方式**：全屏覆盖
- **头部按钮**：
  - 全屏按钮（保留）
  - **关闭按钮**（新增）- 位于全屏按钮右侧
- **关闭行为**：移除页面 + 显示控制按钮

---

## 三、技术实现方案

### 3.1 项目结构调整

#### 3.1.1 新增目录
```
Demo/
├── unity/                    # Unity WebGL 资源（新增）
│   ├── Build/
│   ├── StreamingAssets/
│   ├── TemplateData/
│   ├── main.js
│   ├── ServiceWorker.js
│   └── manifest.webmanifest
├── src/
│   ├── components/
│   │   ├── ControlButton.js      # 控制按钮组件（新增）
│   │   ├── UnityContainer.js     # Unity 容器组件（新增）
│   │   ├── FloatingPanel.js      # 悬浮面板基类（新增）
│   │   ├── ChatWindow.js         # 聊天窗口（改造为悬浮面板）
│   │   ├── SettingsPanel.js      # 设置面板（改造为悬浮面板）
│   │   ├── LoginForm.js          # 登录表单（保持不变）
│   │   └── MessageBubble.js      # 消息气泡（保持不变）
│   ├── utils/
│   │   ├── dom.js                # DOM 工具（保持不变）
│   │   ├── audioPlayer.js        # 音频播放器（保持不变）
│   │   └── gesture.js            # 手势识别工具（新增）
│   ├── app.js                    # 应用入口（重构）
│   └── styles.css                # 样式表（扩展）
└── extract-unity.bat             # Unity 文件提取脚本（新增）
```

#### 3.1.2 文件依赖关系
```
app.js
├── LoginForm.js (登录阶段)
└── UnityContainer.js (登录后)
    ├── Unity WebGL (底层)
    └── ControlButton.js (顶层)
        ├── 单击 → 语音录制（直接调用 SDK）
        ├── 拖拽 → 位置移动（DOM 操作）
        └── 长按 → 菜单
            ├── 设置 → FloatingPanel(SettingsPanel)
            └── 聊天 → FloatingPanel(ChatWindow)
```

### 3.2 核心组件设计

#### 3.2.1 UnityContainer 组件
```javascript
class UnityContainer {
    constructor(container, client) {
        this.container = container;
        this.client = client;
        this.unityInstance = null;
        this.controlButton = null;
        this.currentPanel = null;
    }
    
    async init() {
        // 1. 加载 Unity WebGL
        await this.loadUnity();
        
        // 2. 创建控制按钮
        this.controlButton = new ControlButton(this.client, {
            onMenuSelect: (item) => this.handleMenuSelect(item)
        });
        
        // 3. 监听 Unity 事件
        this.bindUnityEvents();
    }
    
    async loadUnity() {
        // 动态加载 Unity loader
        // 创建 Unity Canvas
        // 初始化 Unity 实例
    }
    
    handleMenuSelect(item) {
        if (item === 'settings') {
            this.showSettingsPanel();
        } else if (item === 'chat') {
            this.showChatPanel();
        }
    }
    
    showSettingsPanel() {
        this.controlButton.hide();
        this.currentPanel = new FloatingPanel(SettingsPanel, {
            onClose: () => this.closePanel()
        });
    }
    
    showChatPanel() {
        this.controlButton.hide();
        this.currentPanel = new FloatingPanel(ChatWindow, {
            onClose: () => this.closePanel()
        });
    }
    
    closePanel() {
        if (this.currentPanel) {
            this.currentPanel.destroy();
            this.currentPanel = null;
        }
        this.controlButton.show();
    }
}
```

#### 3.2.2 ControlButton 组件
```javascript
class ControlButton {
    constructor(client, options) {
        this.client = client;
        this.options = options;
        this.element = null;
        this.isDragging = false;
        this.longPressTimer = null;
        this.menu = null;
        
        this.init();
    }
    
    init() {
        this.createElement();
        this.bindEvents();
        this.updateSize();
        this.setDefaultPosition();
    }
    
    createElement() {
        // 创建按钮 DOM
        // 设置样式和图标
    }
    
    bindEvents() {
        // 鼠标事件
        this.element.addEventListener('mousedown', (e) => this.handlePointerDown(e));
        this.element.addEventListener('mousemove', (e) => this.handlePointerMove(e));
        this.element.addEventListener('mouseup', (e) => this.handlePointerUp(e));
        
        // 触控事件
        this.element.addEventListener('touchstart', (e) => this.handlePointerDown(e));
        this.element.addEventListener('touchmove', (e) => this.handlePointerMove(e));
        this.element.addEventListener('touchend', (e) => this.handlePointerUp(e));
    }
    
    handlePointerDown(e) {
        // 记录初始位置
        // 启动长按定时器（500ms）
    }
    
    handlePointerMove(e) {
        // 如果移动超过阈值，取消长按，进入拖拽模式
        // 拖拽时更新位置（限制在页面范围内）
    }
    
    handlePointerUp(e) {
        // 清除长按定时器
        // 如果是拖拽，结束拖拽
        // 如果是单击，触发语音录制
    }
    
    handleLongPress() {
        // 显示菜单
        this.showMenu();
    }
    
    showMenu() {
        // 计算菜单位置（上方/下方）
        // 创建菜单 DOM
        // 绑定菜单项点击事件
    }
    
    async toggleVoice() {
        // 调用 SDK 的录音接口
        if (this.client.isRecording) {
            await this.client.stopRecording();
        } else {
            await this.client.startRecording({
                vadEnabled: this.client.vadEnabled,
                vadParams: this.client.config.vadParams
            });
        }
    }
    
    updateSize() {
        // 根据视口尺寸计算按钮大小
        const minDimension = Math.min(window.innerWidth, window.innerHeight);
        const size = Math.max(30, Math.min(100, minDimension * 0.1));
        this.element.style.width = size + 'px';
        this.element.style.height = size + 'px';
    }
    
    constrainPosition(x, y) {
        // 限制位置在页面范围内
        const rect = this.element.getBoundingClientRect();
        const maxX = window.innerWidth - rect.width;
        const maxY = window.innerHeight - rect.height;
        
        return {
            x: Math.max(0, Math.min(x, maxX)),
            y: Math.max(0, Math.min(y, maxY))
        };
    }
}
```

#### 3.2.3 FloatingPanel 组件
```javascript
class FloatingPanel {
    constructor(ComponentClass, options) {
        this.ComponentClass = ComponentClass;
        this.options = options;
        this.element = null;
        this.component = null;
        
        this.init();
    }
    
    init() {
        // 创建全屏容器
        this.element = createElement('div', {
            className: 'floating-panel'
        });
        
        // 创建头部（包含关闭按钮）
        const header = this.createHeader();
        this.element.appendChild(header);
        
        // 创建内容区域
        const content = createElement('div', {
            className: 'floating-panel-content'
        });
        this.element.appendChild(content);
        
        // 实例化组件
        this.component = new this.ComponentClass(content, ...);
        
        // 添加到页面
        document.body.appendChild(this.element);
    }
    
    createHeader() {
        const header = createElement('div', {
            className: 'floating-panel-header'
        });
        
        // 全屏按钮
        const fullscreenBtn = createElement('button', {
            className: 'fullscreen-button',
            textContent: '◱'
        });
        fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        
        // 关闭按钮
        const closeBtn = createElement('button', {
            className: 'close-button',
            textContent: '✕'
        });
        closeBtn.addEventListener('click', () => this.close());
        
        header.appendChild(fullscreenBtn);
        header.appendChild(closeBtn);
        
        return header;
    }
    
    close() {
        if (this.options.onClose) {
            this.options.onClose();
        }
    }
    
    destroy() {
        if (this.component && this.component.destroy) {
            this.component.destroy();
        }
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}
```

### 3.3 Unity 文件提取脚本

#### extract-unity.bat
```batch
@echo off
chcp 65001 >nul
echo ========================================
echo Unity WebGL 文件提取脚本
echo ========================================
echo.

set SOURCE_DIR=E:\Project\Python\MuseumAgent_Server\client\web\Unity\build
set TARGET_DIR=E:\Project\Python\MuseumAgent_Server\client\web\Demo\unity

echo [1/4] 检查源目录...
if not exist "%SOURCE_DIR%" (
    echo [错误] 源目录不存在: %SOURCE_DIR%
    pause
    exit /b 1
)

echo [2/4] 创建目标目录...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [3/4] 复制文件...
echo   - Build/
xcopy "%SOURCE_DIR%\Build" "%TARGET_DIR%\Build\" /E /I /Y /Q
echo   - StreamingAssets/
xcopy "%SOURCE_DIR%\StreamingAssets" "%TARGET_DIR%\StreamingAssets\" /E /I /Y /Q
echo   - TemplateData/
xcopy "%SOURCE_DIR%\TemplateData" "%TARGET_DIR%\TemplateData\" /E /I /Y /Q
echo   - main.js
copy "%SOURCE_DIR%\main.js" "%TARGET_DIR%\main.js" /Y >nul
echo   - ServiceWorker.js
copy "%SOURCE_DIR%\ServiceWorker.js" "%TARGET_DIR%\ServiceWorker.js" /Y >nul
echo   - manifest.webmanifest
copy "%SOURCE_DIR%\manifest.webmanifest" "%TARGET_DIR%\manifest.webmanifest" /Y >nul

echo [4/4] 验证文件...
set ERROR=0
if not exist "%TARGET_DIR%\Build\build.loader.js" (
    echo [错误] build.loader.js 未找到
    set ERROR=1
)
if not exist "%TARGET_DIR%\main.js" (
    echo [错误] main.js 未找到
    set ERROR=1
)

if %ERROR%==0 (
    echo.
    echo ========================================
    echo 提取完成！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 提取失败，请检查错误信息
    echo ========================================
)

pause
```

---

## 四、实施步骤

### 阶段 1：准备工作
- [x] 分析 Unity 项目结构
- [x] 分析当前 Demo 项目结构
- [x] 编写需求文档和升级计划
- [ ] 创建 Unity 文件提取脚本
- [ ] 测试 Unity 文件提取

### 阶段 2：基础组件开发
- [ ] 创建 `gesture.js` 手势识别工具
- [ ] 创建 `ControlButton.js` 控制按钮组件
- [ ] 创建 `FloatingPanel.js` 悬浮面板基类
- [ ] 创建 `UnityContainer.js` Unity 容器组件

### 阶段 3：现有组件改造
- [ ] 改造 `ChatWindow.js` 适配悬浮面板模式
- [ ] 改造 `SettingsPanel.js` 适配悬浮面板模式
- [ ] 扩展 `styles.css` 添加新组件样式

### 阶段 4：应用入口重构
- [ ] 重构 `app.js` 集成 Unity 容器
- [ ] 调整登录后的页面流程
- [ ] 处理 Unity 与智能体的交互

### 阶段 5：测试与优化
- [ ] 功能测试（单击、拖拽、长按）
- [ ] 兼容性测试（桌面浏览器、移动浏览器）
- [ ] 性能优化（Unity 加载、内存管理）
- [ ] 用户体验优化（动画、反馈）

### 阶段 6：文档更新
- [ ] 更新 `Demo/README.md`
- [ ] 添加 Unity 集成说明
- [ ] 添加控制按钮使用说明

---

## 五、技术要点

### 5.1 手势识别
- **单击判定**：按下到抬起时间 < 500ms，且移动距离 < 10px
- **长按判定**：按下超过 500ms，且移动距离 < 10px
- **拖拽判定**：按下后移动距离 >= 10px

### 5.2 位置约束
```javascript
function constrainPosition(x, y, elementWidth, elementHeight) {
    const maxX = window.innerWidth - elementWidth;
    const maxY = window.innerHeight - elementHeight;
    
    return {
        x: Math.max(0, Math.min(x, maxX)),
        y: Math.max(0, Math.min(y, maxY))
    };
}
```

### 5.3 菜单方向计算
```javascript
function getMenuDirection(buttonRect) {
    const spaceAbove = buttonRect.top;
    const spaceBelow = window.innerHeight - buttonRect.bottom;
    
    return spaceBelow >= spaceAbove ? 'down' : 'up';
}
```

### 5.4 Unity 与智能体通信
- Unity → 智能体：通过 `window.unityInstance.SendMessage()`
- 智能体 → Unity：通过 `window.SendMessageToUnity()`（需在 Unity 中注册）

### 5.5 样式层级
```css
/* 层级定义 */
.unity-container {
    z-index: 1;  /* Unity Canvas 底层 */
}

.control-button {
    z-index: 1000;  /* 控制按钮中层 */
}

.floating-panel {
    z-index: 2000;  /* 悬浮面板顶层 */
}
```

---

## 六、风险与注意事项

### 6.1 技术风险
1. **Unity WebGL 性能**：移动端性能可能不足
2. **音频冲突**：Unity 音频与智能体 TTS 可能冲突
3. **内存占用**：Unity + 智能体同时运行可能占用大量内存

### 6.2 兼容性风险
1. **触控事件**：不同设备的触控事件行为可能不一致
2. **全屏 API**：部分浏览器不支持全屏 API
3. **Service Worker**：部分浏览器不支持 PWA

### 6.3 用户体验风险
1. **加载时间**：Unity 首次加载可能较慢
2. **操作复杂度**：悬浮按钮的多种交互可能让用户困惑
3. **视觉遮挡**：控制按钮可能遮挡 Unity 内容

### 6.4 解决方案
1. 添加加载进度提示
2. 提供操作引导（首次使用）
3. 允许用户自定义按钮位置和大小
4. 添加音频混音策略（降低 Unity 音量）

---

## 七、后续优化方向

### 7.1 功能增强
- 支持多个控制按钮（不同功能）
- 支持按钮自定义（图标、大小、位置）
- 支持手势快捷操作（双击、滑动）
- 支持语音唤醒（免按钮交互）

### 7.2 性能优化
- Unity 资源懒加载
- 智能体功能按需加载
- 内存管理和垃圾回收

### 7.3 体验优化
- 添加动画效果（按钮、菜单、面板）
- 添加音效反馈
- 添加触觉反馈（移动端）
- 添加主题切换（跟随 Unity 场景）

---

## 八、验收标准

### 8.1 功能验收
- [ ] 登录后正确加载 Unity WebGL
- [ ] 控制按钮正确显示在右下角
- [ ] 单击控制按钮可以开始/停止语音
- [ ] 拖拽控制按钮可以移动位置（限制在页面内）
- [ ] 长按控制按钮弹出菜单
- [ ] 菜单方向根据位置自动调整
- [ ] 点击"设置"打开设置页面，控制按钮隐藏
- [ ] 点击"聊天"打开聊天页面，控制按钮隐藏
- [ ] 设置/聊天页面有关闭按钮
- [ ] 关闭设置/聊天页面后控制按钮恢复显示
- [ ] 智能体功能正常工作（语音、文本、TTS）

### 8.2 兼容性验收
- [ ] Chrome 桌面版正常运行
- [ ] Firefox 桌面版正常运行
- [ ] Edge 桌面版正常运行
- [ ] Safari 桌面版正常运行
- [ ] Chrome 移动版正常运行
- [ ] Safari 移动版正常运行

### 8.3 性能验收
- [ ] Unity 加载时间 < 10s（正常网络）
- [ ] 控制按钮响应时间 < 100ms
- [ ] 拖拽流畅度 >= 30fps
- [ ] 内存占用 < 500MB（桌面）
- [ ] 内存占用 < 300MB（移动）

### 8.4 体验验收
- [ ] 操作逻辑清晰，无困惑
- [ ] 视觉效果美观，无遮挡
- [ ] 交互反馈及时，无延迟
- [ ] 错误提示友好，有引导

---

## 九、时间估算

- **阶段 1**：准备工作 - 0.5 天
- **阶段 2**：基础组件开发 - 2 天
- **阶段 3**：现有组件改造 - 1 天
- **阶段 4**：应用入口重构 - 1 天
- **阶段 5**：测试与优化 - 1.5 天
- **阶段 6**：文档更新 - 0.5 天

**总计**：约 6.5 天

---

## 十、附录

### 10.1 参考资料
- Unity WebGL 文档：https://docs.unity3d.com/Manual/webgl.html
- Touch Events API：https://developer.mozilla.org/en-US/docs/Web/API/Touch_events
- Pointer Events API：https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events
- Fullscreen API：https://developer.mozilla.org/en-US/docs/Web/API/Fullscreen_API

### 10.2 相关文件
- Unity 源目录：`E:\Project\Python\MuseumAgent_Server\client\web\Unity\build`
- Demo 目录：`E:\Project\Python\MuseumAgent_Server\client\web\Demo`
- SDK 库：`Demo/lib/museum-agent-sdk.min.js`

### 10.3 联系方式
- 项目负责人：[待填写]
- 技术支持：[待填写]

