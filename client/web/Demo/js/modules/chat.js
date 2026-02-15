/**
 * 聊天模块
 * 处理消息发送、接收、显示等功能
 */
class ChatModule {
    /**
     * 构造函数
     */
    constructor() {
        this.messageHistory = null;
        this.logContent = null;
        this.audioUrls = new Map(); // 存储音频URL，用于后续清理
        this.init();
    }

    /**
     * 初始化聊天模块
     */
    init() {
        this.updateElements();
    }

    /**
     * 更新DOM元素引用
     */
    updateElements() {
        this.messageHistory = document.getElementById('messageHistory');
        this.logContent = document.getElementById('logContent');
    }

    /**
     * 添加消息到聊天窗口
     * @param {string} type - 消息类型 (sent 或 received)
     * @param {string|null} content - 消息内容
     * @param {Blob|null} audioData - 音频数据
     * @param {number|null} duration - 音频时长
     * @param {Object} options - 选项
     * @returns {HTMLElement|null} - 创建的消息元素
     */
    addMessage(type, content, audioData = null, duration = null, options = {}) {
        // 在添加消息之前更新元素引用
        this.updateElements();
        
        if (!this.messageHistory) {
            console.warn('消息历史容器不存在');
            return null;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const now = new Date();
        const timeString = now.toLocaleTimeString();

        if (audioData) {
            // 语音消息
            try {
                const audioId = `audio-${Date.now()}`;
                let audioUrl = null;
                let durationText = '加载中...';

                // 验证音频数据
                if (audioData instanceof Blob && audioData.size > 0) {
                    try {
                        audioUrl = URL.createObjectURL(audioData);
                        // 存储音频URL，用于后续清理
                        this.audioUrls.set(audioId, audioUrl);
                        console.log(`[Audio] 创建音频URL: ${audioUrl}, size: ${audioData.size} bytes, type: ${audioData.type}`);
                    } catch (urlError) {
                        console.error(`创建音频URL失败: ${urlError.message}`);
                        // 降级为文本消息
                        messageDiv.innerHTML = `
                            ${type === 'received' ? '<div class="message-avatar"></div>' : ''}
                            <div class="message-content">
                                <div class="message-text">[语音消息]</div>
                            </div>
                            <div class="message-time">${timeString}</div>
                            ${type === 'sent' ? '<div class="message-avatar"></div>' : ''}
                        `;
                        this.messageHistory.appendChild(messageDiv);
                        this.messageHistory.scrollTop = this.messageHistory.scrollHeight;
                        return messageDiv;
                    }
                } else {
                    console.error('无效的音频数据:', audioData);
                    // 降级为文本消息
                    messageDiv.innerHTML = `
                        ${type === 'received' ? '<div class="message-avatar"></div>' : ''}
                        <div class="message-content">
                            <div class="message-text">[语音消息]</div>
                        </div>
                        <div class="message-time">${timeString}</div>
                        ${type === 'sent' ? '<div class="message-avatar"></div>' : ''}
                    `;
                    this.messageHistory.appendChild(messageDiv);
                    this.messageHistory.scrollTop = this.messageHistory.scrollHeight;
                    return messageDiv;
                }

                // 如果直接提供了时长，使用它
                if (duration !== null && !isNaN(duration)) {
                    const minutes = Math.floor(duration / 60).toString().padStart(2, '0');
                    const seconds = Math.floor(duration % 60).toString().padStart(2, '0');
                    durationText = `${minutes}:${seconds}`;
                } else {
                    // 否则尝试从音频元素获取时长
                    const audio = new Audio(audioUrl);
                    audio.onloadedmetadata = () => {
                        try {
                            const audioDuration = audio.duration;
                            if (!isNaN(audioDuration) && isFinite(audioDuration)) {
                                const minutes = Math.floor(audioDuration / 60).toString().padStart(2, '0');
                                const seconds = Math.floor(audioDuration % 60).toString().padStart(2, '0');
                                const newDurationText = `${minutes}:${seconds}`;

                                const voiceMessageDiv = messageDiv.querySelector('.voice-message');
                                if (voiceMessageDiv) {
                                    voiceMessageDiv.innerHTML = `
                                        <span class="voice-duration">${newDurationText}</span>
                                    `;
                                }
                            }
                        } catch (error) {
                            console.error(`获取音频时长失败: ${error.message}`);
                        }
                    };
                    audio.onerror = (event) => {
                        console.error(`音频加载失败: ${event.target.error?.message || '未知错误'}`);
                    };
                }

                messageDiv.innerHTML = `
                    ${type === 'received' ? '<div class="message-avatar"></div>' : ''}
                    <div class="message-content">
                        <div class="voice-message" data-audio-url="${audioUrl}" data-audio-id="${audioId}">
                            <span class="voice-duration">${durationText}</span>
                        </div>
                    </div>
                    <div class="message-time">${timeString}</div>
                    ${type === 'sent' ? '<div class="message-avatar"></div>' : ''}
                `;

                // 点击整个气泡播放/停止语音
                const voiceMessageDiv = messageDiv.querySelector('.voice-message');
                if (voiceMessageDiv) {
                    voiceMessageDiv.addEventListener('click', () => this.toggleVoiceMessage(voiceMessageDiv));
                }

                // 当消息被移除时清理音频URL
                messageDiv.addEventListener('remove', () => {
                    this.cleanupAudio(audioId);
                });
            } catch (error) {
                console.error(`创建语音消息失败: ${error.message}`);
                // 降级为文本消息
                messageDiv.innerHTML = `
                    ${type === 'received' ? '<div class="message-avatar"></div>' : ''}
                    <div class="message-content">
                        <div class="message-text">[语音消息]</div>
                    </div>
                    <div class="message-time">${timeString}</div>
                    ${type === 'sent' ? '<div class="message-avatar"></div>' : ''}
                `;
            }
        } else {
            // 文本消息
            let contentHtml = '';

            // 检查是否是复合消息（包含文本内容和函数调用）
            if (options.hasFunctionCall && options.functionCallDisplay) {
                // 显示文本内容在上，函数调用在下
                contentHtml = `
                    <div class="message-text">${content || ''}</div>
                    <div class="message-function-call">${options.functionCallDisplay}</div>
                `;
            } else if (options.isFunctionCall) {
                // 仅显示函数调用
                contentHtml = `
                    <div class="message-function-call">${content}</div>
                `;
            } else {
                // 仅显示普通文本内容
                contentHtml = `<div class="message-text">${content || ''}</div>`;
            }

            messageDiv.innerHTML = `
                ${type === 'received' ? '<div class="message-avatar"></div>' : ''}
                <div class="message-content">
                    ${contentHtml}
                </div>
                <div class="message-time">${timeString}</div>
                ${type === 'sent' ? '<div class="message-avatar"></div>' : ''}
            `;
        }

        this.messageHistory.appendChild(messageDiv);
        this.messageHistory.scrollTop = this.messageHistory.scrollHeight;

        return messageDiv;
    }

    /**
     * 清理音频资源
     * @param {string} audioId - 音频ID
     */
    cleanupAudio(audioId) {
        if (this.audioUrls.has(audioId)) {
            const audioUrl = this.audioUrls.get(audioId);
            try {
                URL.revokeObjectURL(audioUrl);
                console.log(`[Audio] 清理音频URL: ${audioUrl}`);
            } catch (error) {
                console.error(`清理音频URL失败: ${error.message}`);
            }
            this.audioUrls.delete(audioId);
        }
        
        // 清理对应的音频元素
        const audioElement = document.getElementById('audio-' + audioId);
        if (audioElement) {
            try {
                audioElement.pause();
                audioElement.src = '';
                document.body.removeChild(audioElement);
                console.log(`[Audio] 清理音频元素: audio-${audioId}`);
            } catch (error) {
                console.error(`清理音频元素失败: ${error.message}`);
            }
        }
    }

    /**
     * 清理所有音频资源
     */
    cleanupAllAudio() {
        for (const audioId of this.audioUrls.keys()) {
            this.cleanupAudio(audioId);
        }
    }

    /**
     * 切换语音消息的播放状态
     * @param {HTMLElement} voiceMessageElement - 语音消息元素
     */
    toggleVoiceMessage(voiceMessageElement) {
        console.log(`[Audio] toggleVoiceMessage 被调用`);
        console.log(`[Audio] _fullAudioBlob:`, voiceMessageElement._fullAudioBlob);

        // 检查是否正在播放
        const isPlaying = voiceMessageElement.classList.contains('playing');

        // 如果正在播放，停止播放
        if (isPlaying) {
            console.log(`[Audio] 停止播放音频`);
            this.stopAllAudio();
            voiceMessageElement.classList.remove('playing');
            return;
        }

        // 停止其他正在播放的音频
        this.stopAllAudio();

        // 优先使用存储的完整音频Blob（app.js中设置的）
        if (voiceMessageElement._fullAudioBlob) {
            console.log(`[Audio] 使用存储的完整音频Blob播放，大小:`, voiceMessageElement._fullAudioBlob.size);
            this._playFullAudioBlob(voiceMessageElement._fullAudioBlob, voiceMessageElement);
            return;
        }

        const audioUrl = voiceMessageElement.dataset.audioUrl;
        const audioId = voiceMessageElement.dataset.audioId;

        console.log(`[Audio] audioUrl:`, audioUrl);
        console.log(`[Audio] audioId:`, audioId);

        if (!audioUrl) {
            console.error('[Audio] 音频URL不存在');
            return;
        }

        // 创建或获取音频元素
        let audioElement = document.getElementById('audio-' + audioId);
        if (!audioElement) {
            try {
                audioElement = document.createElement('audio');
                audioElement.id = 'audio-' + audioId;
                audioElement.src = audioUrl;
                audioElement.style.display = 'none';
                document.body.appendChild(audioElement);

                console.log(`[Audio] 创建音频元素: audio-${audioId}, URL: ${audioUrl}`);

                // 添加错误事件监听
                audioElement.addEventListener('error', (event) => {
                    console.error(`[Audio] 音频元素错误: ${event.target.error?.message || '未知错误'}`);
                    console.error(`[Audio] 音频URL: ${audioUrl}`);
                    console.error(`[Audio] 音频元素状态:`, {
                        readyState: audioElement.readyState,
                        networkState: audioElement.networkState,
                        error: audioElement.error
                    });
                    voiceMessageElement.classList.remove('playing');
                });

                // 添加加载事件监听
                audioElement.addEventListener('loadedmetadata', () => {
                    console.log(`[Audio] 音频元数据加载完成: duration = ${audioElement.duration}s`);
                });

                // 添加结束事件监听
                audioElement.addEventListener('ended', () => {
                    console.log(`[Audio] 音频播放完成`);
                    voiceMessageElement.classList.remove('playing');
                });
            } catch (error) {
                console.error(`[Audio] 创建音频元素失败: ${error.message}`);
                return;
            }
        } else {
            // 如果音频元素已存在，重置播放位置
            audioElement.currentTime = 0;
        }

        // 验证音频元素状态
        if (audioElement.error) {
            console.error(`[Audio] 音频元素存在错误: ${audioElement.error.message}`);
            return;
        }

        // 开始播放音频
        console.log(`[Audio] 开始播放音频: ${audioUrl}`);
        audioElement.play().then(() => {
            console.log(`[Audio] 音频播放开始成功`);
            voiceMessageElement.classList.add('playing');
        }).catch(error => {
            console.error(`[Audio] 播放音频失败: ${error.message}`);
            console.error(`[Audio] 错误详情:`, error);
            // 尝试使用Web Audio API播放
            this._playWithWebAudio(audioUrl, voiceMessageElement);
        });
    }

    /**
     * 播放完整的音频Blob
     * @param {Blob} audioBlob - 完整的音频数据
     * @param {HTMLElement} voiceMessageElement - 语音消息元素
     */
    async _playFullAudioBlob(audioBlob, voiceMessageElement) {
        console.log(`[Audio] 播放完整音频Blob，大小: ${audioBlob.size} bytes`);

        // 停止其他正在播放的音频
        this.stopAllAudio();

        try {
            // 初始化AudioContext
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();

            if (audioContext.state === 'suspended') {
                await audioContext.resume();
                console.log(`[Audio] AudioContext已恢复`);
            }

            // 读取音频数据
            const arrayBuffer = await audioBlob.arrayBuffer();
            console.log(`[Audio] 音频数据读取完成，大小: ${arrayBuffer.byteLength} bytes`);

            // 检查是否是WAV格式
            const headerView = new DataView(arrayBuffer, 0, 12);
            const riffId = String.fromCharCode(
                headerView.getUint8(0),
                headerView.getUint8(1),
                headerView.getUint8(2),
                headerView.getUint8(3)
            );
            console.log(`[Audio] 文件头标识: ${riffId}`);

            let audioBuffer;
            if (riffId === 'RIFF') {
                // 标准WAV格式，使用decodeAudioData解码
                console.log(`[Audio] 检测到WAV格式，使用decodeAudioData解码`);
                audioBuffer = await audioContext.decodeAudioData(arrayBuffer.slice(0));
                console.log(`[Audio] WAV解码成功，时长: ${audioBuffer.duration}s, 采样率: ${audioBuffer.sampleRate}Hz, 声道数: ${audioBuffer.numberOfChannels}`);

                // 检查音频内容
                const channelData = audioBuffer.getChannelData(0);
                let hasSound = false;
                let maxSample = 0;
                let nonZeroCount = 0;
                for (let i = 0; i < Math.min(channelData.length, 1000); i++) {
                    if (Math.abs(channelData[i]) > 0.001) {
                        hasSound = true;
                    }
                    if (Math.abs(channelData[i]) > maxSample) {
                        maxSample = Math.abs(channelData[i]);
                    }
                    if (Math.abs(channelData[i]) > 0.0001) {
                        nonZeroCount++;
                    }
                }
                console.log(`[Audio] 音频内容检查 - 总帧数: ${channelData.length}, 前1000帧有声音: ${hasSound}, 非零样本: ${nonZeroCount}/1000, 最大振幅: ${maxSample}`);
            } else {
                // 原始PCM数据，手动创建AudioBuffer
                console.log(`[Audio] 检测到原始PCM数据，手动创建AudioBuffer`);

                const sampleRate = 16000;
                const numChannels = 1;
                const bytesPerSample = 2; // 16-bit PCM
                const frameCount = Math.floor(arrayBuffer.byteLength / (numChannels * bytesPerSample));

                audioBuffer = audioContext.createBuffer(numChannels, frameCount, sampleRate);
                const channelData = audioBuffer.getChannelData(0);

                const dataView = new DataView(arrayBuffer);
                for (let i = 0; i < frameCount; i++) {
                    const sample = dataView.getInt16(i * bytesPerSample, true);
                    channelData[i] = sample / 32768;
                }

                console.log(`[Audio] PCM转换完成，时长: ${audioBuffer.duration}s`);
            }

            // 创建音频源并播放
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);

            // 存储source和audioContext，以便在stopAllAudio中停止
            voiceMessageElement._audioSource = source;
            voiceMessageElement._audioContext = audioContext;

            console.log(`[Audio] 开始播放完整音频，时长: ${audioBuffer.duration}s`);
            voiceMessageElement.classList.add('playing');

            // 播放完成回调
            source.onended = () => {
                console.log(`[Audio] 完整音频播放完成`);
                voiceMessageElement.classList.remove('playing');
                // 清理存储的音频源和上下文
                delete voiceMessageElement._audioSource;
                delete voiceMessageElement._audioContext;
            };

            // 开始播放
            source.start();
        } catch (error) {
            console.error(`[Audio] 播放完整音频Blob失败: ${error.message}`);
            voiceMessageElement.classList.remove('playing');
            // 清理存储的音频源和上下文
            delete voiceMessageElement._audioSource;
            delete voiceMessageElement._audioContext;
        }
    }

    /**
     * 使用Web Audio API播放音频
     * @param {string} audioUrl - 音频URL
     * @param {HTMLElement} voiceMessageElement - 语音消息元素
     */
    async _playWithWebAudio(audioUrl, voiceMessageElement) {
        console.log(`[WebAudio] 尝试使用Web Audio API播放音频`);
        
        try {
            // 初始化AudioContext
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // 加载音频数据
            const response = await fetch(audioUrl);
            const arrayBuffer = await response.arrayBuffer();
            
            // 解码音频数据
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            
            // 创建音频源
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            
            console.log(`[WebAudio] 开始播放音频，时长: ${audioBuffer.duration}s`);
            voiceMessageElement.classList.add('playing');
            
            // 播放完成回调
            source.onended = () => {
                console.log(`[WebAudio] 音频播放完成`);
                voiceMessageElement.classList.remove('playing');
            };
            
            // 开始播放
            source.start();
        } catch (error) {
            console.error(`[WebAudio] 播放音频失败: ${error.message}`);
        }
    }

    /**
     * 停止所有正在播放的音频
     */
    stopAllAudio() {
        // 停止HTML5音频元素
        const audioElements = document.querySelectorAll('audio');
        audioElements.forEach(audio => {
            if (!audio.paused) {
                audio.pause();
                audio.currentTime = 0;
            }
        });

        // 停止使用Web Audio API播放的音频
        const voiceMessages = document.querySelectorAll('.voice-message');
        voiceMessages.forEach(message => {
            if (message._audioSource) {
                try {
                    message._audioSource.stop();
                    console.log('[Audio] 停止Web Audio API音频');
                } catch (error) {
                    // 忽略已停止的音频源的错误
                }
                delete message._audioSource;
                delete message._audioContext;
            }
            message.classList.remove('playing');
        });
    }

    /**
     * 记录日志
     * @param {string} level - 日志级别
     * @param {string} message - 日志消息
     */
    log(level, message) {
        // 每次调用时更新元素引用，确保能获取到最新的DOM元素
        this.updateElements();
        
        if (!this.logContent) {
            // 如果元素仍然不存在，只输出到控制台
            console[level === 'error' ? 'error' : level === 'warning' ? 'warn' : 'log'](`[${level.toUpperCase()}] ${message}`);
            return;
        }

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level}`;

        const timestamp = new Date().toLocaleTimeString();
        logEntry.innerHTML = `
            <span class="log-time">${timestamp}</span>
            <span class="log-level">${level.toUpperCase()}</span>
            <span class="log-message">${message}</span>
        `;

        this.logContent.appendChild(logEntry);
        this.logContent.scrollTop = this.logContent.scrollHeight;

        // 同时输出到控制台
        console[level === 'error' ? 'error' : level === 'warning' ? 'warn' : 'log'](`[${level.toUpperCase()}] ${message}`);
    }

    /**
     * 清空日志
     */
    clearLog() {
        if (this.logContent) {
            this.logContent.innerHTML = '';
            this.log('info', '日志已清空');
        }
    }

    /**
     * 更新会话状态显示
     * @param {string} status - 会话状态
     * @param {string} sessionId - 会话ID
     */
    updateSessionStatus(status, sessionId) {
        const sessionIdElement = document.getElementById('sessionId');
        const sessionStatusElement = document.getElementById('sessionStatus');

        if (sessionIdElement) {
            sessionIdElement.textContent = sessionId ? sessionId.substring(0, 8) + '...' : '-';
        }

        if (sessionStatusElement) {
            if (status === 'connected') {
                sessionStatusElement.textContent = '已连接';
                sessionStatusElement.className = 'status-badge status-online';
            } else {
                sessionStatusElement.textContent = '未连接';
                sessionStatusElement.className = 'status-badge status-offline';
            }
        }
    }
}

// 导出单例实例
export const chatModule = new ChatModule();
