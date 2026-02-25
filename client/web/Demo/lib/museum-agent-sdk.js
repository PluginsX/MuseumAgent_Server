/**
 * MuseumAgent Client SDK v2.0
 * (c) 2024 MuseumAgent Team
 * @license MIT
 */
(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
    typeof define === 'function' && define.amd ? define(['exports'], factory) :
    (global = typeof globalThis !== 'undefined' ? globalThis : global || self, factory(global.MuseumAgentSDK = {}));
})(this, (function (exports) { 'use strict';

    var _documentCurrentScript = typeof document !== 'undefined' ? document.currentScript : null;
    /**
     * 事件总线
     * 提供发布-订阅模式的事件系统
     */

    class EventBus {
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

    /**
     * WebSocket 客户端
     * 纯粹的连接管理，不包含业务逻辑
     */

    class WebSocketClient {
        constructor(config = {}) {
            this.config = {
                baseUrl: config.baseUrl || 'ws://localhost:8001',
                reconnectInterval: config.reconnectInterval || 5000,
                maxReconnectAttempts: config.maxReconnectAttempts || 5,
                heartbeatTimeout: config.heartbeatTimeout || 120000
            };
            
            this.ws = null;
            this.sessionId = null;
            this.reconnectAttempts = 0;
            this.heartbeatTimer = null;
            
            // 消息处理器
            this.onMessage = null;
            this.onOpen = null;
            this.onClose = null;
            this.onError = null;
        }

        /**
         * 连接到服务器
         */
        async connect() {
            return new Promise((resolve, reject) => {
                const wsUrl = `${this.config.baseUrl}/ws/agent/stream`;
                console.log('[WebSocketClient] 连接:', wsUrl);

                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('[WebSocketClient] 连接成功');
                    this.reconnectAttempts = 0;
                    if (this.onOpen) this.onOpen();
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    if (this.onMessage) {
                        try {
                            const data = JSON.parse(event.data);
                            this.onMessage(data);
                        } catch (error) {
                            console.error('[WebSocketClient] 消息解析失败:', error);
                        }
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('[WebSocketClient] 错误:', error);
                    if (this.onError) this.onError(error);
                    reject(error);
                };

                this.ws.onclose = (event) => {
                    console.log('[WebSocketClient] 连接关闭:', event.code, event.reason);
                    this._stopHeartbeatMonitor();
                    if (this.onClose) this.onClose(event);
                };

                // 连接超时
                setTimeout(() => {
                    if (this.ws.readyState !== WebSocket.OPEN) {
                        reject(new Error('连接超时'));
                    }
                }, 10000);
            });
        }

        /**
         * 注册会话（V2.0：支持角色配置和场景描述）
         */
        async register(authData, platform = 'WEB', requireTTS = false, enableSRS = true, functionCalling = [], roleDescription = null, responseRequirements = null, sceneDescription = null) {
            const message = {
                version: '1.0',
                msg_type: 'REGISTER',
                session_id: null,
                payload: {
                    auth: authData,
                    platform: platform,
                    require_tts: requireTTS,
                    enable_srs: enableSRS,
                    function_calling: functionCalling
                },
                timestamp: Date.now()
            };

            // ✅ V2.0: 添加角色配置
            if (roleDescription || responseRequirements) {
                message.payload.system_prompt = {
                    role_description: roleDescription || '',
                    response_requirements: responseRequirements || ''
                };
            }

            // ✅ V2.0: 添加场景描述
            if (sceneDescription) {
                message.payload.scene_context = {
                    scene_description: sceneDescription
                };
            }

            return new Promise((resolve, reject) => {
                const handler = (data) => {
                    if (data.msg_type === 'REGISTER_ACK') {
                        this.sessionId = data.payload.session_id;
                        this._startHeartbeatMonitor();
                        resolve(data.payload);
                    } else if (data.msg_type === 'ERROR') {
                        // 处理注册错误
                        this.onMessage = originalHandler;
                        reject(new Error(data.payload.error_msg || '注册失败'));
                    }
                };

                // 临时注册消息处理器
                const originalHandler = this.onMessage;
                this.onMessage = (data) => {
                    handler(data);
                    if (originalHandler) originalHandler(data);
                };

                this.send(message);

                setTimeout(() => {
                    this.onMessage = originalHandler;
                    reject(new Error('注册超时'));
                }, 30000);
            });
        }

        /**
         * 发送 JSON 消息
         */
        send(message) {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(message));
            } else {
                console.warn('[WebSocketClient] WebSocket 未连接，无法发送消息');
            }
        }

        /**
         * 发送二进制数据
         */
        sendBinary(data) {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(data);
            } else {
                console.warn('[WebSocketClient] WebSocket 未连接，无法发送二进制数据');
            }
        }

        /**
         * 断开连接
         */
        async disconnect(reason = '客户端主动断开') {
            const message = {
                version: '1.0',
                msg_type: 'SHUTDOWN',
                session_id: this.sessionId,
                payload: { reason },
                timestamp: Date.now()
            };

            this.send(message);
            this._stopHeartbeatMonitor();
            
            if (this.ws) {
                this.ws.close(1000, reason);
            }
        }

        /**
         * 启动心跳监控
         */
        _startHeartbeatMonitor() {
            this._stopHeartbeatMonitor();
            this.heartbeatTimer = setTimeout(() => {
                console.warn('[WebSocketClient] 心跳超时');
                if (this.onClose) {
                    this.onClose({ code: 1006, reason: '心跳超时' });
                }
            }, this.config.heartbeatTimeout);
        }

        /**
         * 重置心跳监控
         */
        _resetHeartbeatMonitor() {
            this._startHeartbeatMonitor();
        }

        /**
         * 停止心跳监控
         */
        _stopHeartbeatMonitor() {
            if (this.heartbeatTimer) {
                clearTimeout(this.heartbeatTimer);
                this.heartbeatTimer = null;
            }
        }

        /**
         * 处理心跳消息
         */
        handleHeartbeat() {
            this._resetHeartbeatMonitor();

            const reply = {
                version: '1.0',
                msg_type: 'HEARTBEAT_REPLY',
                session_id: this.sessionId,
                payload: { client_status: 'ONLINE' },
                timestamp: Date.now()
            };

            this.send(reply);
        }

        /**
         * 检查连接状态
         */
        isConnected() {
            return this.ws && this.ws.readyState === WebSocket.OPEN;
        }

        /**
         * 生成唯一 ID
         */
        generateId() {
            return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }
    }

    /**
     * 发送管理器
     * 负责所有发送操作，独立于接收流程
     */

    class SendManager {
        constructor(wsClient, sessionId, clientConfig, settingsPanel = null, client = null) {
            this.wsClient = wsClient;
            this.sessionId = sessionId;
            this.clientConfig = clientConfig;  // ✅ 保存客户端配置引用
            this.settingsPanel = settingsPanel;  // ✅ 保存设置面板引用
            this.client = client;  // ✅ 保存客户端实例引用
            
            // 当前语音流
            this.currentVoiceStream = null;
        }

        /**
         * 更新 session ID
         */
        setSessionId(sessionId) {
            this.sessionId = sessionId;
        }

        /**
         * 发送文本消息
         * @param {string} text - 文本内容
         * @param {Object} options - 选项
         * @returns {string} requestId
         */
        sendText(text, options = {}) {
            const requestId = this.wsClient.generateId();
            
            const message = {
                version: '1.0',
                msg_type: 'REQUEST',
                session_id: this.sessionId,
                payload: {
                    request_id: requestId,
                    data_type: 'TEXT',
                    stream_flag: false,
                    stream_seq: 0,
                    require_tts: options.requireTTS || false,
                    content: { text }
                },
                timestamp: Date.now()
            };

            if (options.enableSRS !== undefined) {
                message.payload.enable_srs = options.enableSRS;
            }

            if (options.functionCallingOp) {
                message.payload.function_calling_op = options.functionCallingOp;
                message.payload.function_calling = options.functionCalling || [];
            }

            // ✅ 添加配置更新（每次请求都携带最新配置）
            message.payload.update_session = this._buildUpdateSession();

            this.wsClient.send(message);
            
            return requestId;
        }

        /**
         * ✅ 构建配置更新对象（差异更新）
         * 只返回用户手动标记需要更新的配置项
         * @private
         */
        _buildUpdateSession() {
            // 如果有客户端实例，使用客户端的内部标记机制
            if (this.client) {
                // 获取需要更新的配置（差异更新）
                const updates = this.client.getPendingUpdates();
                
                // 如果有更新，发送后自动清除标记
                if (Object.keys(updates).length > 0) {
                    console.log('[SendManager] 携带配置更新:', updates);
                    
                    // ✅ 发送成功后自动清除更新标记
                    setTimeout(() => {
                        this.client.clearUpdateMarks();
                    }, 100);
                }
                
                return updates;
            } else if (this.settingsPanel) {
                // 保持向后兼容：如果有设置面板引用，使用设置面板的待更新配置
                const updates = this.settingsPanel.getPendingUpdates();
                
                // 如果有更新，发送后自动关闭开关
                if (Object.keys(updates).length > 0) {
                    console.log('[SendManager] 携带配置更新（设置面板）:', updates);
                    
                    // ✅ 发送成功后自动关闭所有更新开关
                    setTimeout(() => {
                        this.settingsPanel.clearUpdateSwitches();
                    }, 100);
                }
                
                return updates;
            } else {
                // 如果没有客户端实例和设置面板引用，返回所有可能的上下文配置
                const updates = {};
                
                // 检查并添加上下文相关配置
                if (this.clientConfig.sceneDescription) {
                    updates.sceneContext = {
                        description: this.clientConfig.sceneDescription
                    };
                }
                
                if (this.clientConfig.roleDescription || this.clientConfig.responseRequirements) {
                    updates.systemPrompt = {};
                    if (this.clientConfig.roleDescription) {
                        updates.systemPrompt.role_description = this.clientConfig.roleDescription;
                    }
                    if (this.clientConfig.responseRequirements) {
                        updates.systemPrompt.response_requirements = this.clientConfig.responseRequirements;
                    }
                }
                
                if (this.clientConfig.functionCalling) {
                    updates.functionCalling = this.clientConfig.functionCalling;
                }
                
                if (Object.keys(updates).length > 0) {
                    console.log('[SendManager] 携带上下文配置更新（无客户端实例）:', updates);
                }
                
                return updates;
            }
        }

        /**
         * 开始语音流
         * @param {Object} options - 选项
         * @returns {Object} { requestId, controller }
         */
        startVoiceStream(options = {}) {
            const requestId = this.wsClient.generateId();
            
            // 创建流控制器
            let controller = null;
            const stream = new ReadableStream({
                start: (ctrl) => {
                    controller = ctrl;
                },
                cancel: (reason) => {
                    console.log('[SendManager] 语音流取消:', reason);
                }
            });

            // 保存当前语音流信息（包括配置参数）
            this.currentVoiceStream = {
                requestId,
                controller,
                stream,
                startTime: Date.now(),
                chunkCount: 0,
                requireTTS: options.requireTTS || false,  // ✅ 保存配置
                enableSRS: options.enableSRS
            };

            // 发送开始消息
            const startMessage = {
                version: '1.0',
                msg_type: 'REQUEST',
                session_id: this.sessionId,
                payload: {
                    request_id: requestId,
                    data_type: 'VOICE',
                    stream_flag: true,
                    stream_seq: 0,
                    require_tts: options.requireTTS || false,
                    content: { 
                        voice_mode: 'BINARY',
                        audio_format: 'pcm'
                    }
                },
                timestamp: Date.now()
            };

            if (options.enableSRS !== undefined) {
                startMessage.payload.enable_srs = options.enableSRS;
            }

            // ✅ 添加配置更新（每次请求都携带最新配置）
            startMessage.payload.update_session = this._buildUpdateSession();

            this.wsClient.send(startMessage);
            
            return { requestId, controller };
        }

        /**
         * 发送音频数据块
         * @param {ArrayBuffer} audioData - 音频数据
         */
        sendAudioChunk(audioData) {
            if (!this.currentVoiceStream) {
                // ✅ 静默忽略，不输出警告（录音停止后可能还有残留数据）
                return;
            }

            if (!this.wsClient.isConnected()) {
                console.warn('[SendManager] WebSocket 未连接');
                return;
            }

            // 通过 WebSocket 发送二进制数据
            this.wsClient.sendBinary(audioData);
            
            // 更新计数
            this.currentVoiceStream.chunkCount++;
        }

        /**
         * 结束语音流
         */
        endVoiceStream() {
            if (!this.currentVoiceStream) {
                return;
            }

            const { requestId, controller, requireTTS, enableSRS } = this.currentVoiceStream;

            // 关闭流控制器
            if (controller) {
                try {
                    controller.close();
                } catch (error) {
                    console.warn('[SendManager] 关闭流控制器失败:', error.message);
                }
            }

            // 发送结束消息（使用保存的配置参数）
            const endMessage = {
                version: '1.0',
                msg_type: 'REQUEST',
                session_id: this.sessionId,
                payload: {
                    request_id: requestId,
                    data_type: 'VOICE',
                    stream_flag: true,
                    stream_seq: -1,
                    require_tts: requireTTS,  // ✅ 使用保存的配置
                    content: { 
                        voice_mode: 'BINARY',
                        audio_format: 'pcm'
                    }
                },
                timestamp: Date.now()
            };

            // ✅ 添加 enableSRS 参数
            if (enableSRS !== undefined) {
                endMessage.payload.enable_srs = enableSRS;
            }

            // ✅ 语音流结束包不携带配置更新（配置更新已在首包发送）
            // 因为首包发送时就清除了开关，这里再调用 _buildUpdateSession() 会返回空对象

            this.wsClient.send(endMessage);

            console.log(`[SendManager] 语音流结束: ${requestId}, 发送了 ${this.currentVoiceStream.chunkCount} 个音频块, requireTTS: ${requireTTS}`);
            
            // 清理
            this.currentVoiceStream = null;
        }

        /**
         * 发送打断消息
         * @param {string} requestId - 要打断的请求 ID
         * @param {string} reason - 打断原因
         */
        sendInterrupt(requestId, reason = 'USER_NEW_INPUT') {
            const message = {
                version: '1.0',
                msg_type: 'INTERRUPT',
                session_id: this.sessionId,
                payload: {
                    interrupt_request_id: requestId,
                    reason: reason
                },
                timestamp: Date.now()
            };

            this.wsClient.send(message);
        }

        /**
         * 获取当前语音流信息
         */
        getCurrentVoiceStream() {
            return this.currentVoiceStream;
        }

        /**
         * 检查是否有活跃的语音流
         */
        hasActiveVoiceStream() {
            return this.currentVoiceStream !== null;
        }
    }

    /**
     * 接收管理器
     * 负责所有接收操作，独立于发送流程
     */

    class ReceiveManager {
        constructor(wsClient) {
            this.wsClient = wsClient;
            
            // 响应处理器映射 requestId -> handler
            this.responseHandlers = new Map();
            
            // 活跃的响应集合
            this.activeResponses = new Set();
            
            // 打断确认处理器
            this.interruptHandlers = new Map();
        }

        /**
         * 注册响应处理器
         * @param {string} requestId - 请求 ID
         * @param {Object} handler - 处理器
         */
        registerHandler(requestId, handler) {
            this.responseHandlers.set(requestId, {
                ...handler,
                textEnded: false,
                voiceEnded: false,
                hasCheckedStreams: false,
                hasTextStream: false,
                hasVoiceStream: false,
                timeoutId: null
            });
            
            this.activeResponses.add(requestId);

            // 设置超时
            const timeoutId = setTimeout(() => {
                if (this.responseHandlers.has(requestId)) {
                    console.warn(`[ReceiveManager] 请求超时: ${requestId}`);
                    const handler = this.responseHandlers.get(requestId);
                    if (handler.onError) {
                        handler.onError(new Error('请求超时'));
                    }
                    this.unregisterHandler(requestId);
                }
            }, 120000); // 120秒超时

            this.responseHandlers.get(requestId).timeoutId = timeoutId;
        }

        /**
         * 取消注册响应处理器
         * @param {string} requestId - 请求 ID
         */
        unregisterHandler(requestId) {
            const handler = this.responseHandlers.get(requestId);
            if (handler && handler.timeoutId) {
                clearTimeout(handler.timeoutId);
            }
            
            this.responseHandlers.delete(requestId);
            this.activeResponses.delete(requestId);
        }

        /**
         * 处理接收到的消息
         * @param {Object} message - 消息对象
         */
        handleMessage(message) {
            const { msg_type, payload } = message;

            // 处理心跳
            if (msg_type === 'HEARTBEAT') {
                this.wsClient.handleHeartbeat();
                return;
            }

            // 处理打断确认
            if (msg_type === 'INTERRUPT_ACK') {
                this._handleInterruptAck(message);
                return;
            }

            // 处理响应
            if (msg_type === 'RESPONSE') {
                this._handleResponse(message);
                return;
            }

            // 处理错误
            if (msg_type === 'ERROR') {
                this._handleError(message);
                return;
            }
        }

        /**
         * 处理响应消息
         */
        _handleResponse(message) {
            const payload = message.payload;
            const requestId = payload.request_id;
            
            const handler = this.responseHandlers.get(requestId);
            if (!handler) {
                // 可能是已经被打断的请求
                return;
            }

            // 检查是否被打断
            if (payload.interrupted) {
                if (handler.onInterrupted) {
                    handler.onInterrupted({
                        requestId,
                        reason: payload.interrupt_reason
                    });
                }
                this.unregisterHandler(requestId);
                return;
            }

            // 处理函数调用
            if (payload.function_call) {
                if (handler.onFunctionCall) {
                    handler.onFunctionCall(payload.function_call);
                }
            }

            // 处理文本流
            if (payload.content?.text) {
                if (handler.onTextChunk) {
                    handler.onTextChunk(payload.content.text);
                }
            }

            // 处理语音流
            if (payload.content?.voice) {
                if (handler.onVoiceChunk) {
                    const audioData = this._decodeBase64(payload.content.voice);
                    handler.onVoiceChunk(audioData, payload.voice_stream_seq);
                }
            }

            // 检查流结束状态
            const textEnded = payload.text_stream_seq === -1;
            const voiceEnded = payload.voice_stream_seq === -1;

            if (!handler.textEnded && textEnded) {
                handler.textEnded = true;
            }

            if (!handler.voiceEnded && voiceEnded) {
                handler.voiceEnded = true;
            }

            // 首次检查流类型
            if (!handler.hasCheckedStreams) {
                handler.hasTextStream = payload.text_stream_seq !== undefined;
                handler.hasVoiceStream = payload.voice_stream_seq !== undefined;
                handler.hasCheckedStreams = true;
            }
            
            // 检查是否所有流都结束
            const textComplete = !handler.hasTextStream || handler.textEnded;
            const voiceComplete = !handler.hasVoiceStream || handler.voiceEnded;
            
            if (textComplete && voiceComplete) {
                if (handler.onComplete) {
                    handler.onComplete(message);
                }
                this.unregisterHandler(requestId);
            }
        }

        /**
         * 处理错误消息
         */
        _handleError(message) {
            const payload = message.payload;
            console.error('[ReceiveManager] 服务器错误:', payload);

            // 会话无效错误
            if (payload.error_code === 'SESSION_INVALID') {
                if (this.onSessionExpired) {
                    this.onSessionExpired(payload);
                }
            }

            // 请求相关错误
            if (payload.request_id) {
                const handler = this.responseHandlers.get(payload.request_id);
                if (handler && handler.onError) {
                    handler.onError(new Error(payload.error_msg));
                }
                this.unregisterHandler(payload.request_id);
            }
        }

        /**
         * 处理打断确认
         */
        _handleInterruptAck(message) {
            const payload = message.payload;
            const requestId = payload.interrupt_request_id;
            
            const handler = this.interruptHandlers.get(requestId);
            if (handler) {
                handler.resolve(payload);
                this.interruptHandlers.delete(requestId);
            }
        }

        /**
         * 打断指定请求
         * @param {string} requestId - 请求 ID
         * @param {string} reason - 打断原因
         */
        async interruptRequest(requestId, reason = 'USER_NEW_INPUT') {
            // 立即清理本地处理器
            const handler = this.responseHandlers.get(requestId);
            if (handler) {
                if (handler.onInterrupted) {
                    handler.onInterrupted({ requestId, reason });
                }
                this.unregisterHandler(requestId);
            }

            // 发送打断消息（不等待确认）
            return new Promise((resolve, reject) => {
                this.interruptHandlers.set(requestId, { resolve, reject });

                // 通过 SendManager 发送打断消息
                // 这里直接通过 wsClient 发送
                const message = {
                    version: '1.0',
                    msg_type: 'INTERRUPT',
                    session_id: this.wsClient.sessionId,
                    payload: {
                        interrupt_request_id: requestId,
                        reason: reason
                    },
                    timestamp: Date.now()
                };

                this.wsClient.send(message);

                // 15秒超时
                setTimeout(() => {
                    if (this.interruptHandlers.has(requestId)) {
                        this.interruptHandlers.delete(requestId);
                        console.debug('[ReceiveManager] 打断确认超时（已本地处理）');
                        resolve({ timeout: true });
                    }
                }, 15000);
            });
        }

        /**
         * 解码 Base64 音频数据
         */
        _decodeBase64(base64) {
            const binaryString = atob(base64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            return bytes.buffer;
        }

        /**
         * 获取活跃响应数量
         */
        getActiveResponseCount() {
            return this.activeResponses.size;
        }

        /**
         * 检查是否有活跃的响应
         */
        hasActiveResponses() {
            return this.activeResponses.size > 0;
        }

        /**
         * 清理所有处理器
         */
        cleanup() {
            // 清理所有超时定时器
            this.responseHandlers.forEach((handler) => {
                if (handler.timeoutId) {
                    clearTimeout(handler.timeoutId);
                }
            });
            
            this.responseHandlers.clear();
            this.activeResponses.clear();
            this.interruptHandlers.clear();
        }
    }

    /**
     * 音频管理器
     * 封装音频录制、播放、VAD 等功能
     */

    // ==================== 流式音频播放器 ====================
    class StreamingAudioPlayer {
        constructor(audioContext) {
            this.audioContext = audioContext;
            this.sampleRate = 16000;
            this.currentMessageId = null;
            this.isPlaying = false;
            this.isStopped = false;
            this.audioQueue = [];
            this.isProcessing = false;
            this.nextStartTime = 0;
            this.startTime = 0;
            this.activeSources = [];
        }
        
        startMessage(messageId) {
            if (this.currentMessageId && this.currentMessageId !== messageId) {
                this.stop();
            }
            
            this.currentMessageId = messageId;
            this.isPlaying = false;
            this.isStopped = false;
            this.audioQueue = [];
            this.isProcessing = false;
            this.nextStartTime = 0;
            this.activeSources = [];
        }
        
        addChunk(messageId, pcmData) {
            if (messageId !== this.currentMessageId) return;
            if (this.isStopped) return;
            
            this.audioQueue.push(pcmData);
            
            if (!this.isPlaying) {
                this.start();
            }
            
            this.processQueue();
        }
        
        start() {
            if (this.isPlaying || this.isStopped) return;
            
            this.isPlaying = true;
            this.startTime = this.audioContext.currentTime;
            this.nextStartTime = this.startTime;
        }
        
        async processQueue() {
            if (this.isProcessing || this.isStopped) return;
            
            this.isProcessing = true;
            
            while (this.audioQueue.length > 0 && !this.isStopped) {
                const pcmData = this.audioQueue.shift();
                
                try {
                    const audioBuffer = this.audioContext.createBuffer(
                        1,
                        pcmData.byteLength / 2,
                        this.sampleRate
                    );
                    
                    const channelData = audioBuffer.getChannelData(0);
                    const pcmArray = new Int16Array(pcmData);
                    
                    for (let i = 0; i < pcmArray.length; i++) {
                        channelData[i] = pcmArray[i] / 32768;
                    }
                    
                    const source = this.audioContext.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(this.audioContext.destination);
                    
                    this.activeSources.push(source);
                    
                    source.onended = () => {
                        const index = this.activeSources.indexOf(source);
                        if (index > -1) {
                            this.activeSources.splice(index, 1);
                        }
                    };
                    
                    const now = this.audioContext.currentTime;
                    const startTime = Math.max(now, this.nextStartTime);
                    
                    source.start(startTime);
                    this.nextStartTime = startTime + audioBuffer.duration;
                    
                } catch (error) {
                    console.error('[StreamingAudioPlayer] 播放失败:', error);
                }
            }
            
            this.isProcessing = false;
        }
        
        endMessage(messageId) {
            if (messageId !== this.currentMessageId) return;
            this.processQueue();
        }
        
        stop() {
            if (this.isStopped) return;
            
            for (const source of this.activeSources) {
                try {
                    source.stop();
                    source.disconnect();
                } catch (error) {
                    // 忽略
                }
            }
            
            this.activeSources = [];
            this.isStopped = true;
            this.isPlaying = false;
            this.audioQueue = [];
            this.currentMessageId = null;
        }
        
        reset() {
            this.stop();
            this.isStopped = false;
        }
    }

    // ==================== 音频管理器 ====================
    class AudioManager {
        constructor() {
            this.audioContext = null;
            this.mediaStream = null;
            this.audioWorkletNode = null;
            this.isRecording = false;
            
            // VAD 相关
            this.vadEnabled = false;
            this.vadParams = null;
            this.vadState = {
                isSpeaking: false,
                silenceStart: null,
                speechStart: null,
                audioBuffer: []
            };
            
            // 播放相关
            this.streamingPlayer = null;
            this.currentSource = null;
            this.currentPlayingMessageId = null;
        }
        
        /**
         * 初始化音频上下文
         */
        async init() {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 16000
                });
                
                if (this.audioContext.state === 'suspended') {
                    await this.audioContext.resume();
                }
                
                this.streamingPlayer = new StreamingAudioPlayer(this.audioContext);
            }
            
            if (this.audioContext && this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
        }

        /**
         * 开始录音
         */
        async startRecording(onDataCallback) {
            await this.init();

            try {
                // 检查浏览器是否支持媒体设备API
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    throw new Error('浏览器不支持录音功能或需要HTTPS连接');
                }

                this.mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        channelCount: 1,
                        sampleRate: 16000,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                // 加载 AudioWorklet 处理器
                const processorUrl = new URL('./vad-processor.js', (typeof document === 'undefined' && typeof location === 'undefined' ? require('u' + 'rl').pathToFileURL(__filename).href : typeof document === 'undefined' ? location.href : (_documentCurrentScript && _documentCurrentScript.tagName.toUpperCase() === 'SCRIPT' && _documentCurrentScript.src || new URL('museum-agent-sdk.js', document.baseURI).href)));
                await this.audioContext.audioWorklet.addModule(processorUrl);

                const source = this.audioContext.createMediaStreamSource(this.mediaStream);
                const workletNode = new AudioWorkletNode(this.audioContext, 'vad-processor');
                
                // 监听来自 AudioWorklet 的消息
                workletNode.port.onmessage = (event) => {
                    const { type, data } = event.data;
                    
                    if (type === 'audioData' && onDataCallback) {
                        onDataCallback(data);
                    }
                };
                
                // 初始化 AudioWorklet（非 VAD 模式）
                workletNode.port.postMessage({
                    type: 'init',
                    data: {
                        vadEnabled: false,
                        vadParams: null
                    }
                });

                source.connect(workletNode);
                workletNode.connect(this.audioContext.destination);

                this.audioWorkletNode = workletNode;
                this.isRecording = true;
                this.vadEnabled = false;

            } catch (error) {
                console.error('[AudioManager] 录音启动失败:', error);
                throw error;
            }
        }

        /**
         * 开始录音（启用 VAD）
         */
        async startRecordingWithVAD(vadParams, onSpeechStart, onAudioData, onSpeechEnd) {
            await this.init();

            this.vadParams = vadParams;
            this.vadEnabled = true;
            this.vadState = {
                isSpeaking: false,
                silenceStart: null,
                speechStart: null,
                audioBuffer: [],
                speechStartCallback: onSpeechStart,
                audioDataCallback: onAudioData,
                speechEndCallback: onSpeechEnd
            };

            try {
                this.mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        channelCount: 1,
                        sampleRate: 16000,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                // 加载 AudioWorklet 处理器
                const processorUrl = new URL('./vad-processor.js', (typeof document === 'undefined' && typeof location === 'undefined' ? require('u' + 'rl').pathToFileURL(__filename).href : typeof document === 'undefined' ? location.href : (_documentCurrentScript && _documentCurrentScript.tagName.toUpperCase() === 'SCRIPT' && _documentCurrentScript.src || new URL('museum-agent-sdk.js', document.baseURI).href)));
                await this.audioContext.audioWorklet.addModule(processorUrl);

                const source = this.audioContext.createMediaStreamSource(this.mediaStream);
                const workletNode = new AudioWorkletNode(this.audioContext, 'vad-processor');
                
                // 监听来自 AudioWorklet 的消息
                workletNode.port.onmessage = (event) => {
                    const { type, data } = event.data;
                    
                    if (type === 'speechStart' && onSpeechStart) {
                        onSpeechStart();
                    } else if (type === 'audioData' && onAudioData) {
                        onAudioData(data);
                    } else if (type === 'speechEnd' && onSpeechEnd) {
                        onSpeechEnd();
                    }
                };
                
                // 初始化 AudioWorklet（VAD 模式）
                workletNode.port.postMessage({
                    type: 'init',
                    data: {
                        vadEnabled: true,
                        vadParams: vadParams
                    }
                });

                source.connect(workletNode);
                workletNode.connect(this.audioContext.destination);

                this.audioWorkletNode = workletNode;
                this.isRecording = true;

            } catch (error) {
                console.error('[AudioManager] 录音启动失败:', error);
                throw error;
            }
        }

        /**
         * 停止录音
         */
        stopRecording() {
            this.isRecording = false;

            if (this.audioWorkletNode) {
                // ✅ 通知 AudioWorklet 停止（这会让 process() 返回 false）
                this.audioWorkletNode.port.postMessage({
                    type: 'stop'
                });
                
                // ✅ 等待一小段时间让 AudioWorklet 处理完最后的消息
                setTimeout(() => {
                    if (this.audioWorkletNode) {
                        try {
                this.audioWorkletNode.disconnect();
                        } catch (error) {
                            // 忽略断开连接时的错误
                        }
                this.audioWorkletNode = null;
                    }
                }, 50);
            }

            if (this.mediaStream) {
                this.mediaStream.getTracks().forEach(track => track.stop());
                this.mediaStream = null;
            }
            
            // ✅ 重置 VAD 状态
            this.vadEnabled = false;
            this.vadParams = null;
            this.vadState = {
                isSpeaking: false,
                silenceStart: null,
                speechStart: null,
                audioBuffer: []
            };
        }

        /**
         * 播放 PCM 音频
         */
        async playPCM(pcmData, sampleRate = 16000) {
            await this.init();

            try {
                if (this.currentSource) {
                    this.currentSource.stop();
                    this.currentSource = null;
                }

                const audioBuffer = this.audioContext.createBuffer(
                    1,
                    pcmData.byteLength / 2,
                    sampleRate
                );

                const channelData = audioBuffer.getChannelData(0);
                const pcmArray = new Int16Array(pcmData);

                for (let i = 0; i < pcmArray.length; i++) {
                    channelData[i] = pcmArray[i] / 32768;
                }

                const source = this.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(this.audioContext.destination);

                this.currentSource = source;

                return new Promise((resolve) => {
                    source.onended = () => {
                        this.currentSource = null;
                        resolve();
                    };
                    source.start();
                });

            } catch (error) {
                console.error('[AudioManager] 播放失败:', error);
                throw error;
            }
        }

        /**
         * 开始流式播放
         */
        async startStreamingMessage(messageId) {
            try {
                await this.init();
            } catch (error) {
                console.error('[AudioManager] 初始化失败:', error);
                return false;
            }
            
            if (!this.streamingPlayer) {
                return false;
            }
            
            if (this.currentPlayingMessageId && this.currentPlayingMessageId !== messageId) {
                this.streamingPlayer.stop();
            }
            
            this.streamingPlayer.startMessage(messageId);
            this.currentPlayingMessageId = messageId;
            
            return true;
        }
        
        /**
         * 添加音频块
         */
        async addStreamingChunk(messageId, pcmData) {
            if (!this.streamingPlayer) {
                try {
                    await this.init();
                } catch (error) {
                    console.error('[AudioManager] 初始化失败:', error);
                    return;
                }
            }
            
            if (!this.streamingPlayer) return;
            
            this.streamingPlayer.addChunk(messageId, pcmData);
        }
        
        /**
         * 结束流式消息
         */
        endStreamingMessage(messageId) {
            if (!this.streamingPlayer) return;
            
            this.streamingPlayer.endMessage(messageId);
            
            if (this.currentPlayingMessageId === messageId) {
                this.currentPlayingMessageId = null;
            }
        }
        
        /**
         * 停止所有播放
         */
        stopAllPlayback() {
            if (this.streamingPlayer) {
                this.streamingPlayer.stop();
            }
            
            if (this.currentSource) {
                this.currentSource.stop();
                this.currentSource = null;
            }
            
            this.currentPlayingMessageId = null;
        }

        /**
         * 清理资源
         */
        cleanup() {
            this.stopRecording();
            this.stopAllPlayback();

            if (this.audioContext) {
                this.audioContext.close();
                this.audioContext = null;
            }
            
            this.streamingPlayer = null;
        }
    }

    /**
     * 存储工具函数（纯函数，无状态）
     * 提供统一的 localStorage 操作接口
     */

    const DEFAULT_PREFIX = 'museumAgent_';

    /**
     * 保存数据到 localStorage
     * @param {string} key - 键名
     * @param {*} value - 值（会自动序列化）
     * @param {string} prefix - 键名前缀
     * @returns {boolean} 是否成功
     */
    function setStorage(key, value, prefix = DEFAULT_PREFIX) {
        try {
            const fullKey = prefix + key;
            const serialized = JSON.stringify(value);
            localStorage.setItem(fullKey, serialized);
            return true;
        } catch (error) {
            console.error('[Storage] 保存失败:', error);
            return false;
        }
    }

    /**
     * 从 localStorage 读取数据
     * @param {string} key - 键名
     * @param {*} defaultValue - 默认值
     * @param {string} prefix - 键名前缀
     * @returns {*} 读取的值或默认值
     */
    function getStorage(key, defaultValue = null, prefix = DEFAULT_PREFIX) {
        try {
            const fullKey = prefix + key;
            const serialized = localStorage.getItem(fullKey);
            return serialized ? JSON.parse(serialized) : defaultValue;
        } catch (error) {
            console.error('[Storage] 读取失败:', error);
            return defaultValue;
        }
    }

    /**
     * 删除数据
     * @param {string} key - 键名
     * @param {string} prefix - 键名前缀
     */
    function removeStorage(key, prefix = DEFAULT_PREFIX) {
        const fullKey = prefix + key;
        localStorage.removeItem(fullKey);
    }

    /**
     * 清空所有数据（按前缀）
     * @param {string} prefix - 键名前缀
     */
    function clearStorage(prefix = DEFAULT_PREFIX) {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith(prefix)) {
                localStorage.removeItem(key);
            }
        });
    }

    /**
     * 检查是否存在
     * @param {string} key - 键名
     * @param {string} prefix - 键名前缀
     * @returns {boolean} 是否存在
     */
    function hasStorage(key, prefix = DEFAULT_PREFIX) {
        const fullKey = prefix + key;
        return localStorage.getItem(fullKey) !== null;
    }

    /**
     * 安全工具函数（纯函数）
     * 提供加密、解密、XSS 防护等功能
     */

    /**
     * 使用 Web Crypto API 加密数据
     * @param {string} data - 要加密的数据
     * @returns {Promise<string>} Base64 编码的加密数据
     */
    async function encryptData(data) {
        try {
            const encoder = new TextEncoder();
            const dataBuffer = encoder.encode(data);
            
            // 生成密钥
            const key = await getEncryptionKey();
            
            // 生成随机 IV
            const iv = crypto.getRandomValues(new Uint8Array(12));
            
            // 加密
            const encryptedBuffer = await crypto.subtle.encrypt(
                { name: 'AES-GCM', iv },
                key,
                dataBuffer
            );
            
            // 组合 IV 和加密数据
            const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength);
            combined.set(iv, 0);
            combined.set(new Uint8Array(encryptedBuffer), iv.length);
            
            // 转换为 Base64
            return btoa(String.fromCharCode(...combined));
            
        } catch (error) {
            console.error('[Security] 加密失败:', error);
            // 降级：使用 Base64（不安全，仅用于开发）
            return btoa(data);
        }
    }

    /**
     * 解密数据
     * @param {string} encryptedData - Base64 编码的加密数据
     * @returns {Promise<string>} 解密后的数据
     */
    async function decryptData(encryptedData) {
        try {
            // 从 Base64 解码
            const combined = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
            
            // 提取 IV 和加密数据
            const iv = combined.slice(0, 12);
            const encrypted = combined.slice(12);
            
            // 获取密钥
            const key = await getEncryptionKey();
            
            // 解密
            const decryptedBuffer = await crypto.subtle.decrypt(
                { name: 'AES-GCM', iv },
                key,
                encrypted
            );
            
            // 转换为字符串
            const decoder = new TextDecoder();
            return decoder.decode(decryptedBuffer);
            
        } catch (error) {
            console.error('[Security] 解密失败:', error);
            // 降级：使用 Base64
            try {
                return atob(encryptedData);
            } catch (e) {
                throw new Error('解密失败');
            }
        }
    }

    /**
     * 获取加密密钥（从浏览器指纹生成）
     * @private
     */
    async function getEncryptionKey() {
        // 使用浏览器指纹作为密钥材料
        const fingerprint = await getBrowserFingerprint();
        
        const encoder = new TextEncoder();
        const keyMaterial = await crypto.subtle.importKey(
            'raw',
            encoder.encode(fingerprint),
            { name: 'PBKDF2' },
            false,
            ['deriveBits', 'deriveKey']
        );
        
        return crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt: encoder.encode('museumAgent'),
                iterations: 100000,
                hash: 'SHA-256'
            },
            keyMaterial,
            { name: 'AES-GCM', length: 256 },
            false,
            ['encrypt', 'decrypt']
        );
    }

    /**
     * 获取浏览器指纹
     * @private
     */
    async function getBrowserFingerprint() {
        const components = [
            navigator.userAgent,
            navigator.language,
            screen.width,
            screen.height,
            new Date().getTimezoneOffset()
        ];
        
        return components.join('|');
    }

    /**
     * XSS 防护：转义 HTML
     * @param {string} text - 要转义的文本
     * @returns {string} 转义后的文本
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * XSS 防护：清理 HTML（保留安全标签）
     * @param {string} html - 要清理的 HTML
     * @returns {string} 清理后的 HTML
     */
    function sanitizeHtml(html) {
        const allowedTags = ['b', 'i', 'em', 'strong', 'a', 'br', 'p'];
        const allowedAttributes = {
            'a': ['href', 'title']
        };
        
        const div = document.createElement('div');
        div.innerHTML = html;
        
        // 递归清理
        cleanNode(div);
        
        return div.innerHTML;
        
        function cleanNode(node) {
            const children = Array.from(node.childNodes);
            
            for (const child of children) {
                if (child.nodeType === Node.ELEMENT_NODE) {
                    const tagName = child.tagName.toLowerCase();
                    
                    // 移除不允许的标签
                    if (!allowedTags.includes(tagName)) {
                        child.replaceWith(...child.childNodes);
                        continue;
                    }
                    
                    // 移除不允许的属性
                    const allowedAttrs = allowedAttributes[tagName] || [];
                    const attrs = Array.from(child.attributes);
                    
                    for (const attr of attrs) {
                        if (!allowedAttrs.includes(attr.name)) {
                            child.removeAttribute(attr.name);
                        }
                    }
                    
                    // 递归处理子节点
                    cleanNode(child);
                }
            }
        }
    }

    /**
     * 验证输入
     * @param {string} value - 要验证的值
     * @param {Object} rules - 验证规则
     * @returns {Object} 验证结果 { valid, errors }
     */
    function validateInput(value, rules = {}) {
        const errors = [];
        
        // 必填验证
        if (rules.required && !value) {
            errors.push('此字段为必填项');
        }
        
        // 最小长度
        if (rules.minLength && value.length < rules.minLength) {
            errors.push(`最小长度为 ${rules.minLength} 个字符`);
        }
        
        // 最大长度
        if (rules.maxLength && value.length > rules.maxLength) {
            errors.push(`最大长度为 ${rules.maxLength} 个字符`);
        }
        
        // 正则验证
        if (rules.pattern && !rules.pattern.test(value)) {
            errors.push(rules.patternMessage || '格式不正确');
        }
        
        // 自定义验证
        if (rules.validator) {
            const result = rules.validator(value);
            if (result !== true) {
                errors.push(result);
            }
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * 生成安全的随机 ID
     * @returns {string} 随机 ID
     */
    function generateSecureId() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    /**
     * MuseumAgent SDK 常量定义
     * 集中管理所有常量，便于维护和 tree-shaking
     */

    /**
     * 事件常量
     */
    const Events = {
        // 连接事件
        CONNECTED: 'connected',
        DISCONNECTED: 'disconnected',
        CONNECTION_ERROR: 'connection_error',
        SESSION_EXPIRED: 'session_expired',
        
        // 消息事件
        MESSAGE_SENT: 'message_sent',
        TEXT_CHUNK: 'text_chunk',
        VOICE_CHUNK: 'voice_chunk',
        MESSAGE_COMPLETE: 'message_complete',
        MESSAGE_ERROR: 'message_error',
        
        // 录音事件
        RECORDING_START: 'recording_start',
        RECORDING_STOP: 'recording_stop',
        RECORDING_ERROR: 'recording_error',
        RECORDING_COMPLETE: 'recording_complete',
        
        // VAD 事件
        SPEECH_START: 'speech_start',
        SPEECH_END: 'speech_end',
        
        // 函数调用事件
        FUNCTION_CALL: 'function_call',
        
        // 打断事件
        INTERRUPTED: 'interrupted'
    };

    /**
     * 默认配置
     */
    const DEFAULT_CONFIG = {
        serverUrl: 'ws://localhost:8001',
        platform: 'WEB',
        requireTTS: true,
        enableSRS: true,
        autoPlay: true,
        vadEnabled: true,
        vadParams: {
            silenceThreshold: 0.005,
            silenceDuration: 500,
            speechThreshold: 0.015,
            minSpeechDuration: 150,
            preSpeechPadding: 1000,
            postSpeechPadding: 100
        },
        roleDescription: '你叫韩立，辽宁省博物馆智能讲解员，男性。性格热情、阳光、开朗、健谈、耐心。你精通辽博的历史文物、展览背景、文化知识，擅长用通俗的语言讲解复杂的知识。只回答与辽宁省博物馆、文物、历史文化、参观导览相关的内容，保持专业又友好的讲解员形象。',
        responseRequirements: '基于当前所处的场景以及场景的内容，综合相关材料，回答用户的提问。同时你要分析用户的需求！在合适的时机选择合适函数，传入合适的参数返回函数调用响应，调用函数也必须要有语言回答内容！',
        sceneDescription: '当前所处的是"卷体夔纹蟠龙盖罍展示场景"，主要内容为该青铜器表面包含的各种纹样的图形和寓意展示，以及各部分组成结构的造型寓意。',
        functionCalling: []
    };

    /**
     * 存储键名
     */
    const STORAGE_KEYS = {
        SESSION: 'session',
        CONFIG: 'config',
        AUTH: 'auth'
    };

    /**
     * 错误类型
     */
    const ERROR_TYPES = {
        NETWORK_ERROR: 'NETWORK_ERROR',
        AUTH_ERROR: 'AUTH_ERROR',
        SESSION_EXPIRED: 'SESSION_EXPIRED',
        UNKNOWN_ERROR: 'UNKNOWN_ERROR'
    };

    /**
     * 日志级别
     */
    const LOG_LEVELS = {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3,
        NONE: 4
    };

    /**
     * 日志工具（纯函数）
     * 提供可配置的日志输出
     */


    let currentLevel = LOG_LEVELS.INFO;
    let prefix = '[MuseumAgent]';

    /**
     * 设置日志级别
     * @param {string|number} level - 日志级别
     */
    function setLogLevel(level) {
        if (typeof level === 'string') {
            currentLevel = LOG_LEVELS[level.toUpperCase()] ?? LOG_LEVELS.INFO;
        } else {
            currentLevel = level;
        }
    }

    /**
     * 设置日志前缀
     * @param {string} newPrefix - 新的前缀
     */
    function setLogPrefix(newPrefix) {
        prefix = newPrefix;
    }

    /**
     * 调试日志
     * @param {...any} args - 日志参数
     */
    function debug(...args) {
        if (currentLevel <= LOG_LEVELS.DEBUG) {
            console.debug(prefix, ...args);
        }
    }

    /**
     * 信息日志
     * @param {...any} args - 日志参数
     */
    function info(...args) {
        if (currentLevel <= LOG_LEVELS.INFO) {
            console.info(prefix, ...args);
        }
    }

    /**
     * 警告日志
     * @param {...any} args - 日志参数
     */
    function warn(...args) {
        if (currentLevel <= LOG_LEVELS.WARN) {
            console.warn(prefix, ...args);
        }
    }

    /**
     * 错误日志
     * @param {...any} args - 日志参数
     */
    function error(...args) {
        if (currentLevel <= LOG_LEVELS.ERROR) {
            console.error(prefix, ...args);
        }
    }

    /**
     * 会话管理器
     * 负责会话的保存、加载、验证和清除
     */


    class SessionManager {
        constructor() {
            this.currentSession = null;
        }
        
        /**
         * 保存会话（加密存储）
         * @param {string} serverUrl - 服务器地址
         * @param {Object} authData - 认证数据
         * @param {string} sessionId - 会话 ID
         * @returns {Promise<boolean>} 是否成功
         */
        async saveSession(serverUrl, authData, sessionId) {
            try {
                const sessionData = {
                    serverUrl,
                    authData,
                    sessionId,
                    timestamp: Date.now()
                };
                
                const encrypted = await encryptData(JSON.stringify(sessionData));
                setStorage(STORAGE_KEYS.SESSION, encrypted);
                this.currentSession = sessionData;
                
                info('[SessionManager] 会话已保存');
                return true;
            } catch (error) {
                warn('[SessionManager] 保存会话失败:', error);
                return false;
            }
        }
        
        /**
         * 加载会话（解密）
         * @returns {Promise<Object|null>} 会话数据或 null
         */
        async loadSession() {
            try {
                const encrypted = getStorage(STORAGE_KEYS.SESSION);
                if (!encrypted) {
                    return null;
                }
                
                const decrypted = await decryptData(encrypted);
                const sessionData = JSON.parse(decrypted);
                
                // 检查是否过期（24小时）
                if (!this.isSessionValid(sessionData)) {
                    this.clearSession();
                    return null;
                }
                
                this.currentSession = sessionData;
                info('[SessionManager] 会话已加载');
                return sessionData;
            } catch (error) {
                warn('[SessionManager] 加载会话失败:', error);
                this.clearSession();
                return null;
            }
        }
        
        /**
         * 清除会话
         */
        clearSession() {
            removeStorage(STORAGE_KEYS.SESSION);
            this.currentSession = null;
            info('[SessionManager] 会话已清除');
        }
        
        /**
         * 检查会话是否有效
         * @param {Object} session - 会话数据
         * @returns {boolean} 是否有效
         */
        isSessionValid(session) {
            if (!session || !session.timestamp) {
                return false;
            }
            
            const maxAge = 24 * 60 * 60 * 1000; // 24小时
            return Date.now() - session.timestamp < maxAge;
        }
        
        /**
         * 获取当前会话
         * @returns {Object|null} 当前会话数据
         */
        getCurrentSession() {
            return this.currentSession;
        }
    }

    /**
     * 配置管理器
     * 负责配置的保存、加载、更新和重置
     */


    class ConfigManager {
        constructor(customDefaults = {}) {
            this.defaults = { ...DEFAULT_CONFIG, ...customDefaults };
            this.current = { ...this.defaults };
        }
        
        /**
         * 加载配置（合并默认值和保存的配置）
         * @returns {Object} 配置对象
         */
        load() {
            const saved = getStorage(STORAGE_KEYS.CONFIG);
            if (saved) {
                this.current = { ...this.defaults, ...saved };
                info('[ConfigManager] 配置已加载');
            }
            return this.current;
        }
        
        /**
         * 保存配置
         * @param {Object} config - 配置对象（可选，默认保存当前配置）
         */
        save(config = this.current) {
            this.current = config;
            setStorage(STORAGE_KEYS.CONFIG, config);
            info('[ConfigManager] 配置已保存');
        }
        
        /**
         * 更新单个配置项
         * @param {string} key - 配置键
         * @param {*} value - 配置值
         */
        update(key, value) {
            this.current[key] = value;
            this.save();
        }
        
        /**
         * 批量更新配置
         * @param {Object} updates - 要更新的配置项
         */
        updateMultiple(updates) {
            Object.assign(this.current, updates);
            this.save();
        }
        
        /**
         * 获取配置项
         * @param {string} key - 配置键
         * @returns {*} 配置值
         */
        get(key) {
            return this.current[key];
        }
        
        /**
         * 获取所有配置
         * @returns {Object} 配置对象副本
         */
        getAll() {
            return { ...this.current };
        }
        
        /**
         * 重置为默认值
         */
        reset() {
            this.current = { ...this.defaults };
            removeStorage(STORAGE_KEYS.CONFIG);
            info('[ConfigManager] 配置已重置');
        }
        
        /**
         * 获取差异（用于增量更新）
         * @param {Object} newConfig - 新配置
         * @returns {Object} 差异对象
         */
        getDiff(newConfig) {
            const diff = {};
            for (const key in newConfig) {
                if (JSON.stringify(newConfig[key]) !== JSON.stringify(this.current[key])) {
                    diff[key] = newConfig[key];
                }
            }
            return diff;
        }
    }

    /**
     * MuseumAgent 客户端 SDK V2.0
     * 
     * 全新架构：发送和接收完全解耦，异步并行运行
     * 
     * 核心改进：
     * - 发送管理器（SendManager）：独立管理所有发送操作
     * - 接收管理器（ReceiveManager）：独立管理所有接收操作
     * - 无阻塞发送：任何时候都可以立即开始发送
     * - 智能路由：通过 request_id 匹配请求和响应
     * - 会话管理：自动保存和恢复会话
     * - 配置管理：统一的配置持久化
     * 
     * API 保持完全兼容，用户层面 0 感知
     */


    // ==================== 主客户端类 ====================
    class MuseumAgentClient {
        constructor(config = {}) {
            this.config = {
                serverUrl: config.serverUrl || 'ws://localhost:8001',
                platform: config.platform || 'WEB',
                requireTTS: config.requireTTS !== undefined ? config.requireTTS : true,
                enableSRS: config.enableSRS !== undefined ? config.enableSRS : true,
                autoPlay: config.autoPlay !== undefined ? config.autoPlay : true,
                functionCalling: config.functionCalling || [],
                vadParams: config.vadParams || {
                    silenceThreshold: 0.005,
                    silenceDuration: 500,
                    speechThreshold: 0.015,
                    minSpeechDuration: 150,
                    preSpeechPadding: 1000,
                    postSpeechPadding: 100
                },
                // 智能体角色配置
                roleDescription: config.roleDescription || '你叫韩立，辽宁省博物馆智能讲解员，男性。性格热情、阳光、开朗、健谈、耐心。你精通辽博的历史文物、展览背景、文化知识，擅长用通俗的语言讲解复杂的知识。只回答与辽宁省博物馆、文物、历史文化、参观导览相关的内容，保持专业又友好的讲解员形象。',
                responseRequirements: config.responseRequirements || '基于当前所处的场景以及场景的内容，综合相关材料，回答用户的提问。同时你要分析用户的需求！在合适的时机选择合适函数，传入合适的参数返回函数调用响应，调用函数也必须要有语言回答内容！',
                // 场景描述
                sceneDescription: config.sceneDescription || '当前所处的是“卷体夔纹蟠龙盖罍展示场景”，主要内容为该青铜器表面包含的各种纹样的图形和寓意展示，以及各部分组成结构的造型寓意。'
            };
            
            // 事件总线
            this.eventBus = new EventBus();
            
            // WebSocket 客户端
            this.wsClient = new WebSocketClient({
                baseUrl: this.config.serverUrl
            });
            
            // 发送管理器
            this.sendManager = null;
            
            // 接收管理器
            this.receiveManager = null;
            
            // 音频管理器
            this.audioManager = new AudioManager();
            
            // 会话管理器
            this.sessionManager = new SessionManager();
            
            // 配置管理器
            this.configManager = new ConfigManager();
            
            // 状态
            this.sessionId = null;
            this.isConnected = false;
            this.latestRequestId = null; // 用于打断
            this.currentVoiceRequestId = null; // 当前语音请求
            
            // 录音状态
            this.isRecording = false;
            this.vadEnabled = config.vadEnabled !== undefined ? config.vadEnabled : true;
            this.audioChunks = [];
            this.recordingStartTime = null;
            
            // 配置更新标记
            this.pendingUpdates = {
                basic: false,      // 基本配置（requireTTS, enableSRS）
                role: false,       // 角色配置（roleDescription, responseRequirements）
                scene: false,      // 场景配置（sceneDescription）
                functions: false   // 函数定义（functionCalling）
            };
            
            // 绑定回调
            this._bindCallbacks(config);
        }
        
        /**
         * 绑定用户回调
         */
        _bindCallbacks(config) {
            if (config.onTextChunk) {
                this.on(Events.TEXT_CHUNK, config.onTextChunk);
            }
            if (config.onVoiceChunk) {
                this.on(Events.VOICE_CHUNK, config.onVoiceChunk);
            }
            if (config.onMessageComplete) {
                this.on(Events.MESSAGE_COMPLETE, config.onMessageComplete);
            }
            if (config.onError) {
                this.on(Events.MESSAGE_ERROR, config.onError);
                this.on(Events.CONNECTION_ERROR, config.onError);
            }
            if (config.onFunctionCall) {
                this.on(Events.FUNCTION_CALL, config.onFunctionCall);
            }
            if (config.onSpeechStart) {
                this.on(Events.SPEECH_START, config.onSpeechStart);
            }
            if (config.onSpeechEnd) {
                this.on(Events.SPEECH_END, config.onSpeechEnd);
            }
        }
        
        /**
         * 连接到服务器并注册会话
         * @param {Object} authData - 认证数据
         */
        async connect(authData) {
            try {
                info('[MuseumAgentClient] 开始连接服务器...');
                
                // 连接 WebSocket
                await this.wsClient.connect();
                
                // 初始化接收管理器
                this.receiveManager = new ReceiveManager(this.wsClient);
                
                // 设置 WebSocket 消息处理器
                this.wsClient.onMessage = (message) => {
                    this.receiveManager.handleMessage(message);
                };
                
                // 设置会话过期回调
                this.receiveManager.onSessionExpired = (payload) => {
                    this.isConnected = false;
                    this.sessionId = null;
                    this.sessionManager.clearSession();
                    this.eventBus.emit(Events.SESSION_EXPIRED, payload);
                };
                
                // 设置连接关闭回调
                this.wsClient.onClose = (event) => {
                    if (event.code !== 1000) {
                        this.sessionId = null;
                        this.isConnected = false;
                        this.sessionManager.clearSession();
                        this.eventBus.emit(Events.SESSION_EXPIRED, {
                            error_code: 'CONNECTION_LOST',
                            error_msg: '连接已断开，请重新登录',
                            error_detail: `code: ${event.code}, reason: ${event.reason}`,
                            retryable: false
                        });
                    }
                };
                
                // ✅ V2.0: 注册会话（包含角色配置和场景描述）
                const result = await this.wsClient.register(
                    authData,
                    this.config.platform,
                    this.config.requireTTS,
                    this.config.enableSRS,
                    this.config.functionCalling,
                    this.config.roleDescription,
                    this.config.responseRequirements,
                    this.config.sceneDescription
                );
                
                this.sessionId = result.session_id;
                this.isConnected = true;
                this.lastAuthData = authData; // 保存认证数据
                
                // 初始化发送管理器（传递配置引用和客户端实例）
                this.sendManager = new SendManager(this.wsClient, this.sessionId, this.config, null, this);
                
                info('[MuseumAgentClient] 连接成功，会话ID:', this.sessionId);
                this.eventBus.emit(Events.CONNECTED, result);
                
                return result;
                
            } catch (err) {
                error('[MuseumAgentClient] 连接失败:', err);
                this.eventBus.emit(Events.CONNECTION_ERROR, err);
                throw err;
            }
        }
        
        /**
         * ✅ 新增：保存会话（用于下次自动恢复）
         * @returns {Promise<boolean>} 是否成功
         */
        async saveSession() {
            if (!this.isConnected || !this.lastAuthData) {
                warn('[MuseumAgentClient] 无法保存会话：未连接或缺少认证数据');
                return false;
            }
            
            return await this.sessionManager.saveSession(
                this.config.serverUrl,
                this.lastAuthData,
                this.sessionId
            );
        }
        
        /**
         * ✅ 新增：从保存的会话恢复连接
         * @returns {Promise<boolean>} 是否成功恢复
         */
        async reconnectFromSavedSession() {
            try {
                info('[MuseumAgentClient] 尝试从保存的会话恢复...');
                
                const session = await this.sessionManager.loadSession();
                if (!session) {
                    info('[MuseumAgentClient] 没有保存的会话');
                    return false;
                }
                
                // 更新服务器地址
                this.config.serverUrl = session.serverUrl;
                this.wsClient.config.baseUrl = session.serverUrl;
                
                // 尝试连接
                await this.connect(session.authData);
                
                info('[MuseumAgentClient] 会话恢复成功');
                return true;
            } catch (err) {
                warn('[MuseumAgentClient] 会话恢复失败:', err);
                this.sessionManager.clearSession();
                return false;
            }
        }
        
        /**
         * 断开连接
         * @param {string} reason - 断开原因
         * @param {boolean} clearSession - 是否清除保存的会话（默认 false）
         */
        async disconnect(reason = '客户端主动断开', clearSession = false) {
            info('[MuseumAgentClient] 断开连接:', reason);
            
            if (this.wsClient) {
                await this.wsClient.disconnect(reason);
            }
            
            this.isConnected = false;
            this.sessionId = null;
            
            // 可选：清除保存的会话
            if (clearSession) {
                this.sessionManager.clearSession();
            }
            
            this.eventBus.emit(Events.DISCONNECTED);
        }
        
        /**
         * ✅ 新增：更新配置（自动保存）
         * @param {string} key - 配置键
         * @param {*} value - 配置值
         */
        updateConfig(key, value) {
            this.config[key] = value;
            this.configManager.update(key, value);
            
            // 自动标记需要更新的配置项
            this._markConfigForUpdate(key);
            
            info('[MuseumAgentClient] 配置已更新:', key, '=', value);
        }
        
        /**
         * ✅ 新增：批量更新配置
         * @param {Object} updates - 配置更新对象
         */
        updateConfigs(updates) {
            Object.assign(this.config, updates);
            this.configManager.updateMultiple(updates);
            
            // 自动标记需要更新的配置项
            Object.keys(updates).forEach(key => {
                this._markConfigForUpdate(key);
            });
            
            info('[MuseumAgentClient] 配置已批量更新');
        }
        
        /**
         * ✅ 新增：重置配置为默认值
         */
        resetConfig() {
            this.configManager.reset();
            this.config = this.configManager.getAll();
            info('[MuseumAgentClient] 配置已重置为默认值');
        }
        
        /**
         * 发送文本消息
         * @param {string} text - 文本内容
         * @param {Object} options - 选项
         */
        async sendText(text, options = {}) {
            if (!this.isConnected) {
                throw new Error('未连接到服务器');
            }
            
            // 如果有之前的请求，打断它（不等待）
            if (this.latestRequestId) {
                this.receiveManager.interruptRequest(this.latestRequestId, 'USER_NEW_INPUT');
                this.audioManager.stopAllPlayback();
            }
            
            // 立即发送文本消息
            const requestId = this.sendManager.sendText(text, {
                requireTTS: options.requireTTS !== undefined ? options.requireTTS : this.config.requireTTS,
                enableSRS: options.enableSRS !== undefined ? options.enableSRS : this.config.enableSRS,
                functionCallingOp: options.functionCalling ? 'REPLACE' : undefined,
                functionCalling: options.functionCalling
            });
            
            this.latestRequestId = requestId;
            
            // 发送消息事件
            this.eventBus.emit(Events.MESSAGE_SENT, { 
                id: requestId, 
                type: 'text', 
                content: text 
            });
            
            // 注册响应处理器
            this.receiveManager.registerHandler(requestId, {
                onTextChunk: (chunk) => {
                    this.eventBus.emit(Events.TEXT_CHUNK, { messageId: requestId, chunk });
                },
                
                onVoiceChunk: async (audioData, seq) => {
                    this.eventBus.emit(Events.VOICE_CHUNK, { messageId: requestId, audioData, seq });
                    
                    // 自动播放
                    if (this.config.autoPlay) {
                        if (seq === 0) {
                            await this.audioManager.startStreamingMessage(requestId);
                        }
                        await this.audioManager.addStreamingChunk(requestId, audioData);
                    }
                },
                
                onFunctionCall: (functionCall) => {
                    this.eventBus.emit(Events.FUNCTION_CALL, functionCall);
                },
                
                onComplete: (data) => {
                    this.eventBus.emit(Events.MESSAGE_COMPLETE, { messageId: requestId });
                    
                    // 结束流式播放
                    if (this.config.autoPlay) {
                        this.audioManager.endStreamingMessage(requestId);
                    }
                },
                
                onInterrupted: (data) => {
                    this.eventBus.emit(Events.INTERRUPTED, { 
                        messageId: requestId, 
                        reason: data.reason 
                    });
                },
                
                onError: (error) => {
                    this.eventBus.emit(Events.MESSAGE_ERROR, error);
                }
            });
        }
        
        /**
         * 开始录音
         * @param {Object} options - 选项
         */
        async startRecording(options = {}) {
            if (this.isRecording) {
                console.warn('[MuseumAgentClient] 已在录音中');
                return;
            }
            
            const vadEnabled = options.vadEnabled !== undefined ? options.vadEnabled : this.vadEnabled;
            const vadParams = options.vadParams || this.config.vadParams;
            
            try {
                if (vadEnabled) {
                    // 启用 VAD
                    await this.audioManager.startRecordingWithVAD(
                        vadParams,
                        // onSpeechStart
                        async () => {
                            this.eventBus.emit(Events.SPEECH_START);
                            
                            // ✅ 立即创建新的语音流（不等待打断）
                            await this._startNewVoiceStream();
                        },
                        // onAudioData
                        (audioData) => {
                            // ✅ 立即发送音频数据（不会丢失）
                            this.audioChunks.push(audioData);
                            this.sendManager.sendAudioChunk(audioData);
                        },
                        // onSpeechEnd
                        () => {
                            this.eventBus.emit(Events.SPEECH_END);
                            this._endCurrentVoiceStream();
                        }
                    );
                } else {
                    // 不启用 VAD，立即创建语音流
                    await this._startNewVoiceStream();
                    
                    await this.audioManager.startRecording((audioData) => {
                        this.audioChunks.push(audioData);
                        this.sendManager.sendAudioChunk(audioData);
                    });
                }
                
                this.isRecording = true;
                this.eventBus.emit(Events.RECORDING_START);
                
            } catch (error) {
                this.eventBus.emit(Events.RECORDING_ERROR, error);
                throw error;
            }
        }
        
        /**
         * 停止录音
         */
        async stopRecording() {
            if (!this.isRecording) {
                return;
            }
            
            // 结束当前语音流
            if (this.currentVoiceRequestId) {
                this._endCurrentVoiceStream();
            }
            
            // 停止录音
            this.audioManager.stopRecording();
            
            this.isRecording = false;
            this.eventBus.emit(Events.RECORDING_STOP);
        }
        
        /**
         * 创建新的语音流（立即创建，不等待）
         */
        async _startNewVoiceStream() {
            // ✅ 如果有之前的请求，立即打断（不等待确认）
            if (this.latestRequestId) {
                this.receiveManager.interruptRequest(this.latestRequestId, 'USER_VOICE_INPUT');
                this.audioManager.stopAllPlayback();
            }
            
            // ✅ 立即开始语音流
            const { requestId, controller } = this.sendManager.startVoiceStream({
                requireTTS: this.config.requireTTS,
                enableSRS: this.config.enableSRS
            });
            
            this.latestRequestId = requestId;
            this.currentVoiceRequestId = requestId;
            this.audioChunks = [];
            // 调整开始时间，包含前填充时长
            this.recordingStartTime = Date.now() - this.config.vadParams.preSpeechPadding;
            
            // 发送消息创建事件
            this.eventBus.emit(Events.MESSAGE_SENT, { 
                id: requestId, 
                type: 'voice',
                startTime: this.recordingStartTime
            });
            
            // 注册响应处理器
            this.receiveManager.registerHandler(requestId, {
                onTextChunk: (chunk) => {
                    this.eventBus.emit(Events.TEXT_CHUNK, { messageId: requestId, chunk });
                },
                
                onVoiceChunk: async (audioData, seq) => {
                    this.eventBus.emit(Events.VOICE_CHUNK, { messageId: requestId, audioData, seq });
                    
                    if (this.config.autoPlay) {
                        if (seq === 0) {
                            await this.audioManager.startStreamingMessage(requestId);
                        }
                        await this.audioManager.addStreamingChunk(requestId, audioData);
                    }
                },
                
                onFunctionCall: (functionCall) => {
                    this.eventBus.emit(Events.FUNCTION_CALL, functionCall);
                },
                
                onComplete: (data) => {
                    this.eventBus.emit(Events.MESSAGE_COMPLETE, { messageId: requestId });
                    
                    if (this.config.autoPlay) {
                        this.audioManager.endStreamingMessage(requestId);
                    }
                },
                
                onInterrupted: (data) => {
                    this.eventBus.emit(Events.INTERRUPTED, { 
                        messageId: requestId, 
                        reason: data.reason 
                    });
                },
                
                onError: (error) => {
                    this.eventBus.emit(Events.MESSAGE_ERROR, error);
                }
            });
        }
        
        /**
         * 结束当前语音流
         */
        _endCurrentVoiceStream() {
            if (!this.currentVoiceRequestId) return;
            
            // 计算录音时长（基于调整后的开始时间，已包含前填充；实际录音时间已包含后填充）
            const duration = this.recordingStartTime ? (Date.now() - this.recordingStartTime) / 1000 : 0;
            
            // 合并所有音频块
            const totalSize = this.audioChunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
            const mergedAudio = new Uint8Array(totalSize);
            let offset = 0;
            for (const chunk of this.audioChunks) {
                mergedAudio.set(new Uint8Array(chunk), offset);
                offset += chunk.byteLength;
            }
            
            // 发送录音完成事件
            this.eventBus.emit(Events.RECORDING_COMPLETE, {
                id: this.currentVoiceRequestId,
                audioData: mergedAudio.buffer,
                duration: duration
            });
            
            // 结束语音流
            this.sendManager.endVoiceStream();
            
            this.currentVoiceRequestId = null;
            this.audioChunks = [];
            this.recordingStartTime = null;
        }
        
        /**
         * 打断当前请求
         */
        async interrupt(reason = 'USER_NEW_INPUT') {
            if (!this.latestRequestId) {
                return;
            }
            
            // 停止音频播放
            this.audioManager.stopAllPlayback();
            
            // 打断请求
            await this.receiveManager.interruptRequest(this.latestRequestId, reason);
        }
        
        /**
         * 播放音频
         */
        async playAudio(pcmData, sampleRate = 16000) {
            await this.audioManager.playPCM(pcmData, sampleRate);
        }
        
        /**
         * 停止播放
         */
        stopPlayback() {
            this.audioManager.stopAllPlayback();
        }
        
        /**
         * 订阅事件
         */
        on(event, callback) {
            return this.eventBus.on(event, callback);
        }
        
        /**
         * 取消订阅
         */
        off(event, callback) {
            this.eventBus.off(event, callback);
        }
        
        /**
         * 订阅一次性事件
         */
        once(event, callback) {
            return this.eventBus.once(event, callback);
        }
        
        /**
         * 清理资源
         */
        cleanup() {
            if (this.receiveManager) {
                this.receiveManager.cleanup();
            }
            this.audioManager.cleanup();
            this.eventBus.clear();
        }
        
        /**
         * ✅ 设置设置面板引用（用于差异配置更新）
         */
        setSettingsPanel(settingsPanel) {
            if (this.sendManager) {
                this.sendManager.settingsPanel = settingsPanel;
            }
        }
        
        /**
         * ✅ 新增：标记配置为需要更新
         * @private
         */
        _markConfigForUpdate(key) {
            switch (key) {
                case 'requireTTS':
                case 'enableSRS':
                    this.pendingUpdates.basic = true;
                    break;
                case 'roleDescription':
                case 'responseRequirements':
                    this.pendingUpdates.role = true;
                    break;
                case 'sceneDescription':
                    this.pendingUpdates.scene = true;
                    break;
                case 'functionCalling':
                    this.pendingUpdates.functions = true;
                    break;
            }
        }
        
        /**
         * ✅ 新增：获取待更新的配置项
         * @returns {Object} 待更新的配置项
         */
        getPendingUpdates() {
            const updates = {};
            
            if (this.pendingUpdates.basic) {
                updates.require_tts = this.config.requireTTS;
                updates.enable_srs = this.config.enableSRS;
            }
            
            if (this.pendingUpdates.role) {
                updates.system_prompt = {
                    role_description: this.config.roleDescription || '',
                    response_requirements: this.config.responseRequirements || ''
                };
            }
            
            if (this.pendingUpdates.scene) {
                updates.scene_context = {
                    scene_description: this.config.sceneDescription || ''
                };
            }
            
            if (this.pendingUpdates.functions) {
                updates.function_calling = this.config.functionCalling;
            }
            
            return updates;
        }
        
        /**
         * ✅ 新增：清除更新标记
         */
        clearUpdateMarks() {
            this.pendingUpdates = {
                basic: false,
                role: false,
                scene: false,
                functions: false
            };
            info('[MuseumAgentClient] 配置更新标记已清除');
        }
        
        /**
         * ✅ 新增：获取更新标记
         * @returns {Object} 更新标记状态
         */
        getUpdateMarks() {
            return { ...this.pendingUpdates };
        }
        
        /**
         * ✅ 新增：获取配置和更新标记
         * @returns {Object} 配置和更新标记
         */
        getConfigWithUpdates() {
            return {
                config: { ...this.config },
                updates: this.getPendingUpdates(),
                marks: this.getUpdateMarks()
            };
        }
        
        /**
         * ✅ 新增：更新智能体上下文
         * @param {Object} contextData - 上下文数据
         */
        updateContext(contextData) {
            info('[MuseumAgentClient] 更新智能体上下文:', contextData);
            
            try {
                // 标记需要更新的配置项
                const needUpdate = {
                    scene: false,
                    role: false,
                    functions: false
                };
                
                // 更新上下文相关配置
                if (contextData.sceneDescription) {
                    this.config.sceneDescription = contextData.sceneDescription;
                    this.configManager.update('sceneDescription', contextData.sceneDescription);
                    needUpdate.scene = true;
                }
                if (contextData.roleDescription) {
                    this.config.roleDescription = contextData.roleDescription;
                    this.configManager.update('roleDescription', contextData.roleDescription);
                    needUpdate.role = true;
                }
                if (contextData.responseRequirements) {
                    this.config.responseRequirements = contextData.responseRequirements;
                    this.configManager.update('responseRequirements', contextData.responseRequirements);
                    needUpdate.role = true;
                }
                if (contextData.functionCalling !== undefined) {
                    this.config.functionCalling = contextData.functionCalling;
                    this.configManager.update('functionCalling', contextData.functionCalling);
                    needUpdate.functions = true;
                }
                if (contextData.functions) {
                    try {
                        // 解析functions字段
                        const functionsData = typeof contextData.functions === 'string' 
                            ? JSON.parse(contextData.functions) 
                            : contextData.functions;
                        if (functionsData.functions) {
                            this.config.functionCalling = functionsData.functions;
                            this.configManager.update('functionCalling', functionsData.functions);
                            needUpdate.functions = true;
                        } else if (Array.isArray(functionsData)) {
                            // 如果直接是函数数组
                            this.config.functionCalling = functionsData;
                            this.configManager.update('functionCalling', functionsData);
                            needUpdate.functions = true;
                        }
                    } catch (error) {
                        warn('[MuseumAgentClient] 解析functions字段失败:', error);
                    }
                }
                
                // 自动标记需要更新的配置项
                if (needUpdate.scene) {
                    this.pendingUpdates.scene = true;
                }
                if (needUpdate.role) {
                    this.pendingUpdates.role = true;
                }
                if (needUpdate.functions) {
                    this.pendingUpdates.functions = true;
                }
                
                // 保持向后兼容：如果有设置面板引用，设置相应的更新开关
                if (this.sendManager && this.sendManager.settingsPanel) {
                    const settingsPanel = this.sendManager.settingsPanel;
                    if (needUpdate.scene) {
                        settingsPanel.autoEnableUpdate('scene');
                    }
                    if (needUpdate.role) {
                        settingsPanel.autoEnableUpdate('role');
                    }
                    if (needUpdate.functions) {
                        settingsPanel.autoEnableUpdate('functions');
                    }
                }
                
                // 触发配置更新事件
                this.eventBus.emit('configUpdated', this.config);
                info('[MuseumAgentClient] 智能体上下文更新成功');
            } catch (error) {
                error('[MuseumAgentClient] 更新智能体上下文失败:', error);
                throw error;
            }
        }
        
        /**
         * 获取连接状态
         */
        get connected() {
            return this.isConnected;
        }
        
        /**
         * 获取会话 ID
         */
        get session() {
            return this.sessionId;
        }
        
        /**
         * 获取WebSocket客户端实例
         */
        get wsClient() {
            return this._wsClient;
        }
    }

    /**
     * 错误处理工具（纯函数）
     * 提供统一的错误分类和格式化
     */


    /**
     * 分类错误
     * @param {Error} error - 错误对象
     * @returns {Object} 分类结果
     */
    function classifyError(error) {
        const message = error.message || '';
        
        // 网络错误
        if (message.includes('网络') || message.includes('连接') || message.includes('timeout') || message.includes('Network')) {
            return {
                type: ERROR_TYPES.NETWORK_ERROR,
                userMessage: '网络连接失败，请检查网络设置',
                recoverable: true
            };
        }
        
        // 认证错误
        if (message.includes('认证') || message.includes('登录') || message.includes('auth') || message.includes('Auth')) {
            return {
                type: ERROR_TYPES.AUTH_ERROR,
                userMessage: '认证失败，请重新登录',
                recoverable: false
            };
        }
        
        // 会话过期
        if (message.includes('会话') || message.includes('过期') || message.includes('session') || message.includes('Session')) {
            return {
                type: ERROR_TYPES.SESSION_EXPIRED,
                userMessage: '会话已过期，请重新登录',
                recoverable: false
            };
        }
        
        // 默认错误
        return {
            type: ERROR_TYPES.UNKNOWN_ERROR,
            userMessage: '操作失败：' + message,
            recoverable: false
        };
    }

    /**
     * 格式化错误信息
     * @param {Error} error - 错误对象
     * @param {string} context - 错误上下文
     * @returns {Object} 格式化后的错误信息
     */
    function formatError(error, context = '') {
        const classified = classifyError(error);
        return {
            ...classified,
            context,
            timestamp: Date.now(),
            originalError: error
        };
    }

    exports.AudioManager = AudioManager;
    exports.ConfigManager = ConfigManager;
    exports.DEFAULT_CONFIG = DEFAULT_CONFIG;
    exports.ERROR_TYPES = ERROR_TYPES;
    exports.EventBus = EventBus;
    exports.Events = Events;
    exports.LOG_LEVELS = LOG_LEVELS;
    exports.MuseumAgentClient = MuseumAgentClient;
    exports.ReceiveManager = ReceiveManager;
    exports.STORAGE_KEYS = STORAGE_KEYS;
    exports.SendManager = SendManager;
    exports.SessionManager = SessionManager;
    exports.WebSocketClient = WebSocketClient;
    exports.classifyError = classifyError;
    exports.clearStorage = clearStorage;
    exports.debug = debug;
    exports.decryptData = decryptData;
    exports.default = MuseumAgentClient;
    exports.encryptData = encryptData;
    exports.error = error;
    exports.escapeHtml = escapeHtml;
    exports.formatError = formatError;
    exports.generateSecureId = generateSecureId;
    exports.getStorage = getStorage;
    exports.hasStorage = hasStorage;
    exports.info = info;
    exports.removeStorage = removeStorage;
    exports.sanitizeHtml = sanitizeHtml;
    exports.setLogLevel = setLogLevel;
    exports.setLogPrefix = setLogPrefix;
    exports.setStorage = setStorage;
    exports.validateInput = validateInput;
    exports.warn = warn;

    Object.defineProperty(exports, '__esModule', { value: true });

}));
//# sourceMappingURL=museum-agent-sdk.js.map
