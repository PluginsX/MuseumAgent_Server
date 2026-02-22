/**
 * AgentController - 智能体前端的唯一入口
 * 职责：
 * 1. 管理 MuseumAgentClient 实例
 * 2. 维护消息历史（单一数据源）
 * 3. 统一订阅 client 事件
 * 4. 提供 ChatWindow 和 SettingsPanel 单例
 * 
 * ✅ 现代化方案：EventTarget + 响应式状态
 */

import { ChatWindow } from './components/ChatWindow.js';
import { SettingsPanel } from './components/SettingsPanel.js';

// 从全局变量获取 SDK
const { Events } = window.MuseumAgentSDK;

export class AgentController extends EventTarget {
    constructor(client) {
        super();
        
        this.client = client;
        this.messages = [];  // 单一数据源
        
        // 单例组件（懒加载）
        this.chatWindow = null;
        this.settingsPanel = null;
        
        // 订阅 client 事件
        this.subscribeToClient();
    }
    
    /**
     * 订阅 client 事件（唯一订阅点）
     */
    subscribeToClient() {
        // 消息发送
        this.client.on(Events.MESSAGE_SENT, (data) => {
            console.log('[AgentController] 消息发送:', data);
            const message = {
                id: data.id || `sent_${Date.now()}_${Math.random()}`,
                type: 'sent',  // ✅ 发送的消息
                content: data.text || data.content || '',
                timestamp: new Date(),
                messageType: data.type === 'voice' ? 'voice' : 'text',
                duration: data.type === 'voice' ? 0 : undefined,
                startTime: data.type === 'voice' ? data.startTime : undefined
            };
            console.log('[AgentController] 创建发送消息:', message);
            this.addMessage(message);
        });
        
        // 文本块接收
        this.client.on(Events.TEXT_CHUNK, (data) => {
            console.log('[AgentController] 文本块:', {
                messageId: data.messageId,
                chunk: data.chunk?.substring(0, 20),
                text: data.text?.substring(0, 20)
            });
            
            // ✅ 为文本消息创建独立的 ID（与语音消息分开，避免冲突）
            const textMessageId = `${data.messageId}_text`;
            
            // 查找或创建当前消息
            let currentMessage = this.messages.find(
                msg => msg.id === textMessageId
            );
            
            if (!currentMessage) {
                currentMessage = {
                    id: textMessageId,
                    type: 'received',  // ✅ 接收的消息
                    content: data.chunk || data.text || '',
                    timestamp: new Date(),
                    messageType: 'text',
                    isStreaming: true
                };
                console.log('[AgentController] 创建接收消息（文本）:', {
                    id: currentMessage.id,
                    type: currentMessage.type,
                    messageType: currentMessage.messageType,
                    content: currentMessage.content.substring(0, 30)
                });
                this.addMessage(currentMessage);
            } else {
                // 追加文本
                currentMessage.content += data.chunk || data.text || '';
                
                // 通知更新
                this.dispatchEvent(new CustomEvent('messageUpdated', {
                    detail: { message: currentMessage }
                }));
            }
        });
        
        // 消息完成
        this.client.on(Events.MESSAGE_COMPLETE, (data) => {
            console.log('[AgentController] 消息完成:', { messageId: data.messageId });
            
            // ✅ 标记文本消息完成（使用 _text 后缀）
            const textMessageId = `${data.messageId}_text`;
            const textMessage = this.messages.find(
                msg => msg.id === textMessageId
            );
            
            if (textMessage && textMessage.isStreaming) {
                textMessage.isStreaming = false;
                console.log('[AgentController] 文本消息完成:', textMessageId);
                this.dispatchEvent(new CustomEvent('messageCompleted', {
                    detail: { message: textMessage }
                }));
            }
            
            // ✅ 标记语音消息完成（使用 _voice 后缀）
            const voiceMessageId = `${data.messageId}_voice`;
            const voiceMessage = this.messages.find(
                msg => msg.id === voiceMessageId
            );
            
            if (voiceMessage && voiceMessage.isStreamingVoice) {
                voiceMessage.isStreamingVoice = false;
                console.log('[AgentController] 语音消息完成:', voiceMessageId);
                this.dispatchEvent(new CustomEvent('messageCompleted', {
                    detail: { message: voiceMessage }
                }));
            }
        });
        
        // 语音块接收
        this.client.on(Events.VOICE_CHUNK, (data) => {
            console.log('[AgentController] 语音块:', data);
            
            // 为语音消息创建独立的 ID（与文本消息分开）
            const voiceMessageId = `${data.messageId}_voice`;
            
            // 查找或创建当前语音消息
            let currentMessage = this.messages.find(
                msg => msg.id === voiceMessageId
            );
            
            if (!currentMessage) {
                currentMessage = {
                    id: voiceMessageId,
                    type: 'received',  // ✅ 接收的语音消息
                    content: '语音消息',
                    timestamp: new Date(),
                    messageType: 'voice',
                    isStreamingVoice: true,
                    audioUrl: null,
                    duration: 0
                };
                console.log('[AgentController] 创建接收消息（语音）:', currentMessage);
                this.addMessage(currentMessage);
            } else {
                // 更新语音信息
                if (data.audioUrl) {
                    currentMessage.audioUrl = data.audioUrl;
                }
                if (data.duration) {
                    currentMessage.duration = data.duration;
                }
                
                // 通知更新
                this.dispatchEvent(new CustomEvent('messageUpdated', {
                    detail: { message: currentMessage }
                }));
            }
        });
        
        // 函数调用
        this.client.on(Events.FUNCTION_CALL, (data) => {
            console.log('[AgentController] 函数调用:', data);
            const message = {
                id: `func_${Date.now()}_${Math.random()}`,
                type: 'received',  // ✅ 函数调用是接收的消息
                content: data,
                timestamp: new Date(),
                messageType: 'function'
            };
            console.log('[AgentController] 创建接收消息（函数）:', message);
            this.addMessage(message);
        });
        
        // 录音完成（更新语音消息的时长和音频数据）
        this.client.on(Events.RECORDING_COMPLETE, (data) => {
            console.log('[AgentController] 录音完成:', data);
            
            const message = this.messages.find(m => m.id === data.id);
            if (message && message.messageType === 'voice') {
                message.duration = data.duration;
                message.audioData = data.audioData;
                
                this.dispatchEvent(new CustomEvent('messageUpdated', {
                    detail: { message }
                }));
            }
        });
        
        // 错误处理
        this.client.on(Events.ERROR, (error) => {
            console.error('[AgentController] 错误:', error);
            this.dispatchEvent(new CustomEvent('error', {
                detail: { error }
            }));
        });
    }
    
    /**
     * 添加消息
     */
    addMessage(message) {
        this.messages.push(message);
        this.dispatchEvent(new CustomEvent('messageAdded', {
            detail: { message }
        }));
    }
    
    /**
     * ✅ 获取 ChatWindow 单例
     */
    getChatWindow(container) {
        if (!this.chatWindow) {
            // 创建临时容器（如果没有提供）
            const tempContainer = container || document.createElement('div');
            this.chatWindow = new ChatWindow(tempContainer, this.client, this);
            console.log('[AgentController] ChatWindow 单例已创建');
        }
        return this.chatWindow;
    }
    
    /**
     * ✅ 获取 SettingsPanel 单例
     */
    getSettingsPanel(container) {
        if (!this.settingsPanel) {
            // 创建临时容器（如果没有提供）
            const tempContainer = container || document.createElement('div');
            this.settingsPanel = new SettingsPanel(tempContainer, this.client);
            console.log('[AgentController] SettingsPanel 单例已创建');
        }
        return this.settingsPanel;
    }
    
    /**
     * 获取所有消息
     */
    getMessages() {
        return this.messages;
    }
    
    /**
     * 清空消息
     */
    clearMessages() {
        this.messages = [];
        this.dispatchEvent(new CustomEvent('messagesCleared'));
    }
    
    /**
     * 销毁
     */
    destroy() {
        // 销毁组件
        if (this.chatWindow) {
            this.chatWindow.destroy();
            this.chatWindow = null;
        }
        
        if (this.settingsPanel) {
            this.settingsPanel.destroy();
            this.settingsPanel = null;
        }
        
        // 清空消息
        this.messages = [];
        
        console.log('[AgentController] 已销毁');
    }
}

