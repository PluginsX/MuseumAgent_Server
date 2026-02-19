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
            heartbeatTimeout: config.heartbeatTimeout || 120000  // 120秒（从60秒增加）
        };
        
        this.ws = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.heartbeatTimer = null;
        this.messageHandlers = new Map();
        this.pendingRequests = new Map();
        this.onSessionExpired = null; // 会话过期回调
        this.latestRequestId = null; // ✅ 跟踪最新的请求ID（用于客户端打断）
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
    async register(authData, platform = 'WEB', requireTTS = false, enableSRS = true, functionCalling = []) {
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
                enable_srs: enableSRS,
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
     * 返回 { requestId, promise } 对象
     */
    sendTextRequest(text, options = {}) {
        const requestId = this._generateId();
        
        // ✅ 更新最新请求ID（用于客户端打断）
        this.latestRequestId = requestId;
        console.log('[WebSocket] 更新最新请求ID:', requestId);
        
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

        // 添加 EnableSRS 配置（如果有）
        if (options.enableSRS !== undefined) {
            message.payload.enable_srs = options.enableSRS;
        }

        // 添加 Function Calling 配置（如果有）
        if (options.functionCallingOp) {
            message.payload.function_calling_op = options.functionCallingOp;
            message.payload.function_calling = options.functionCalling || [];
        }

        const promise = this._sendRequest(
            requestId, 
            message, 
            options.onChunk, 
            options.onComplete,
            options.onVoiceChunk,
            options.onFunctionCall
        );
        
        // ✅ 返回 requestId 和 promise
        return { requestId, promise };
    }

    /**
     * 发送语音请求（协议 REQUEST - VOICE，流式 BINARY 模式）
     * 正确实现：起始帧 → 实时二进制帧 → 结束帧
     * 返回 { requestId, promise } 对象
     */
    sendVoiceRequestStream(audioStream, options = {}) {
        const requestId = this._generateId();

        // ✅ 更新最新请求ID（用于客户端打断）
        this.latestRequestId = requestId;
        console.log('[WebSocket] 开始流式语音发送, requestId:', requestId);

        // 先注册响应处理器
        const responsePromise = this._waitForResponse(
            requestId, 
            options.onChunk, 
            options.onComplete,
            options.onVoiceChunk,
            options.onFunctionCall
        );
        
        // ✅ 立即返回 requestId 和 promise
        const result = { requestId, promise: this._sendVoiceStream(audioStream, requestId, options, responsePromise) };
        return result;
    }
    
    /**
     * 内部方法：发送语音流数据
     */
    async _sendVoiceStream(audioStream, requestId, options, responsePromise) {
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
                content: { 
                    voice_mode: 'BINARY',
                    audio_format: 'pcm'  // ✅ 明确指定 PCM 格式
                }
            },
            timestamp: Date.now()
        };

        // 添加 EnableSRS 配置（如果有）
        if (options.enableSRS !== undefined) {
            startMessage.payload.enable_srs = options.enableSRS;
        }

        this._send(startMessage);
        console.log('[WebSocket] 已发送起始帧 (PCM 格式), requestId:', requestId);

        // 2. 实时发送二进制音频数据
        const reader = audioStream.getReader();
        let chunkCount = 0;
        let streamError = null;
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('[WebSocket] 音频流读取完成，共发送', chunkCount, '个数据块, requestId:', requestId);
                    break;
                }
                
                // 立即发送二进制帧
                if (this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(value);
                    chunkCount++;
                    if (chunkCount % 10 === 0) {  // 每10个块输出一次日志
                        console.log('[WebSocket] 已发送', chunkCount, '个音频数据块, requestId:', requestId);
                    }
                } else {
                    console.error('[WebSocket] 连接已断开，无法发送音频数据, requestId:', requestId);
                    streamError = new Error('WebSocket连接已断开');
                    break;
                }
            }
        } catch (error) {
            console.error('[WebSocket] 读取音频流失败, requestId:', requestId, 'error:', error);
            streamError = error;
        } finally {
            try {
                reader.releaseLock();
                console.log('[WebSocket] 音频流 reader 已释放, requestId:', requestId);
            } catch (e) {
                console.warn('[WebSocket] 释放 reader 失败:', e.message);
            }
        }

        // ✅ 只有在没有错误且连接正常时才发送结束帧
        if (!streamError && this.ws.readyState === WebSocket.OPEN) {
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
                    content: { 
                        voice_mode: 'BINARY',
                        audio_format: 'pcm'  // ✅ 明确指定 PCM 格式
                    }
                },
                timestamp: Date.now()
            };

            this._send(endMessage);
            console.log('[WebSocket] 已发送结束帧 (PCM 格式), requestId:', requestId);
        } else {
            console.warn('[WebSocket] 跳过发送结束帧，原因:', streamError ? streamError.message : 'WebSocket未连接', 'requestId:', requestId);
            // ✅ 清理请求处理器
            if (this.pendingRequests.has(requestId)) {
                const request = this.pendingRequests.get(requestId);
                if (request.timeoutId) {
                    clearTimeout(request.timeoutId);
                }
                this.pendingRequests.delete(requestId);
                console.log('[WebSocket] 已清理未完成的请求处理器, requestId:', requestId);
            }
            throw streamError || new Error('WebSocket连接已断开');
        }

        // 等待响应
        return responsePromise;
    }

    /**
     * 发送打断请求（协议 INTERRUPT）
     */
    async sendInterrupt(requestId, reason = 'USER_NEW_INPUT') {
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

        console.log('[WebSocket] 发送打断请求:', requestId, '原因:', reason);

        return new Promise((resolve, reject) => {
            let timeoutId = null;
            
            // 设置一次性处理器
            const handler = (data) => {
                // ✅ 清除超时定时器
                if (timeoutId) {
                    clearTimeout(timeoutId);
                    timeoutId = null;
                }
                this.messageHandlers.delete('INTERRUPT_ACK');
                console.log('[WebSocket] 收到打断确认:', data.payload);
                resolve(data.payload);
            };

            this.messageHandlers.set('INTERRUPT_ACK', handler);
            this._send(message);

            // ✅ 增加超时时间到15秒（从5秒增加）
            timeoutId = setTimeout(() => {
                if (this.messageHandlers.has('INTERRUPT_ACK')) {
                    this.messageHandlers.delete('INTERRUPT_ACK');
                    console.debug('[WebSocket] 打断请求超时（这是正常的，因为使用了乐观更新）');
                    reject(new Error('打断请求超时'));
                }
            }, 15000);
        });
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
            console.log('[WebSocket] 收到消息:', data.msg_type, data.payload?.request_id ? `(req: ${data.payload.request_id.substring(0, 16)}...)` : '');

            // 处理心跳
            if (data.msg_type === 'HEARTBEAT') {
                this._handleHeartbeat(data);
                return;
            }

            // ✅ 优先处理打断确认（避免被其他消息阻塞）
            if (data.msg_type === 'INTERRUPT_ACK') {
                const handler = this.messageHandlers.get('INTERRUPT_ACK');
                if (handler) {
                    console.log('[WebSocket] 处理打断确认');
                    handler(data);
                } else {
                    // ✅ 降低日志级别，这是正常的（乐观更新导致处理器可能已被超时删除）
                    console.debug('[WebSocket] 收到打断确认但处理器已清理（乐观更新，正常现象）');
                }
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
     * 处理 RESPONSE（优化版：正确处理流式响应 + 客户端打断）
     */
    _handleResponse(data) {
        const payload = data.payload;
        const requestId = payload.request_id;
        
        // ✅ 客户端打断：如果这不是最新的请求，直接丢弃响应
        if (requestId !== this.latestRequestId) {
            console.log('[WebSocket] 丢弃旧请求的响应:', requestId, '(最新:', this.latestRequestId, ')');
            
            // 清理旧请求的处理器
            const request = this.pendingRequests.get(requestId);
            if (request) {
                if (request.timeoutId) {
                    clearTimeout(request.timeoutId);
                }
                // 调用完成回调，标记为被打断
                if (request.onComplete) {
                    request.onComplete({
                        ...data,
                        interrupted: true,
                        interrupt_reason: 'CLIENT_SIDE_INTERRUPT'
                    });
                }
                this.pendingRequests.delete(requestId);
            }
            return;
        }
        
        const request = this.pendingRequests.get(requestId);
        if (!request) {
            // ✅ 降低日志级别，这是正常现象（请求已完成）
            console.debug('[WebSocket] 请求已完成或不存在:', requestId);
            return;
        }

        // ✅ 检查是否被中断
        if (payload.interrupted) {
            console.log('[WebSocket] 请求被中断:', requestId, '原因:', payload.interrupt_reason);
            
            // 清除超时定时器
            if (request.timeoutId) {
                clearTimeout(request.timeoutId);
            }
            
            // 调用完成回调（标记为中断）
            if (request.onComplete) {
                request.onComplete({
                    ...data,
                    interrupted: true,
                    interrupt_reason: payload.interrupt_reason
                });
            }
            
            this.pendingRequests.delete(requestId);
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

        // ✅ 检查流是否结束（更严格的判断）
        const textEnded = payload.text_stream_seq === -1;
        const voiceEnded = payload.voice_stream_seq === -1;

        if (!request.textEnded && textEnded) {
            request.textEnded = true;
            console.log('[WebSocket] 文本流结束:', requestId);
        }

        if (!request.voiceEnded && voiceEnded) {
            request.voiceEnded = true;
            console.log('[WebSocket] 语音流结束:', requestId);
        }

        // ✅ 只有当所有预期的流都结束时，才删除请求
        // 第一次收到响应时，记录该请求包含哪些流
        if (!request.hasCheckedStreams) {
            request.hasTextStream = payload.text_stream_seq !== undefined;
            request.hasVoiceStream = payload.voice_stream_seq !== undefined;
            request.hasCheckedStreams = true;
            console.log('[WebSocket] 检测到流类型:', {
                requestId: requestId,
                hasText: request.hasTextStream,
                hasVoice: request.hasVoiceStream
            });
        }
        
        const textComplete = !request.hasTextStream || request.textEnded;
        const voiceComplete = !request.hasVoiceStream || request.voiceEnded;
        
        const allEnded = textComplete && voiceComplete;

        if (allEnded) {
            console.log('[WebSocket] 请求完成:', requestId);
            
            // ✅ 清除超时定时器
            if (request.timeoutId) {
                clearTimeout(request.timeoutId);
            }
            
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
        console.log('[WebSocket] 收到心跳，剩余时间:', data.payload?.remaining_seconds, '秒');
        
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
        console.log('[WebSocket] 已发送心跳回复');
    }

    /**
     * 处理错误
     */
    _handleError(data) {
        const payload = data.payload;
        console.error('[WebSocket] 服务器错误:', payload);

        // 如果是会话无效，触发会话过期事件
        if (payload.error_code === 'SESSION_INVALID') {
            this.sessionId = null;
            // 触发会话过期回调（如果有注册）
            if (this.onSessionExpired) {
                this.onSessionExpired(payload);
            }
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
     * 发送请求并等待响应（优化版：增加超时保护）
     */
    _sendRequest(requestId, message, onChunk, onComplete, onVoiceChunk, onFunctionCall) {
        return new Promise((resolve, reject) => {
            console.log('[WebSocket] 发送请求:', requestId);
            
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
                voiceEnded: false,
                hasCheckedStreams: false,  // ✅ 标记是否已检查流类型
                hasTextStream: false,
                hasVoiceStream: false
            });

            this._send(message);

            // ✅ 超时处理（120秒）
            const timeoutId = setTimeout(() => {
                if (this.pendingRequests.has(requestId)) {
                    console.error('[WebSocket] 请求超时:', requestId);
                    this.pendingRequests.delete(requestId);
                    reject(new Error('请求超时'));
                }
            }, 120000);
            
            // 保存超时ID
            this.pendingRequests.get(requestId).timeoutId = timeoutId;
        });
    }

    /**
     * 等待响应（优化版：增加超时保护）
     */
    _waitForResponse(requestId, onChunk, onComplete, onVoiceChunk, onFunctionCall) {
        return new Promise((resolve, reject) => {
            console.log('[WebSocket] 注册请求处理器:', requestId);
            
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
                voiceEnded: false,
                hasCheckedStreams: false,  // ✅ 标记是否已检查流类型
                hasTextStream: false,
                hasVoiceStream: false
            });

            // ✅ 增加超时保护（120秒，足够长）
            const timeoutId = setTimeout(() => {
                if (this.pendingRequests.has(requestId)) {
                    console.error('[WebSocket] 请求超时:', requestId);
                    this.pendingRequests.delete(requestId);
                    reject(new Error('请求超时'));
                }
            }, 120000);  // 120秒超时
            
            // 保存超时ID，以便在请求完成时清除
            this.pendingRequests.get(requestId).timeoutId = timeoutId;
        });
    }

    /**
     * 启动心跳监控
     */
    _startHeartbeatMonitor() {
        this._stopHeartbeatMonitor();
        console.log('[WebSocket] 启动心跳监控，超时时间:', this.config.heartbeatTimeout / 1000, '秒');
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

        // ✅ 心跳超时或异常断开，不自动重连，而是触发会话过期
        if (event.code !== 1000) {
            console.error('[WebSocket] 连接异常关闭，code:', event.code, 'reason:', event.reason);
            
            // ✅ 清空会话ID
            this.sessionId = null;
            
            // ✅ 触发会话过期回调，让用户重新登录
            if (this.onSessionExpired) {
                this.onSessionExpired({
                    error_code: 'CONNECTION_LOST',
                    error_msg: '连接已断开，请重新登录',
                    error_detail: `code: ${event.code}, reason: ${event.reason}`,
                    retryable: false
                });
            }
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

