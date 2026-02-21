/**
 * 事件总线
 * 提供发布-订阅模式的事件系统
 */

export class EventBus {
    constructor() {
        this.events = new Map();
    }

    /**
     * 订阅事件
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     * @returns {Function} 取消订阅函数
     */
    on(event, callback) {
        if (!this.events.has(event)) {
            this.events.set(event, new Set());
        }
        this.events.get(event).add(callback);
        
        // 返回取消订阅函数
        return () => {
            const callbacks = this.events.get(event);
            if (callbacks) {
                callbacks.delete(callback);
            }
        };
    }

    /**
     * 订阅一次性事件
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     * @returns {Function} 取消订阅函数
     */
    once(event, callback) {
        const wrapper = (...args) => {
            callback(...args);
            this.off(event, wrapper);
        };
        return this.on(event, wrapper);
    }

    /**
     * 取消订阅
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数（可选，不传则清空所有）
     */
    off(event, callback) {
        const callbacks = this.events.get(event);
        if (callbacks) {
            if (callback) {
                callbacks.delete(callback);
            } else {
                callbacks.clear();
            }
        }
    }

    /**
     * 触发事件
     * @param {string} event - 事件名称
     * @param {...any} args - 参数
     */
    emit(event, ...args) {
        const callbacks = this.events.get(event);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(...args);
                } catch (error) {
                    console.error(`[EventBus] 事件处理错误 [${event}]:`, error);
                }
            });
        }
    }

    /**
     * 清空所有事件
     */
    clear() {
        this.events.clear();
    }
}

