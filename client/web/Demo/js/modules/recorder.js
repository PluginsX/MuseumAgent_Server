/**
 * 录音模块
 * 处理音频录制、流式传输等功能
 * 集成 VAD (Voice Activity Detection) 语音活动检测
 */
class RecorderModule {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recordStartTime = 0;
        this.recordTimer = null;
        this.isRecording = false;
        this.streamWs = null;
        this.client = null;
        
        // VAD 相关
        this.vadModule = null;
        this.vadEnabled = false;
        this.isVoiceActive = false;
        this.vadStats = {
            totalTime: 0,
            voiceTime: 0,
            silenceTime: 0
        };
    }
    
    /**
     * 获取录音开始时间
     * @returns {number} - 录音开始时间戳
     */
    getRecordStartTime() {
        return this.recordStartTime;
    }

    /**
     * 初始化录音模块
     * @param {Object} client - MuseumAgent客户端实例
     * @param {Object} vadModule - VAD模块实例（可选）
     */
    init(client, vadModule = null) {
        this.client = client;
        this.vadModule = vadModule;
        
        if (this.vadModule) {
            console.log('[Recorder] VAD模块已集成');
        }
    }
    
    /**
     * 设置VAD配置
     * @param {Object} config - VAD配置
     */
    setVADConfig(config) {
        this.vadEnabled = config.enabled || false;
        
        if (this.vadModule) {
            this.vadModule.updateConfig(config);
        }
        
        console.log('[Recorder] VAD配置已更新:', config);
    }

    /**
     * 开始录音
     * @returns {Promise<void>}
     */
    async startRecording() {
        if (!this.client) {
            console.error('客户端未初始化');
            throw new Error('客户端未初始化');
        }

        // 检查会话状态
        if (!this.client.sessionId) {
            console.error('会话未注册，请先登录');
            throw new Error('会话未注册，请先登录');
        }

        try {
            // 🔧 优化：获取麦克风权限，配置为16k/16bit/单声道
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,        // 单声道
                    sampleRate: 16000,      // 16kHz采样率
                    sampleSize: 16,         // 16bit采样位数
                    echoCancellation: true, // 回声消除
                    noiseSuppression: true, // 噪声抑制
                    autoGainControl: true   // 自动增益
                }
            });
            
            console.log('[Recorder] 音频流配置:', {
                channelCount: 1,
                sampleRate: 16000,
                sampleSize: 16
            });
            
            // 🔧 优化：使用AudioContext直接采集PCM数据
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000  // 强制16kHz采样率
            });
            
            this.mediaStreamSource = this.audioContext.createMediaStreamSource(stream);
            this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
            
            // 连接音频处理节点
            this.mediaStreamSource.connect(this.scriptProcessor);
            this.scriptProcessor.connect(this.audioContext.destination);
            
            this.audioChunks = [];
            this.recordStartTime = Date.now();
            this.isRecording = true;
            this.stream = stream;

            // 开始计时
            this.startRecordTimer();

            // 获取WebSocket连接
            this.streamWs = this.client.getCurrentWebSocket();
            
            if (!this.streamWs) {
                console.log('没有找到现有的WebSocket连接，创建一个新的连接');
                const savedUsername = localStorage.getItem('museumAgent_username');
                const savedPassword = localStorage.getItem('museumAgent_password');
                
                if (!savedUsername || !savedPassword) {
                    console.error('缺少认证信息，请重新登录');
                    throw new Error('缺少认证信息，请重新登录');
                }
                
                const authData = {
                    type: 'ACCOUNT',
                    account: savedUsername,
                    password: savedPassword
                };
                
                this.streamWs = await this.client.connectAgentStream(authData);
            } else {
                console.log('使用现有的WebSocket连接');
            }
            
            if (!this.client.sessionId) {
                console.error('会话未注册，无法发送语音数据');
                throw new Error('会话未注册，请先登录');
            }
            
            await new Promise(resolve => setTimeout(resolve, 500));
            console.log('会话注册完成，准备开始语音传输');
            
            try {
                await this.client.querySessionInfo([]);
                console.log('会话验证成功');
            } catch (error) {
                console.error('会话验证失败:', error);
                throw new Error('会话已失效，请重新登录');
            }
            
            // 初始化VAD（如果启用）
            if (this.vadEnabled && this.vadModule) {
                try {
                    // 从UI读取VAD配置
                    const vadConfig = this._getVADConfigFromUI();
                    
                    await this.vadModule.init(stream, vadConfig);
                    
                    // 设置VAD回调
                    this.vadModule.onVoiceStart = () => {
                        console.log('[Recorder] VAD: 检测到语音，开始采集');
                        this.isVoiceActive = true;
                        this._updateVADStatus('voice');
                    };
                    
                    this.vadModule.onVoiceEnd = async () => {
                        console.log('[Recorder] VAD: 检测到静音，停止采集');
                        this.isVoiceActive = false;
                        this._updateVADStatus('silence');
                        
                        // 创建语音气泡，记录用户有效发出的语音消息
                        await this._createVoiceMessageBubble();
                    };
                    
                    this.vadModule.start();
                    console.log('[Recorder] VAD已启动');
                } catch (error) {
                    console.error('[Recorder] VAD初始化失败，继续使用普通录音:', error);
                    this.vadEnabled = false;
                }
            }
            
            // 🔧 优化：使用ScriptProcessor采集PCM数据并实时发送
            this.scriptProcessor.onaudioprocess = async (audioProcessingEvent) => {
                if (!this.isRecording) return;
                
                // VAD检测：如果启用VAD且当前无语音活动，跳过采集
                if (this.vadEnabled && !this.isVoiceActive) {
                    console.log('[Recorder] VAD: 静音中，跳过采集');
                    return;
                }
                
                // 获取PCM数据（Float32Array，范围-1.0到1.0）
                const inputBuffer = audioProcessingEvent.inputBuffer;
                const pcmFloat32 = inputBuffer.getChannelData(0);
                
                // 🔍 调试：检查音频数据
                let maxAmplitude = 0;
                let nonZeroCount = 0;
                for (let i = 0; i < pcmFloat32.length; i++) {
                    if (pcmFloat32[i] !== 0) nonZeroCount++;
                    maxAmplitude = Math.max(maxAmplitude, Math.abs(pcmFloat32[i]));
                }
                
                console.log('[Recorder] Audio data analysis:', {
                    samples: pcmFloat32.length,
                    nonZero: nonZeroCount,
                    maxAmplitude: maxAmplitude.toFixed(4),
                    isSilent: maxAmplitude < 0.01,
                    vadActive: this.vadEnabled ? this.isVoiceActive : 'N/A'
                });
                
                // 转换为16bit PCM（Int16Array）
                const pcmInt16 = new Int16Array(pcmFloat32.length);
                for (let i = 0; i < pcmFloat32.length; i++) {
                    // 将Float32 [-1.0, 1.0] 转换为 Int16 [-32768, 32767]
                    const s = Math.max(-1, Math.min(1, pcmFloat32[i]));
                    pcmInt16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                
                // 🔍 调试：检查转换后的PCM数据
                console.log('[Recorder] PCM Int16 samples (first 10):', Array.from(pcmInt16.slice(0, 10)));
                
                // 创建Blob（原始PCM数据）
                // ⚠️ 重要：必须使用 pcmInt16 而不是 pcmInt16.buffer，避免包含额外字节
                const pcmBlob = new Blob([pcmInt16], { type: 'audio/pcm' });
                this.audioChunks.push(pcmBlob);
                
                // 🔧 实时发送PCM数据块（每4096样本约256ms）
                await this.sendAudioChunk(pcmBlob);
            };
            
            console.log('[Recorder] PCM录音已开始，采样率: 16kHz, 位深: 16bit, 声道: 单声道');
        } catch (error) {
            console.error(`开始语音失败: ${error.message}`);
            this.isRecording = false;
            this.stopRecordTimer();
            throw error;
        }
    }

    /**
     * 停止录音
     * @returns {Promise<Blob|null>} - 完整的音频文件
     */
    async stopRecording() {
        this.isRecording = false;
        this.stopRecordTimer();
        
        // 停止VAD
        if (this.vadModule) {
            // 清除VAD回调函数
            this.vadModule.onVoiceStart = null;
            this.vadModule.onVoiceEnd = null;
            this.vadModule.onVoiceActivity = null;
            
            // 暂停并销毁VAD处理器
            this.vadModule.pause();
            this.vadModule.destroy();
            
            // 显示VAD统计信息
            const stats = this.vadModule.getStats();
            console.log('[Recorder] VAD统计:', stats);
            
            // 重置VAD相关状态
            this.isVoiceActive = false;
            this.vadEnabled = false;
        }
        
        // 🔧 优化：清理AudioContext资源
        if (this.scriptProcessor) {
            // 断开事件监听器
            this.scriptProcessor.onaudioprocess = null;
            this.scriptProcessor.disconnect();
            this.scriptProcessor = null;
        }
        
        if (this.mediaStreamSource) {
            this.mediaStreamSource.disconnect();
            this.mediaStreamSource = null;
        }
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }
        
        console.log('[Recorder] PCM录音已停止');
        
        // 组合缓存的PCM数据成完整的音频文件
        if (this.audioChunks.length > 0) {
            try {
                // 🔧 创建WAV格式的音频文件（PCM编码，16k/16bit/单声道）
                const audioBlob = this._createWavBlob(this.audioChunks);
                console.log('[Recorder] 完整WAV音频文件已创建:', audioBlob.size, 'bytes');
                
                // 重置缓存
                this.audioChunks = [];
                
                return audioBlob;
            } catch (error) {
                console.error('[Recorder] 创建完整音频文件失败:', error);
                return null;
            }
        }
        
        return null;
    }
    
    /**
     * 从UI读取VAD配置
     * @private
     */
    _getVADConfigFromUI() {
        return {
            enabled: document.getElementById('vadEnabled')?.checked || false,
            silenceDuration: parseInt(document.getElementById('vadSilenceDuration')?.value || '1000'),
            positiveSpeechThreshold: parseFloat(document.getElementById('vadPositiveThreshold')?.value || '0.5'),
            negativeSpeechThreshold: parseFloat(document.getElementById('vadNegativeThreshold')?.value || '0.35'),
            preSpeechPadFrames: parseInt(document.getElementById('vadPreSpeechPad')?.value || '1'),
            redemptionFrames: parseInt(document.getElementById('vadRedemptionFrames')?.value || '8'),
            minSpeechFrames: parseInt(document.getElementById('vadMinSpeechFrames')?.value || '3')
        };
    }
    
    /**
     * 更新VAD状态显示
     * @private
     */
    _updateVADStatus(status) {
        const vadStatusElement = document.getElementById('vadStatus');
        if (vadStatusElement) {
            if (status === 'voice') {
                vadStatusElement.textContent = '🎤 检测到语音';
                vadStatusElement.className = 'vad-status vad-active';
            } else {
                vadStatusElement.textContent = '🔇 静音中';
                vadStatusElement.className = 'vad-status vad-inactive';
            }
        }
    }
    
    /**
     * 创建语音气泡，记录用户有效发出的语音消息
     * @private
     */
    async _createVoiceMessageBubble() {
        // 检查录音是否仍在进行中
        if (!this.isRecording) {
            console.log('[Recorder] 录音已停止，跳过创建语音气泡');
            return;
        }
        
        // 检查是否有音频数据
        if (this.audioChunks.length === 0) {
            console.log('[Recorder] 没有音频数据，跳过创建语音气泡');
            return;
        }
        
        try {
            // 创建WAV格式的音频文件
            const audioBlob = this._createWavBlob(this.audioChunks);
            console.log('[Recorder] 语音消息音频已创建:', audioBlob.size, 'bytes');
            
            // 计算音频时长（16kHz采样率，16bit位深，单声道）
            const duration = (audioBlob.size - 44) / (16000 * 2); // 44是WAV头大小，2是每样本字节数
            console.log('[Recorder] 语音消息时长:', duration.toFixed(2), '秒');
            
            // 创建语音气泡
            if (window.chatModule) {
                const messageElement = window.chatModule.addMessage('sent', null, audioBlob, duration, {
                    showPlayButton: true,
                    autoPlay: false
                });
                console.log('[Recorder] 语音气泡已创建:', messageElement);
            } else {
                console.error('[Recorder] chatModule 未初始化，无法创建语音气泡');
            }
            
            // 重置音频数据缓存
            this.audioChunks = [];
        } catch (error) {
            console.error('[Recorder] 创建语音气泡失败:', error);
        }
    }
    
    /**
     * 创建WAV格式的Blob（PCM编码）
     * @param {Array<Blob>} pcmChunks - PCM数据块数组
     * @returns {Blob} - WAV格式的Blob
     */
    _createWavBlob(pcmChunks) {
        // 合并所有PCM数据块
        const pcmBuffers = [];
        let totalLength = 0;
        
        pcmChunks.forEach(chunk => {
            // 注意：chunk是Blob，需要同步读取（这里我们直接返回原始PCM）
            totalLength += chunk.size;
        });
        
        // 创建WAV文件头（44字节）
        const sampleRate = 16000;
        const numChannels = 1;
        const bitsPerSample = 16;
        const byteRate = sampleRate * numChannels * bitsPerSample / 8;
        const blockAlign = numChannels * bitsPerSample / 8;
        const dataSize = totalLength;
        const fileSize = 36 + dataSize;
        
        const wavHeader = new ArrayBuffer(44);
        const view = new DataView(wavHeader);
        
        // RIFF chunk descriptor
        this._writeString(view, 0, 'RIFF');
        view.setUint32(4, fileSize, true);
        this._writeString(view, 8, 'WAVE');
        
        // fmt sub-chunk
        this._writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true); // Sub-chunk size
        view.setUint16(20, 1, true);  // Audio format (PCM)
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, byteRate, true);
        view.setUint16(32, blockAlign, true);
        view.setUint16(34, bitsPerSample, true);
        
        // data sub-chunk
        this._writeString(view, 36, 'data');
        view.setUint32(40, dataSize, true);
        
        // 合并WAV头和PCM数据
        return new Blob([wavHeader, ...pcmChunks], { type: 'audio/wav' });
    }
    
    /**
     * 向DataView写入字符串
     */
    _writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }

    /**
     * 发送音频数据块（PCM格式）
     * @param {Blob} audioChunk - PCM音频数据块
     * @returns {Promise<void>}
     */
    async sendAudioChunk(audioChunk) {
        if (!this.streamWs || !this.client) {
            console.error('[Recorder] WebSocket连接或客户端未初始化');
            return;
        }

        if (!this.client.sessionId) {
            console.error('[Recorder] 会话未注册，无法发送语音数据');
            return;
        }

        try {
            const enableTTS = document.getElementById('enableTTS')?.checked || false;

            // 🔧 优化：发送PCM数据，使用voiceMode='PCM'
            await this.client.sendVoiceRequest(
                this.streamWs,
                audioChunk,
                (chunk) => {
                    // 实时更新消息内容
                    const lastMessage = document.querySelector('.message.received:last-child .message-content');
                    if (lastMessage) {
                        lastMessage.textContent += chunk;
                    } else {
                        const chatModule = window.chatModule;
                        if (chatModule) {
                            chatModule.addMessage('received', chunk);
                        }
                    }
                },
                (data) => {
                    console.log('[Recorder] 语音流式生成完成');
                },
                { 
                    enableTTS,
                    voiceMode: 'BASE64',  // 使用BASE64传输PCM数据
                    audioFormat: 'pcm',   // 标记为PCM格式
                    sampleRate: 16000,    // 16kHz
                    channels: 1,          // 单声道
                    bitDepth: 16          // 16bit
                }
            );
        } catch (error) {
            console.error(`[Recorder] 发送语音数据块失败: ${error.message}`);
            if (error.message.includes('SESSION_INVALID') || error.message.includes('会话不存在或已超时')) {
                console.error('[Recorder] 会话已失效，请重新登录');
            }
        }
    }

    /**
     * 开始录音计时器
     */
    startRecordTimer() {
        this.stopRecordTimer(); // 先停止之前的计时器
        
        this.recordTimer = setInterval(() => {
            const recordTime = document.getElementById('recordTime');
            if (recordTime) {
                const elapsed = Math.floor((Date.now() - this.recordStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
                const seconds = (elapsed % 60).toString().padStart(2, '0');
                recordTime.textContent = `${minutes}:${seconds}`;
            }
        }, 1000);
    }

    /**
     * 停止录音计时器
     */
    stopRecordTimer() {
        if (this.recordTimer) {
            clearInterval(this.recordTimer);
            this.recordTimer = null;
        }
    }

    /**
     * 重置录音状态
     */
    resetState() {
        this.stopRecording();
        this.audioChunks = [];
        this.recordStartTime = 0;
        this.streamWs = null;
    }

    /**
     * 检查是否正在录音
     * @returns {boolean} - 是否正在录音
     */
    getIsRecording() {
        return this.isRecording;
    }

    /**
     * 转换webm到mp3格式（已废弃，保留用于兼容）
     * @deprecated 现在直接采集PCM数据，无需转换
     * @param {Blob} webmBlob - webm格式的音频
     * @returns {Promise<Blob>} - mp3格式的音频
     */
    async convertWebmToMp3(webmBlob) {
        console.log('开始转换webm到mp3');
        
        try {
            const arrayBuffer = await webmBlob.arrayBuffer();
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            
            const channels = audioBuffer.numberOfChannels;
            const originalSampleRate = audioBuffer.sampleRate;
            const targetSampleRate = 16000;
            const samples = audioBuffer.length;
            
            console.log(`原始采样率: ${originalSampleRate}Hz, 目标采样率: ${targetSampleRate}Hz`);
            
            let resampledBuffer = audioBuffer;
            
            if (originalSampleRate !== targetSampleRate) {
                console.log(`重采样: ${originalSampleRate}Hz -> ${targetSampleRate}Hz`);
                
                const offlineContext = new OfflineAudioContext(
                    channels,
                    samples * targetSampleRate / originalSampleRate,
                    targetSampleRate
                );
                
                const source = offlineContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(offlineContext.destination);
                source.start();
                
                resampledBuffer = await offlineContext.startRendering();
            }
            
            const mp3encoder = new lamejs.Mp3Encoder(channels, targetSampleRate, 128);
            const mp3Data = [];
            
            const resampledSamples = resampledBuffer.length;
            const left = new Int16Array(resampledSamples);
            const right = new Int16Array(resampledSamples);
            
            for (let i = 0; i < resampledSamples; i++) {
                const leftSample = Math.max(-1, Math.min(1, resampledBuffer.getChannelData(0)[i]));
                left[i] = leftSample < 0 ? leftSample * 0x8000 : leftSample * 0x7FFF;
                
                if (channels === 2) {
                    const rightSample = Math.max(-1, Math.min(1, resampledBuffer.getChannelData(1)[i]));
                    right[i] = rightSample < 0 ? rightSample * 0x8000 : rightSample * 0x7FFF;
                }
            }
            
            const blockSize = 1152;
            for (let i = 0; i < resampledSamples; i += blockSize) {
                const leftChunk = left.subarray(i, i + blockSize);
                const rightChunk = right.subarray(i, i + blockSize);
                const mp3buf = mp3encoder.encodeBuffer(leftChunk, rightChunk);
                if (mp3buf.length > 0) {
                    mp3Data.push(mp3buf);
                }
            }
            
            const mp3buf = mp3encoder.flush();
            if (mp3buf.length > 0) {
                mp3Data.push(mp3buf);
            }
            
            const mp3Blob = new Blob(mp3Data, { type: 'audio/mp3' });
            console.log(`转换完成: ${webmBlob.size} bytes -> ${mp3Blob.size} bytes`);
            
            return mp3Blob;
        } catch (error) {
            console.error(`转换失败: ${error.message}`);
            throw error;
        }
    }
}

// 导出单例实例
export const recorderModule = new RecorderModule();
