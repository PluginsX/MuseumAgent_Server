/**
 * 消息气泡组件
 * 显示单条消息（文本、语音、函数调用）
 */

import { createElement, formatTime } from '../utils/dom.js';
import { escapeHtml } from '../utils/security.js';
import { audioService } from '../services/AudioService.js';

export class MessageBubble {
    constructor(message) {
        this.message = message;
        this.element = null;
        this.contentElement = null;
        
        this.render();
    }

    /**
     * 渲染
     */
    render() {
        const isSent = this.message.type === 'sent';
        
        this.element = createElement('div', {
            className: `message-bubble ${isSent ? 'sent' : 'received'}`
        });

        const bubbleContent = createElement('div', {
            className: 'bubble-content'
        });

        // 根据内容类型渲染
        if (this.message.contentType === 'text') {
            this.contentElement = this.renderTextContent();
        } else if (this.message.contentType === 'voice') {
            this.contentElement = this.renderVoiceContent();
        } else if (this.message.contentType === 'function') {
            this.contentElement = this.renderFunctionContent();
        }

        bubbleContent.appendChild(this.contentElement);

        // 时间戳
        const timeElement = createElement('div', {
            className: 'message-time',
            textContent: formatTime(this.message.timestamp)
        });

        bubbleContent.appendChild(timeElement);
        this.element.appendChild(bubbleContent);
    }

    /**
     * 渲染文本内容
     */
    renderTextContent() {
        const textElement = createElement('div', {
            className: 'message-text'
        });

        // 使用 textContent 防止 XSS
        textElement.textContent = this.message.content;

        // 如果正在流式传输，显示光标
        if (this.message.isStreaming) {
            const cursor = createElement('span', {
                className: 'typing-cursor',
                textContent: '▋'
            });
            textElement.appendChild(cursor);
        }

        return textElement;
    }

    /**
     * 渲染语音内容
     */
    renderVoiceContent() {
        const voiceElement = createElement('div', {
            className: 'message-voice'
        });

        const icon = createElement('span', {
            textContent: '🎤'
        });

        // 格式化时长显示
        const duration = this.message.duration || 0;
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        const durationText = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        const durationElement = createElement('span', {
            textContent: durationText
        });

        voiceElement.appendChild(icon);
        voiceElement.appendChild(durationElement);

        // 点击播放（仅接收的消息）
        if (this.message.type === 'received' && this.message.audioData) {
            voiceElement.addEventListener('click', () => {
                this.playVoice();
            });
            voiceElement.style.cursor = 'pointer';
        }

        return voiceElement;
    }

    /**
     * 渲染函数调用内容
     */
    renderFunctionContent() {
        const funcElement = createElement('div', {
            className: 'message-function'
        });

        const functionCall = this.message.content;
        const params = Object.entries(functionCall.parameters || {})
            .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
            .join(', ');

        funcElement.textContent = `${functionCall.name}(${params})`;

        return funcElement;
    }

    /**
     * 播放语音
     */
    async playVoice() {
        if (this.message.audioData) {
            try {
                await audioService.playPCM(this.message.audioData);
            } catch (error) {
                console.error('[MessageBubble] 播放语音失败:', error);
            }
        }
    }

    /**
     * 更新消息
     */
    update(message) {
        this.message = message;

        // 根据内容类型更新
        if (this.message.contentType === 'text') {
            const textElement = this.contentElement.querySelector('.message-text') || this.contentElement;
            textElement.textContent = this.message.content;

            // 更新光标
            const cursor = textElement.querySelector('.typing-cursor');
            if (this.message.isStreaming && !cursor) {
                const newCursor = createElement('span', {
                    className: 'typing-cursor',
                    textContent: '▋'
                });
                textElement.appendChild(newCursor);
            } else if (!this.message.isStreaming && cursor) {
                cursor.remove();
            }
        } else if (this.message.contentType === 'voice') {
            // 更新语音时长显示
            const durationElement = this.contentElement.querySelector('span:last-child');
            if (durationElement && this.message.duration !== undefined) {
                const duration = this.message.duration || 0;
                const minutes = Math.floor(duration / 60);
                const seconds = Math.floor(duration % 60);
                const durationText = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                durationElement.textContent = durationText;
            }
        }
    }

    /**
     * 销毁
     */
    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

