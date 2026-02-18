/**
 * 消息服务
 * 处理消息发送、接收、显示
 */

import { eventBus, Events } from '../core/EventBus.js';
import { stateManager } from '../core/StateManager.js';
import { WebSocketClient } from '../core/WebSocketClient.js';
import { audioService } from './AudioService.js';

export class MessageService {
    constructor() {
        this.wsClient = null;
        this.currentRequestId = null;  // ✅ 当前正在处理的请求ID（req_xxx）
        this.currentMessageId = null;  // ✅ 当前消息ID（msg_xxx）
        this.isReceivingResponse = false;  // 是否正在接收响应
        this.audioChunks = [];
    }

    /**
     * 发送打断信号
     */
    async interruptCurrentRequest(reason = 'USER_NEW_INPUT') {
        if (!this.currentRequestId || !this.isReceivingResponse) {
            console.log('[MessageService] 无活跃请求需要打断');
            return;
        }
        
        console.log('[MessageService] 发送打断信号 - 请求ID:', this.currentRequestId, '消息ID:', this.currentMessageId, '原因:', reason);
        
        try {
            // 1. 停止音频播放
            audioService.stopAllPlayback();
            
            // 2. 发送 INTERRUPT 消息（使用请求ID，不是消息ID）
            await this.wsClient.sendInterrupt(this.currentRequestId, reason);
            
            // 3. 清理客户端状态
            const oldRequestId = this.currentRequestId;
            const oldMessageId = this.currentMessageId;
            this.isReceivingResponse = false;
            this.currentRequestId = null;
            this.currentMessageId = null;
            
            // 4. 触发事件
            eventBus.emit(Events.REQUEST_INTERRUPTED, {
                requestId: oldRequestId,
                messageId: oldMessageId,
                reason: reason
            });
            
            console.log('[MessageService] 打断信号已发送');
            
        } catch (error) {
            console.error('[MessageService] 打断失败:', error);
        }
    }

    /**
     * 初始化（连接 WebSocket）
     */
    async init(serverUrl, authData) {
        try {
            // 创建 WebSocket 客户端
            this.wsClient = new WebSocketClient({
                baseUrl: serverUrl
            });

            // 注册会话过期回调
            this.wsClient.onSessionExpired = (payload) => {
                console.error('[MessageService] 会话已过期:', payload);
                stateManager.setState('connection.isConnected', false);
                stateManager.setState('auth.sessionId', null);
                eventBus.emit(Events.SESSION_EXPIRED);
            };

            // 连接
            await this.wsClient.connect();
            stateManager.setState('connection.isConnected', true);
            eventBus.emit(Events.CONNECTION_OPEN);

            // 注册会话
            const sessionConfig = stateManager.getState('session');
            const result = await this.wsClient.register(
                authData,
                sessionConfig.platform,
                sessionConfig.requireTTS,
                sessionConfig.enableSRS !== false ? sessionConfig.enableSRS : true,
                sessionConfig.functionCalling
            );

            stateManager.setState('auth.sessionId', result.session_id);
            eventBus.emit(Events.SESSION_REGISTERED, result);

            console.log('[MessageService] 初始化成功，会话ID:', result.session_id);

        } catch (error) {
            console.error('[MessageService] 初始化失败:', error);
            stateManager.setState('connection.isConnected', false);
            eventBus.emit(Events.CONNECTION_ERROR, error);
            throw error;
        }
    }

    /**
     * 发送文本消息
     */
    async sendTextMessage(text) {
        if (!this.wsClient || !this.wsClient.isConnected()) {
            throw new Error('未连接到服务器');
        }

        // ✅ 如果正在接收响应，先打断
        if (this.isReceivingResponse) {
            console.log('[MessageService] 检测到新输入，打断当前响应');
            await this.interruptCurrentRequest('USER_NEW_INPUT');
            // 等待一小段时间确保打断完成
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        // 添加发送的消息到状态
        const messageId = this._generateMessageId();
        stateManager.addMessage({
            id: messageId,
            type: 'sent',
            contentType: 'text',
            content: text,
            timestamp: Date.now()
        });

        eventBus.emit(Events.MESSAGE_SENT, { id: messageId, text });

        try {
            // 为每种类型的响应创建独立的消息气泡ID
            let textMessageId = null;
            let voiceMessageId = null;
            const voiceChunks = [];

            // 发送请求
            const sessionConfig = stateManager.getState('session');
            const options = {
                requireTTS: sessionConfig.requireTTS,
                
                // 文本流回调
                onChunk: (chunk) => {
                    // 第一次收到文本时创建文本气泡
                    if (!textMessageId) {
                        textMessageId = this._generateMessageId();
                        stateManager.addMessage({
                            id: textMessageId,
                            type: 'received',
                            contentType: 'text',
                            content: chunk,
                            timestamp: Date.now(),
                            isStreaming: true
                        });
                    } else {
                        // 更新文本气泡内容
                        const message = stateManager.getState('messages').find(m => m.id === textMessageId);
                        if (message) {
                            stateManager.updateMessage(textMessageId, {
                                content: message.content + chunk
                            });
                        }
                    }
                    eventBus.emit(Events.MESSAGE_TEXT_CHUNK, { id: textMessageId, chunk });
                },

                // 语音流回调（实时流式播放）
                onVoiceChunk: async (audioData, seq) => {
                    // 第一次收到语音时创建语音气泡
                    if (!voiceMessageId) {
                        voiceMessageId = this._generateMessageId();
                        stateManager.addMessage({
                            id: voiceMessageId,
                            type: 'received',
                            contentType: 'voice',
                            content: null,
                            audioData: null,
                            duration: 0,
                            timestamp: Date.now(),
                            isStreaming: true
                        });
                        
                        // 如果启用自动播放，开始流式播放
                        if (sessionConfig.autoPlay !== false) {
                            console.log('[MessageService] 开始流式播放:', voiceMessageId);
                            await audioService.startStreamingMessage(voiceMessageId);
                        }
                    }
                    
                    // 保存音频数据（用于后续手动播放）
                    voiceChunks.push(audioData);
                    
                    // 如果启用自动播放，实时播放音频块
                    if (sessionConfig.autoPlay !== false) {
                        await audioService.addStreamingChunk(voiceMessageId, audioData);
                    }
                    
                    eventBus.emit(Events.MESSAGE_VOICE_CHUNK, { id: voiceMessageId, audioData, seq });
                },

                // 函数调用回调
                onFunctionCall: (functionCall) => {
                    // 每个函数调用创建独立气泡
                    const funcMessageId = this._generateMessageId();
                    stateManager.addMessage({
                        id: funcMessageId,
                        type: 'received',
                        contentType: 'function',
                        content: functionCall,
                        timestamp: Date.now()
                    });
                    eventBus.emit(Events.FUNCTION_CALL, functionCall);
                },
                
                // 完成回调
                onComplete: async (data) => {
                    // ✅ 检查是否被中断
                    if (data.interrupted) {
                        console.log('[MessageService] 请求被中断:', textMessageId || voiceMessageId);
                        this.isReceivingResponse = false;
                        this.currentRequestId = null;
                        this.currentMessageId = null;
                        return;
                    }
                    
                    // 标记文本流结束
                    if (textMessageId) {
                        stateManager.updateMessage(textMessageId, {
                            isStreaming: false
                        });
                    }

                    // 处理语音数据
                    if (voiceMessageId && voiceChunks.length > 0) {
                        // 合并所有语音数据（用于保存和手动播放）
                        const totalLength = voiceChunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
                        const combined = new Uint8Array(totalLength);
                        let offset = 0;
                        for (const chunk of voiceChunks) {
                            combined.set(new Uint8Array(chunk), offset);
                            offset += chunk.byteLength;
                        }

                        // 计算语音时长（16kHz, 16bit, mono）
                        const duration = (combined.length / 2) / 16000;

                        // 更新语音气泡
                        stateManager.updateMessage(voiceMessageId, {
                            audioData: combined.buffer,
                            duration: duration,
                            isStreaming: false
                        });

                        // 如果启用自动播放，通知流式播放器结束
                        if (sessionConfig.autoPlay !== false) {
                            audioService.endStreamingMessage(voiceMessageId);
                        }
                    }

                    // ✅ 标记响应接收完成
                    this.isReceivingResponse = false;
                    this.currentRequestId = null;
                    this.currentMessageId = null;

                    eventBus.emit(Events.MESSAGE_COMPLETE, { textMessageId, voiceMessageId });
                }
            };

            // 检查是否需要更新 FunctionCalling
            if (sessionConfig.functionCallingModified) {
                options.functionCallingOp = 'REPLACE';
                options.functionCalling = sessionConfig.functionCalling;
                // 重置修改标记
                stateManager.setState('session.functionCallingModified', false);
            }

            // 检查是否需要更新 EnableSRS
            if (sessionConfig.enableSRSModified) {
                options.enableSRS = sessionConfig.enableSRS;
                // 重置修改标记
                stateManager.setState('session.enableSRSModified', false);
            }

            // ✅ 发送请求并获取实际的请求ID
            const { requestId, promise: sendPromise } = this.wsClient.sendTextRequest(text, options);
            
            // ✅ 标记开始接收响应（使用实际的请求ID）
            this.currentRequestId = requestId;
            this.currentMessageId = messageId;
            this.isReceivingResponse = true;
            
            console.log('[MessageService] 开始接收响应 - 请求ID:', requestId, '消息ID:', messageId);
            
            await sendPromise;

        } catch (error) {
            // ✅ 发生错误时清理状态
            this.isReceivingResponse = false;
            this.currentRequestId = null;
            this.currentMessageId = null;
            console.error('[MessageService] 发送消息失败:', error);
            eventBus.emit(Events.MESSAGE_ERROR, error);
            throw error;
        }
    }

    /**
     * 发送语音消息（流式）
     */
    async sendVoiceMessageStream(audioStream) {
        if (!this.wsClient || !this.wsClient.isConnected()) {
            throw new Error('未连接到服务器');
        }

        // ✅ 如果正在接收响应，先打断
        if (this.isReceivingResponse) {
            console.log('[MessageService] 检测到新语音输入，打断当前响应');
            await this.interruptCurrentRequest('USER_NEW_INPUT');
            // 等待一小段时间确保打断完成
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        try {
            // 为每种类型的响应创建独立的消息气泡ID
            let textMessageId = null;
            let voiceMessageId = null;
            const voiceChunks = [];

            // 添加发送的语音消息到状态（初始时长为0）
            const messageId = this._generateMessageId();
            stateManager.addMessage({
                id: messageId,
                type: 'sent',
                contentType: 'voice',
                content: null,
                duration: 0,
                timestamp: Date.now()
            });

            eventBus.emit(Events.MESSAGE_SENT, { id: messageId, type: 'voice' });

            // 发送语音请求（流式）
            const sessionConfig = stateManager.getState('session');
            
            const voiceOptions = {
                requireTTS: sessionConfig.requireTTS,
                
                // 文本流回调
                onChunk: (chunk) => {
                    if (!textMessageId) {
                        textMessageId = this._generateMessageId();
                        stateManager.addMessage({
                            id: textMessageId,
                            type: 'received',
                            contentType: 'text',
                            content: chunk,
                            timestamp: Date.now(),
                            isStreaming: true
                        });
                    } else {
                        const message = stateManager.getState('messages').find(m => m.id === textMessageId);
                        if (message) {
                            stateManager.updateMessage(textMessageId, {
                                content: message.content + chunk
                            });
                        }
                    }
                    eventBus.emit(Events.MESSAGE_TEXT_CHUNK, { id: textMessageId, chunk });
                },

                // 语音流回调（实时流式播放）
                onVoiceChunk: async (audioData, seq) => {
                    // 第一次收到语音时创建语音气泡
                    if (!voiceMessageId) {
                        voiceMessageId = this._generateMessageId();
                        stateManager.addMessage({
                            id: voiceMessageId,
                            type: 'received',
                            contentType: 'voice',
                            content: null,
                            audioData: null,
                            duration: 0,
                            timestamp: Date.now(),
                            isStreaming: true
                        });
                        
                        // 如果启用自动播放，开始流式播放
                        if (sessionConfig.autoPlay !== false) {
                            console.log('[MessageService] 开始流式播放:', voiceMessageId);
                            await audioService.startStreamingMessage(voiceMessageId);
                        }
                    }
                    
                    // 保存音频数据（用于后续手动播放）
                    voiceChunks.push(audioData);
                    
                    // 如果启用自动播放，实时播放音频块
                    if (sessionConfig.autoPlay !== false) {
                        await audioService.addStreamingChunk(voiceMessageId, audioData);
                    }
                    
                    eventBus.emit(Events.MESSAGE_VOICE_CHUNK, { id: voiceMessageId, audioData, seq });
                },

                // 函数调用回调
                onFunctionCall: (functionCall) => {
                    const funcMessageId = this._generateMessageId();
                    stateManager.addMessage({
                        id: funcMessageId,
                        type: 'received',
                        contentType: 'function',
                        content: functionCall,
                        timestamp: Date.now()
                    });
                    eventBus.emit(Events.FUNCTION_CALL, functionCall);
                },
                
                // 完成回调
                onComplete: async (data) => {
                    // ✅ 检查是否被中断
                    if (data.interrupted) {
                        console.log('[MessageService] 语音请求被中断:', textMessageId || voiceMessageId);
                        this.isReceivingResponse = false;
                        this.currentRequestId = null;
                        this.currentMessageId = null;
                        return;
                    }
                    
                    // 标记文本流结束
                    if (textMessageId) {
                        stateManager.updateMessage(textMessageId, {
                            isStreaming: false
                        });
                    }

                    // 处理语音数据
                    if (voiceMessageId && voiceChunks.length > 0) {
                        // 合并所有语音数据（用于保存和手动播放）
                        const totalLength = voiceChunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
                        const combined = new Uint8Array(totalLength);
                        let offset = 0;
                        for (const chunk of voiceChunks) {
                            combined.set(new Uint8Array(chunk), offset);
                            offset += chunk.byteLength;
                        }

                        const duration = (combined.length / 2) / 16000;

                        stateManager.updateMessage(voiceMessageId, {
                            audioData: combined.buffer,
                            duration: duration,
                            isStreaming: false
                        });

                        // 如果启用自动播放，通知流式播放器结束
                        if (sessionConfig.autoPlay !== false) {
                            audioService.endStreamingMessage(voiceMessageId);
                        }
                    }

                    // ✅ 标记响应接收完成
                    this.isReceivingResponse = false;
                    this.currentRequestId = null;
                    this.currentMessageId = null;

                    eventBus.emit(Events.MESSAGE_COMPLETE, { textMessageId, voiceMessageId });
                }
            };

            // 检查是否需要更新 FunctionCalling
            if (sessionConfig.functionCallingModified) {
                voiceOptions.functionCallingOp = 'REPLACE';
                voiceOptions.functionCalling = sessionConfig.functionCalling;
                // 重置修改标记
                stateManager.setState('session.functionCallingModified', false);
            }

            // 检查是否需要更新 EnableSRS
            if (sessionConfig.enableSRSModified) {
                voiceOptions.enableSRS = sessionConfig.enableSRS;
                // 重置修改标记
                stateManager.setState('session.enableSRSModified', false);
            }

            // ✅ 异步发送语音请求（不阻塞，立即返回 messageId）
            const { requestId, promise: sendPromise } = this.wsClient.sendVoiceRequestStream(audioStream, voiceOptions);
            
            // ✅ 标记开始接收响应（使用实际的请求ID）
            this.currentRequestId = requestId;
            this.currentMessageId = messageId;
            this.isReceivingResponse = true;
            
            console.log('[MessageService] 开始接收语音响应 - 请求ID:', requestId, '消息ID:', messageId);
            
            sendPromise.catch(error => {
                // ✅ 发生错误时清理状态
                this.isReceivingResponse = false;
                this.currentRequestId = null;
                this.currentMessageId = null;
                console.error('[MessageService] 语音请求失败:', error);
                eventBus.emit(Events.MESSAGE_ERROR, error);
            });

            // ✅ 立即返回消息ID，不等待流读取完成
            return messageId;

        } catch (error) {
            // ✅ 发生错误时清理状态
            this.isReceivingResponse = false;
            this.currentRequestId = null;
            this.currentMessageId = null;
            console.error('[MessageService] 发送语音消息失败:', error);
            eventBus.emit(Events.MESSAGE_ERROR, error);
            throw error;
        }
    }

    /**
     * 发送语音消息（旧方法，保留兼容性）
     */
    async sendVoiceMessage(audioStream, duration) {
        if (!this.wsClient || !this.wsClient.isConnected()) {
            throw new Error('未连接到服务器');
        }

        try {
            // 添加发送的语音消息到状态（显示实际发出的语音时长）
            const messageId = this._generateMessageId();
            stateManager.addMessage({
                id: messageId,
                type: 'sent',
                contentType: 'voice',
                content: null,
                duration: duration || 0,
                timestamp: Date.now()
            });

            eventBus.emit(Events.MESSAGE_SENT, { id: messageId, type: 'voice' });

            // 为每种类型的响应创建独立的消息气泡ID
            let textMessageId = null;
            let voiceMessageId = null;
            const voiceChunks = [];

            // 发送语音请求
            const sessionConfig = stateManager.getState('session');
            await this.wsClient.sendVoiceRequestStream(audioStream, {
                requireTTS: sessionConfig.requireTTS,
                
                // 文本流回调
                onChunk: (chunk) => {
                    // 第一次收到文本时创建文本气泡
                    if (!textMessageId) {
                        textMessageId = this._generateMessageId();
                        stateManager.addMessage({
                            id: textMessageId,
                            type: 'received',
                            contentType: 'text',
                            content: chunk,
                            timestamp: Date.now(),
                            isStreaming: true
                        });
                    } else {
                        // 更新文本气泡内容
                        const message = stateManager.getState('messages').find(m => m.id === textMessageId);
                        if (message) {
                            stateManager.updateMessage(textMessageId, {
                                content: message.content + chunk
                            });
                        }
                    }
                    eventBus.emit(Events.MESSAGE_TEXT_CHUNK, { id: textMessageId, chunk });
                },

                // 语音流回调
                onVoiceChunk: (audioData, seq) => {
                    // 第一次收到语音时创建语音气泡
                    if (!voiceMessageId) {
                        voiceMessageId = this._generateMessageId();
                        stateManager.addMessage({
                            id: voiceMessageId,
                            type: 'received',
                            contentType: 'voice',
                            content: null,
                            audioData: null,
                            duration: 0,
                            timestamp: Date.now(),
                            isStreaming: true
                        });
                    }
                    voiceChunks.push(audioData);
                    eventBus.emit(Events.MESSAGE_VOICE_CHUNK, { id: voiceMessageId, audioData, seq });
                },

                // 函数调用回调
                onFunctionCall: (functionCall) => {
                    // 每个函数调用创建独立气泡
                    const funcMessageId = this._generateMessageId();
                    stateManager.addMessage({
                        id: funcMessageId,
                        type: 'received',
                        contentType: 'function',
                        content: functionCall,
                        timestamp: Date.now()
                    });
                    eventBus.emit(Events.FUNCTION_CALL, functionCall);
                },
                
                // 完成回调
                onComplete: async (data) => {
                    // 标记文本流结束
                    if (textMessageId) {
                        stateManager.updateMessage(textMessageId, {
                            isStreaming: false
                        });
                    }

                    // 处理语音数据
                    if (voiceMessageId && voiceChunks.length > 0) {
                        // 合并所有语音数据
                        const totalLength = voiceChunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
                        const combined = new Uint8Array(totalLength);
                        let offset = 0;
                        for (const chunk of voiceChunks) {
                            combined.set(new Uint8Array(chunk), offset);
                            offset += chunk.byteLength;
                        }

                        // 计算语音时长（16kHz, 16bit, mono）
                        const duration = (combined.length / 2) / 16000;

                        // 更新语音气泡
                        stateManager.updateMessage(voiceMessageId, {
                            audioData: combined.buffer,
                            duration: duration,
                            isStreaming: false
                        });

                        // 自动播放（如果启用）
                        if (sessionConfig.autoPlay !== false) {
                            try {
                                // 停止当前正在播放的语音
                                if (audioService.currentPlayingMessageId) {
                                    audioService.stopPlayback();
                                }
                                
                                // 设置当前播放的消息ID
                                audioService.currentPlayingMessageId = voiceMessageId;
                                
                                await audioService.playPCM(combined.buffer);
                                
                                // 播放完成后清除ID
                                audioService.currentPlayingMessageId = null;
                            } catch (error) {
                                console.error('[MessageService] 音频播放失败:', error);
                                audioService.currentPlayingMessageId = null;
                            }
                        }
                    }

                    eventBus.emit(Events.MESSAGE_COMPLETE, { textMessageId, voiceMessageId });
                }
            });

        } catch (error) {
            console.error('[MessageService] 发送语音消息失败:', error);
            eventBus.emit(Events.MESSAGE_ERROR, error);
            throw error;
        }
    }

    /**
     * 断开连接
     */
    async disconnect() {
        if (this.wsClient) {
            await this.wsClient.disconnect();
            this.wsClient = null;
        }

        stateManager.setState('connection.isConnected', false);
        eventBus.emit(Events.CONNECTION_CLOSE);
    }

    /**
     * 生成消息 ID
     */
    _generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

// 创建全局单例
export const messageService = new MessageService();

