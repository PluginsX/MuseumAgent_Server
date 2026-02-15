/**
 * 全局状态管理器
 * 使用观察者模式，集中管理应用状态
 */

export class StateManager {
    constructor() {
        this.state = {
            // 认证状态
            auth: {
                isAuthenticated: false,
                sessionId: null,
                username: null,
                serverUrl: null
            },
            
            // 连接状态
            connection: {
                isConnected: false,
                reconnecting: false,
                lastHeartbeat: null
            },
            
            // 会话配置
            session: {
                requireTTS: true,
                autoPlay: true,
                functionCalling: [],
                platform: 'WEB'
            },
            
            // 消息状态
            messages: [],
            
            // 录音状态
            recording: {
                isRecording: false,
                vadEnabled: true,
                duration: 0,
                vadParams: {
                    silenceThreshold: 0.01,
                    silenceDuration: 1500,
                    speechThreshold: 0.05,
                    minSpeechDuration: 300,
                    preSpeechPadding: 300,
                    postSpeechPadding: 500
                }
            },
            
            // 音频播放状态
            audio: {
                isPlaying: false,
                currentMessageId: null
            }
        };
        
        this.listeners = new Map();
    }

    /**
     * 获取状态
     */
    getState(path) {
        if (!path) return this.state;
        
        const keys = path.split('.');
        let value = this.state;
        
        for (const key of keys) {
            value = value[key];
            if (value === undefined) return undefined;
        }
        
        return value;
    }

    /**
     * 设置状态
     */
    setState(path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        
        let target = this.state;
        for (const key of keys) {
            if (!target[key]) target[key] = {};
            target = target[key];
        }
        
        const oldValue = target[lastKey];
        target[lastKey] = value;
        
        // 通知监听器
        this._notify(path, value, oldValue);
    }

    /**
     * 更新状态（合并对象）
     */
    updateState(path, updates) {
        const current = this.getState(path);
        if (typeof current === 'object' && !Array.isArray(current)) {
            this.setState(path, { ...current, ...updates });
        } else {
            this.setState(path, updates);
        }
    }

    /**
     * 订阅状态变化
     */
    subscribe(path, callback) {
        if (!this.listeners.has(path)) {
            this.listeners.set(path, new Set());
        }
        
        this.listeners.get(path).add(callback);
        
        // 返回取消订阅函数
        return () => {
            const listeners = this.listeners.get(path);
            if (listeners) {
                listeners.delete(callback);
            }
        };
    }

    /**
     * 通知监听器
     */
    _notify(path, newValue, oldValue) {
        // 通知精确路径的监听器
        const listeners = this.listeners.get(path);
        if (listeners) {
            listeners.forEach(callback => {
                callback(newValue, oldValue);
            });
        }
        
        // 通知父路径的监听器
        const parts = path.split('.');
        for (let i = parts.length - 1; i > 0; i--) {
            const parentPath = parts.slice(0, i).join('.');
            const parentListeners = this.listeners.get(parentPath);
            if (parentListeners) {
                parentListeners.forEach(callback => {
                    callback(this.getState(parentPath), null);
                });
            }
        }
    }

    /**
     * 添加消息
     */
    addMessage(message) {
        const messages = [...this.state.messages, message];
        this.setState('messages', messages);
        return message.id;
    }

    /**
     * 更新消息
     */
    updateMessage(messageId, updates) {
        const messages = this.state.messages.map(msg => 
            msg.id === messageId ? { ...msg, ...updates } : msg
        );
        this.setState('messages', messages);
    }

    /**
     * 清空消息
     */
    clearMessages() {
        this.setState('messages', []);
    }

    /**
     * 重置状态
     */
    reset() {
        this.state = {
            auth: {
                isAuthenticated: false,
                sessionId: null,
                username: null,
                serverUrl: null
            },
            connection: {
                isConnected: false,
                reconnecting: false,
                lastHeartbeat: null
            },
            session: {
                requireTTS: true,
                autoPlay: true,
                functionCalling: [],
                platform: 'WEB'
            },
            messages: [],
            recording: {
                isRecording: false,
                vadEnabled: true,
                duration: 0,
                vadParams: {
                    silenceThreshold: 0.01,
                    silenceDuration: 1500,
                    speechThreshold: 0.05,
                    minSpeechDuration: 300,
                    preSpeechPadding: 300,
                    postSpeechPadding: 500
                }
            },
            audio: {
                isPlaying: false,
                currentMessageId: null
            }
        };
        
        this._notify('', this.state, null);
    }
}

// 创建全局单例
export const stateManager = new StateManager();

