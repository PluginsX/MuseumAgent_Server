/**
 * 音频管理器
 * 封装音频录制、播放、VAD 等功能
 */

// ==================== 流式音频播放器 ====================
class StreamingAudioPlayer {
    constructor(audioContext) {
        this.audioContext = audioContext;
        this.sampleRate = 16000;
        this.currentMessageId = null;
        this.isPlaying = false;
        this.isStopped = false;
        this.audioQueue = [];
        this.isProcessing = false;
        this.nextStartTime = 0;
        this.startTime = 0;
        this.activeSources = [];
    }
    
    startMessage(messageId) {
        if (this.currentMessageId && this.currentMessageId !== messageId) {
            this.stop();
        }
        
        this.currentMessageId = messageId;
        this.isPlaying = false;
        this.isStopped = false;
        this.audioQueue = [];
        this.isProcessing = false;
        this.nextStartTime = 0;
        this.activeSources = [];
    }
    
    addChunk(messageId, pcmData) {
        if (messageId !== this.currentMessageId) return;
        if (this.isStopped) return;
        
        this.audioQueue.push(pcmData);
        
        if (!this.isPlaying) {
            this.start();
        }
        
        this.processQueue();
    }
    
    start() {
        if (this.isPlaying || this.isStopped) return;
        
        this.isPlaying = true;
        this.startTime = this.audioContext.currentTime;
        this.nextStartTime = this.startTime;
    }
    
    async processQueue() {
        if (this.isProcessing || this.isStopped) return;
        
        this.isProcessing = true;
        
        while (this.audioQueue.length > 0 && !this.isStopped) {
            const pcmData = this.audioQueue.shift();
            
            try {
                const audioBuffer = this.audioContext.createBuffer(
                    1,
                    pcmData.byteLength / 2,
                    this.sampleRate
                );
                
                const channelData = audioBuffer.getChannelData(0);
                const pcmArray = new Int16Array(pcmData);
                
                for (let i = 0; i < pcmArray.length; i++) {
                    channelData[i] = pcmArray[i] / 32768;
                }
                
                const source = this.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(this.audioContext.destination);
                
                this.activeSources.push(source);
                
                source.onended = () => {
                    const index = this.activeSources.indexOf(source);
                    if (index > -1) {
                        this.activeSources.splice(index, 1);
                    }
                };
                
                const now = this.audioContext.currentTime;
                const startTime = Math.max(now, this.nextStartTime);
                
                source.start(startTime);
                this.nextStartTime = startTime + audioBuffer.duration;
                
            } catch (error) {
                console.error('[StreamingAudioPlayer] 播放失败:', error);
            }
        }
        
        this.isProcessing = false;
    }
    
    endMessage(messageId) {
        if (messageId !== this.currentMessageId) return;
        this.processQueue();
    }
    
    stop() {
        if (this.isStopped) return;
        
        for (const source of this.activeSources) {
            try {
                source.stop();
                source.disconnect();
            } catch (error) {
                // 忽略
            }
        }
        
        this.activeSources = [];
        this.isStopped = true;
        this.isPlaying = false;
        this.audioQueue = [];
        this.currentMessageId = null;
    }
    
    reset() {
        this.stop();
        this.isStopped = false;
    }
}

// ==================== 音频管理器 ====================
export class AudioManager {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.audioWorkletNode = null;
        this.isRecording = false;
        
        // VAD 相关
        this.vadEnabled = false;
        this.vadParams = null;
        this.vadState = {
            isSpeaking: false,
            silenceStart: null,
            speechStart: null,
            audioBuffer: []
        };
        
        // 播放相关
        this.streamingPlayer = null;
        this.currentSource = null;
        this.currentPlayingMessageId = null;
    }
    
    /**
     * 初始化音频上下文
     */
    async init() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });
            
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
            
            this.streamingPlayer = new StreamingAudioPlayer(this.audioContext);
        }
        
        if (this.audioContext && this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
    }

    /**
     * 开始录音
     */
    async startRecording(onDataCallback) {
        await this.init();

        try {
            // 检查浏览器是否支持媒体设备API
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('浏览器不支持录音功能或需要HTTPS连接');
            }

            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // 加载 AudioWorklet 处理器
            const processorUrl = new URL('./vad-processor.js', import.meta.url);
            await this.audioContext.audioWorklet.addModule(processorUrl);

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            const workletNode = new AudioWorkletNode(this.audioContext, 'vad-processor');
            
            // 监听来自 AudioWorklet 的消息
            workletNode.port.onmessage = (event) => {
                const { type, data } = event.data;
                
                if (type === 'audioData' && onDataCallback) {
                    onDataCallback(data);
                }
            };
            
            // 初始化 AudioWorklet（非 VAD 模式）
            workletNode.port.postMessage({
                type: 'init',
                data: {
                    vadEnabled: false,
                    vadParams: null
                }
            });

            source.connect(workletNode);
            workletNode.connect(this.audioContext.destination);

            this.audioWorkletNode = workletNode;
            this.isRecording = true;
            this.vadEnabled = false;

        } catch (error) {
            console.error('[AudioManager] 录音启动失败:', error);
            throw error;
        }
    }

    /**
     * 开始录音（启用 VAD）
     */
    async startRecordingWithVAD(vadParams, onSpeechStart, onAudioData, onSpeechEnd) {
        await this.init();

        this.vadParams = vadParams;
        this.vadEnabled = true;
        this.vadState = {
            isSpeaking: false,
            silenceStart: null,
            speechStart: null,
            audioBuffer: [],
            speechStartCallback: onSpeechStart,
            audioDataCallback: onAudioData,
            speechEndCallback: onSpeechEnd
        };

        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // 加载 AudioWorklet 处理器
            const processorUrl = new URL('./vad-processor.js', import.meta.url);
            await this.audioContext.audioWorklet.addModule(processorUrl);

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            const workletNode = new AudioWorkletNode(this.audioContext, 'vad-processor');
            
            // 监听来自 AudioWorklet 的消息
            workletNode.port.onmessage = (event) => {
                const { type, data } = event.data;
                
                if (type === 'speechStart' && onSpeechStart) {
                    onSpeechStart();
                } else if (type === 'audioData' && onAudioData) {
                    onAudioData(data);
                } else if (type === 'speechEnd' && onSpeechEnd) {
                    onSpeechEnd();
                }
            };
            
            // 初始化 AudioWorklet（VAD 模式）
            workletNode.port.postMessage({
                type: 'init',
                data: {
                    vadEnabled: true,
                    vadParams: vadParams
                }
            });

            source.connect(workletNode);
            workletNode.connect(this.audioContext.destination);

            this.audioWorkletNode = workletNode;
            this.isRecording = true;

        } catch (error) {
            console.error('[AudioManager] 录音启动失败:', error);
            throw error;
        }
    }

    /**
     * 停止录音
     */
    stopRecording() {
        this.isRecording = false;

        if (this.audioWorkletNode) {
            // 通知 AudioWorklet 停止
            this.audioWorkletNode.port.postMessage({
                type: 'stop'
            });
            
            this.audioWorkletNode.disconnect();
            this.audioWorkletNode = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
    }

    /**
     * 播放 PCM 音频
     */
    async playPCM(pcmData, sampleRate = 16000) {
        await this.init();

        try {
            if (this.currentSource) {
                this.currentSource.stop();
                this.currentSource = null;
            }

            const audioBuffer = this.audioContext.createBuffer(
                1,
                pcmData.byteLength / 2,
                sampleRate
            );

            const channelData = audioBuffer.getChannelData(0);
            const pcmArray = new Int16Array(pcmData);

            for (let i = 0; i < pcmArray.length; i++) {
                channelData[i] = pcmArray[i] / 32768;
            }

            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            this.currentSource = source;

            return new Promise((resolve) => {
                source.onended = () => {
                    this.currentSource = null;
                    resolve();
                };
                source.start();
            });

        } catch (error) {
            console.error('[AudioManager] 播放失败:', error);
            throw error;
        }
    }

    /**
     * 开始流式播放
     */
    async startStreamingMessage(messageId) {
        try {
            await this.init();
        } catch (error) {
            console.error('[AudioManager] 初始化失败:', error);
            return false;
        }
        
        if (!this.streamingPlayer) {
            return false;
        }
        
        if (this.currentPlayingMessageId && this.currentPlayingMessageId !== messageId) {
            this.streamingPlayer.stop();
        }
        
        this.streamingPlayer.startMessage(messageId);
        this.currentPlayingMessageId = messageId;
        
        return true;
    }
    
    /**
     * 添加音频块
     */
    async addStreamingChunk(messageId, pcmData) {
        if (!this.streamingPlayer) {
            try {
                await this.init();
            } catch (error) {
                console.error('[AudioManager] 初始化失败:', error);
                return;
            }
        }
        
        if (!this.streamingPlayer) return;
        
        this.streamingPlayer.addChunk(messageId, pcmData);
    }
    
    /**
     * 结束流式消息
     */
    endStreamingMessage(messageId) {
        if (!this.streamingPlayer) return;
        
        this.streamingPlayer.endMessage(messageId);
        
        if (this.currentPlayingMessageId === messageId) {
            this.currentPlayingMessageId = null;
        }
    }
    
    /**
     * 停止所有播放
     */
    stopAllPlayback() {
        if (this.streamingPlayer) {
            this.streamingPlayer.stop();
        }
        
        if (this.currentSource) {
            this.currentSource.stop();
            this.currentSource = null;
        }
        
        this.currentPlayingMessageId = null;
    }

    /**
     * 清理资源
     */
    cleanup() {
        this.stopRecording();
        this.stopAllPlayback();

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        this.streamingPlayer = null;
    }
}

