/**
 * 发送管理器
 * 负责所有发送操作，独立于接收流程
 */

export class SendManager {
    constructor(wsClient, sessionId, clientConfig, settingsPanel = null) {
        this.wsClient = wsClient;
        this.sessionId = sessionId;
        this.clientConfig = clientConfig;  // ✅ 保存客户端配置引用
        this.settingsPanel = settingsPanel;  // ✅ 保存设置面板引用
        
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
        // 如果没有设置面板引用，返回空对象（不更新任何配置）
        if (!this.settingsPanel) {
            return {};
        }
        
        // 获取需要更新的配置（差异更新）
        const updates = this.settingsPanel.getPendingUpdates();
        
        // 如果有更新，发送后自动关闭开关
        if (Object.keys(updates).length > 0) {
            console.log('[SendManager] 携带配置更新:', updates);
            
            // ✅ 发送成功后自动关闭所有更新开关
            setTimeout(() => {
                this.settingsPanel.clearUpdateSwitches();
            }, 100);
        }
        
        return updates;
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

