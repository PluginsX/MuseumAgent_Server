/**
 * 手势识别工具
 * 用于识别单击、长按、拖拽等手势
 * ✅ 重构版本：解决时序冲突，实现实时跟手拖拽
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
            longPressTimer: null,
            longPressTriggered: false  // ✅ 标记长按是否已触发
        };
        
        this.handlers = {
            onClick: null,
            onLongPress: null,
            onDragStart: null,
            onDragMove: null,
            onDragEnd: null
        };
        
        // ✅ 绑定方法到实例，避免 this 指向问题
        this.handlePointerDown = this.handlePointerDown.bind(this);
        this.handlePointerMove = this.handlePointerMove.bind(this);
        this.handlePointerUp = this.handlePointerUp.bind(this);
        
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
        // ✅ 只在元素上绑定按下事件，移动和抬起事件在按下时动态绑定
        this.element.addEventListener('mousedown', this.handlePointerDown, { passive: false });
        this.element.addEventListener('touchstart', this.handlePointerDown, { passive: false });
        
        // ✅ 防止上下文菜单
        this.element.addEventListener('contextmenu', (e) => {
            if (this.state.isPressed || this.state.isDragging) {
                e.preventDefault();
            }
        });
    }
    
    /**
     * 移除全局事件监听器
     */
    removeGlobalListeners() {
        document.removeEventListener('mousemove', this.handlePointerMove);
        document.removeEventListener('mouseup', this.handlePointerUp);
        document.removeEventListener('touchmove', this.handlePointerMove);
        document.removeEventListener('touchend', this.handlePointerUp);
        document.removeEventListener('touchcancel', this.handlePointerUp);
    }
    
    /**
     * 处理指针按下
     */
    handlePointerDown(e) {
        // ✅ 阻止默认行为和事件冒泡
        e.preventDefault();
        e.stopPropagation();
        
        // 获取坐标
        const point = this.getPointerPosition(e);
        
        console.log('[GestureRecognizer] 指针按下:', {
            x: point.x,
            y: point.y,
            type: e.type
        });
        
        // 重置状态
        this.state.isPressed = true;
        this.state.isDragging = false;
        this.state.longPressTriggered = false;
        this.state.startX = point.x;
        this.state.startY = point.y;
        this.state.currentX = point.x;
        this.state.currentY = point.y;
        this.state.startTime = Date.now();
        
        // ✅ 立即绑定全局移动和抬起事件（确保不会丢失事件）
        document.addEventListener('mousemove', this.handlePointerMove, { passive: false });
        document.addEventListener('mouseup', this.handlePointerUp, { passive: false });
        document.addEventListener('touchmove', this.handlePointerMove, { passive: false });
        document.addEventListener('touchend', this.handlePointerUp, { passive: false });
        document.addEventListener('touchcancel', this.handlePointerUp, { passive: false });
        
        console.log('[GestureRecognizer] 全局事件监听器已绑定');
        
        // 启动长按定时器
        this.state.longPressTimer = setTimeout(() => {
            if (this.state.isPressed && !this.state.isDragging && !this.state.longPressTriggered) {
                this.state.longPressTriggered = true;
                console.log('[GestureRecognizer] 触发长按');
                this.triggerLongPress();
            }
        }, this.options.longPressDelay);
    }
    
    /**
     * 处理指针移动
     */
    handlePointerMove(e) {
        if (!this.state.isPressed) return;
        
        // ✅ 阻止默认行为（防止页面滚动）
        e.preventDefault();
        
        // 获取坐标
        const point = this.getPointerPosition(e);
        this.state.currentX = point.x;
        this.state.currentY = point.y;
        
        // 计算移动距离
        const deltaX = point.x - this.state.startX;
        const deltaY = point.y - this.state.startY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        // ✅ 添加详细日志
        if (!this.state.isDragging && distance >= this.options.moveThreshold) {
            console.log('[GestureRecognizer] 开始拖拽:', {
                startX: this.state.startX,
                startY: this.state.startY,
                currentX: point.x,
                currentY: point.y,
                deltaX: deltaX,
                deltaY: deltaY,
                distance: distance,
                threshold: this.options.moveThreshold
            });
        }
        
        // 如果移动超过阈值，取消长按，进入拖拽模式
        if (distance >= this.options.moveThreshold) {
            this.cancelLongPress();
            
            if (!this.state.isDragging) {
                // ✅ 开始拖拽
                this.state.isDragging = true;
                this.triggerDragStart(point);
            }
            
            // ✅ 拖拽中（实时触发，不等待下一帧）
            console.log('[GestureRecognizer] 拖拽移动:', {
                x: point.x,
                y: point.y,
                deltaX: deltaX,
                deltaY: deltaY
            });
            this.triggerDragMove(point, deltaX, deltaY);
        }
    }
    
    /**
     * 处理指针抬起
     */
    handlePointerUp(e) {
        if (!this.state.isPressed) return;
        
        // ✅ 移除全局事件监听器
        this.removeGlobalListeners();
        
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
        } else if (!this.state.longPressTriggered && distance < this.options.moveThreshold && duration < this.options.clickMaxDuration) {
            // 单击（没有触发长按，移动距离小，时长短）
            this.triggerClick(point);
        }
        
        // 重置状态
        this.state.isPressed = false;
        this.state.isDragging = false;
        this.state.longPressTriggered = false;
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
        this.removeGlobalListeners();
        
        // 移除元素事件监听器
        this.element.removeEventListener('mousedown', this.handlePointerDown);
        this.element.removeEventListener('touchstart', this.handlePointerDown);
    }
}

