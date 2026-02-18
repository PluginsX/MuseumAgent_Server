/**
 * 事件总线
 * 用于模块间解耦通信
 */

export class EventBus {
    constructor() {
        this.events = new Map();
    }

    /**
     * 订阅事件
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

// 创建全局单例
export const eventBus = new EventBus();

// 定义事件常量
export const Events = {
    // 认证事件
    AUTH_LOGIN_SUCCESS: 'auth:login:success',
    AUTH_LOGIN_FAILED: 'auth:login:failed',
    AUTH_LOGOUT: 'auth:logout',
    
    // 连接事件
    CONNECTION_OPEN: 'connection:open',
    CONNECTION_CLOSE: 'connection:close',
    CONNECTION_ERROR: 'connection:error',
    CONNECTION_RECONNECTING: 'connection:reconnecting',
    
    // 会话事件
    SESSION_REGISTERED: 'session:registered',
    SESSION_EXPIRED: 'session:expired',
    SESSION_UPDATED: 'session:updated',
    
    // 消息事件
    MESSAGE_SENT: 'message:sent',
    MESSAGE_RECEIVED: 'message:received',
    MESSAGE_TEXT_CHUNK: 'message:text:chunk',
    MESSAGE_VOICE_CHUNK: 'message:voice:chunk',
    MESSAGE_COMPLETE: 'message:complete',
    MESSAGE_ERROR: 'message:error',
    
    // 打断事件
    REQUEST_INTERRUPTED: 'request:interrupted',
    
    // 函数调用事件
    FUNCTION_CALL: 'function:call',
    
    // 录音事件
    RECORDING_START: 'recording:start',
    RECORDING_STOP: 'recording:stop',
    RECORDING_ERROR: 'recording:error',
    RECORDING_DATA: 'recording:data',
    
    // VAD 事件
    VAD_VOICE_START: 'vad:voice:start',
    VAD_VOICE_END: 'vad:voice:end',
    
    // 音频播放事件
    AUDIO_PLAY_START: 'audio:play:start',
    AUDIO_PLAY_END: 'audio:play:end',
    AUDIO_PLAY_ERROR: 'audio:play:error',
    
    // UI 事件
    UI_SHOW_ERROR: 'ui:show:error',
    UI_SHOW_SUCCESS: 'ui:show:success',
    UI_SHOW_LOADING: 'ui:show:loading',
    UI_HIDE_LOADING: 'ui:hide:loading'
};

