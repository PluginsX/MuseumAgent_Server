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

import { EventBus } from './core/EventBus.js';
import { WebSocketClient } from './core/WebSocketClient.js';
import { SendManager } from './core/SendManager.js';
import { ReceiveManager } from './core/ReceiveManager.js';
import { AudioManager } from './managers/AudioManager.js';
import { SessionManager } from './managers/SessionManager.js';
import { ConfigManager } from './managers/ConfigManager.js';
import { Events, DEFAULT_CONFIG } from './constants.js';
import { info, warn, error } from './utils/logger.js';

// ==================== 主客户端类 ====================
export class MuseumAgentClient {
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
            
            // 初始化发送管理器（传递配置引用）
            this.sendManager = new SendManager(this.wsClient, this.sessionId, this.config);
            
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
        info('[MuseumAgentClient] 配置已更新:', key, '=', value);
    }
    
    /**
     * ✅ 新增：批量更新配置
     * @param {Object} updates - 配置更新对象
     */
    updateConfigs(updates) {
        Object.assign(this.config, updates);
        this.configManager.updateMultiple(updates);
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
}

// 默认导出
export default MuseumAgentClient;

