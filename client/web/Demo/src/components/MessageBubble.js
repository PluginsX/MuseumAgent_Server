/**
 * 消息气泡组件
 * 基于 MuseumAgentSDK 客户端库开发
 */

import { createElement, formatTime } from '../utils/dom.js';
import globalAudioPlayer from '../utils/audioPlayer.js';

export class MessageBubble {
    constructor(message) {
        this.message = message;
        this.element = null;
        this.contentElement = null;
        this.isPlaying = false;
        this.audioData = null; // 存储音频数据
        
        this.render();
    }

    /**
     * 渲染
     */
    render() {
        const isSent = this.message.type === 'sent';
        
        // 根据消息类型添加不同的类名，实现视觉区分
        const typeClass = `message-${this.message.contentType}`;
        
        this.element = createElement('div', {
            className: `message-bubble ${isSent ? 'sent' : 'received'} ${typeClass}`
        });

        const bubbleContent = createElement('div', {
            className: 'bubble-content'
        });

        // 根据内容类型渲染不同的气泡样式
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

        // 添加点击播放功能
        voiceElement.style.cursor = 'pointer';
        voiceElement.addEventListener('click', () => {
            this.togglePlayVoice();
        });

        // 格式化时长显示为 MM:SS 格式
        const duration = this.message.duration || 0;
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        const durationText = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        const durationElement = createElement('span', {
            className: 'voice-duration',
            textContent: durationText
        });

        voiceElement.appendChild(durationElement);

        return voiceElement;
    }

    /**
     * 切换语音播放
     */
    async togglePlayVoice() {
        if (!this.audioData) {
            console.warn('[MessageBubble] 没有音频数据可播放');
            return;
        }

        try {
            await globalAudioPlayer.play(this.audioData, this, () => {
                // 播放结束回调
                this.setPlayingState(false);
            });
            
            // 更新播放状态
            this.setPlayingState(globalAudioPlayer.isPlayingBubble(this));
        } catch (error) {
            console.error('[MessageBubble] 播放失败:', error);
            this.setPlayingState(false);
        }
    }

    /**
     * 设置播放状态
     */
    setPlayingState(playing) {
        this.isPlaying = playing;
        
        if (this.message.contentType === 'voice') {
            // 添加/移除播放中的样式
            if (playing) {
                this.contentElement.classList.add('playing');
            } else {
                this.contentElement.classList.remove('playing');
            }
        }
    }

    /**
     * 设置音频数据
     */
    setAudioData(audioData) {
        this.audioData = audioData;
    }

    /**
     * 渲染函数调用内容
     */
    renderFunctionContent() {
        const funcElement = createElement('div', {
            className: 'message-function'
        });

        const functionCall = this.message.content;
        
        // 函数图标
        const icon = createElement('span', {
            className: 'function-icon',
            textContent: '⚙️ '
        });
        funcElement.appendChild(icon);
        
        // 函数名称
        const nameElement = createElement('span', {
            className: 'function-name',
            textContent: functionCall.name
        });
        funcElement.appendChild(nameElement);
        
        // 添加左括号
        funcElement.appendChild(document.createTextNode('('));
        
        // 如果有参数，显示参数
        if (functionCall.arguments && Object.keys(functionCall.arguments).length > 0) {
            const entries = Object.entries(functionCall.arguments);
            
            entries.forEach(([key, value], index) => {
                // 参数键
                const paramKey = createElement('span', {
                    className: 'param-key',
                    textContent: key
                });
                funcElement.appendChild(paramKey);
                
                // 等号
                funcElement.appendChild(document.createTextNode('='));
                
                // 参数值
                const paramValue = createElement('span', {
                    className: 'param-value',
                    textContent: JSON.stringify(value)
                });
                funcElement.appendChild(paramValue);
                
                // 如果不是最后一个参数，添加逗号和空格
                if (index < entries.length - 1) {
                    funcElement.appendChild(document.createTextNode(', '));
                }
            });
        }
        
        // 添加右括号
        funcElement.appendChild(document.createTextNode(')'));

        return funcElement;
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
            const durationElement = this.contentElement.querySelector('.voice-duration');
            if (durationElement && this.message.duration !== undefined) {
                const duration = this.message.duration || 0;
                const minutes = Math.floor(duration / 60);
                const seconds = Math.floor(duration % 60);
                const durationText = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                durationElement.textContent = durationText;
                
                // 调试日志
                // console.log('[MessageBubble] 更新语音时长显示:', durationText);
            } else {
                console.warn('[MessageBubble] 无法更新语音时长:', {
                    hasDurationElement: !!durationElement,
                    duration: this.message.duration
                });
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
