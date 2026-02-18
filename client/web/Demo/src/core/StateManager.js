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
                enableSRS: true,
                autoPlay: true,
                functionCalling: [
                    {
                        name: "play_animation",
                        description: "播放指定的动画效果，让桌面宠物做出相应动作",
                        parameters: [
                            { name: "animation_name", type: "string", description: "动画名称，如：wave(挥手)、jump(跳跃)、dance(跳舞)、sleep(睡觉)、happy(开心)" }
                        ]
                    },
                    {
                        name: "change_expression",
                        description: "改变桌面宠物的表情",
                        parameters: [
                            { name: "expression", type: "string", description: "表情类型，如：smile(微笑)、sad(伤心)、angry(生气)、surprised(惊讶)、love(爱心)" }
                        ]
                    },
                    {
                        name: "move_to_position",
                        description: "移动桌面宠物到屏幕指定位置",
                        parameters: [
                            { name: "x", type: "number", description: "X坐标（像素）" },
                            { name: "y", type: "number", description: "Y坐标（像素）" }
                        ]
                    },
                    {
                        name: "set_mood",
                        description: "设置桌面宠物的心情状态",
                        parameters: [
                            { name: "mood", type: "string", description: "心情状态，如：happy(开心)、normal(正常)、tired(疲惫)、excited(兴奋)" },
                            { name: "duration", type: "number", description: "持续时间（秒），默认60" }
                        ]
                    },
                    {
                        name: "speak_text",
                        description: "让桌面宠物说出指定文字（显示气泡对话框）",
                        parameters: [
                            { name: "text", type: "string", description: "要说的文字内容" },
                            { name: "duration", type: "number", description: "显示时长（秒），默认3" }
                        ]
                    }
                ],
                platform: 'WEB',
                functionCallingModified: false, // 标记用户是否修改过函数定义
                enableSRSModified: false // 标记用户是否修改过EnableSRS
            },
            
            // 消息状态
            messages: [],
            
            // 录音状态
            recording: {
                isRecording: false,
                vadEnabled: true,
                duration: 0,
                vadParams: {
                    silenceThreshold: 0.01,      // 静音阈值：保持不变，用于判断是否停止说话
                    silenceDuration: 800,         // 静音持续时长：1500ms → 800ms（更快结束）
                    speechThreshold: 0.02,        // 语音阈值：0.05 → 0.02（更敏感，更快开始）
                    minSpeechDuration: 200,       // 最小语音时长：300ms → 200ms（减少误判延迟）
                    preSpeechPadding: 150,        // 语音前填充：300ms → 150ms（减少预填充，更快响应）
                    postSpeechPadding: 300        // 语音后填充：500ms → 300ms（更快结束）
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
                enableSRS: true,
                autoPlay: true,
                functionCalling: [
                    {
                        name: "play_animation",
                        description: "播放指定的动画效果，让桌面宠物做出相应动作",
                        parameters: [
                            { name: "animation_name", type: "string", description: "动画名称，如：wave(挥手)、jump(跳跃)、dance(跳舞)、sleep(睡觉)、happy(开心)" }
                        ]
                    },
                    {
                        name: "change_expression",
                        description: "改变桌面宠物的表情",
                        parameters: [
                            { name: "expression", type: "string", description: "表情类型，如：smile(微笑)、sad(伤心)、angry(生气)、surprised(惊讶)、love(爱心)" }
                        ]
                    },
                    {
                        name: "move_to_position",
                        description: "移动桌面宠物到屏幕指定位置",
                        parameters: [
                            { name: "x", type: "number", description: "X坐标（像素）" },
                            { name: "y", type: "number", description: "Y坐标（像素）" }
                        ]
                    },
                    {
                        name: "set_mood",
                        description: "设置桌面宠物的心情状态",
                        parameters: [
                            { name: "mood", type: "string", description: "心情状态，如：happy(开心)、normal(正常)、tired(疲惫)、excited(兴奋)" },
                            { name: "duration", type: "number", description: "持续时间（秒），默认60" }
                        ]
                    },
                    {
                        name: "speak_text",
                        description: "让桌面宠物说出指定文字（显示气泡对话框）",
                        parameters: [
                            { name: "text", type: "string", description: "要说的文字内容" },
                            { name: "duration", type: "number", description: "显示时长（秒），默认3" }
                        ]
                    }
                ],
                platform: 'WEB',
                functionCallingModified: false, // 标记用户是否修改过函数定义
                enableSRSModified: false // 标记用户是否修改过EnableSRS
            },
            messages: [],
            recording: {
                isRecording: false,
                vadEnabled: true,
                duration: 0,
                vadParams: {
                    silenceThreshold: 0.01,      // 静音阈值：保持不变，用于判断是否停止说话
                    silenceDuration: 800,         // 静音持续时长：1500ms → 800ms（更快结束）
                    speechThreshold: 0.02,        // 语音阈值：0.05 → 0.02（更敏感，更快开始）
                    minSpeechDuration: 200,       // 最小语音时长：300ms → 200ms（减少误判延迟）
                    preSpeechPadding: 150,        // 语音前填充：300ms → 150ms（减少预填充，更快响应）
                    postSpeechPadding: 300        // 语音后填充：500ms → 300ms（更快结束）
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

