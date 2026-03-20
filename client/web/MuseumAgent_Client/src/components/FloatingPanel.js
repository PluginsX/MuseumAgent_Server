/**
 * 悬浮面板基类
 * ✅ 重构版本：支持传入已有组件实例（单例模式）
 * 用于包装设置和聊天组件，提供窗口/全屏模式切换和关闭功能
 */

import { createElement } from '../utils/dom.js';
import { detectDeviceEnvironment } from '../commonFunction.js';

export class FloatingPanel {
    constructor(componentOrInstance, options = {}) {
        // ✅ 支持两种模式：
        // 1. 传入组件实例（单例模式）
        // 2. 传入组件类 + client（旧模式，向后兼容）
        
        if (typeof componentOrInstance === 'function') {
            // 旧模式：传入组件类
            this.ComponentClass = componentOrInstance;
            this.component = null;
            this.isExternalComponent = false;
            this.client = options.client || null;
        } else {
            // 新模式：传入组件实例
            this.component = componentOrInstance;
            this.ComponentClass = null;
            this.isExternalComponent = true;
        }
        
        // ✅ 获取设备信息
        this.deviceInfo = options.deviceInfo || detectDeviceEnvironment();
        
        // 用户可自定义初始模式，如果没有则使用设备预设
        this.useWindowMode = options.useWindowMode !== undefined 
            ? options.useWindowMode 
            : (this.deviceInfo ? this.deviceInfo.shouldUseWindowMode : false);
        
        // 保存用户偏好（持久化到 localStorage）
        this.userPreferredMode = options.useWindowMode;
        
        this.options = {
            title: options.title || '',
            onClose: options.onClose || null,
            showFullscreenButton: options.showFullscreenButton !== false
        };
        
        this.draggable = options.draggable !== false; // 默认启用拖拽
        this.useDragInFullscreen = options.useDragInFullscreen !== false; // 全屏模式下默认启用拖拽
        
        // ✅ 尺寸调整配置
        this.resizable = options.resizable !== false; // 默认启用尺寸调整
        this.resizeHandleWidth = options.resizeHandleWidth || 10; // 手柄宽度（像素）
        this.minWindowWidth = options.minWindowWidth || 300; // 最小窗口宽
        this.minWindowHeight = options.minWindowHeight || 200; // 最小窗口高
        
        this.element = null;
        this.contentContainer = null;
        this.resizeHandlesContainer = null;
        
        this.init();
    }
    
    /**
     * 初始化
     */
    init() {
        // 切换到网页模式（允许右键、选择等）
        this.switchToWebMode();
        
        // 加载用户偏好模式
        const savedMode = this.loadUserPreference();
        if (savedMode !== null) {
            this.useWindowMode = savedMode;
        }
        
        this.createElement();
        this.attachComponent();
        
        // 根据模式启用拖拽功能
        if (this.useWindowMode && this.draggable) {
            this.enableDrag();
        } else if (!this.useWindowMode && this.useDragInFullscreen) {
            this.enableDrag();
        }
        
        // ✅ 根据模式启用尺寸调整功能
        if (this.useWindowMode && this.resizable) {
            this.enableResize();
        }
        
        // ✅ 监听浏览器窗口大小变化（仅在窗口模式）
        if (this.useWindowMode) {
            this._bindWindowResizeListener();
        }
    }
    
    /**
     * ✅ 禁用 Unity 输入
     */
    disableUnityInput() {
        const canvas = document.querySelector('#unity-canvas');
        if (canvas) {
            canvas.style.pointerEvents = 'none';
            canvas.setAttribute('tabindex', '-1');
            console.log('[FloatingPanel] Unity 输入已禁用');
        }
    }
    
    /**
     * ✅ 启用 Unity 输入
     */
    enableUnityInput() {
        const canvas = document.querySelector('#unity-canvas');
        if (canvas) {
            canvas.style.pointerEvents = 'auto';
            canvas.setAttribute('tabindex', '0');
            console.log('[FloatingPanel] Unity 输入已启用');
        }
    }
    
    /**
     * 创建元素
     */
    createElement() {
        // 创建容器（根据模式设置不同样式）
        this.element = createElement('div', {
            className: `floating-panel ${this.useWindowMode ? 'window-mode' : 'fullscreen-mode'}`
        });
        
        // 窗口模式样式
        if (this.useWindowMode) {
            this.element.style.width = '80%';
            this.element.style.height = '80%';
            this.element.style.maxWidth = '800px';
            this.element.style.maxHeight = '600px';
            this.element.style.left = '50%';
            this.element.style.top = '50%';
            this.element.style.transform = 'translate(-50%, -50%)';
            this.element.style.position = 'fixed';
            this.element.style.zIndex = '9999';
        } else {
            // 全屏模式样式
            this.element.style.width = '100vw';
            this.element.style.height = '100vh';
            this.element.style.left = '0';
            this.element.style.top = '0';
            this.element.style.transform = 'none';
            this.element.style.position = 'fixed';
            this.element.style.zIndex = '9999';
        }
        
        // ✅ 创建内容包装容器（仅窗口模式）- 用于实现圆角裁切
        if (this.useWindowMode) {
            const contentWrapper = createElement('div', {
                className: 'floating-panel-content-wrapper'
            });
            
            // 创建头部
            const header = this.createHeader();
            contentWrapper.appendChild(header);
            
            // 创建内容区域
            this.contentContainer = createElement('div', {
                className: 'floating-panel-content'
            });
            contentWrapper.appendChild(this.contentContainer);
            this.element.appendChild(contentWrapper);
            
            // ✅ 使用 setTimeout 延迟到下一事件循环，确保浏览器完成样式计算
            setTimeout(() => {
                if (this.resizable) {
                    this.createResizeHandles();
                    this.enableResize();  // ✅ 启用尺寸调整
                }
            }, 0);
        } else {
            // 全屏模式 - 直接创建头部和内容
            const header = this.createHeader();
            this.element.appendChild(header);
            
            this.contentContainer = createElement('div', {
                className: 'floating-panel-content'
            });
            this.element.appendChild(this.contentContainer);
        }
        
        // 添加到页面
        document.body.appendChild(this.element);
        
        // 添加淡入动画
        setTimeout(() => {
            this.element.classList.add('visible');
        }, 10);
    }
    
    /**
     * ✅ 创建尺寸调整手柄
     */
    createResizeHandles() {
        // 创建手柄容器
        this.resizeHandlesContainer = createElement('div', {
            className: 'floating-panel-resize-handles'
        });
        
        // ✅ 获取内容包装容器的圆角值
        const contentWrapper = this.element.querySelector('.floating-panel-content-wrapper');
        let borderRadius = 0;
        
        if (contentWrapper) {
            // ✅ 强制浏览器计算样式（通过访问 offsetHeight 等属性触发重排）
            void contentWrapper.offsetHeight;
            
            const computedStyle = getComputedStyle(contentWrapper);
            const borderRadiusStr = computedStyle.borderTopLeftRadius;
            
            console.log(`[FloatingPanel] wrapper 圆角原始值："${borderRadiusStr}"`);
            
            if (borderRadiusStr && borderRadiusStr !== '0px') {
                const radiusValue = borderRadiusStr.split(' ')[0];
                borderRadius = parseFloat(radiusValue) || 0;
            }
            
            console.log(`[FloatingPanel] 解析后的圆角值：${borderRadius}px`);
        } else {
            console.error('[FloatingPanel] 未找到 wrapper 元素！');
        }
        
        // 设置 CSS 变量
        this.resizeHandlesContainer.style.setProperty('--handle-width', `${this.resizeHandleWidth}px`);
        this.resizeHandlesContainer.style.setProperty('--border-radius', `${borderRadius}px`);
        
        console.log(`[FloatingPanel] 创建手柄：边宽=${this.resizeHandleWidth}px, 圆角=${borderRadius}px`);
        console.log(`[FloatingPanel] CSS 变量设置：--handle-width=${this.resizeHandleWidth}px, --border-radius=${borderRadius}px`);
        
        // 定义 8 个手柄
        const handles = [
            { name: 'top-left', className: 'corner top-left' },
            { name: 'top', className: 'edge top' },
            { name: 'top-right', className: 'corner top-right' },
            { name: 'left', className: 'edge left' },
            { name: 'right', className: 'edge right' },
            { name: 'bottom-left', className: 'corner bottom-left' },
            { name: 'bottom', className: 'edge bottom' },
            { name: 'bottom-right', className: 'corner bottom-right' }
        ];
        
        // 创建每个手柄
        handles.forEach(handle => {
            const handleEl = createElement('div', {
                className: `resize-handle ${handle.className}`
            });
            handleEl.setAttribute('data-handle', handle.name);
            this.resizeHandlesContainer.appendChild(handleEl);
        });
        
        // 添加到面板顶部（在其他内容之前）
        this.element.insertBefore(this.resizeHandlesContainer, this.element.firstChild);
        
        // ✅ 验证：检查所有手柄元素的位置和尺寸
        setTimeout(() => {
            const allHandles = this.resizeHandlesContainer.querySelectorAll('.resize-handle');
            allHandles.forEach(handle => {
                const handleName = handle.getAttribute('data-handle');
                const style = getComputedStyle(handle);
                console.log(`[FloatingPanel] 手柄 "${handleName}":`, {
                    position: { left: style.left, right: style.right, top: style.top, bottom: style.bottom },
                    size: { width: style.width, height: style.height }
                });
            });
        }, 100);
    }
    
    /**
     * 创建头部
     */
    createHeader() {
        const header = createElement('div', {
            className: 'floating-panel-header'
        });
        
        // 标题
        if (this.options.title) {
            const title = createElement('h2', {
                className: 'floating-panel-title',
                textContent: this.options.title
            });
            header.appendChild(title);
        }
        
        // 按钮容器
        const buttonContainer = createElement('div', {
            className: 'floating-panel-buttons'
        });
        
        // ✅ 窗口/全屏切换按钮（替换原来的全屏按钮）
        const modeToggleBtn = createElement('button', {
            className: 'floating-panel-button mode-toggle-button',
            textContent: this.useWindowMode ? '◱' : '⛶',  // 窗口模式显示全屏图标，全屏模式显示窗口图标
            title: this.useWindowMode ? '切换到全屏模式' : '切换到窗口模式'
        });
        modeToggleBtn.addEventListener('click', () => this.toggleWindowMode());
        buttonContainer.appendChild(modeToggleBtn);
        
        // 关闭按钮
        const closeBtn = createElement('button', {
            className: 'floating-panel-button close-button',
            textContent: '✕',
            title: '关闭'
        });
        closeBtn.addEventListener('click', () => this.close());
        buttonContainer.appendChild(closeBtn);
        
        header.appendChild(buttonContainer);
        
        // ✅ 双击标题栏切换窗口/全屏模式
        // 仅在非按钮区域双击时触发，避免与按钮点击冲突
        header.addEventListener('dblclick', (e) => {
            // 排除按钮区域
            if (e.target.closest('.floating-panel-button')) {
                return;
            }
            
            // 排除标题文本的三连击选中等情况
            if (e.target.closest('.floating-panel-title')) {
                e.preventDefault();
            }
            
            this.toggleWindowMode();
        });
        
        return header;
    }
    
    /**
     * ✅ 附加组件（新旧模式兼容）
     */
    attachComponent() {
        if (this.isExternalComponent) {
            // 新模式：使用已有组件实例
            
            // 1. 更新组件的 container 属性
            if (this.component.container !== undefined) {
                this.component.container = this.contentContainer;
            }
            
            // 2. 如果组件有 show 方法，调用它（会触发重新渲染）
            if (typeof this.component.show === 'function') {
                this.component.show();
            }
            // 3. 否则，如果组件有 render 方法，调用它
            else if (typeof this.component.render === 'function') {
                this.component.render();
            }
            
            // 4. 确保内容显示
            if (this.contentContainer) {
                this.contentContainer.style.display = 'flex';
                this.contentContainer.style.flexDirection = 'column';
                this.contentContainer.style.height = '100%';
                
                // 只在设置面板时添加10px的padding
                if (this.options.title === '客户端配置') {
                    this.contentContainer.style.padding = '10px';
                } else {
                    this.contentContainer.style.padding = '0';
                }
            }
        } else {
            // 旧模式：创建新组件实例
            this.component = new this.ComponentClass(this.contentContainer, this.client);
        }
        
        // ✅ 关键修复：在面板内容区域捕获所有键盘事件，阻止冒泡到 Unity WebGL 框架
        // Unity WebGL 在全局注册了键盘监听器并调用 preventDefault()，会导致面板内
        // 所有输入框的英文输入和退格键失效（中文 IME 不受影响，故仅英文/退格失效）
        // 
        // 注意：Unity 的监听器注册在 window 上（捕获阶段），仅用 stopPropagation() 无法阻止。
        // 必须在 window 上用捕获阶段 + stopImmediatePropagation() 才能在 Unity 之前拦截。
        if (this.element) {
            // 在面板元素上阻止冒泡（兜底）
            this.element.addEventListener('keydown', (e) => {
                e.stopPropagation();
            }, true);
            this.element.addEventListener('keyup', (e) => {
                e.stopPropagation();
            }, true);
            this.element.addEventListener('keypress', (e) => {
                e.stopPropagation();
            }, true);
            
            // ✅ 核心修复：在 window 上注册捕获阶段监听器
            // 当焦点在面板内的输入框时，拦截键盘事件，阻止 Unity 的监听器执行
            this._keyboardGuard = (e) => {
                // 只拦截焦点在面板内的键盘事件
                if (this.element && this.element.contains(document.activeElement)) {
                    e.stopImmediatePropagation();  // 阻止同级的所有其他监听器（包括 Unity）
                    // 注意：不调用 preventDefault()，保留浏览器默认的字符输入行为
                }
            };
            
            window.addEventListener('keydown', this._keyboardGuard, true);
            window.addEventListener('keyup', this._keyboardGuard, true);
            window.addEventListener('keypress', this._keyboardGuard, true);
        }
    }
    
    /**
     * ✅ 切换窗口/全屏模式
     */
    toggleWindowMode() {
        this.useWindowMode = !this.useWindowMode;
        
        // 切换 CSS 类
        this.element.classList.remove('window-mode', 'fullscreen-mode');
        this.element.classList.add(this.useWindowMode ? 'window-mode' : 'fullscreen-mode');
        
        // 应用模式样式
        if (this.useWindowMode) {
            // 窗口模式
            // ✅ 尝试加载用户之前保存的窗口尺寸
            const savedSize = this.loadUserWindowSize();
            
            if (savedSize) {
                // 恢复用户保存的尺寸和位置
                this.element.style.width = savedSize.width + 'px';
                this.element.style.height = savedSize.height + 'px';
                this.element.style.left = savedSize.left + 'px';
                this.element.style.top = savedSize.top + 'px';
                this.element.style.transform = 'none';
                this.element.style.maxWidth = 'none';
                this.element.style.maxHeight = 'none';
                console.log('[FloatingPanel] 恢复用户保存的窗口尺寸:', savedSize);
            } else {
                // 使用默认尺寸
                this.element.style.width = '80%';
                this.element.style.height = '80%';
                this.element.style.maxWidth = '800px';
                this.element.style.maxHeight = '600px';
                this.element.style.left = '50%';
                this.element.style.top = '50%';
                this.element.style.transform = 'translate(-50%, -50%)';
                this.element.style.position = 'fixed';
                this.element.style.zIndex = '9999';
            }
            
            // 启用拖拽（窗口模式下需要）
            if (this.draggable) {
                this.enableDrag();
            }
            
            // ✅ 创建并显示手柄（窗口模式）- 如果之前不存在则创建
            if (this.resizable) {
                if (!this.resizeHandlesContainer) {
                    this.createResizeHandles();
                    this.enableResize();  // ✅ 首次创建时需要启用
                } else {
                    this.resizeHandlesContainer.style.display = 'block';
                    // ✅ 重新计算并设置 CSS 变量（确保使用最新的圆角值）
                    this.resizeHandlesContainer.style.setProperty('--handle-width', `${this.resizeHandleWidth}px`);
                    
                    // 重新计算四角手柄尺寸
                    const contentWrapper = this.element.querySelector('.floating-panel-content-wrapper');
                    let borderRadius = 0; // ✅ 默认值为 0，真实获取
                    
                    if (contentWrapper) {
                        // ✅ 强制浏览器计算样式（通过访问 offsetHeight 等属性触发重排）
                        void contentWrapper.offsetHeight; // 触发重排
                        
                        const computedStyle = getComputedStyle(contentWrapper);
                        const borderRadiusStr = computedStyle.borderTopLeftRadius;
                        console.log(`[FloatingPanel] 切换模式 - wrapper 圆角原始值："${borderRadiusStr}"`);
                        
                        if (borderRadiusStr && borderRadiusStr !== '0px') {
                            const radiusValue = borderRadiusStr.split(' ')[0];
                            borderRadius = parseFloat(radiusValue) || 0;
                        }
                        console.log(`[FloatingPanel] 切换模式 - 解析后的圆角值：${borderRadius}px`);
                    }
                    
                    const cornerHandleSize = this.resizeHandleWidth + borderRadius;
                    console.log(`[FloatingPanel] 切换模式 - 四角手柄尺寸：${cornerHandleSize}px`);
                    this.resizeHandlesContainer.style.setProperty('--corner-handle-size', `${cornerHandleSize}px`);
                    this.resizeHandlesContainer.style.setProperty('--border-radius', `${borderRadius}px`); // ✅ 设置圆角变量
                }
            }
            
            // 更新按钮图标和提示
            const modeToggleBtn = this.element.querySelector('.mode-toggle-button');
            if (modeToggleBtn) {
                modeToggleBtn.textContent = '⛶';
                modeToggleBtn.title = '切换到全屏模式';
            }
            
            // ✅ 重新绑定窗口大小变化监听器
            this._bindWindowResizeListener();
            
            console.log('[FloatingPanel] 切换到窗口模式');
        } else {
            // 全屏模式
            this.element.style.width = '100vw';
            this.element.style.height = '100vh';
            this.element.style.left = '0';
            this.element.style.top = '0';
            this.element.style.transform = 'none';
            this.element.style.position = 'fixed';
            this.element.style.zIndex = '9999';
            
            // 启用拖拽（全屏模式下可选）
            if (this.useDragInFullscreen) {
                this.enableDrag();
            }
            
            // ✅ 隐藏手柄（全屏模式）
            if (this.resizeHandlesContainer) {
                this.resizeHandlesContainer.style.display = 'none';
            }
            
            // 更新按钮图标和提示
            const modeToggleBtn = this.element.querySelector('.mode-toggle-button');
            if (modeToggleBtn) {
                modeToggleBtn.textContent = '◱';
                modeToggleBtn.title = '切换到窗口模式';
            }
            
            console.log('[FloatingPanel] 切换到全屏模式');
        }
        
        // 保存用户偏好
        this.saveUserPreference();
    }
    
    /**
     * ✅ 保存用户偏好到 localStorage
     */
    saveUserPreference() {
        const preference = {
            useWindowMode: this.useWindowMode,
            timestamp: Date.now()
        };
        localStorage.setItem('floatingPanelModePreference', JSON.stringify(preference));
    }
    
    /**
     * ✅ 从 localStorage 加载用户偏好
     */
    loadUserPreference() {
        try {
            const preference = JSON.parse(localStorage.getItem('floatingPanelModePreference'));
            if (preference && preference.useWindowMode !== undefined) {
                return preference.useWindowMode;
            }
        } catch (error) {
            console.error('[FloatingPanel] 加载用户偏好失败:', error);
        }
        return null;
    }
    
    /**
     * ✅ 保存用户调整的窗口尺寸到 localStorage
     */
    saveUserWindowSize() {
        if (!this.element || !this.useWindowMode) return;
        
        const rect = this.element.getBoundingClientRect();
        const sizeData = {
            width: rect.width,
            height: rect.height,
            left: rect.left,
            top: rect.top,
            timestamp: Date.now()
        };
        localStorage.setItem('floatingPanelWindowSize', JSON.stringify(sizeData));
        console.log('[FloatingPanel] 保存窗口尺寸:', sizeData);
    }
    
    /**
     * ✅ 从 localStorage 加载用户调整的窗口尺寸
     */
    loadUserWindowSize() {
        try {
            const sizeData = JSON.parse(localStorage.getItem('floatingPanelWindowSize'));
            if (sizeData && sizeData.width && sizeData.height) {
                return sizeData;
            }
        } catch (error) {
            console.error('[FloatingPanel] 加载窗口尺寸失败:', error);
        }
        return null;
    }
    
    /**
     * ✅ 清除用户调整的窗口尺寸（用于恢复默认）
     */
    clearUserWindowSize() {
        localStorage.removeItem('floatingPanelWindowSize');
        console.log('[FloatingPanel] 已清除窗口尺寸记忆');
    }
    
    /**
     * ✅ 绑定浏览器窗口大小变化监听器
     */
    _bindWindowResizeListener() {
        // 使用防抖，避免频繁触发
        let resizeTimeout;
        
        window.addEventListener('resize', () => {
            if (!this.useWindowMode) return;
            
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this._adjustToViewport();
            }, 100); // 100ms 防抖
        });
        
        console.log('[FloatingPanel] 已绑定窗口大小变化监听器');
    }
    
    /**
     * ✅ 调整窗口位置以确保在视口内（浏览器窗口大小变化时调用）
     */
    _adjustToViewport() {
        if (!this.element || !this.useWindowMode) return;
        
        const rect = this.element.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let newLeft = rect.left;
        let newTop = rect.top;
        let newWidth = rect.width;
        let newHeight = rect.height;
        
        let needsAdjustment = false;
        
        // ✅ 检测并调整宽度
        if (rect.right > viewportWidth) {
            // 右侧超出
            if (rect.width > viewportWidth) {
                // 窗口比视口宽 → 缩小窗口（但不小于最小宽度）
                newWidth = Math.max(this.minWindowWidth, viewportWidth);
                newLeft = 0;
                needsAdjustment = true;
                console.log(`[FloatingPanel] 窗口宽度超出视口，缩小窗口到 ${newWidth}px`);
            } else {
                // 窗口可以容纳 → 只移动位置
                newLeft = Math.max(0, viewportWidth - rect.width);
                needsAdjustment = true;
                console.log('[FloatingPanel] 窗口右侧超出，向左移动');
            }
        } else if (rect.left < 0) {
            // 左侧超出
            newLeft = 0;
            needsAdjustment = true;
            console.log('[FloatingPanel] 窗口左侧超出，向右移动');
        }
        
        // ✅ 检测并调整高度
        if (rect.bottom > viewportHeight) {
            // 底部超出
            if (rect.height > viewportHeight) {
                // 窗口比视口高 → 缩小窗口（但不小于最小高度）
                newHeight = Math.max(this.minWindowHeight, viewportHeight);
                newTop = 0;
                needsAdjustment = true;
                console.log(`[FloatingPanel] 窗口高度超出视口，缩小窗口到 ${newHeight}px`);
            } else {
                // 窗口可以容纳 → 只移动位置
                newTop = Math.max(0, viewportHeight - rect.height);
                needsAdjustment = true;
                console.log('[FloatingPanel] 窗口底部超出，向上移动');
            }
        } else if (rect.top < 0) {
            // 顶部超出
            newTop = 0;
            needsAdjustment = true;
            console.log('[FloatingPanel] 窗口顶部超出，向下移动');
        }
        
        // ✅ 应用调整
        if (needsAdjustment) {
            this.element.style.left = newLeft + 'px';
            this.element.style.top = newTop + 'px';
            
            if (newWidth !== rect.width) {
                this.element.style.width = newWidth + 'px';
            }
            if (newHeight !== rect.height) {
                this.element.style.height = newHeight + 'px';
            }
            
            console.log(`[FloatingPanel] 调整完成：left=${newLeft}, top=${newTop}, width=${newWidth}, height=${newHeight}`);
            
            // ✅ 保存调整后的尺寸
            this.saveUserWindowSize();
        }
    }
    
    /**
     * ✅ 启用拖拽功能（仅窗口模式）
     */
    enableDrag() {
        if (!this.element) return;
        
        let isDragging = false;
        let dragStartX = 0;
        let dragStartY = 0;
        let initialLeft = 0;
        let initialTop = 0;
        let totalDragDistance = 0;  // ✅ 记录总拖拽距离，防止拖拽时误触发双击
        
        const header = this.element.querySelector('.floating-panel-header');
        if (!header) return;
        
        // Pointer Down
        header.addEventListener('pointerdown', (e) => {
            if (e.target.closest('.close-button') || e.target.closest('.mode-toggle-button')) {
                return; // 点击按钮时不拖拽
            }
            
            // 如果点击的是输入框或textarea，不阻止默认行为，允许输入
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
                return;
            }
            
            e.preventDefault();
            header.setPointerCapture(e.pointerId);
            
            isDragging = true;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            totalDragDistance = 0;  // ✅ 重置拖拽距离
            
            // 获取当前位置
            const rect = this.element.getBoundingClientRect();
            initialLeft = rect.left;
            initialTop = rect.top;
            
            this.element.style.transition = 'none';
            this.element.classList.add('dragging');
        });
        
        // Pointer Move (绑定到 document 以确保在 header 外也能捕获)
        document.addEventListener('pointermove', (e) => {
            if (!isDragging) return;
            
            e.preventDefault();
            
            const deltaX = e.clientX - dragStartX;
            const deltaY = e.clientY - dragStartY;
            totalDragDistance += Math.sqrt(deltaX * deltaX + deltaY * deltaY);  // ✅ 累计拖拽距离
            
            const newLeft = initialLeft + deltaX;
            const newTop = initialTop + deltaY;
            
            // 约束在视口内
            const maxX = window.innerWidth - this.element.offsetWidth;
            const maxY = window.innerHeight - this.element.offsetHeight;
            
            this.element.style.left = `${Math.max(0, Math.min(newLeft, maxX))}px`;
            this.element.style.top = `${Math.max(0, Math.min(newTop, maxY))}px`;
            this.element.style.transform = 'none';
        });
        
        // Pointer Up (绑定到 document)
        document.addEventListener('pointerup', (e) => {
            if (!isDragging) return;
            
            header.releasePointerCapture(e.pointerId);
            isDragging = false;
            this.element.classList.remove('dragging');
            
            // ✅ 如果拖拽距离过大，禁用本次双击（防止拖拽后立即双击误触发）
            if (totalDragDistance > 5) {
                header.style.pointerEvents = 'none';
                setTimeout(() => {
                    header.style.pointerEvents = 'auto';
                }, 100);
            }
        });
        
        // Pointer Cancel (绑定到 document)
        document.addEventListener('pointercancel', () => {
            isDragging = false;
            this.element.classList.remove('dragging');
        });
    }
    
    /**
     * ✅ 禁用拖拽功能
     */
    disableDrag() {
        console.log('[FloatingPanel] 拖拽功能已禁用');
    }
    
    /**
     * ✅ 启用尺寸调整功能
     */
    enableResize() {
        if (!this.resizeHandlesContainer || !this.element) return;
        
        const handles = this.resizeHandlesContainer.querySelectorAll('.resize-handle');
        
        handles.forEach(handle => {
            handle.addEventListener('pointerdown', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const handleType = handle.getAttribute('data-handle');
                const rect = this.element.getBoundingClientRect();
                const startX = e.clientX;
                const startY = e.clientY;
                const startWidth = rect.width;
                const startHeight = rect.height;
                const startLeft = rect.left;
                const startTop = rect.top;
                
                handle.setPointerCapture(e.pointerId);
                handle.classList.add('resizing');
                this.element.style.transition = 'none';
                
                // ✅ Pointer Move
                const handleMove = (moveEvent) => {
                    const deltaX = moveEvent.clientX - startX;
                    const deltaY = moveEvent.clientY - startY;
                    
                    let newWidth = startWidth;
                    let newHeight = startHeight;
                    let newLeft = startLeft;
                    let newTop = startTop;
                    
                    // 根据手柄类型计算新尺寸
                    switch (handleType) {
                        case 'top-left':
                            newWidth = Math.max(this.minWindowWidth, startWidth - deltaX);
                            newHeight = Math.max(this.minWindowHeight, startHeight - deltaY);
                            newLeft = startLeft + (startWidth - newWidth);
                            newTop = startTop + (startHeight - newHeight);
                            break;
                        case 'top':
                            newHeight = Math.max(this.minWindowHeight, startHeight - deltaY);
                            newTop = startTop + (startHeight - newHeight);
                            break;
                        case 'top-right':
                            newWidth = Math.max(this.minWindowWidth, startWidth + deltaX);
                            newHeight = Math.max(this.minWindowHeight, startHeight - deltaY);
                            newTop = startTop + (startHeight - newHeight);
                            break;
                        case 'left':
                            newWidth = Math.max(this.minWindowWidth, startWidth - deltaX);
                            newLeft = startLeft + (startWidth - newWidth);
                            break;
                        case 'right':
                            newWidth = Math.max(this.minWindowWidth, startWidth + deltaX);
                            break;
                        case 'bottom-left':
                            newWidth = Math.max(this.minWindowWidth, startWidth - deltaX);
                            newHeight = Math.max(this.minWindowHeight, startHeight + deltaY);
                            newLeft = startLeft + (startWidth - newWidth);
                            break;
                        case 'bottom':
                            newHeight = Math.max(this.minWindowHeight, startHeight + deltaY);
                            break;
                        case 'bottom-right':
                            newWidth = Math.max(this.minWindowWidth, startWidth + deltaX);
                            newHeight = Math.max(this.minWindowHeight, startHeight + deltaY);
                            break;
                    }
                    
                    // ✅ 限制最大尺寸为视口尺寸
                    const maxWindowWidth = window.innerWidth;
                    const maxWindowHeight = window.innerHeight;
                    newWidth = Math.min(newWidth, maxWindowWidth);
                    newHeight = Math.min(newHeight, maxWindowHeight);
                    
                    // 约束在视口内（确保窗口不会超出边界）
                    const maxX = window.innerWidth - newWidth;
                    const maxY = window.innerHeight - newHeight;
                    newLeft = Math.max(0, Math.min(newLeft, maxX));
                    newTop = Math.max(0, Math.min(newTop, maxY));
                    
                    // 应用新尺寸和位置
                    this.element.style.width = newWidth + 'px';
                    this.element.style.height = newHeight + 'px';
                    this.element.style.left = newLeft + 'px';
                    this.element.style.top = newTop + 'px';
                    this.element.style.transform = 'none';
                    this.element.style.maxWidth = 'none';
                    this.element.style.maxHeight = 'none';
                };
                
                // ✅ Pointer Up
                const handleUp = (upEvent) => {
                    handle.releasePointerCapture(e.pointerId);
                    handle.classList.remove('resizing');
                    
                    // ✅ 检测是否调整到与页面同尺寸（全屏）
                    // 从实际元素获取尺寸（因为 newWidth/newHeight 是 handleMove 的局部变量）
                    const currentRect = this.element.getBoundingClientRect();
                    const isMaximized = (currentRect.width >= window.innerWidth - 1) && (currentRect.height >= window.innerHeight - 1);
                    
                    if (isMaximized) {
                        console.log('[FloatingPanel] 检测到窗口最大化，自动切换到全屏模式');
                        
                        // ✅ 清除窗口模式的尺寸和位置记忆
                        this.clearUserWindowSize();
                        
                        // ✅ 切换到全屏模式
                        this.toggleWindowMode();
                    } else {
                        // ✅ 保存用户调整的尺寸（非最大化时）
                        this.saveUserWindowSize();
                    }
                    
                    document.removeEventListener('pointermove', handleMove);
                    document.removeEventListener('pointerup', handleUp);
                    document.removeEventListener('pointercancel', handleCancel);
                };
                
                // ✅ Pointer Cancel
                const handleCancel = () => {
                    handle.classList.remove('resizing');
                    
                    document.removeEventListener('pointermove', handleMove);
                    document.removeEventListener('pointerup', handleUp);
                    document.removeEventListener('pointercancel', handleCancel);
                };
                
                document.addEventListener('pointermove', handleMove);
                document.addEventListener('pointerup', handleUp);
                document.addEventListener('pointercancel', handleCancel);
            });
        });
    }
    
    /**
     * 关闭
     */
    close() {
        // 添加淡出动画
        this.element.classList.remove('visible');
        
        // 等待动画完成后销毁
        setTimeout(() => {
            if (this.options.onClose) {
                this.options.onClose();
            }
        }, 300);
    }
    
    /**
     * ✅ 切换到网页模式（允许右键、选择等）
     */
    switchToWebMode() {
        console.log('[FloatingPanel] 切换到网页模式');
        
        const doc = document.body;
        doc.classList.add('web-mode');
        doc.classList.remove('unity-mode');
        
        // 通知 ControlButton 切换模式
        if (window.controlButton && typeof window.controlButton.setViewMode === 'function') {
            window.controlButton.setViewMode('web');
        }
    }
    
    /**
     * ✅ 切换到 Unity 模式（禁用右键、选择等）
     */
    switchToUnityMode() {
        console.log('[FloatingPanel] 切换到 Unity 模式');
        
        const doc = document.body;
        doc.classList.add('unity-mode');
        doc.classList.remove('web-mode');
        
        // 通知 ControlButton 切换模式
        if (window.controlButton && typeof window.controlButton.setViewMode === 'function') {
            window.controlButton.setViewMode('unity');
        }
    }
    
    /**
     * ✅ 销毁（不销毁外部组件实例）
     */
    destroy() {
        // 切换到 Unity 模式
        this.switchToUnityMode();
        
        // ✅ 清理 window 上注册的键盘守卫监听器，防止内存泄漏
        if (this._keyboardGuard) {
            window.removeEventListener('keydown', this._keyboardGuard, true);
            window.removeEventListener('keyup', this._keyboardGuard, true);
            window.removeEventListener('keypress', this._keyboardGuard, true);
            this._keyboardGuard = null;
        }
        
        // 如果是外部组件，只隐藏，不销毁
        if (this.isExternalComponent) {
            if (typeof this.component.hide === 'function') {
                this.component.hide();
            } else if (this.component.element && this.component.element.parentNode) {
                this.component.element.parentNode.removeChild(this.component.element);
            }
        } else {
            // 旧模式：销毁组件
            if (this.component && typeof this.component.destroy === 'function') {
                this.component.destroy();
            }
        }
        
        // 移除面板元素
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}
