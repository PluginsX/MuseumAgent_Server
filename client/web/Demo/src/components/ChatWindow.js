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
     * 切换语音录制
     */
    async toggleVoiceRecording() {
        const isRecording = stateManager.getState('recording.isRecording');
        const vadEnabled = stateManager.getState('recording.vadEnabled');

        if (isRecording) {
            // 停止录音
            console.log('[ChatWindow] 停止录音');
            
            // 计算实际发出的语音时长（秒）
            const duration = this.audioChunks.length > 0 
                ? (this.audioChunks.reduce((sum, chunk) => sum + chunk.byteLength, 0) / 2) / 16000 
                : 0;

            console.log('[ChatWindow] 语音录制结束，数据块数量:', this.audioChunks.length, '时长:', duration.toFixed(2), '秒');
            
            // 更新发送的语音消息的时长
            if (this.currentVoiceMessageId) {
                stateManager.updateMessage(this.currentVoiceMessageId, {
                    duration: duration
                });
            }
            
            // 结束流式发送
            if (this.voiceStreamController) {
                this.voiceStreamController.close();
                this.voiceStreamController = null;
            }
            
            audioService.stopRecording();
            
            // 清空缓存
            this.audioChunks = [];
            this.currentVoiceMessageId = null;
        } else {
            // 开始录音
            try {
                console.log('[ChatWindow] 开始录音, VAD启用:', vadEnabled);
                this.audioChunks = [];
                
                // 创建实时流式传输的ReadableStream
                const stream = new ReadableStream({
                    start: (controller) => {
                        this.voiceStreamController = controller;
                        console.log('[ChatWindow] 流式传输已准备就绪');
                    }
                });

                // 立即开始发送语音请求（流式），并保存消息ID
                this.currentVoiceMessageId = await messageService.sendVoiceMessageStream(stream);

                // 开始录音，实时推送数据到流
                if (vadEnabled) {
                    // 启用VAD：实时采集音频，但由VAD控制何时发送
                    const vadParams = stateManager.getState('recording.vadParams') || {
                        silenceThreshold: 0.01,
                        silenceDuration: 1500,
                        speechThreshold: 0.05,
                        minSpeechDuration: 300,
                        preSpeechPadding: 300,
                        postSpeechPadding: 500
                    };

                    await audioService.startRecordingWithVAD(vadParams, (audioData) => {
                        // VAD决定发送时，实时推送到流
                        this.audioChunks.push(audioData);
                        if (this.voiceStreamController) {
                            this.voiceStreamController.enqueue(new Uint8Array(audioData));
                            console.log('[ChatWindow] 实时发送音频数据:', audioData.byteLength, '字节');
                        }
                    });
                } else {
                    // 不启用VAD：直接实时采集并发送
                    await audioService.startRecording((audioData) => {
                        this.audioChunks.push(audioData);
                        if (this.voiceStreamController) {
                            this.voiceStreamController.enqueue(new Uint8Array(audioData));
                            console.log('[ChatWindow] 实时发送音频数据:', audioData.byteLength, '字节');
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
        this.messageBubbles.forEach(bubble => bubble.destroy());
        this.messageBubbles.clear();
        this.container.innerHTML = '';
    }
}

