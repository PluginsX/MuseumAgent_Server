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
    
    // SVG 图标路径常量
    static ICONS = {
        voice:          './res/svg/bu_voice_normal.svg',      // 未录音时的语音图标
        voiceHighlight: './res/svg/bu_voice_highlight.svg',   // 录音中的高亮图标
        settings:       './res/svg/bu_settings_normal.svg',
        chat:           './res/svg/bu_message_normal.svg'
    };

    /**
     * 创建元素
     */
    createElement() {
        this.element = createElement('div', {
            className: 'control-button'
        });
        
        // 设置默认图标（语音按钮）
        this.setIcon(ControlButton.ICONS.voice);
        
        // 添加到页面
        document.body.appendChild(this.element);
    }
    
    /**
     * 设置图标（替换为 SVG img）
     * @param {string} src - SVG 文件路径
     */
    setIcon(src) {
        this.element.innerHTML = '';
        const img = document.createElement('img');
        
        // ✅ 解析为相对于页面根目录的绝对路径
        const absolutePath = src.startsWith('./') ? src.substring(2) : src;
        const fullUrl = new URL(absolutePath, window.location.origin).href;
        
        img.src = fullUrl;
        img.alt = '';
        img.draggable = false;
        // ✅ 不设置内联样式，让 CSS 完全控制
        this.element.appendChild(img);
        
        // ✅ 监听加载和错误
        img.onload = () => {
            console.log('[ControlButton] SVG 加载成功:', fullUrl, '尺寸:', img.naturalWidth, 'x', img.naturalHeight);
        };
        img.onerror = () => {
            console.error('[ControlButton] SVG 加载失败:', fullUrl, '当前页面 URL:', window.location.href);
        };
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
            this.setIcon(ControlButton.ICONS.voiceHighlight);  // ✅ 录音时显示高亮图标
            this.element.classList.add('recording');
        });
        
        this.client.on(Events.RECORDING_STOP, () => {
            this.setIcon(ControlButton.ICONS.voice);  // ✅ 停止录音时显示普通图标
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
     * ✅ 四方位智能定位：以控制按钮为中心，根据四周可用空间选择最优角落展开菜单
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
        
        // ── 步骤1：获取按钮几何信息 ──
        const buttonRect = this.element.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        
        // 按钮中心坐标
        const cx = buttonRect.left + buttonRect.width / 2;
        const cy = buttonRect.top  + buttonRect.height / 2;
        
        // 中心到四边的距离
        const Dis_Top    = cy;
        const Dis_Bottom = vh - cy;
        const Dis_Left   = cx;
        const Dis_Right  = vw - cx;
        
        // ── 步骤2：决策方向 ──
        // ToB: true = 菜单在按钮下方，false = 菜单在按钮上方
        const ToB = Dis_Bottom >= Dis_Top;
        // LoR: true = 菜单在按钮右侧，false = 菜单在按钮左侧
        const LoR = Dis_Right  >= Dis_Left;
        
        // ── 步骤3：设置排列方向 ──
        // ToB=true(下方)：从上到下排列，第一项最靠近按钮
        // ToB=false(上方)：从下到上排列，第一项最靠近按钮
        this.menu.style.flexDirection = ToB ? 'column' : 'column-reverse';
        
        // ── 步骤4：创建菜单项 ──
        const menuItems = [
            { icon: ControlButton.ICONS.settings, action: 'settings', label: '设置' },
            { icon: ControlButton.ICONS.chat,     action: 'chat',     label: '聊天' }
        ];
        
        menuItems.forEach(item => {
            const menuItem = createElement('button', {
                className: 'control-menu-item'
            });
            const img = document.createElement('img');
            
            // ✅ 解析为相对于页面根目录的绝对路径
            const absolutePath = item.icon.startsWith('./') ? item.icon.substring(2) : item.icon;
            const fullUrl = new URL(absolutePath, window.location.origin).href;
            
            img.src = fullUrl;
            img.alt = '';
            img.draggable = false;
            // ✅ 不设置内联样式，让 CSS 完全控制
            menuItem.appendChild(img);
            
            // ✅ 监听加载和错误
            img.onload = () => {
                console.log('[ControlButton] 菜单项 SVG 加载成功:', fullUrl, '尺寸:', img.naturalWidth, 'x', img.naturalHeight);
            };
            img.onerror = () => {
                console.error('[ControlButton] 菜单项 SVG 加载失败:', fullUrl, '当前页面 URL:', window.location.href);
            };
            
            menuItem.setAttribute('data-action', item.action);
            menuItem.setAttribute('title', item.label);
            
            menuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleMenuItemClick(item.action);
            });
            
            this.menu.appendChild(menuItem);
        });
        
        // ── 步骤5：添加到页面并设置宽度 ──
        document.body.appendChild(this.menu);
        
        // 菜单容器宽度与按钮一致
        this.menu.style.width = buttonRect.width + 'px';
        
        // ── 步骤6：计算菜单容器定位 ──
        // 九宫格逻辑：
        //   LoR=true  → 菜单在按钮右侧 → 菜单左边缘对齐按钮右边缘（即 left = buttonRect.right）
        //   LoR=false → 菜单在按钮左侧 → 菜单右边缘对齐按钮左边缘（即 right = vw - buttonRect.left）
        //   ToB=true  → 菜单在按钮下方 → 菜单上边缘对齐按钮下边缘（即 top = buttonRect.bottom）
        //   ToB=false → 菜单在按钮上方 → 菜单下边缘对齐按钮上边缘（即 bottom = vh - buttonRect.top）
        
        if (LoR) {
            this.menu.style.left  = buttonRect.right + 'px';
            this.menu.style.right = '';
        } else {
            this.menu.style.right = (vw - buttonRect.left) + 'px';
            this.menu.style.left  = '';
        }
        
        if (ToB) {
            this.menu.style.top    = buttonRect.bottom + 'px';
            this.menu.style.bottom = '';
        } else {
            this.menu.style.bottom = (vh - buttonRect.top) + 'px';
            this.menu.style.top    = '';
        }
        
        // ── 步骤7：靠近按钮的角圆角归零（气泡效果）──
        // ToB=true,  LoR=true  → 菜单从左上角展开 → 左上角归零
        // ToB=true,  LoR=false → 菜单从右上角展开 → 右上角归零
        // ToB=false, LoR=true  → 菜单从左下角展开 → 左下角归零
        // ToB=false, LoR=false → 菜单从右下角展开 → 右下角归零
        // 圆角值使用固定像素（容器宽的一半），避免非正方形容器用百分比导致椭圆拉伸
        const r = (buttonRect.width / 2) + 'px';
        const zero = '0';
        this.menu.style.borderTopLeftRadius     = ( ToB &&  LoR) ? zero : r;
        this.menu.style.borderTopRightRadius    = ( ToB && !LoR) ? zero : r;
        this.menu.style.borderBottomLeftRadius  = (!ToB &&  LoR) ? zero : r;
        this.menu.style.borderBottomRightRadius = (!ToB && !LoR) ? zero : r;
        
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

