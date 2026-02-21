/**
 * 接收管理器
 * 负责所有接收操作，独立于发送流程
 */

export class ReceiveManager {
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

