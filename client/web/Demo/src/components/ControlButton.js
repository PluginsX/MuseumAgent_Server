/**
 * 控制按钮组件
 * 悬浮在页面顶层的圆形按钮，支持单击、长按、拖拽
 */

import { GestureRecognizer } from '../utils/gesture.js';
import { createElement } from '../utils/dom.js';

// 从全局变量获取 SDK
const { Events } = window.MuseumAgentSDK;

export class ControlButton {
    constructor(client, options = {}) {
        this.client = client;
        this.options = {
            onMenuSelect: options.onMenuSelect || null,
            defaultPosition: options.defaultPosition || 'bottom-right'
        };
        
        this.element = null;
        this.menu = null;
        this.gesture = null;
        this.isVisible = true;
        this.dragStartPosition = { x: 0, y: 0 };
        
        this.init();
    }
    
    /**
     * 初始化
     */
    init() {
        this.createElement();
        this.updateSize();
        this.setDefaultPosition();
        this.bindGestures();
        this.bindClientEvents();
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => {
            this.updateSize();
            this.constrainPosition();
        });
    }
    
    /**
     * 创建元素
     */
    createElement() {
        this.element = createElement('div', {
            className: 'control-button'
        });
        
        // 设置默认图标
        this.setIcon('🎤');
        
        // 添加到页面
        document.body.appendChild(this.element);
    }
    
    /**
     * 设置图标
     */
    setIcon(icon) {
        this.element.textContent = icon;
    }
    
    /**
     * 更新大小
     */
    updateSize() {
        // 根据视口尺寸计算按钮大小
        const minDimension = Math.min(window.innerWidth, window.innerHeight);
        const size = Math.max(30, Math.min(100, minDimension * 0.1));
        
        this.element.style.width = size + 'px';
        this.element.style.height = size + 'px';
        this.element.style.fontSize = (size * 0.5) + 'px';
    }
    
    /**
     * 设置默认位置
     */
    setDefaultPosition() {
        const rect = this.element.getBoundingClientRect();
        const padding = 20;
        
        let x, y;
        
        switch (this.options.defaultPosition) {
            case 'bottom-right':
                x = window.innerWidth - rect.width - padding;
                y = window.innerHeight - rect.height - padding;
                break;
            case 'bottom-left':
                x = padding;
                y = window.innerHeight - rect.height - padding;
                break;
            case 'top-right':
                x = window.innerWidth - rect.width - padding;
                y = padding;
                break;
            case 'top-left':
                x = padding;
                y = padding;
                break;
            default:
                x = window.innerWidth - rect.width - padding;
                y = window.innerHeight - rect.height - padding;
        }
        
        this.setPosition(x, y);
    }
    
    /**
     * 设置位置
     */
    setPosition(x, y) {
        this.element.style.left = x + 'px';
        this.element.style.top = y + 'px';
    }
    
    /**
     * 约束位置（限制在页面范围内）
     */
    constrainPosition() {
        const rect = this.element.getBoundingClientRect();
        const maxX = window.innerWidth - rect.width;
        const maxY = window.innerHeight - rect.height;
        
        const x = Math.max(0, Math.min(rect.left, maxX));
        const y = Math.max(0, Math.min(rect.top, maxY));
        
        this.setPosition(x, y);
    }
    
    /**
     * 绑定手势
     */
    bindGestures() {
        this.gesture = new GestureRecognizer(this.element, {
            longPressDelay: 500,
            moveThreshold: 10
        });
        
        // 单击 - 切换语音录制
        this.gesture.on('click', () => {
            this.handleClick();
        });
        
        // 长按 - 显示菜单
        this.gesture.on('longPress', () => {
            this.handleLongPress();
        });
        
        // 拖拽开始
        this.gesture.on('dragStart', (point) => {
            this.handleDragStart(point);
        });
        
        // 拖拽移动
        this.gesture.on('dragMove', (point, deltaX, deltaY) => {
            this.handleDragMove(point, deltaX, deltaY);
        });
        
        // 拖拽结束
        this.gesture.on('dragEnd', () => {
            this.handleDragEnd();
        });
    }
    
    /**
     * 绑定客户端事件
     */
    bindClientEvents() {
        // 监听录音状态
        this.client.on(Events.RECORDING_START, () => {
            this.setIcon('⏹️');
            this.element.classList.add('recording');
        });
        
        this.client.on(Events.RECORDING_STOP, () => {
            this.setIcon('🎤');
            this.element.classList.remove('recording');
        });
    }
    
    /**
     * 处理单击
     */
    async handleClick() {
        // 如果菜单打开，先关闭菜单
        if (this.menu) {
            this.hideMenu();
            return;
        }
        
        // 切换语音录制
        try {
            if (this.client.isRecording) {
                await this.client.stopRecording();
            } else {
                // ✅ 获取设置面板的待更新配置
                const settingsPanel = window._currentSettingsPanel;
                const updates = settingsPanel ? settingsPanel.getPendingUpdates() : {};
                
                // ✅ 传递当前配置参数 + 待更新配置
                await this.client.startRecording({
                    vadEnabled: this.client.vadEnabled,
                    vadParams: this.client.config.vadParams,
                    requireTTS: this.client.config.requireTTS,
                    enableSRS: this.client.config.enableSRS,
                    functionCalling: this.client.config.functionCalling.length > 0 ? this.client.config.functionCalling : undefined,
                    ...updates
                });
                
                // ✅ 发送成功后清除更新开关
                if (settingsPanel && Object.keys(updates).length > 0) {
                    settingsPanel.clearUpdateSwitches();
                    console.log('[ControlButton] 已发送配置更新:', updates);
                }
            }
        } catch (error) {
            console.error('[ControlButton] 录音失败:', error);
            // ✅ 不要弹出 alert，只在控制台输出错误
            console.error('[ControlButton] 录音错误详情:', error.message);
        }
    }
    
    /**
     * 处理长按
     */
    handleLongPress() {
        this.showMenu();
    }
    
    /**
     * 处理拖拽开始
     */
    handleDragStart(point) {
        const rect = this.element.getBoundingClientRect();
        
        // ✅ 记录鼠标相对于按钮左上角的偏移量
        this.dragOffset = {
            x: point.x - rect.left,
            y: point.y - rect.top
        };
        
        console.log('[ControlButton] 拖拽开始:', {
            point: point,
            rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
            offset: this.dragOffset
        });
        
        this.element.classList.add('dragging');
        
        // 如果菜单打开，关闭菜单
        if (this.menu) {
            this.hideMenu();
        }
    }
    
    /**
     * 处理拖拽移动
     */
    handleDragMove(point, deltaX, deltaY) {
        // ✅ 使用鼠标当前位置减去偏移量，实现实时跟手
        let newX = point.x - this.dragOffset.x;
        let newY = point.y - this.dragOffset.y;
        
        // ✅ 实时约束位置（在设置之前约束）
        const rect = this.element.getBoundingClientRect();
        const maxX = window.innerWidth - rect.width;
        const maxY = window.innerHeight - rect.height;
        
        newX = Math.max(0, Math.min(newX, maxX));
        newY = Math.max(0, Math.min(newY, maxY));
        
        console.log('[ControlButton] 拖拽移动:', {
            point: point,
            offset: this.dragOffset,
            newX: newX,
            newY: newY,
            deltaX: deltaX,
            deltaY: deltaY,
            constrained: {
                maxX: maxX,
                maxY: maxY
            }
        });
        
        // ✅ 设置约束后的位置
        this.setPosition(newX, newY);
    }
    
    /**
     * 处理拖拽结束
     */
    handleDragEnd() {
        this.element.classList.remove('dragging');
    }
    
    /**
     * 显示菜单
     */
    showMenu() {
        // 如果菜单已存在，先移除
        if (this.menu) {
            this.hideMenu();
        }
        
        // 创建菜单
        this.menu = createElement('div', {
            className: 'control-menu'
        });
        
        // 计算菜单方向
        const buttonRect = this.element.getBoundingClientRect();
        const spaceAbove = buttonRect.top;
        const spaceBelow = window.innerHeight - buttonRect.bottom;
        const direction = spaceBelow >= spaceAbove ? 'down' : 'up';
        
        this.menu.classList.add('menu-' + direction);
        
        // 创建菜单项
        const menuItems = [
            { icon: '⚙', action: 'settings', label: '设置' },
            { icon: '✉', action: 'chat', label: '聊天' }
        ];
        
        menuItems.forEach(item => {
            const menuItem = createElement('button', {
                className: 'control-menu-item',
                textContent: item.icon
            });
            
            menuItem.setAttribute('data-action', item.action);
            menuItem.setAttribute('title', item.label);
            
            menuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleMenuItemClick(item.action);
            });
            
            this.menu.appendChild(menuItem);
        });
        
        // ✅ 添加到页面（先添加才能获取尺寸）
        document.body.appendChild(this.menu);
        
        // ✅ 获取菜单尺寸
        const menuRect = this.menu.getBoundingClientRect();
        
        // ✅ 计算菜单位置（与按钮左右居中对齐）
        const buttonCenterX = buttonRect.left + buttonRect.width / 2;
        const menuLeft = buttonCenterX - menuRect.width / 2;
        
        // ✅ 设置菜单位置
        if (direction === 'down') {
            this.menu.style.left = menuLeft + 'px';
            this.menu.style.top = (buttonRect.bottom + 10) + 'px';
        } else {
            this.menu.style.left = menuLeft + 'px';
            this.menu.style.bottom = (window.innerHeight - buttonRect.top + 10) + 'px';
        }
        
        // 点击其他地方关闭菜单
        setTimeout(() => {
            document.addEventListener('click', this.handleDocumentClick);
        }, 0);
    }
    
    /**
     * 隐藏菜单
     */
    hideMenu() {
        if (this.menu) {
            document.removeEventListener('click', this.handleDocumentClick);
            this.menu.remove();
            this.menu = null;
        }
    }
    
    /**
     * 处理文档点击（关闭菜单）
     */
    handleDocumentClick = (e) => {
        if (this.menu && !this.menu.contains(e.target) && !this.element.contains(e.target)) {
            this.hideMenu();
        }
    }
    
    /**
     * 处理菜单项点击
     */
    handleMenuItemClick(action) {
        this.hideMenu();
        
        if (this.options.onMenuSelect) {
            this.options.onMenuSelect(action);
        }
    }
    
    /**
     * 显示
     */
    show() {
        this.isVisible = true;
        this.element.style.display = 'flex';
    }
    
    /**
     * 隐藏
     */
    hide() {
        this.isVisible = false;
        this.element.style.display = 'none';
        
        // 隐藏菜单
        if (this.menu) {
            this.hideMenu();
        }
    }
    
    /**
     * 销毁
     */
    destroy() {
        if (this.gesture) {
            this.gesture.destroy();
        }
        
        if (this.menu) {
            this.hideMenu();
        }
        
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

