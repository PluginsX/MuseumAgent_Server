/**
 * 悬浮面板基类
 * ✅ 重构版本：支持传入已有组件实例（单例模式）
 * 用于包装设置和聊天组件，提供全屏显示和关闭功能
 */

import { createElement } from '../utils/dom.js';

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
        
        this.options = {
            title: options.title || '',
            onClose: options.onClose || null,
            showFullscreenButton: options.showFullscreenButton !== false
        };
        
        this.element = null;
        this.contentContainer = null;
        
        this.init();
    }
    
    /**
     * 初始化
     */
    init() {
        // ✅ 面板打开时禁用 Unity 输入
        this.disableUnityInput();
        
        this.createElement();
        this.attachComponent();
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
        // 创建全屏容器
        this.element = createElement('div', {
            className: 'floating-panel'
        });
        
        // 创建头部
        const header = this.createHeader();
        this.element.appendChild(header);
        
        // 创建内容区域
        this.contentContainer = createElement('div', {
            className: 'floating-panel-content'
        });
        this.element.appendChild(this.contentContainer);
        
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
        
        // 全屏按钮
        if (this.options.showFullscreenButton) {
            const fullscreenBtn = createElement('button', {
                className: 'floating-panel-button fullscreen-button',
                textContent: '◱',
                title: '全屏'
            });
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
            buttonContainer.appendChild(fullscreenBtn);
        }
        
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
            }
        } else {
            // 旧模式：创建新组件实例
            this.component = new this.ComponentClass(this.contentContainer, this.client);
        }
    }
    
    /**
     * 切换全屏
     */
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            // 进入全屏
            if (this.element.requestFullscreen) {
                this.element.requestFullscreen();
            } else if (this.element.webkitRequestFullscreen) {
                this.element.webkitRequestFullscreen();
            } else if (this.element.msRequestFullscreen) {
                this.element.msRequestFullscreen();
            }
        } else {
            // 退出全屏
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        }
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
     * ✅ 销毁（不销毁外部组件实例）
     */
    destroy() {
        // ✅ 面板关闭时恢复 Unity 输入
        this.enableUnityInput();
        
        // ✅ 如果是外部组件，只隐藏，不销毁
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
