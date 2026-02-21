/**
 * 聊天窗口组件
 * 基于 MuseumAgentSDK 客户端库开发
 */

// 从全局变量获取 SDK
const { Events } = window.MuseumAgentSDK;

import { MessageBubble } from './MessageBubble.js';
import { createElement, scrollToBottom } from '../utils/dom.js';

export class ChatWindow {
    constructor(container, client) {
        this.container = container;
        this.client = client;
        this.messageContainer = null;
        this.inputArea = null;
        this.sendButton = null;
        this.voiceButton = null;
        this.messageBubbles = new Map();
        
        // ✅ 使用全局消息历史（所有 ChatWindow 实例共享）
        if (!window._messageHistory) {
            window._messageHistory = [];
        }
        this.messages = window._messageHistory;
        
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        this.render();
        this.bindEvents();
        this.subscribeToClientEvents();
        
        // ✅ 初始化时同步录音状态
        this.syncRecordingState();
        
        // ✅ 加载历史消息
        this.loadHistoryMessages();
    }
    
    /**
     * ✅ 加载历史消息
     */
    loadHistoryMessages() {
        console.log('[ChatWindow] 加载历史消息:', this.messages.length + ' 条');
        
        // 渲染所有历史消息
        this.messages.forEach(message => {
            const bubble = new MessageBubble(message);
            this.messageContainer.appendChild(bubble.element);
            this.messageBubbles.set(message.id, bubble);
        });
        
        // 滚动到底部
        scrollToBottom(this.messageContainer);
    }
    
    /**
     * ✅ 同步录音状态（从客户端获取当前状态）
     */
    syncRecordingState() {
        if (this.client.isRecording) {
            this.voiceButton.textContent = '⏹️';
            this.voiceButton.classList.add('recording');
        } else {
            this.voiceButton.textContent = '🎤';
            this.voiceButton.classList.remove('recording');
        }
    }

    /**
     * 渲染
     */
    render() {
        this.container.innerHTML = '';
        
        // 消息容器
        this.messageContainer = createElement('div', {
            className: 'message-container'
        });

        // 输入区域
        const inputContainer = createElement('div', {
            className: 'input-container'
        });

        this.inputArea = createElement('textarea', {
            className: 'chat-input',
            placeholder: '输入消息...',
            rows: '1'
        });

        this.voiceButton = createElement('button', {
            className: 'voice-button',
            textContent: '🎤'
        });

        this.sendButton = createElement('button', {
            className: 'send-button',
            textContent: '发送'
        });

        inputContainer.appendChild(this.inputArea);
        inputContainer.appendChild(this.voiceButton);
        inputContainer.appendChild(this.sendButton);

        this.container.appendChild(this.messageContainer);
        this.container.appendChild(inputContainer);
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 发送按钮
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // 回车发送
        this.inputArea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 自动调整输入框高度
        this.inputArea.addEventListener('input', () => {
            this.inputArea.style.height = 'auto';
            this.inputArea.style.height = Math.min(this.inputArea.scrollHeight, 120) + 'px';
        });

        // 语音按钮
        this.voiceButton.addEventListener('click', () => {
            this.toggleVoiceRecording();
        });
    }

    /**
     * 订阅客户端事件（仅用于 UI 更新）
     * ✅ 使用实例级别的事件监听器，避免重复监听
     */
    subscribeToClientEvents() {
        // ✅ 全局监听器已在 UnityContainer 中设置，这里只处理 UI 更新
        // ✅ 保存事件处理器引用，用于销毁时移除
        this.eventHandlers = {};
        
        // 语音数据缓存（用于播放）
        const voiceDataCache = new Map(); // {messageId: ArrayBuffer[]}

        // ✅ 监听录音完成（带音频数据）- 用于更新 UI 中的气泡
        this.eventHandlers.RECORDING_COMPLETE = (data) => {
            console.log('[ChatWindow] 录音完成:', {
                id: data.id,
                duration: data.duration.toFixed(2) + 's',
                audioDataSize: data.audioData ? data.audioData.byteLength : 0
            });
            
            // 更新语音消息的最终时长和音频数据
            const message = this.messages.find(m => m.id === data.id);
            if (message) {
                message.duration = data.duration;
                this.updateMessage(message.id, message);
                
                // 设置音频数据到气泡
                const bubble = this.messageBubbles.get(message.id);
                if (bubble && data.audioData) {
                    bubble.setAudioData(data.audioData);
                    console.log('[ChatWindow] 已设置音频数据到气泡');
                }
            }
        };
        this.client.on(Events.RECORDING_COMPLETE, this.eventHandlers.RECORDING_COMPLETE);

        // ✅ 监听文本流 - 用于实时更新 UI
        this.eventHandlers.TEXT_CHUNK = (data) => {
            // 检查消息是否已在历史中
            let message = this.messages.find(m => m.id === data.messageId);
            
            if (!message) {
                // 消息不存在（不应该发生，因为全局监听器应该已创建）
                console.warn('[ChatWindow] 收到未知消息的文本块:', data.messageId);
                return;
            }
            
            // 更新消息内容
            message.content += data.chunk;
            this.updateMessage(message.id, message);
        };
        this.client.on(Events.TEXT_CHUNK, this.eventHandlers.TEXT_CHUNK);

        // ✅ 监听语音流 - 用于缓存音频数据
        this.eventHandlers.VOICE_CHUNK = (data) => {
            const voiceMessageId = `${data.messageId}_voice`;
            
            // 缓存语音数据块
            if (data.audioData) {
                const chunks = voiceDataCache.get(voiceMessageId) || [];
                chunks.push(data.audioData);
                voiceDataCache.set(voiceMessageId, chunks);
            }
        };
        this.client.on(Events.VOICE_CHUNK, this.eventHandlers.VOICE_CHUNK);

        // ✅ 监听消息完成 - 用于合并语音数据
        this.eventHandlers.MESSAGE_COMPLETE = (data) => {
            // 完成文本消息
            const textMessage = this.messages.find(m => m.id === data.messageId && m.contentType === 'text');
            if (textMessage) {
                textMessage.isStreaming = false;
                this.updateMessage(textMessage.id, textMessage);
            }
            
            // 完成语音消息
            const voiceMessageId = `${data.messageId}_voice`;
            const voiceMessage = this.messages.find(m => m.id === voiceMessageId);
            
            if (voiceMessage) {
                voiceMessage.isStreaming = false;
                
                // 合并语音数据并设置到气泡
                const chunks = voiceDataCache.get(voiceMessageId) || [];
                if (chunks.length > 0) {
                    // 计算总大小
                    const totalSize = chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
                    
                    // 合并所有音频块
                    const mergedAudio = new Uint8Array(totalSize);
                    let offset = 0;
                    for (const chunk of chunks) {
                        mergedAudio.set(new Uint8Array(chunk), offset);
                        offset += chunk.byteLength;
                    }
                    
                    // 估算时长（假设 PCM 16kHz 16bit 单声道）
                    const duration = totalSize / (16000 * 2);
                    voiceMessage.duration = duration;
                    
                    // 更新消息
                    this.updateMessage(voiceMessage.id, voiceMessage);
                    
                    // 设置音频数据到气泡
                    const bubble = this.messageBubbles.get(voiceMessage.id);
                    if (bubble) {
                        bubble.setAudioData(mergedAudio.buffer);
                    }
                    
                    // 清理缓存
                    voiceDataCache.delete(voiceMessageId);
                }
            }
        };
        this.client.on(Events.MESSAGE_COMPLETE, this.eventHandlers.MESSAGE_COMPLETE);

        // ✅ 监听录音状态 - 用于更新按钮 UI
        this.eventHandlers.RECORDING_START = () => {
            this.voiceButton.textContent = '⏹️';
            this.voiceButton.classList.add('recording');
        };
        this.client.on(Events.RECORDING_START, this.eventHandlers.RECORDING_START);

        this.eventHandlers.RECORDING_STOP = () => {
            this.voiceButton.textContent = '🎤';
            this.voiceButton.classList.remove('recording');
        };
        this.client.on(Events.RECORDING_STOP, this.eventHandlers.RECORDING_STOP);

        // ✅ 监听语音检测（VAD）
        this.eventHandlers.SPEECH_START = () => {
            console.log('[ChatWindow] 检测到语音开始');
        };
        this.client.on(Events.SPEECH_START, this.eventHandlers.SPEECH_START);

        this.eventHandlers.SPEECH_END = () => {
            console.log('[ChatWindow] 检测到语音结束');
        };
        this.client.on(Events.SPEECH_END, this.eventHandlers.SPEECH_END);
    }

    /**
     * 发送消息
     */
    async sendMessage() {
        const text = this.inputArea.value.trim();
        if (!text) return;

        // 清空输入框
        this.inputArea.value = '';
        this.inputArea.style.height = 'auto';

        try {
            // ✅ 获取设置面板的待更新配置
            const settingsPanel = this.getSettingsPanel();
            const updates = settingsPanel ? settingsPanel.getPendingUpdates() : {};
            
            // ✅ 传递当前配置参数 + 待更新配置
            await this.client.sendText(text, {
                requireTTS: this.client.config.requireTTS,
                enableSRS: this.client.config.enableSRS,
                functionCalling: this.client.config.functionCalling.length > 0 ? this.client.config.functionCalling : undefined,
                ...updates
            });
            
            // ✅ 发送成功后清除更新开关
            if (settingsPanel && Object.keys(updates).length > 0) {
                settingsPanel.clearUpdateSwitches();
                console.log('[ChatWindow] 已发送配置更新:', updates);
            }
        } catch (error) {
            console.error('[ChatWindow] 发送消息失败:', error);
        }
    }

    /**
     * 切换语音录制
     */
    async toggleVoiceRecording() {
        try {
            if (this.client.isRecording) {
                await this.client.stopRecording();
            } else {
                // ✅ 获取设置面板的待更新配置
                const settingsPanel = this.getSettingsPanel();
                const updates = settingsPanel ? settingsPanel.getPendingUpdates() : {};
                
                // ✅ 传递当前配置参数 + 待更新配置
                await this.client.startRecording({
                    vadEnabled: this.client.vadEnabled,
                    vadParams: this.client.config.vadParams,
                    requireTTS: this.client.config.requireTTS,
                    enableSRS: this.client.config.enableSRS,
                    functionCalling: this.client.config.functionCalling.length > 0 ? this.client.config.functionCalling : undefined,
                    ...updates
                });
                
                // ✅ 发送成功后清除更新开关
                if (settingsPanel && Object.keys(updates).length > 0) {
                    settingsPanel.clearUpdateSwitches();
                    console.log('[ChatWindow] 已发送配置更新:', updates);
                }
            }
        } catch (error) {
            console.error('[ChatWindow] 录音失败:', error);
            // ✅ 不要弹出 alert，只在控制台输出错误
            console.error('[ChatWindow] 录音错误详情:', error.message);
        }
    }
    
    /**
     * 获取设置面板实例（从 UnityContainer 中获取）
     */
    getSettingsPanel() {
        // 通过 DOM 查找设置面板实例
        // 这里需要从父容器（UnityContainer）获取
        if (window._currentSettingsPanel) {
            return window._currentSettingsPanel;
        }
        return null;
    }

    /**
     * 添加消息
     */
    addMessage(message) {
        this.messages.push(message);
        
        const bubble = new MessageBubble(message);
        this.messageContainer.appendChild(bubble.element);
        this.messageBubbles.set(message.id, bubble);
        
        scrollToBottom(this.messageContainer);
        
        return bubble; // 返回气泡实例
    }

    /**
     * 更新消息
     */
    updateMessage(messageId, message) {
        const bubble = this.messageBubbles.get(messageId);
        if (bubble) {
            bubble.update(message);
        }
        
        const index = this.messages.findIndex(m => m.id === messageId);
        if (index !== -1) {
            this.messages[index] = message;
        }
        
        scrollToBottom(this.messageContainer);
    }

    /**
     * 清空消息
     */
    clearMessages() {
        this.messages = [];
        this.messageBubbles.clear();
        this.messageContainer.innerHTML = '';
    }

    /**
     * 销毁
     */
    destroy() {
        console.log('[ChatWindow] 销毁组件');
        
        // ✅ 移除事件监听器
        if (this.eventHandlers) {
            for (const eventName in this.eventHandlers) {
                this.client.off(Events[eventName], this.eventHandlers[eventName]);
                console.log('[ChatWindow] 移除事件监听器:', eventName);
            }
            this.eventHandlers = null;
        }
        
        // ✅ 不要停止录音！录音状态应该保持，让用户可以继续使用控制按钮
        // 只清理 UI 相关的资源
        
        // 清理消息气泡
        this.messageBubbles.forEach(bubble => bubble.destroy());
        this.messageBubbles.clear();
        this.container.innerHTML = '';
        
        console.log('[ChatWindow] 组件已销毁');
    }
}
