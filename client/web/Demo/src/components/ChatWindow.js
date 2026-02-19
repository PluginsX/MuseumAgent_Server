/**
 * 聊天窗口组件
 * 基于 MuseumAgentSDK 客户端库开发
 */

import { Events } from '../../lib/MuseumAgentSDK.js';
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
        this.messages = [];
        
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        this.render();
        this.bindEvents();
        this.subscribeToClientEvents();
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
     * 订阅客户端事件
     */
    subscribeToClientEvents() {
        // 当前消息追踪（用于区分不同的消息）
        let currentTextMessage = null;
        let currentVoiceMessage = null;
        let currentFunctionMessage = null;
        let currentSentVoiceMessage = null; // 追踪发送中的语音消息
        let voiceTimerInterval = null; // 时长更新定时器
        
        // 语音数据缓存（用于播放）
        let voiceDataCache = new Map(); // {messageId: ArrayBuffer}

        // 监听消息发送
        this.client.on(Events.MESSAGE_SENT, (data) => {
            if (data.type === 'voice') {
                // 创建语音消息气泡（初始时长为 0）
                const message = {
                    id: data.id,
                    type: 'sent',
                    contentType: 'voice',
                    content: '',
                    timestamp: Date.now(),
                    duration: 0,
                    startTime: data.startTime
                };
                
                currentSentVoiceMessage = message;
                this.addMessage(message);
                
                // 启动定时器，每100ms更新一次时长
                if (voiceTimerInterval) {
                    clearInterval(voiceTimerInterval);
                }
                voiceTimerInterval = setInterval(() => {
                    if (currentSentVoiceMessage && currentSentVoiceMessage.startTime) {
                        const elapsed = (Date.now() - currentSentVoiceMessage.startTime) / 1000;
                        currentSentVoiceMessage.duration = elapsed;
                        this.updateMessage(currentSentVoiceMessage.id, currentSentVoiceMessage);
                        
                        // 调试日志（每秒输出一次）
                        if (Math.floor(elapsed * 10) % 10 === 0) {
                            console.log('[ChatWindow] 更新语音时长:', {
                                id: currentSentVoiceMessage.id,
                                duration: elapsed.toFixed(2) + 's'
                            });
                        }
                    }
                }, 100);
            } else {
                // 文本消息
                const message = {
                    id: data.id,
                    type: 'sent',
                    contentType: 'text',
                    content: data.content || '',
                    timestamp: Date.now()
                };
                this.addMessage(message);
            }
        });
        
        // 监听录音完成（带音频数据）
        this.client.on(Events.RECORDING_COMPLETE, (data) => {
            console.log('[ChatWindow] 录音完成:', {
                id: data.id,
                duration: data.duration.toFixed(2) + 's',
                audioDataSize: data.audioData ? data.audioData.byteLength : 0
            });
            
            // 停止时长更新定时器
            if (voiceTimerInterval) {
                clearInterval(voiceTimerInterval);
                voiceTimerInterval = null;
            }
            
            // 更新语音消息的最终时长和音频数据
            if (currentSentVoiceMessage && currentSentVoiceMessage.id === data.id) {
                currentSentVoiceMessage.duration = data.duration;
                this.updateMessage(currentSentVoiceMessage.id, currentSentVoiceMessage);
                
                // 设置音频数据到气泡
                const bubble = this.messageBubbles.get(currentSentVoiceMessage.id);
                if (bubble && data.audioData) {
                    bubble.setAudioData(data.audioData);
                    console.log('[ChatWindow] 已设置音频数据到气泡');
                }
                
                currentSentVoiceMessage = null;
            } else {
                console.warn('[ChatWindow] 录音完成但找不到对应的语音消息:', {
                    dataId: data.id,
                    currentId: currentSentVoiceMessage ? currentSentVoiceMessage.id : 'null'
                });
            }
        });

        // 监听文本流
        this.client.on(Events.TEXT_CHUNK, (data) => {
            // 检查是否是新消息（messageId 变化表示新消息开始）
            if (!currentTextMessage || currentTextMessage.id !== data.messageId) {
                // 如果有旧的文本消息，先标记为完成
                if (currentTextMessage) {
                    currentTextMessage.isStreaming = false;
                    this.updateMessage(currentTextMessage.id, currentTextMessage);
                }
                
                // 创建新的文本消息气泡
                currentTextMessage = {
                    id: data.messageId,
                    type: 'received',
                    contentType: 'text',
                    content: data.chunk,
                    timestamp: Date.now(),
                    isStreaming: true
                };
                this.addMessage(currentTextMessage);
            } else {
                // 累加到当前消息
                currentTextMessage.content += data.chunk;
                this.updateMessage(currentTextMessage.id, currentTextMessage);
            }
        });

        // 监听语音流
        this.client.on(Events.VOICE_CHUNK, (data) => {
            // 为语音消息创建独立的 ID（与文本消息分开）
            const voiceMessageId = `${data.messageId}_voice`;
            
            // 检查是否是新消息
            if (!currentVoiceMessage || currentVoiceMessage.id !== voiceMessageId) {
                // 如果有旧的语音消息，先标记为完成
                if (currentVoiceMessage) {
                    currentVoiceMessage.isStreaming = false;
                    this.updateMessage(currentVoiceMessage.id, currentVoiceMessage);
                }
                
                // 创建新的语音消息气泡（无论是否有文本消息，都要创建）
                currentVoiceMessage = {
                    id: voiceMessageId,
                    type: 'received',
                    contentType: 'voice',
                    content: '语音消息',
                    timestamp: Date.now(),
                    isStreaming: true,
                    duration: 0
                };
                this.addMessage(currentVoiceMessage);
                
                // 初始化语音数据缓存
                voiceDataCache.set(voiceMessageId, []);
            }
            
            // 缓存语音数据块
            if (data.audioData) {
                const chunks = voiceDataCache.get(voiceMessageId) || [];
                chunks.push(data.audioData);
                voiceDataCache.set(voiceMessageId, chunks);
            }
        });

        // 监听函数调用
        this.client.on(Events.FUNCTION_CALL, (functionCall) => {
            console.log('[ChatWindow] 收到函数调用:', functionCall);
            console.log('[ChatWindow] 函数调用类型:', typeof functionCall);
            console.log('[ChatWindow] 函数调用 keys:', Object.keys(functionCall));
            console.log('[ChatWindow] 函数调用完整结构:', JSON.stringify(functionCall, null, 2));
            
            // 函数调用总是创建新的独立气泡
            const message = {
                id: `func_${Date.now()}_${Math.random()}`,
                type: 'received',
                contentType: 'function',
                content: functionCall,
                timestamp: Date.now()
            };
            this.addMessage(message);
        });

        // 监听消息完成
        this.client.on(Events.MESSAGE_COMPLETE, (data) => {
            // 完成文本消息
            if (currentTextMessage && currentTextMessage.id === data.messageId) {
                currentTextMessage.isStreaming = false;
                this.updateMessage(currentTextMessage.id, currentTextMessage);
                currentTextMessage = null;
            }
            
            // 完成语音消息
            if (currentVoiceMessage) {
                const voiceMessageId = currentVoiceMessage.id;
                currentVoiceMessage.isStreaming = false;
                
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
                    const duration = totalSize / (16000 * 2); // 字节数 / (采样率 * 字节/采样)
                    currentVoiceMessage.duration = duration;
                    
                    // 更新消息
                    this.updateMessage(currentVoiceMessage.id, currentVoiceMessage);
                    
                    // 设置音频数据到气泡
                    const bubble = this.messageBubbles.get(currentVoiceMessage.id);
                    if (bubble) {
                        bubble.setAudioData(mergedAudio.buffer);
                    }
                    
                    // 清理缓存
                    voiceDataCache.delete(voiceMessageId);
                }
                
                currentVoiceMessage = null;
            }
        });

        // 监听打断事件 - 清理当前消息状态
        this.client.on(Events.INTERRUPTED, (data) => {
            console.log('[ChatWindow] 请求被打断:', data.reason);
            
            // 打断时，标记当前消息为完成，下一条消息会创建新气泡
            if (currentTextMessage) {
                currentTextMessage.isStreaming = false;
                this.updateMessage(currentTextMessage.id, currentTextMessage);
                currentTextMessage = null;
            }
            
            // ✅ 打断时，保存已接收的语音数据
            if (currentVoiceMessage) {
                const voiceMessageId = currentVoiceMessage.id;
                currentVoiceMessage.isStreaming = false;
                
                // 合并已接收的语音数据并设置到气泡（即使被打断也要缓存）
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
                    currentVoiceMessage.duration = duration;
                    
                    // 更新消息
                    this.updateMessage(currentVoiceMessage.id, currentVoiceMessage);
                    
                    // 设置音频数据到气泡
                    const bubble = this.messageBubbles.get(currentVoiceMessage.id);
                    if (bubble) {
                        bubble.setAudioData(mergedAudio.buffer);
                    }
                    
                    console.log('[ChatWindow] 打断时已缓存语音数据:', {
                        messageId: voiceMessageId,
                        duration: duration.toFixed(2) + 's',
                        size: totalSize + ' bytes'
                    });
                }
                
                // 清理缓存
                voiceDataCache.delete(voiceMessageId);
                currentVoiceMessage = null;
            }
            
            // ✅ 停止发送语音消息的时长更新定时器
            if (voiceTimerInterval) {
                clearInterval(voiceTimerInterval);
                voiceTimerInterval = null;
            }
            
            // ✅ 如果发送的语音消息被打断，也要保存音频数据
            if (currentSentVoiceMessage) {
                // 注意：发送的语音消息的音频数据会在 RECORDING_COMPLETE 事件中处理
                // 这里只需要停止定时器即可
                currentSentVoiceMessage = null;
            }
        });

        // 监听录音状态
        this.client.on(Events.RECORDING_START, () => {
            this.voiceButton.textContent = '⏹️';
            this.voiceButton.classList.add('recording');
        });

        this.client.on(Events.RECORDING_STOP, () => {
            this.voiceButton.textContent = '🎤';
            this.voiceButton.classList.remove('recording');
        });

        // 监听语音检测（VAD）
        this.client.on(Events.SPEECH_START, () => {
            console.log('[ChatWindow] 检测到语音开始');
        });

        this.client.on(Events.SPEECH_END, () => {
            console.log('[ChatWindow] 检测到语音结束');
        });
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
            await this.client.sendText(text);
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
                await this.client.startRecording();
            }
        } catch (error) {
            console.error('[ChatWindow] 录音失败:', error);
            alert('录音失败: ' + error.message);
        }
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
        
        // 停止录音
        if (this.client && this.client.isRecording) {
            this.client.stopRecording();
        }
        
        // 清理消息气泡
        this.messageBubbles.forEach(bubble => bubble.destroy());
        this.messageBubbles.clear();
        this.container.innerHTML = '';
        
        console.log('[ChatWindow] 组件已销毁');
    }
}
