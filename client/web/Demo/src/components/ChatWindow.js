/**
 * 聊天窗口组件
 * 显示消息列表和输入框
 */

import { stateManager } from '../core/StateManager.js';
import { eventBus, Events } from '../core/EventBus.js';
import { messageService } from '../services/MessageService.js';
import { audioService } from '../services/AudioService.js';
import { MessageBubble } from './MessageBubble.js';
import { SettingsPanel } from './SettingsPanel.js';
import { createElement, $, scrollToBottom } from '../utils/dom.js';

export class ChatWindow {
    constructor(container) {
        this.container = container;
        this.messageContainer = null;
        this.inputArea = null;
        this.sendButton = null;
        this.voiceButton = null;
        this.messageBubbles = new Map();
        this.audioChunks = []; // 录音数据缓存（用于计算时长）
        this.voiceStreamController = null; // 流式传输控制器
        this.currentVoiceMessageId = null; // 当前语音消息ID
        
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        this.render();
        this.bindEvents();
        this.subscribeToState();
    }

    /**
     * 渲染
     */
    render() {
        console.log('[ChatWindow] 开始渲染');
        
        this.container.innerHTML = '';
        
        // 头部区域已在App.js中创建，这里不再创建

        // 消息容器
        this.messageContainer = createElement('div', {
            className: 'message-container'
        });
        console.log('[ChatWindow] 消息容器已创建:', this.messageContainer);

        // 输入区域
        const inputContainer = createElement('div', {
            className: 'input-container'
        });

        this.inputArea = createElement('textarea', {
            className: 'chat-input',
            placeholder: '输入消息...',
            rows: '1'
        });

        this.sendButton = createElement('button', {
            className: 'send-button',
            textContent: '发送'
        });

        this.voiceButton = createElement('button', {
            className: 'voice-button',
            textContent: '🎤'
        });

        inputContainer.appendChild(this.inputArea);
        inputContainer.appendChild(this.voiceButton);
        inputContainer.appendChild(this.sendButton);

        this.container.appendChild(this.messageContainer);
        this.container.appendChild(inputContainer);
        
        console.log('[ChatWindow] 渲染完成');
        console.log('[ChatWindow] container.children:', this.container.children);
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 设置按钮事件已在App.js中处理，这里不再处理

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
     * 订阅状态变化
     */
    subscribeToState() {
        // 监听消息变化
        stateManager.subscribe('messages', (messages) => {
            this.updateMessages(messages);
        });

        // 监听录音状态
        stateManager.subscribe('recording.isRecording', (isRecording) => {
            if (isRecording) {
                this.voiceButton.textContent = '⏹️';
                this.voiceButton.classList.add('recording');
            } else {
                this.voiceButton.textContent = '🎤';
                this.voiceButton.classList.remove('recording');
            }
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
            await messageService.sendTextMessage(text);
        } catch (error) {
            console.error('[ChatWindow] 发送消息失败:', error);
            eventBus.emit(Events.UI_SHOW_ERROR, '发送消息失败: ' + error.message);
        }
    }

    /**
     * 切换语音录制（话筒开关）
     */
    async toggleVoiceRecording() {
        const isRecording = stateManager.getState('recording.isRecording');
        const vadEnabled = stateManager.getState('recording.vadEnabled');

        if (isRecording) {
            // 用户手动关闭话筒
            console.log('[ChatWindow] 用户关闭话筒');
            
            // 如果有正在发送的语音消息，先结束它
            if (this.currentVoiceMessageId) {
                this.endCurrentVoiceMessage();
            }
            
            // 停止录音
            audioService.stopRecording();
            
            console.log('[ChatWindow] 话筒已关闭');
        } else {
            // 用户手动开启话筒
            try {
                console.log('[ChatWindow] 用户开启话筒, VAD启用:', vadEnabled);
                
                if (vadEnabled) {
                    // 启用VAD：话筒开启，等待VAD检测人声
                    const vadParams = stateManager.getState('recording.vadParams') || {
                        silenceThreshold: 0.01,
                        silenceDuration: 1500,
                        speechThreshold: 0.05,
                        minSpeechDuration: 300,
                        preSpeechPadding: 300,
                        postSpeechPadding: 500
                    };

                    await audioService.startRecordingWithVAD(
                        vadParams,
                        // onSpeechStart: VAD检测到人声，创建新的语音消息
                        async () => {
                            console.log('[ChatWindow] VAD检测到人声，立即打断当前AI语音并创建新的语音消息');
                            
                            // ✅ 如果有旧的语音消息还在发送，先结束它
                            if (this.currentVoiceMessageId) {
                                console.log('[ChatWindow] 检测到旧的语音消息未结束，先结束它:', this.currentVoiceMessageId);
                                this.endCurrentVoiceMessage();
                                // 等待一小段时间确保流完全关闭
                                await new Promise(resolve => setTimeout(resolve, 50));
                            }
                            
                            // ✅ 先打断当前正在播放的AI语音
                            await messageService.interruptCurrentRequest('USER_VOICE_INPUT');
                            
                            // 然后创建新的语音消息
                            await this.startNewVoiceMessage();
                        },
                        // onAudioData: 实时音频数据回调
                        (audioData) => {
                            // 只有在有活动消息时才发送数据
                            if (this.currentVoiceMessageId) {
                                this.audioChunks.push(audioData);
                                if (this.voiceStreamController) {
                                    this.voiceStreamController.enqueue(new Uint8Array(audioData));
                                    console.log('[ChatWindow] 实时发送音频数据:', audioData.byteLength, '字节');
                                }
                            }
                        },
                        // onSpeechEnd: VAD检测到静音，结束本次语音消息
                        () => {
                            console.log('[ChatWindow] VAD检测到静音，结束本次语音消息');
                            this.endCurrentVoiceMessage();
                            // 注意：不关闭话筒，继续监听下一次人声
                        }
                    );
                } else {
                    // 不启用VAD：话筒开启立即创建气泡
                    console.log('[ChatWindow] 话筒开启，立即打断当前AI语音并创建新的语音消息');
                    // ✅ 先打断当前正在播放的AI语音
                    await messageService.interruptCurrentRequest('USER_VOICE_INPUT');
                    
                    // ✅ 先创建新的语音消息和流
                    await this.startNewVoiceMessage();
                    
                    // ✅ 然后开始录音，实时推送数据到流
                    await audioService.startRecording((audioData) => {
                        this.audioChunks.push(audioData);
                        if (this.voiceStreamController) {
                            this.voiceStreamController.enqueue(new Uint8Array(audioData));
                            console.log('[ChatWindow] 实时发送音频数据:', audioData.byteLength, '字节');
                        } else {
                            console.warn('[ChatWindow] 流控制器未就绪');
                        }
                    });
                }

            } catch (error) {
                console.error('[ChatWindow] 录音失败:', error);
                eventBus.emit(Events.UI_SHOW_ERROR, '录音失败: ' + error.message);
            }
        }
    }

    /**
     * 开始新的语音消息（创建气泡和流）
     */
    async startNewVoiceMessage() {
        console.log('[ChatWindow] 创建新的语音消息气泡');
        
        // ✅ 清空音频缓存
        this.audioChunks = [];
        
        // ✅ 创建实时流式传输的ReadableStream
        const stream = new ReadableStream({
            start: (controller) => {
                this.voiceStreamController = controller;
                console.log('[ChatWindow] 流式传输已准备就绪，controller:', controller);
            },
            cancel: (reason) => {
                console.log('[ChatWindow] 流被取消，原因:', reason);
                this.voiceStreamController = null;
            }
        });

        // ✅ 创建语音消息气泡并开始发送
        try {
            this.currentVoiceMessageId = await messageService.sendVoiceMessageStream(stream);
            console.log('[ChatWindow] 语音消息已创建，ID:', this.currentVoiceMessageId);
        } catch (error) {
            console.error('[ChatWindow] 创建语音消息失败:', error);
            // 清理状态
            this.voiceStreamController = null;
            this.currentVoiceMessageId = null;
            this.audioChunks = [];
            throw error;
        }
    }

    /**
     * 结束当前语音消息（更新时长和音频数据）
     */
    endCurrentVoiceMessage() {
        if (!this.currentVoiceMessageId) {
            console.log('[ChatWindow] 没有活动的语音消息，跳过结束操作');
            return;
        }
        
        console.log('[ChatWindow] 结束语音消息:', this.currentVoiceMessageId);
        
        // 计算实际发出的语音时长（秒）
        const duration = this.audioChunks.length > 0 
            ? (this.audioChunks.reduce((sum, chunk) => sum + chunk.byteLength, 0) / 2) / 16000 
            : 0;

        console.log('[ChatWindow] 语音数据块数量:', this.audioChunks.length, '时长:', duration.toFixed(2), '秒');
        
        // 合并音频数据用于播放
        let combinedAudioData = null;
        if (this.audioChunks.length > 0) {
            const totalLength = this.audioChunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
            const combined = new Uint8Array(totalLength);
            let offset = 0;
            for (const chunk of this.audioChunks) {
                combined.set(new Uint8Array(chunk), offset);
                offset += chunk.byteLength;
            }
            combinedAudioData = combined.buffer;
        }
        
        // 更新发送的语音消息的时长和音频数据
        stateManager.updateMessage(this.currentVoiceMessageId, {
            duration: duration,
            audioData: combinedAudioData
        });
        
        // ✅ 结束流式发送
        if (this.voiceStreamController) {
            try {
                this.voiceStreamController.close();
                console.log('[ChatWindow] 流式传输已关闭');
            } catch (error) {
                console.warn('[ChatWindow] 关闭流式传输失败（可能已关闭）:', error.message);
            }
            this.voiceStreamController = null;
        }
        
        // ✅ 清空当前消息状态（但不清空 audioChunks，因为 VAD 可能还在缓存）
        this.currentVoiceMessageId = null;
        this.audioChunks = [];
        
        console.log('[ChatWindow] 语音消息已结束，准备接收下一次语音');
    }

    /**
     * 更新消息列表
     */
    updateMessages(messages) {
        // 移除已删除的消息
        for (const [id, bubble] of this.messageBubbles.entries()) {
            if (!messages.find(m => m.id === id)) {
                bubble.destroy();
                this.messageBubbles.delete(id);
            }
        }

        // 添加或更新消息
        for (const message of messages) {
            if (this.messageBubbles.has(message.id)) {
                // 更新现有消息
                this.messageBubbles.get(message.id).update(message);
            } else {
                // 创建新消息
                const bubble = new MessageBubble(message);
                this.messageContainer.appendChild(bubble.element);
                this.messageBubbles.set(message.id, bubble);
            }
        }

        // 滚动到底部
        scrollToBottom(this.messageContainer);
    }

    /**
     * 清空消息
     */
    clearMessages() {
        stateManager.clearMessages();
        this.messageBubbles.clear();
        this.messageContainer.innerHTML = '';
    }

    /**
     * 销毁
     */
    destroy() {
        console.log('[ChatWindow] 销毁组件，清理所有资源');
        
        // ✅ 停止录音
        if (stateManager.getState('recording.isRecording')) {
            console.log('[ChatWindow] 停止录音');
            audioService.stopRecording();
        }
        
        // ✅ 关闭当前语音消息流
        if (this.voiceStreamController) {
            try {
                this.voiceStreamController.close();
            } catch (error) {
                console.warn('[ChatWindow] 关闭流失败:', error.message);
            }
            this.voiceStreamController = null;
        }
        
        // ✅ 清空状态
        this.currentVoiceMessageId = null;
        this.audioChunks = [];
        
        // 清理消息气泡
        this.messageBubbles.forEach(bubble => bubble.destroy());
        this.messageBubbles.clear();
        this.container.innerHTML = '';
        
        console.log('[ChatWindow] 组件已销毁');
    }
}

