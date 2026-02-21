/**
 * 悬浮面板基类
 * 用于包装设置和聊天组件，提供全屏显示和关闭功能
 */

import { createElement } from '../utils/dom.js';

export class FloatingPanel {
    constructor(ComponentClass, client, options = {}) {
        this.ComponentClass = ComponentClass;
        this.client = client;
        this.options = {
            title: options.title || '',
            onClose: options.onClose || null,
            showFullscreenButton: options.showFullscreenButton !== false
        };
        
        this.element = null;
        this.component = null;
        
        this.init();
    }
    
    /**
     * 初始化
     */
    init() {
        this.createElement();
        this.createComponent();
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
     * 创建组件
     */
    createComponent() {
        // 实例化组件
        this.component = new this.ComponentClass(this.contentContainer, this.client);
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
     * 销毁
     */
    destroy() {
        // 销毁组件
        if (this.component && typeof this.component.destroy === 'function') {
            this.component.destroy();
        }
        
        // 移除元素
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

