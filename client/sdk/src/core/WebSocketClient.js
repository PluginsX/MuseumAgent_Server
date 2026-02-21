/**
 * WebSocket 客户端
 * 纯粹的连接管理，不包含业务逻辑
 */

export class WebSocketClient {
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

