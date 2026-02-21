/**
 * 手势识别工具
 * 用于识别单击、长按、拖拽等手势
 */

export class GestureRecognizer {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            longPressDelay: options.longPressDelay || 500,  // 长按延迟（毫秒）
            moveThreshold: options.moveThreshold || 10,     // 移动阈值（像素）
            clickMaxDuration: options.clickMaxDuration || 500, // 单击最大时长（毫秒）
            ...options
        };
        
        this.state = {
            isPressed: false,
            isDragging: false,
            startX: 0,
            startY: 0,
            currentX: 0,
            currentY: 0,
            startTime: 0,
            longPressTimer: null
        };
        
        this.handlers = {
            onClick: null,
            onLongPress: null,
            onDragStart: null,
            onDragMove: null,
            onDragEnd: null
        };
        
        this.init();
    }
    
    /**
     * 初始化
     */
    init() {
        this.bindEvents();
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 鼠标事件
        this.element.addEventListener('mousedown', (e) => this.handlePointerDown(e));
        document.addEventListener('mousemove', (e) => this.handlePointerMove(e));
        document.addEventListener('mouseup', (e) => this.handlePointerUp(e));
        
        // 触控事件
        this.element.addEventListener('touchstart', (e) => this.handlePointerDown(e), { passive: false });
        document.addEventListener('touchmove', (e) => this.handlePointerMove(e), { passive: false });
        document.addEventListener('touchend', (e) => this.handlePointerUp(e));
        document.addEventListener('touchcancel', (e) => this.handlePointerUp(e));
        
        // 防止上下文菜单
        this.element.addEventListener('contextmenu', (e) => {
            if (this.state.isPressed) {
                e.preventDefault();
            }
        });
    }
    
    /**
     * 处理指针按下
     */
    handlePointerDown(e) {
        // 阻止默认行为
        e.preventDefault();
        
        // 获取坐标
        const point = this.getPointerPosition(e);
        
        // 重置状态
        this.state.isPressed = true;
        this.state.isDragging = false;
        this.state.startX = point.x;
        this.state.startY = point.y;
        this.state.currentX = point.x;
        this.state.currentY = point.y;
        this.state.startTime = Date.now();
        
        // 启动长按定时器
        this.state.longPressTimer = setTimeout(() => {
            if (this.state.isPressed && !this.state.isDragging) {
                this.triggerLongPress();
            }
        }, this.options.longPressDelay);
    }
    
    /**
     * 处理指针移动
     */
    handlePointerMove(e) {
        if (!this.state.isPressed) return;
        
        // 获取坐标
        const point = this.getPointerPosition(e);
        this.state.currentX = point.x;
        this.state.currentY = point.y;
        
        // 计算移动距离
        const deltaX = point.x - this.state.startX;
        const deltaY = point.y - this.state.startY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        // 如果移动超过阈值，取消长按，进入拖拽模式
        if (distance >= this.options.moveThreshold) {
            this.cancelLongPress();
            
            if (!this.state.isDragging) {
                // 开始拖拽
                this.state.isDragging = true;
                this.triggerDragStart(point);
            } else {
                // 拖拽中
                this.triggerDragMove(point, deltaX, deltaY);
            }
        }
    }
    
    /**
     * 处理指针抬起
     */
    handlePointerUp(e) {
        if (!this.state.isPressed) return;
        
        // 取消长按定时器
        this.cancelLongPress();
        
        // 获取坐标
        const point = this.getPointerPosition(e);
        const duration = Date.now() - this.state.startTime;
        
        // 计算移动距离
        const deltaX = point.x - this.state.startX;
        const deltaY = point.y - this.state.startY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        if (this.state.isDragging) {
            // 结束拖拽
            this.triggerDragEnd(point, deltaX, deltaY);
        } else if (distance < this.options.moveThreshold && duration < this.options.clickMaxDuration) {
            // 单击
            this.triggerClick(point);
        }
        
        // 重置状态
        this.state.isPressed = false;
        this.state.isDragging = false;
    }
    
    /**
     * 获取指针位置
     */
    getPointerPosition(e) {
        if (e.touches && e.touches.length > 0) {
            return {
                x: e.touches[0].clientX,
                y: e.touches[0].clientY
            };
        } else if (e.changedTouches && e.changedTouches.length > 0) {
            return {
                x: e.changedTouches[0].clientX,
                y: e.changedTouches[0].clientY
            };
        } else {
            return {
                x: e.clientX,
                y: e.clientY
            };
        }
    }
    
    /**
     * 取消长按
     */
    cancelLongPress() {
        if (this.state.longPressTimer) {
            clearTimeout(this.state.longPressTimer);
            this.state.longPressTimer = null;
        }
    }
    
    /**
     * 触发单击
     */
    triggerClick(point) {
        if (this.handlers.onClick) {
            this.handlers.onClick(point);
        }
    }
    
    /**
     * 触发长按
     */
    triggerLongPress() {
        if (this.handlers.onLongPress) {
            this.handlers.onLongPress({
                x: this.state.startX,
                y: this.state.startY
            });
        }
    }
    
    /**
     * 触发拖拽开始
     */
    triggerDragStart(point) {
        if (this.handlers.onDragStart) {
            this.handlers.onDragStart(point);
        }
    }
    
    /**
     * 触发拖拽移动
     */
    triggerDragMove(point, deltaX, deltaY) {
        if (this.handlers.onDragMove) {
            this.handlers.onDragMove(point, deltaX, deltaY);
        }
    }
    
    /**
     * 触发拖拽结束
     */
    triggerDragEnd(point, deltaX, deltaY) {
        if (this.handlers.onDragEnd) {
            this.handlers.onDragEnd(point, deltaX, deltaY);
        }
    }
    
    /**
     * 注册事件处理器
     */
    on(event, handler) {
        if (this.handlers.hasOwnProperty('on' + event.charAt(0).toUpperCase() + event.slice(1))) {
            this.handlers['on' + event.charAt(0).toUpperCase() + event.slice(1)] = handler;
        }
    }
    
    /**
     * 销毁
     */
    destroy() {
        this.cancelLongPress();
        // 注意：这里不移除事件监听器，因为元素可能会被移除
    }
}

