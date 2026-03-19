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
        
        this.element = null;
        this.contentContainer = null;
        
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
        
        // 创建头部
        const header = this.createHeader();
        this.element.appendChild(header);
        
        // 创建内容区域
        this.contentContainer = createElement('div', {
            className: 'floating-panel-content'
        });
        this.element.appendChild(this.contentContainer);
        // this.contentContainer.style.padding = '10px';
        // 添加到页面
        document.body.appendChild(this.element);
        
        // 添加淡入动画
        setTimeout(() => {
            this.element.classList.add('visible');
        }, 10);
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
            this.element.style.width = '80%';
            this.element.style.height = '80%';
            this.element.style.maxWidth = '800px';
            this.element.style.maxHeight = '600px';
            this.element.style.left = '50%';
            this.element.style.top = '50%';
            this.element.style.transform = 'translate(-50%, -50%)';
            this.element.style.position = 'fixed';
            this.element.style.zIndex = '9999';
            
            // 启用拖拽（窗口模式下需要）
            if (this.draggable) {
                this.enableDrag();
            }
            
            // 更新按钮图标和提示
            const modeToggleBtn = this.element.querySelector('.mode-toggle-button');
            if (modeToggleBtn) {
                modeToggleBtn.textContent = '⛶';
                modeToggleBtn.title = '切换到全屏模式';
            }
            
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
     * ✅ 启用拖拽功能（仅窗口模式）
     */
    enableDrag() {
        if (!this.element) return;
        
        let isDragging = false;
        let dragStartX = 0;
        let dragStartY = 0;
        let initialLeft = 0;
        let initialTop = 0;
        
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
            this.element.style.transition = 'all 0.3s';
        });
        
        // Pointer Cancel (绑定到 document)
        document.addEventListener('pointercancel', () => {
            isDragging = false;
            this.element.classList.remove('dragging');
            this.element.style.transition = 'all 0.3s';
        });
    }
    
    /**
     * ✅ 禁用拖拽功能
     */
    disableDrag() {
        console.log('[FloatingPanel] 拖拽功能已禁用');
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
