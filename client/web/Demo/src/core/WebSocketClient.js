/**
 * WebSocket 客户端
 * 严格遵循 CommunicationProtocol_CS.md 协议规范
 */

export class WebSocketClient {
    constructor(config = {}) {
        this.config = {
            baseUrl: config.baseUrl || 'ws://localhost:8001',
            reconnectInterval: config.reconnectInterval || 5000,
            maxReconnectAttempts: config.maxReconnectAttempts || 5,
            heartbeatTimeout: config.heartbeatTimeout || 60000
        };
        
        this.ws = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.heartbeatTimer = null;
        this.messageHandlers = new Map();
        this.pendingRequests = new Map();
    }

    /**
     * 连接 WebSocket
     */
    connect() {
        return new Promise((resolve, reject) => {
            const wsUrl = `${this.config.baseUrl}/ws/agent/stream`;
            console.log('[WebSocket] 连接:', wsUrl);

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('[WebSocket] 连接成功');
                this.reconnectAttempts = 0;
                resolve();
            };

            this.ws.onmessage = (event) => {
                this._handleMessage(event);
            };

            this.ws.onerror = (error) => {
                console.error('[WebSocket] 错误:', error);
                reject(error);
            };

            this.ws.onclose = (event) => {
                console.log('[WebSocket] 连接关闭:', event.code, event.reason);
                this._handleClose(event);
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
     * 注册会话（协议 REGISTER）
     */
    async register(authData, platform = 'WEB', requireTTS = false, functionCalling = []) {
        // 等待连接完全建立
        if (this.ws.readyState !== WebSocket.OPEN) {
            console.log('[WebSocket] 等待连接建立...');
            await new Promise((resolve, reject) => {
                const checkInterval = setInterval(() => {
                    if (this.ws.readyState === WebSocket.OPEN) {
                        clearInterval(checkInterval);
                        resolve();
                    }
                }, 100);
                
                setTimeout(() => {
                    clearInterval(checkInterval);
                    reject(new Error('等待连接超时'));
                }, 5000);
            });
        }

        const message = {
            version: '1.0',
            msg_type: 'REGISTER',
            session_id: null,
            payload: {
                auth: authData,
                platform: platform,
                require_tts: requireTTS,
                function_calling: functionCalling
            },
            timestamp: Date.now()
        };

        return new Promise((resolve, reject) => {
            // 设置一次性处理器
            const handler = (data) => {
                this.sessionId = data.payload.session_id;
                this._startHeartbeatMonitor();
                this.messageHandlers.delete('REGISTER_ACK');
                resolve(data.payload);
            };

            this.messageHandlers.set('REGISTER_ACK', handler);
            this._send(message);

            // 超时处理
            setTimeout(() => {
                if (this.messageHandlers.has('REGISTER_ACK')) {
                    this.messageHandlers.delete('REGISTER_ACK');
                    reject(new Error('注册超时'));
                }
            }, 30000);
        });
    }

    /**
     * 发送文本请求（协议 REQUEST - TEXT）
     */
    async sendTextRequest(text, options = {}) {
        const requestId = this._generateId();
        
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

        // 添加 Function Calling 配置（如果有）
        if (options.functionCallingOp) {
            message.payload.function_calling_op = options.functionCallingOp;
            message.payload.function_calling = options.functionCalling || [];
        }

        return this._sendRequest(
            requestId, 
            message, 
            options.onChunk, 
            options.onComplete,
            options.onVoiceChunk,
            options.onFunctionCall
        );
    }

    /**
     * 发送语音请求（协议 REQUEST - VOICE，流式 BINARY 模式）
     * 正确实现：起始帧 → 实时二进制帧 → 结束帧
     */
    async sendVoiceRequestStream(audioStream, options = {}) {
        const requestId = this._generateId();

        console.log('[WebSocket] 开始流式语音发送, requestId:', requestId);

        // 先注册响应处理器
        const responsePromise = this._waitForResponse(
            requestId, 
            options.onChunk, 
            options.onComplete,
            options.onVoiceChunk,
            options.onFunctionCall
        );

        // 1. 发送起始帧（stream_seq = 0）
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
                content: { voice_mode: 'BINARY' }
            },
            timestamp: Date.now()
        };

        this._send(startMessage);
        console.log('[WebSocket] 已发送起始帧');

        // 2. 实时发送二进制音频数据
        const reader = audioStream.getReader();
        let chunkCount = 0;
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('[WebSocket] 音频流读取完成，共发送', chunkCount, '个数据块');
                    break;
                }
                
                // 立即发送二进制帧
                if (this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(value);
                    chunkCount++;
                    console.log('[WebSocket] 发送音频数据块', chunkCount, ':', value.byteLength, '字节');
                } else {
                    console.error('[WebSocket] 连接已断开，无法发送音频数据');
                    break;
                }
            }
        } catch (error) {
            console.error('[WebSocket] 读取音频流失败:', error);
        } finally {
            reader.releaseLock();
        }

        // 3. 发送结束帧（stream_seq = -1）
        const endMessage = {
            version: '1.0',
            msg_type: 'REQUEST',
            session_id: this.sessionId,
            payload: {
                request_id: requestId,
                data_type: 'VOICE',
                stream_flag: true,
                stream_seq: -1,
                require_tts: options.requireTTS || false,
                content: { voice_mode: 'BINARY' }
            },
            timestamp: Date.now()
        };

        this._send(endMessage);
        console.log('[WebSocket] 已发送结束帧');

        // 等待响应
        return responsePromise;
    }

    /**
     * 查询会话信息（协议 SESSION_QUERY）
     */
    async querySession(queryFields = []) {
        const message = {
            version: '1.0',
            msg_type: 'SESSION_QUERY',
            session_id: this.sessionId,
            payload: { query_fields: queryFields },
            timestamp: Date.now()
        };

        return new Promise((resolve, reject) => {
            const handler = (data) => {
                if (data.msg_type === 'SESSION_INFO') {
                    resolve(data.payload);
                } else if (data.msg_type === 'ERROR') {
                    reject(new Error(data.payload.error_msg));
                }
            };

            this.messageHandlers.set('SESSION_QUERY', handler);
            this._send(message);

            setTimeout(() => {
                this.messageHandlers.delete('SESSION_QUERY');
                reject(new Error('查询超时'));
            }, 10000);
        });
    }

    /**
     * 断开会话（协议 SHUTDOWN）
     */
    async disconnect(reason = '客户端主动断开') {
        const message = {
            version: '1.0',
            msg_type: 'SHUTDOWN',
            session_id: this.sessionId,
            payload: { reason },
            timestamp: Date.now()
        };

        this._send(message);
        this._stopHeartbeatMonitor();
        
        if (this.ws) {
            this.ws.close(1000, reason);
        }
    }

    /**
     * 处理接收到的消息
     */
    _handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('[WebSocket] 收到消息:', data.msg_type);

            // 处理心跳
            if (data.msg_type === 'HEARTBEAT') {
                this._handleHeartbeat(data);
                return;
            }

            // 处理响应
            if (data.msg_type === 'RESPONSE') {
                this._handleResponse(data);
                return;
            }

            // 处理错误
            if (data.msg_type === 'ERROR') {
                this._handleError(data);
                return;
            }

            // 处理其他消息类型
            const handler = this.messageHandlers.get(data.msg_type);
            if (handler) {
                handler(data);
                this.messageHandlers.delete(data.msg_type);
            }

        } catch (error) {
            console.error('[WebSocket] 消息解析失败:', error);
        }
    }

    /**
     * 处理 RESPONSE（正确区分文本流和语音流）
     */
    _handleResponse(data) {
        const payload = data.payload;
        const requestId = payload.request_id;
        
        const request = this.pendingRequests.get(requestId);
        if (!request) {
            console.warn('[WebSocket] 未找到对应的请求:', requestId);
            return;
        }

        // 处理 Function Call
        if (payload.function_call) {
            if (request.onFunctionCall) {
                request.onFunctionCall(payload.function_call);
            }
        }

        // 处理文本流
        if (payload.content?.text) {
            if (request.onTextChunk) {
                request.onTextChunk(payload.content.text);
            }
        }

        // 处理语音流
        if (payload.content?.voice) {
            if (request.onVoiceChunk) {
                const audioData = this._decodeBase64(payload.content.voice);
                request.onVoiceChunk(audioData, payload.voice_stream_seq);
            }
        }

        // 检查流是否结束
        const textEnded = payload.text_stream_seq === -1;
        const voiceEnded = payload.voice_stream_seq === -1;

        if (!request.textEnded && textEnded) {
            request.textEnded = true;
        }

        if (!request.voiceEnded && voiceEnded) {
            request.voiceEnded = true;
        }

        // 当所有流都结束时，调用 onComplete
        const allEnded = (request.textEnded || payload.text_stream_seq === undefined) &&
                         (request.voiceEnded || payload.voice_stream_seq === undefined);

        if (allEnded) {
            if (request.onComplete) {
                request.onComplete(data);
            }
            this.pendingRequests.delete(requestId);
        }
    }

    /**
     * 处理心跳（协议 HEARTBEAT）
     */
    _handleHeartbeat(data) {
        // 重置心跳超时计时器
        this._resetHeartbeatMonitor();

        // 发送心跳回复
        const reply = {
            version: '1.0',
            msg_type: 'HEARTBEAT_REPLY',
            session_id: this.sessionId,
            payload: { client_status: 'ONLINE' },
            timestamp: Date.now()
        };

        this._send(reply);
    }

    /**
     * 处理错误
     */
    _handleError(data) {
        const payload = data.payload;
        console.error('[WebSocket] 服务器错误:', payload);

        // 如果是会话无效，清除会话ID
        if (payload.error_code === 'SESSION_INVALID') {
            this.sessionId = null;
        }

        // 如果有对应的请求，拒绝 Promise
        if (payload.request_id) {
            const request = this.pendingRequests.get(payload.request_id);
            if (request && request.reject) {
                request.reject(new Error(payload.error_msg));
                this.pendingRequests.delete(payload.request_id);
            }
        }
    }

    /**
     * 发送请求并等待响应
     */
    _sendRequest(requestId, message, onChunk, onComplete, onVoiceChunk, onFunctionCall) {
        return new Promise((resolve, reject) => {
            // 保存请求上下文
            this.pendingRequests.set(requestId, {
                onTextChunk: onChunk,
                onVoiceChunk: onVoiceChunk,
                onFunctionCall: onFunctionCall,
                onComplete: (data) => {
                    if (onComplete) onComplete(data);
                    resolve(data);
                },
                reject: reject,
                textEnded: false,
                voiceEnded: false
            });

            this._send(message);

            // 超时处理
            setTimeout(() => {
                if (this.pendingRequests.has(requestId)) {
                    this.pendingRequests.delete(requestId);
                    reject(new Error('请求超时'));
                }
            }, 60000);
        });
    }

    /**
     * 等待响应
     */
    _waitForResponse(requestId, onChunk, onComplete, onVoiceChunk, onFunctionCall) {
        return new Promise((resolve, reject) => {
            this.pendingRequests.set(requestId, {
                onTextChunk: onChunk,
                onVoiceChunk: onVoiceChunk,
                onFunctionCall: onFunctionCall,
                onComplete: (data) => {
                    if (onComplete) onComplete(data);
                    resolve(data);
                },
                reject: reject,
                textEnded: false,
                voiceEnded: false
            });

            setTimeout(() => {
                if (this.pendingRequests.has(requestId)) {
                    this.pendingRequests.delete(requestId);
                    reject(new Error('请求超时'));
                }
            }, 60000);
        });
    }

    /**
     * 启动心跳监控
     */
    _startHeartbeatMonitor() {
        this._stopHeartbeatMonitor();
        this.heartbeatTimer = setTimeout(() => {
            console.warn('[WebSocket] 心跳超时，连接可能已断开');
            this._handleClose({ code: 1006, reason: '心跳超时' });
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
     * 处理连接关闭
     */
    _handleClose(event) {
        this._stopHeartbeatMonitor();

        // 如果不是正常关闭，尝试重连
        if (event.code !== 1000 && this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[WebSocket] 尝试重连 (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect().catch(error => {
                    console.error('[WebSocket] 重连失败:', error);
                });
            }, this.config.reconnectInterval);
        }
    }

    /**
     * 发送消息
     */
    _send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('[WebSocket] 连接未打开，无法发送消息');
        }
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
     * 生成唯一 ID
     */
    _generateId() {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 获取连接状态
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

