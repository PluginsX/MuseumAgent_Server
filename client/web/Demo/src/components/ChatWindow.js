/**
 * 聊天窗口组件
 * ✅ 重构版本：单例、单源数据、完整事件处理
 * 基于 MuseumAgentSDK 客户端库开发
 */

// 从全局变量获取 SDK
const { Events } = window.MuseumAgentSDK;

import { MessageBubble } from './MessageBubble.js';
import { createElement, scrollToBottom } from '../utils/dom.js';

export class ChatWindow {
    constructor(container, client, agentController) {
        this.container = container;
        this.client = client;
        this.agentController = agentController;  // ✅ 引用 AgentController
        
        this.messageContainer = null;
        this.inputArea = null;
        this.sendButton = null;
        this.voiceButton = null;
        this.messageBubbles = new Map();
        
        // ✅ 语音数据缓存（用于播放）
        this.voiceDataCache = new Map();
        this.voiceTimerInterval = null;
        this.currentSentVoiceMessage = null;
        
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        this.render();
        this.bindClientEvents();  // ✅ 只订阅一次客户端事件
        this.subscribeToAgentController();
        this.loadExistingMessages();
    }

    /**
     * 渲染
     */
    render() {
        console.log('[ChatWindow] 渲染界面，container:', this.container);
        this.container.innerHTML = '';
        
        // ✅ 清空 DOM 时，也要清空 messageBubbles Map
        this.messageBubbles.clear();
        console.log('[ChatWindow] 已清空 messageBubbles Map');
        
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
        
        // ✅ 渲染后立即绑定 UI 事件
        this.bindUIEvents();
        
        console.log('[ChatWindow] 界面渲染完成，按钮已绑定事件');
    }

    /**
     * ✅ 绑定 UI 事件（每次 render 后调用）
     */
    bindUIEvents() {
        console.log('[ChatWindow] 绑定 UI 事件');
        
        // 发送按钮
        this.sendButton.addEventListener('click', () => {
            console.log('[ChatWindow] 发送按钮被点击');
            this.sendMessage();
        });

        // 回车发送（在冒泡阶段处理，优先级低于全局保护）
        this.inputArea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();  // 阻止默认换行行为
                this.sendMessage();
            }
            // Shift+Enter 允许换行（默认行为）
        });

        // 自动调整输入框高度
        this.inputArea.addEventListener('input', () => {
            this.inputArea.style.height = 'auto';
            this.inputArea.style.height = Math.min(this.inputArea.scrollHeight, 120) + 'px';
        });

        // 语音按钮
        this.voiceButton.addEventListener('click', () => {
            console.log('[ChatWindow] 语音按钮被点击，当前录音状态:', this.client.isRecording);
            this.toggleVoiceRecording();
        });
    }

    /**
     * ✅ 绑定客户端事件（只调用一次）
     */
    bindClientEvents() {
        if (this._clientEventsBound) {
            return;  // 避免重复订阅
        }
        this._clientEventsBound = true;
        
        console.log('[ChatWindow] 订阅客户端录音事件');
        
        // 监听录音状态
        this.client.on(Events.RECORDING_START, () => {
            console.log('[ChatWindow] 录音开始，更新按钮状态');
            if (this.voiceButton) {
                this.voiceButton.textContent = '⏹️';
                this.voiceButton.classList.add('recording');
            }
        });
        
        this.client.on(Events.RECORDING_STOP, () => {
            console.log('[ChatWindow] 录音停止，更新按钮状态');
            if (this.voiceButton) {
                this.voiceButton.textContent = '🎤';
                this.voiceButton.classList.remove('recording');
            }
        });
    }

    /**
     * ✅ 订阅 AgentController 事件
     */
    subscribeToAgentController() {
        // 新消息添加
        this.agentController.addEventListener('messageAdded', (e) => {
            const message = e.detail.message;
            this.createMessageBubble(message);
        });

        // 消息更新
        this.agentController.addEventListener('messageUpdated', (e) => {
            const message = e.detail.message;
            this.updateMessageBubble(message);
        });
        
        // 消息完成
        this.agentController.addEventListener('messageCompleted', (e) => {
            const message = e.detail.message;
            this.updateMessageBubble(message);
        });

        // 消息清空
        this.agentController.addEventListener('messagesCleared', () => {
            this.clearMessages();
        });
    }

    /**
     * ✅ 加载已有消息
     */
    loadExistingMessages() {
        const messages = this.agentController.getMessages();
        messages.forEach(message => {
            this.createMessageBubble(message);
        });
                }
                
    /**
     * ✅ 创建消息气泡
     */
    createMessageBubble(message) {
        // 使用消息的 ID
        const bubbleId = message.id || `msg_${Date.now()}_${Math.random()}`;
        
        // 检查是否已存在
        if (this.messageBubbles.has(bubbleId)) {
            return;
            }
        
        // ✅ 调试日志：检查消息类型
        console.log('[ChatWindow] 创建消息气泡:', {
            id: bubbleId,
            type: message.type,
            messageType: message.messageType,
            content: typeof message.content === 'string' ? message.content.substring(0, 50) : message.content
        });
            
        // 转换为 MessageBubble 格式
        const bubbleData = {
            id: bubbleId,
            type: message.type,  // 'sent' 或 'received'
            contentType: message.messageType,  // 'text', 'voice', 'function'
            content: message.content || '',
            timestamp: message.timestamp,
            isStreaming: message.isStreaming || message.isStreamingVoice || false,
            duration: message.duration || 0
        };
        
        const bubble = new MessageBubble(bubbleData);
        this.messageContainer.appendChild(bubble.element);
        this.messageBubbles.set(bubbleId, bubble);
                    
        // 如果有音频数据，设置到气泡
        if (message.audioData) {
            bubble.setAudioData(message.audioData);
                }
                
        scrollToBottom(this.messageContainer);
    }

    /**
     * ✅ 更新消息气泡（使用消息 ID 直接查找）
     */
    updateMessageBubble(message) {
        const bubbleId = message.id;
        
        if (!bubbleId) {
            console.warn('[ChatWindow] 消息没有 ID，无法更新气泡');
            return;
                    }
                    
        // 直接通过 ID 查找气泡
        const bubble = this.messageBubbles.get(bubbleId);
        
        if (!bubble) {
            // 如果找不到气泡，创建新的
            console.log('[ChatWindow] 气泡不存在，创建新气泡:', bubbleId);
            this.createMessageBubble(message);
            return;
                    }
                    
        // 更新气泡数据
        const bubbleData = {
            id: bubbleId,
            type: message.type,
            contentType: message.messageType,
            content: message.content || '',
            timestamp: message.timestamp,
            isStreaming: message.isStreaming || message.isStreamingVoice || false,
            duration: message.duration || 0
        };
        
        bubble.update(bubbleData);
        
        // 如果有音频数据，设置到气泡
        if (message.audioData) {
            bubble.setAudioData(message.audioData);
        }
        
        scrollToBottom(this.messageContainer);
    }

    /**
     * 发送消息
     */
    async sendMessage() {
        console.log('[ChatWindow] sendMessage() 被调用');
        const text = this.inputArea.value.trim();
        if (!text) {
            console.log('[ChatWindow] 输入为空，取消发送');
            return;
        }

        console.log('[ChatWindow] 准备发送消息:', text.substring(0, 50));

        // 清空输入框
        this.inputArea.value = '';
        this.inputArea.style.height = 'auto';

        try {
            // ✅ 获取 SettingsPanel 的待更新配置
            const settingsPanel = this.agentController.getSettingsPanel();
            const updates = settingsPanel ? settingsPanel.getPendingUpdates() : {};
            
            console.log('[ChatWindow] 配置更新:', updates);
            
            // ✅ 传递当前配置参数 + 待更新配置
            await this.client.sendText(text, {
                requireTTS: this.client.config.requireTTS,
                enableSRS: this.client.config.enableSRS,
                functionCalling: this.client.config.functionCalling.length > 0 ? this.client.config.functionCalling : undefined,
                ...updates
            });
            
            console.log('[ChatWindow] 消息发送成功');
            
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
        console.log('[ChatWindow] toggleVoiceRecording() 被调用，当前状态:', this.client.isRecording);
        
        try {
            if (this.client.isRecording) {
                console.log('[ChatWindow] 停止录音');
                await this.client.stopRecording();
            } else {
                console.log('[ChatWindow] 开始录音');
                
                // ✅ 获取 SettingsPanel 的待更新配置
                const settingsPanel = this.agentController.getSettingsPanel();
                const updates = settingsPanel ? settingsPanel.getPendingUpdates() : {};
                
                console.log('[ChatWindow] 录音配置更新:', updates);
                
                // ✅ 传递当前配置参数 + 待更新配置
                await this.client.startRecording({
                    vadEnabled: this.client.vadEnabled,
                    vadParams: this.client.config.vadParams,
                    requireTTS: this.client.config.requireTTS,
                    enableSRS: this.client.config.enableSRS,
                    functionCalling: this.client.config.functionCalling.length > 0 ? this.client.config.functionCalling : undefined,
                    ...updates
                });
                
                console.log('[ChatWindow] 录音已开始');
                
                // ✅ 发送成功后清除更新开关
                if (settingsPanel && Object.keys(updates).length > 0) {
                    settingsPanel.clearUpdateSwitches();
                    console.log('[ChatWindow] 已发送配置更新:', updates);
                }
            }
        } catch (error) {
            console.error('[ChatWindow] 录音失败:', error);
            alert('录音失败: ' + error.message);
        }
    }

    /**
     * 清空消息
     */
    clearMessages() {
        this.messageBubbles.forEach(bubble => bubble.destroy());
        this.messageBubbles.clear();
        this.messageContainer.innerHTML = '';
    }

    /**
     * 显示（复用时调用）
     */
    show() {
        console.log('[ChatWindow] show() 被调用，container:', this.container);
        
        // ✅ 如果 container 的子元素为空，重新渲染 UI（但不清空消息记录）
        if (this.container && this.container.children.length === 0) {
            console.log('[ChatWindow] 容器为空，重新渲染 UI');
            this.render();  // render() 内部会调用 bindUIEvents()
            // ✅ 重新渲染后，立即加载所有已有消息
            this.loadExistingMessages();
        }
        
        if (this.container) {
            this.container.style.display = 'flex';
        }
        
        // ✅ 同步语音按钮状态（根据当前录音状态）
        if (this.voiceButton) {
            if (this.client.isRecording) {
                console.log('[ChatWindow] 同步语音按钮状态：录音中');
                this.voiceButton.textContent = '⏹️';
                this.voiceButton.classList.add('recording');
            } else {
                console.log('[ChatWindow] 同步语音按钮状态：未录音');
                this.voiceButton.textContent = '🎤';
                this.voiceButton.classList.remove('recording');
            }
        }
        
        console.log('[ChatWindow] show() 完成');
    }

    /**
     * 隐藏（不销毁）
     */
    hide() {
        this.container.style.display = 'none';
    }

    /**
     * 销毁
     */
    destroy() {
        console.log('[ChatWindow] 销毁组件');
        
        // 清理定时器
        if (this.voiceTimerInterval) {
            clearInterval(this.voiceTimerInterval);
            this.voiceTimerInterval = null;
        }
        
        // 清理消息气泡
        this.messageBubbles.forEach(bubble => bubble.destroy());
        this.messageBubbles.clear();
        this.voiceDataCache.clear();
        
        this.container.innerHTML = '';
        
        console.log('[ChatWindow] 组件已销毁');
    }
}

