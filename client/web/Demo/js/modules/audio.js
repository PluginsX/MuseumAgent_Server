/**
 * 音频处理模块
 * 处理音频播放、音频数据处理等功能
 */

class AudioModule {
    constructor() {
        this.audioContext = null;
        this.allPcmChunks = []; // 存储所有PCM数据块
        this.currentSource = null; // 当前播放的音频源
        this.isPlaying = false;
        this._audioProcessing = false; // 标记音频是否正在处理中
        this._audioQueue = []; // 音频播放队列（用于流式播放）
        this._isPlayingQueue = false; // 是否正在播放队列
        this.audioChunks = [];
        this.currentAudio = null;
        this.currentAudioUrl = null;
        this.voiceMessageDiv = null;
        this.audioStartTime = 0;
        this.audioDuration = 0;
        this.audioTimer = null;
    }

    /**
     * 初始化Web Audio API
     */
    _initWebAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('[WebAudio] AudioContext创建成功，采样率:', this.audioContext.sampleRate);
        } catch (error) {
            console.error('[WebAudio] 初始化失败:', error);
        }
    }

    /**
     * 播放PCM音频（核心方法）
     * @param {ArrayBuffer} pcmData - PCM原始二进制数据
     * @param {Object} config - PCM参数
     */
    async _playPCM(pcmData, config = {}) {
        return new Promise((resolve, reject) => {
            try {
                const { sampleRate = 16000, bitDepth = 16, channels = 1 } = config;
                
                console.log('[WebAudio] 开始播放PCM，参数:', { sampleRate, bitDepth, channels });
                
                // 1. 停止当前播放（避免重复叠加）
                if (this.currentSource) {
                    this.currentSource.stop();
                    this.currentSource.disconnect();
                    this.currentSource = null;
                }
                
                // 2. 初始化音频上下文
                if (!this.audioContext) {
                    this._initWebAudio();
                }
                
                if (this.audioContext && this.audioContext.state === 'suspended') {
                    this.audioContext.resume().then(() => {
                        this._continuePlayPCM(pcmData, config, resolve, reject);
                    }).catch(err => {
                        console.error('[WebAudio] AudioContext恢复失败:', err);
                        reject(err);
                    });
                } else {
                    this._continuePlayPCM(pcmData, config, resolve, reject);
                }
            } catch (error) {
                console.error('[WebAudio] 播放PCM失败:', error);
                this.isPlaying = false;
                reject(error);
            }
        });
    }

    /**
     * 继续播放PCM音频（内部方法）
     */
    _continuePlayPCM(pcmData, config, resolve, reject) {
        try {
            const { sampleRate = 16000, bitDepth = 16, channels = 1 } = config;
            
            // 3. 将PCM数据转换为AudioBuffer可识别的格式
            const sampleCount = pcmData.byteLength / (bitDepth / 8);
            const audioBuffer = this.audioContext.createBuffer(
                channels,
                sampleCount,
                sampleRate
            );
            
            // 4. 将PCM数据填充到AudioBuffer（关键：用Int16Array解析）
            const pcmArray = new Int16Array(pcmData);
            for (let channel = 0; channel < channels; channel++) {
                const channelData = audioBuffer.getChannelData(channel);
                for (let i = 0; i < sampleCount; i++) {
                    channelData[i] = pcmArray[i] / 32768;
                }
            }
            
            // 5. 创建音频源并播放（避免重复）
            this.currentSource = this.audioContext.createBufferSource();
            this.currentSource.buffer = audioBuffer;
            this.currentSource.connect(this.audioContext.destination);
            
            this.currentSource.onended = () => {
                console.log('[WebAudio] 音频播放完成');
                this.isPlaying = false;
                this.currentSource = null;
                resolve();
            };
            
            this.isPlaying = true;
            this.currentSource.start();
            console.log('[WebAudio] 开始播放音频');
            
        } catch (error) {
            console.error('[WebAudio] 播放PCM失败:', error);
            this.isPlaying = false;
            reject(error);
        }
    }

    /**
     * 播放完整的PCM音频数据
     */
    async _playPcmAudio() {
        if (this.allPcmChunks.length === 0 || this.isPlaying) {
            return;
        }
        
        try {
            // 合并所有PCM数据块
            const totalLength = this.allPcmChunks.reduce((sum, chunk) => sum + chunk.length, 0);
            const combinedPcm = new Uint8Array(totalLength);
            let offset = 0;
            for (const chunk of this.allPcmChunks) {
                combinedPcm.set(chunk, offset);
                offset += chunk.length;
            }
            
            console.log('[WebAudio] 合并PCM数据，总长度:', combinedPcm.length, 'bytes');
            
            // 播放PCM音频
            await this._playPCM(combinedPcm.buffer, {
                sampleRate: 16000,
                bitDepth: 16,
                channels: 1
            });
            
        } catch (error) {
            console.error('[WebAudio] 播放音频失败:', error);
            this.isPlaying = false;
        }
    }

    /**
     * 处理音频数据块，直接缓存
     */
    async _processAudioChunks() {
        const validAudioChunks = this.audioChunks.filter(chunk => chunk !== null);

        console.log('[WebAudio] 开始处理音频数据块，有效数据块数量:', validAudioChunks.length);

        if (validAudioChunks.length === 0) {
            console.log('[WebAudio] 没有有效音频数据块，跳过处理');
            return;
        }

        try {
            // 直接缓存音频数据块，不进行任何转换
            console.log('[WebAudio] 音频数据块已缓存，等待处理');
            console.log('[WebAudio] 音频数据块详情:', validAudioChunks.map(chunk => ({
                size: chunk.size,
                type: chunk.type
            })));
        } catch (error) {
            console.error('[WebAudio] 处理音频数据块失败:', error);
        }
    }
    
    /**
     * 处理完整的音频数据（立即执行，不延迟）
     */
    async _finalizeAudio(voiceMessageDiv) {
        // 检查是否已经处理过音频数据
        if (this._audioProcessing) {
            console.log('[WebAudio] 音频数据已经在处理中，跳过重复处理');
            return;
        }

        this._audioProcessing = true;

        try {
            // 立即处理音频数据，不使用异步延迟
            if (this.audioChunks.length > 0) {
                console.log('[WebAudio] 开始处理音频数据，数据块数量:', this.audioChunks.length);

                // 合并所有音频数据块
                const totalSize = this.audioChunks.reduce((sum, chunk) => sum + chunk.size, 0);
                console.log('[WebAudio] 总音频数据大小:', totalSize, 'bytes');

                // 读取所有音频数据块并合并为Uint8Array
                const audioArrays = await Promise.all(
                    this.audioChunks.map(async (chunk) => {
                        const arrayBuffer = await chunk.arrayBuffer();
                        return new Uint8Array(arrayBuffer);
                    })
                );

                const combinedAudio = new Uint8Array(totalSize);
                let offset = 0;
                for (const arr of audioArrays) {
                    combinedAudio.set(arr, offset);
                    offset += arr.length;
                }

                console.log('[WebAudio] PCM音频数据已合并，大小:', combinedAudio.length, 'bytes');

                // 可选：移除过长的静音片段（如果需要更紧凑的播放）
                const removeExcessiveSilence = false; // 设为 true 启用静音移除
                let processedAudio = combinedAudio;
                
                if (removeExcessiveSilence) {
                    console.log('[WebAudio] 开始移除过长静音片段...');
                    processedAudio = this._removeSilence(combinedAudio, 0.2); // 移除超过200ms的静音
                    console.log('[WebAudio] 静音移除完成，原始大小:', combinedAudio.length, '处理后:', processedAudio.length);
                }

                // 服务端现在统一发送裸PCM格式（16kHz/16bit/单声道）
                // 直接创建PCM Blob，无需WAV封装
                const audioBlob = new Blob([processedAudio.buffer], { type: 'audio/pcm' });
                
                // PCM时长 = 数据大小 / (采样率 * 声道数 * 每样本字节数)
                // 16-bit PCM, 16kHz, 单声道: 每秒 = 16000 * 1 * 2 = 32000 字节
                const duration = Math.round(processedAudio.length / 32000);
                console.log('[WebAudio] PCM音频信息:', { dataSize: processedAudio.length, duration, sampleRate: 16000, channels: 1 });

                console.log('[WebAudio] 创建PCM Blob，大小:', audioBlob.size, 'bytes', '类型:', audioBlob.type, '时长:', duration, 's');

                // 更新语音消息的时长
                if (voiceMessageDiv) {
                    const durationElement = voiceMessageDiv.querySelector('.voice-duration');
                    if (durationElement) {
                        const minutes = Math.floor(duration / 60).toString().padStart(2, '0');
                        const seconds = (duration % 60).toString().padStart(2, '0');
                        durationElement.textContent = `${minutes}:${seconds}`;
                        console.log('[WebAudio] 更新语音消息时长:', durationElement.textContent);
                    }
                }

                // 更新语音消息的音频数据
                if (voiceMessageDiv) {
                    const voiceMessage = voiceMessageDiv.querySelector('.voice-message');
                    if (voiceMessage) {
                        // 保存旧的URL，等新的URL设置成功后再清理
                        const oldAudioUrl = voiceMessage.dataset.audioUrl;

                        // 更新语音消息的data-audio-url和data-audio-id属性
                        const audioUrl = URL.createObjectURL(audioBlob);
                        const audioId = `audio-${Date.now()}`;
                        voiceMessage.dataset.audioUrl = audioUrl;
                        voiceMessage.dataset.audioId = audioId;
                        console.log('[WebAudio] 语音消息音频数据已更新（可反复播放）:', { audioUrl, audioId, blobSize: audioBlob.size });

                        // 将完整的音频Blob存储到语音消息对象中，供点击事件使用
                        voiceMessage._fullAudioBlob = audioBlob;
                        console.log('[WebAudio] 完整音频Blob已存储到语音消息元素，支持点击反复播放');

                        // 延迟清理旧的音频URL（确保新的URL已经设置成功）
                        if (oldAudioUrl && oldAudioUrl !== audioUrl) {
                            setTimeout(() => {
                                try {
                                    URL.revokeObjectURL(oldAudioUrl);
                                    console.log('[WebAudio] 清理旧的音频URL:', oldAudioUrl);
                                } catch (error) {
                                    console.error('[WebAudio] 清理旧URL失败:', error);
                                }
                            }, 100);
                        }
                    }
                }
            } else {
                console.log('[WebAudio] 没有音频数据可处理');
            }

        } catch (error) {
            console.error('[WebAudio] 处理音频数据失败:', error);
        } finally {
            // 清理资源
            this._cleanupAudioResources();
            this._audioProcessing = false;
            console.log('[WebAudio] 音频处理完成，资源已清理');
        }
    }

    /**
     * 立即播放音频片段（流式播放 - 优化版）
     * @param {Blob} audioChunk - 音频片段
     */
    async _playAudioChunkImmediately(audioChunk) {
        try {
            const chunkReceiveTime = performance.now();
            
            // 将音频片段加入播放队列
            this._audioQueue.push(audioChunk);
            console.log('[WebAudio] 音频片段加入播放队列，队列长度:', this._audioQueue.length, 
                       '片段大小:', audioChunk.size, 'bytes');

            // 如果没有正在播放，立即开始播放队列
            if (!this._isPlayingQueue) {
                const playStartTime = performance.now();
                const queueDelay = playStartTime - chunkReceiveTime;
                console.log('[WebAudio] 启动播放队列，队列延迟:', queueDelay.toFixed(2), 'ms');
                
                // 不使用 await，让播放在后台进行，避免阻塞后续音频片段的接收
                this._playAudioQueue().catch(error => {
                    console.error('[WebAudio] 播放队列失败:', error);
                });
            } else {
                console.log('[WebAudio] 播放队列正在运行，音频片段已加入队列等待播放');
            }
        } catch (error) {
            console.error('[WebAudio] 播放音频片段失败:', error);
        }
    }

    /**
     * 播放音频队列（边解码边播放，PCM优化版）
     * 收到PCM数据后立即解码并播放，无需等待所有片段
     */
    async _playAudioQueue() {
        if (this._isPlayingQueue) {
            return;
        }

        this._isPlayingQueue = true;

        // 初始化AudioContext
        if (!this.audioContext) {
            this._initWebAudio();
        }

        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
            console.log('[WebAudio] 恢复AudioContext');
        }

        console.log('[WebAudio] 开始播放音频队列（PCM流式模式），初始队列长度:', this._audioQueue.length);

        // 初始化播放调度时间
        let nextStartTime = this.audioContext.currentTime + 0.05; // 50ms初始缓冲
        const sources = [];
        
        // 持续处理队列中的PCM音频片段
        while (this._audioQueue.length > 0) {
            const audioChunk = this._audioQueue.shift();
            console.log('[WebAudio] 处理PCM片段，剩余队列:', this._audioQueue.length);
            
            try {
                // 立即解码PCM数据（无需等待）
                const decodeStartTime = performance.now();
                const audioBuffer = await this._decodeAudioChunk(audioChunk);
                const decodeTime = performance.now() - decodeStartTime;
                
                if (!audioBuffer) {
                    console.warn('[WebAudio] PCM片段解码失败，跳过');
                    continue;
                }
                
                console.log('[WebAudio] PCM片段解码完成，耗时:', decodeTime.toFixed(2), 'ms，时长:', audioBuffer.duration.toFixed(3), 's');
                
                // 创建音频源并立即调度
                const source = this.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                
                const gainNode = this.audioContext.createGain();
                gainNode.gain.value = 1.0;
                source.connect(gainNode);
                gainNode.connect(this.audioContext.destination);
                
                // 计算播放时间（确保无缝衔接）
                const startTime = Math.max(nextStartTime, this.audioContext.currentTime);
                nextStartTime = startTime + audioBuffer.duration;
                
                // 开始播放
                source.start(startTime);
                sources.push({ source, gainNode, startTime, duration: audioBuffer.duration });
                
                console.log('[WebAudio] PCM片段已调度播放，开始时间:', startTime.toFixed(3), '下一片段时间:', nextStartTime.toFixed(3));
                
            } catch (error) {
                console.error('[WebAudio] 处理PCM片段失败:', error);
            }
        }

        // 等待所有音频播放完成
        if (sources.length > 0) {
            const lastSource = sources[sources.length - 1];
            const totalDuration = (lastSource.startTime + lastSource.duration - this.audioContext.currentTime) * 1000;
            
            console.log('[WebAudio] 所有音频片段已调度，共', sources.length, '个片段，总时长:', (totalDuration / 1000).toFixed(3), 's');
            
            // 等待播放完成
            await new Promise(resolve => {
                setTimeout(() => {
                    console.log('[WebAudio] 音频队列播放完成');
                    // 清理资源
                    sources.forEach(({ source, gainNode }) => {
                        try {
                            gainNode.disconnect();
                        } catch (e) {
                            // 忽略断开连接时的错误
                        }
                    });
                    resolve();
                }, Math.max(totalDuration + 100, 100)); // 至少等待100ms
            });
        }

        this._isPlayingQueue = false;
        console.log('[WebAudio] 播放队列已结束');
    }

    /**
     * 解码音频片段（统一PCM解码逻辑）
     * @param {Blob} audioChunk - 音频片段（裸PCM格式）
     * @returns {Promise<AudioBuffer>} - 解码后的AudioBuffer
     */
    async _decodeAudioChunk(audioChunk) {
        const startTime = performance.now();
        const arrayBuffer = await audioChunk.arrayBuffer();
        const readTime = performance.now() - startTime;
        
        if (arrayBuffer.byteLength < 4) {
            console.warn('[WebAudio] 音频数据太小，跳过');
            return null;
        }

        // 服务端现在统一发送裸PCM格式（16kHz/16bit/单声道）
        // 直接使用PCM解码，无需检测WAV头
        let audioBuffer;
        const decodeStartTime = performance.now();
        
        try {
            audioBuffer = await this._createAudioBufferFromPCM(arrayBuffer);
            const decodeTime = performance.now() - decodeStartTime;
            console.log('[WebAudio] PCM解码完成，大小:', arrayBuffer.byteLength, 'bytes，时长:', audioBuffer.duration.toFixed(3), 's，耗时:', decodeTime.toFixed(2), 'ms');
        } catch (error) {
            console.error('[WebAudio] PCM解码失败:', error);
            return null;
        }

        // 验证音频内容（快速检查）
        if (audioBuffer) {
            const channelData = audioBuffer.getChannelData(0);
            let nonZeroCount = 0;
            const checkSamples = Math.min(100, channelData.length);
            for (let i = 0; i < checkSamples; i++) {
                if (Math.abs(channelData[i]) > 0.001) {
                    nonZeroCount++;
                }
            }
            
            if (nonZeroCount === 0) {
                console.warn('[WebAudio] 警告：音频片段可能是静音（前', checkSamples, '个样本全为0）');
            }
        }

        return audioBuffer;
    }

    /**
     * 从PCM数据创建AudioBuffer
     * @param {ArrayBuffer} pcmData - PCM数据
     * @returns {Promise<AudioBuffer>} - AudioBuffer
     */
    async _createAudioBufferFromPCM(pcmData) {
        if (!this.audioContext) {
            this._initWebAudio();
        }

        const sampleRate = 16000;
        const channels = 1;
        const bitDepth = 16;
        
        const sampleCount = pcmData.byteLength / (bitDepth / 8);
        const audioBuffer = this.audioContext.createBuffer(
            channels,
            sampleCount,
            sampleRate
        );
        
        const pcmArray = new Int16Array(pcmData);
        for (let channel = 0; channel < channels; channel++) {
            const channelData = audioBuffer.getChannelData(channel);
            for (let i = 0; i < sampleCount; i++) {
                channelData[i] = pcmArray[i] / 32768;
            }
        }
        
        return audioBuffer;
    }

    /**
     * 播放单个音频片段（已废弃，保留用于兼容）
     * @deprecated 请使用预调度播放模式
     */
    async _playSingleAudioChunk(audioChunk) {
        console.warn('[WebAudio] _playSingleAudioChunk已废弃，请使用预调度播放模式');
        const audioBuffer = await this._decodeAudioChunk(audioChunk);
        if (!audioBuffer) return;

        return new Promise((resolve) => {
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            const gainNode = this.audioContext.createGain();
            gainNode.gain.value = 1.0;
            source.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            source.onended = () => {
                gainNode.disconnect();
                resolve();
            };
            
            source.start();
            
            setTimeout(() => {
                gainNode.disconnect();
                resolve();
            }, audioBuffer.duration * 1000 + 50);
        });
    }

    /**
     * 移除PCM数据中过长的静音片段
     * @param {Uint8Array} pcmData - PCM数据
     * @param {number} maxSilenceDuration - 最大允许的静音时长（秒）
     * @returns {Uint8Array} - 处理后的PCM数据
     */
    _removeSilence(pcmData, maxSilenceDuration = 0.2) {
        const sampleRate = 16000;
        const bytesPerSample = 2;
        const silenceThreshold = 100; // 振幅阈值
        const maxSilenceSamples = Math.floor(maxSilenceDuration * sampleRate);
        
        const dataView = new DataView(pcmData.buffer, pcmData.byteOffset, pcmData.byteLength);
        const totalSamples = Math.floor(pcmData.length / bytesPerSample);
        
        // 第一遍：标记需要保留的样本
        const keepSamples = new Array(totalSamples).fill(false);
        let consecutiveSilent = 0;
        let silentStart = -1;
        
        for (let i = 0; i < totalSamples; i++) {
            const sample = dataView.getInt16(i * bytesPerSample, true);
            const isSilent = Math.abs(sample) < silenceThreshold;
            
            if (isSilent) {
                if (silentStart === -1) {
                    silentStart = i;
                }
                consecutiveSilent++;
            } else {
                // 遇到非静音样本
                if (silentStart !== -1) {
                    // 决定是否保留这段静音
                    const silentDuration = consecutiveSilent;
                    if (silentDuration <= maxSilenceSamples) {
                        // 保留短静音
                        for (let j = silentStart; j < i; j++) {
                            keepSamples[j] = true;
                        }
                    } else {
                        // 只保留最大允许长度的静音
                        const keepStart = i - maxSilenceSamples;
                        for (let j = keepStart; j < i; j++) {
                            keepSamples[j] = true;
                        }
                    }
                    silentStart = -1;
                    consecutiveSilent = 0;
                }
                keepSamples[i] = true;
            }
        }
        
        // 第二遍：构建新的PCM数据
        const keptSamples = keepSamples.filter(k => k).length;
        const newPcmData = new Uint8Array(keptSamples * bytesPerSample);
        const newDataView = new DataView(newPcmData.buffer);
        
        let writeIndex = 0;
        for (let i = 0; i < totalSamples; i++) {
            if (keepSamples[i]) {
                const sample = dataView.getInt16(i * bytesPerSample, true);
                newDataView.setInt16(writeIndex * bytesPerSample, sample, true);
                writeIndex++;
            }
        }
        
        return newPcmData;
    }

    /**
     * 清理音频资源
     */
    _cleanupAudioResources() {
        // 清理音频数据
        this.audioChunks = [];
        this.allPcmChunks = [];
        
        // 停止音频播放
        if (this.currentSource) {
            try {
                this.currentSource.stop();
                this.currentSource.disconnect();
            } catch (error) {
                // 忽略错误
            }
            this.currentSource = null;
        }
        
        // 清理音频URL
        if (this.currentAudioUrl) {
            try {
                URL.revokeObjectURL(this.currentAudioUrl);
            } catch (error) {
                // 忽略错误
            }
            this.currentAudioUrl = null;
        }
        
        // 清理音频元素
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.src = '';
            this.currentAudio = null;
        }
        
        // 清理定时器
        if (this.audioTimer) {
            clearInterval(this.audioTimer);
            this.audioTimer = null;
        }
        
        // 清理播放队列
        this._audioQueue = [];
        this._isPlayingQueue = false;
        
        // 重置状态
        this.isPlaying = false;
        this._audioProcessing = false;
        this.voiceMessageDiv = null;
        this.audioDuration = 0;
    }
}

// 导出AudioModule类
export { AudioModule };