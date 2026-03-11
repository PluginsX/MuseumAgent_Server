/**
 * 控制按钮组件
 * 悬浮在页面顶层的圆形按钮，支持单击、长按、拖拽
 * ✅ 现代化方案：Transform + Pointer Events + RAF
 */

import { createElement } from '../utils/dom.js';

// 从全局变量获取 SDK
const { Events } = window.MuseumAgentSDK;

export class ControlButton {
    constructor(client, agentController, options = {}) {
        this.client = client;
        this.agentController = agentController;  // ✅ 引用 AgentController
        this.options = {
            onMenuSelect: options.onMenuSelect || null,
            defaultPosition: options.defaultPosition || 'bottom-right'
        };
        
        this.element = null;
        this.menu = null;
        this.isVisible = true;
        
        // ✅ 拖拽状态（单一数据源）
        this.position = { x: 0, y: 0 };
        this.buttonSize = 60;  // 固定尺寸
        this.isDragging = false;
        this.dragStartOffset = { x: 0, y: 0 };
        this.rafId = null;
        
        // ✅ 手势识别状态
        this.gestureState = {
            isPressed: false,
            startX: 0,
            startY: 0,
            startTime: 0,
            longPressTimer: null,
            longPressTriggered: false,
            moveThreshold: 10,
            longPressDelay: 500
        };
        
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
        // 根据视口尺寸计算按钮大小（增大30%）
        const minDimension = Math.min(window.innerWidth, window.innerHeight);
        const baseSize = minDimension * 0.1;
        const size = Math.max(40, Math.min(130, baseSize));  // 原值: 30-100, 现值: 39-130
        
        this.buttonSize = size;  // ✅ 更新逻辑尺寸
        this.element.style.width = size + 'px';
        this.element.style.height = size + 'px';
        this.element.style.fontSize = (size * 0.5) + 'px';
    }
    
    /**
     * 设置默认位置
     */
    setDefaultPosition() {
        const padding = 20;
        
        switch (this.options.defaultPosition) {
            case 'bottom-right':
                this.position.x = window.innerWidth - this.buttonSize - padding;
                this.position.y = window.innerHeight - this.buttonSize - padding;
                break;
            case 'bottom-left':
                this.position.x = padding;
                this.position.y = window.innerHeight - this.buttonSize - padding;
                break;
            case 'top-right':
                this.position.x = window.innerWidth - this.buttonSize - padding;
                this.position.y = padding;
                break;
            case 'top-left':
                this.position.x = padding;
                this.position.y = padding;
                break;
            default:
                this.position.x = window.innerWidth - this.buttonSize - padding;
                this.position.y = window.innerHeight - this.buttonSize - padding;
        }
        
        this.updatePosition();
    }
    
    /**
     * ✅ 更新位置（使用 transform，GPU 加速）
     */
    updatePosition() {
        this.element.style.transform = `translate(${this.position.x}px, ${this.position.y}px)`;
    }
    
    /**
     * 约束位置（限制在页面范围内）
     */
    constrainPosition() {
        const maxX = window.innerWidth - this.buttonSize;
        const maxY = window.innerHeight - this.buttonSize;
        
        this.position.x = Math.max(0, Math.min(this.position.x, maxX));
        this.position.y = Math.max(0, Math.min(this.position.y, maxY));
        
        this.updatePosition();
    }
    
    /**
     * ✅ 绑定手势（使用 Pointer Events）
     */
    bindGestures() {
        // Pointer Down
        this.element.addEventListener('pointerdown', (e) => {
            // ✅ 只在按钮自身上阻止默认行为
            if (e.target === this.element || this.element.contains(e.target)) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            // ✅ 自动捕获后续事件
            this.element.setPointerCapture(e.pointerId);
            
            // 记录手势状态
            this.gestureState.isPressed = true;
            this.gestureState.startX = e.clientX;
            this.gestureState.startY = e.clientY;
            this.gestureState.startTime = Date.now();
            this.gestureState.longPressTriggered = false;
            
            // 启动长按定时器
            this.gestureState.longPressTimer = setTimeout(() => {
                if (this.gestureState.isPressed && !this.isDragging) {
                    this.gestureState.longPressTriggered = true;
                    this.handleLongPress();
                }
            }, this.gestureState.longPressDelay);
        });
        
        // Pointer Move
        this.element.addEventListener('pointermove', (e) => {
            if (!this.gestureState.isPressed) return;
            
            // ✅ 只在拖拽时阻止默认行为
            if (this.isDragging || Math.sqrt(
                Math.pow(e.clientX - this.gestureState.startX, 2) + 
                Math.pow(e.clientY - this.gestureState.startY, 2)
            ) >= this.gestureState.moveThreshold) {
                e.preventDefault();
            }
            
            const deltaX = e.clientX - this.gestureState.startX;
            const deltaY = e.clientY - this.gestureState.startY;
            const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            
            // 超过阈值，进入拖拽模式
            if (distance >= this.gestureState.moveThreshold) {
                // 取消长按
                if (this.gestureState.longPressTimer) {
                    clearTimeout(this.gestureState.longPressTimer);
                    this.gestureState.longPressTimer = null;
                }
                
                // 开始拖拽
                if (!this.isDragging) {
                    this.isDragging = true;
                    this.dragStartOffset = {
                        x: e.clientX - this.position.x,
                        y: e.clientY - this.position.y
                    };
                    this.element.classList.add('dragging');
                    
                    // 关闭菜单
                    if (this.menu) {
                        this.hideMenu();
                    }
                }
                
                // ✅ 拖拽移动（实时跟手）
                this.position.x = e.clientX - this.dragStartOffset.x;
                this.position.y = e.clientY - this.dragStartOffset.y;
                
                // 约束范围
                const maxX = window.innerWidth - this.buttonSize;
                const maxY = window.innerHeight - this.buttonSize;
                this.position.x = Math.max(0, Math.min(this.position.x, maxX));
                this.position.y = Math.max(0, Math.min(this.position.y, maxY));
                
                // ✅ 使用 RAF 批量更新
                if (!this.rafId) {
                    this.rafId = requestAnimationFrame(() => {
                        this.updatePosition();
                        this.rafId = null;
                    });
                }
            }
        });
        
        // Pointer Up
        this.element.addEventListener('pointerup', (e) => {
            if (!this.gestureState.isPressed) return;
            
            // 释放捕获
            this.element.releasePointerCapture(e.pointerId);
            
            // 取消长按定时器
            if (this.gestureState.longPressTimer) {
                clearTimeout(this.gestureState.longPressTimer);
                this.gestureState.longPressTimer = null;
            }
            
            // 取消 RAF
            if (this.rafId) {
                cancelAnimationFrame(this.rafId);
                this.rafId = null;
            }
            
            const deltaX = e.clientX - this.gestureState.startX;
            const deltaY = e.clientY - this.gestureState.startY;
            const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            const duration = Date.now() - this.gestureState.startTime;
            
            if (this.isDragging) {
                // 结束拖拽
                this.isDragging = false;
                this.element.classList.remove('dragging');
            } else if (!this.gestureState.longPressTriggered && 
                       distance < this.gestureState.moveThreshold && 
                       duration < 500) {
                // 单击
                this.handleClick();
            }
            
            // 重置状态
            this.gestureState.isPressed = false;
        });
        
        // Pointer Cancel
        this.element.addEventListener('pointercancel', (e) => {
            if (this.gestureState.longPressTimer) {
                clearTimeout(this.gestureState.longPressTimer);
                this.gestureState.longPressTimer = null;
            }
            if (this.rafId) {
                cancelAnimationFrame(this.rafId);
                this.rafId = null;
            }
            this.isDragging = false;
            this.gestureState.isPressed = false;
            this.element.classList.remove('dragging');
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
                // ✅ 通过 AgentController 获取设置面板的待更新配置
                const settingsPanel = this.agentController ? this.agentController.getSettingsPanel() : null;
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
        
        // ✅ 设置菜单宽度与按钮宽度一致
        this.menu.style.width = buttonRect.width + 'px';
        
        // ✅ 计算菜单位置（与按钮左右对齐）
        const menuLeft = buttonRect.left;
        
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
     * 设置视图模式（Unity 模式 / 网页模式）
     * @param {string} mode - 'unity' 或 'web'
     */
    setViewMode(mode) {
        console.log('[ControlButton] 切换到', mode, '模式');
        
        const doc = document.body;
        
        if (mode === 'unity') {
            // Unity 模式：禁用右键、选择等
            doc.classList.add('unity-mode');
            doc.classList.remove('web-mode');
        } else if (mode === 'web') {
            // 网页模式：允许正常交互
            doc.classList.add('web-mode');
            doc.classList.remove('unity-mode');
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
        // 清理定时器
        if (this.gestureState.longPressTimer) {
            clearTimeout(this.gestureState.longPressTimer);
        }
        
        // 清理 RAF
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
        }
        
        if (this.menu) {
            this.hideMenu();
        }
        
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

