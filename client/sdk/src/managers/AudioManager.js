/**
 * 音频管理器
 * 封装音频录制、播放、VAD 等功能
 *
 * v2.1 AEC修复：
 * - AudioContext 使用浏览器默认采样率（通常48kHz），确保Chrome硬件AEC正常工作
 * - 录音侧：getUserMedia 不约束 sampleRate，让AEC在原生采样率下对齐参考信号
 *   在 vad-processor.js（AudioWorklet）内部完成 nativeSampleRate→16kHz 的降采样
 * - 播放侧：StreamingAudioPlayer 将服务器下发的16kHz PCM升采样到 nativeSampleRate 再播放
 *   保证扬声器输出和麦克风采集全程在同一采样率下，AEC参考信号时序完全对齐
 */

// ==================== 线性插值重采样工具 ====================
/**
 * 将 Float32Array 从 fromRate 线性插值重采样到 toRate
 * 用于播放侧：16000 → nativeSampleRate（升采样）
 */
function resampleLinear(input, fromRate, toRate) {
    if (fromRate === toRate) return input;
    const outputLength = Math.round(input.length * toRate / fromRate);
    const output = new Float32Array(outputLength);
    const ratio = fromRate / toRate;
    for (let i = 0; i < outputLength; i++) {
        const pos = i * ratio;
        const idx = Math.floor(pos);
        const frac = pos - idx;
        const a = input[idx] !== undefined ? input[idx] : 0;
        const b = input[idx + 1] !== undefined ? input[idx + 1] : a;
        output[i] = a + frac * (b - a);
    }
    return output;
}

// ==================== 流式音频播放器 ====================
class StreamingAudioPlayer {
    constructor(audioContext) {
        this.audioContext = audioContext;
        this.sourceSampleRate = 16000;                    // 服务器下发的PCM采样率
        this.nativeSampleRate = audioContext.sampleRate;  // AudioContext原生采样率（通常48000）
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
                // 1. 将服务器16kHz Int16 PCM 解码为 Float32
                const pcmArray = new Int16Array(pcmData);
                const float32At16k = new Float32Array(pcmArray.length);
                for (let i = 0; i < pcmArray.length; i++) {
                    float32At16k[i] = pcmArray[i] / 32768;
                }

                // 2. 升采样到 AudioContext 原生采样率（保证 AEC 参考信号与麦克风采集同频）
                const float32Native = resampleLinear(
                    float32At16k,
                    this.sourceSampleRate,
                    this.nativeSampleRate
                );

                // 3. 按原生采样率创建 AudioBuffer 并播放
                const audioBuffer = this.audioContext.createBuffer(
                    1,
                    float32Native.length,
                    this.nativeSampleRate
                );
                audioBuffer.getChannelData(0).set(float32Native);

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
        this.nativeSampleRate = null;  // AudioContext 实际采样率（由浏览器决定，通常48000）
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
     * ✅ 不传 sampleRate，让 AudioContext 使用浏览器/系统原生采样率（通常48kHz）
     * 这是 Chrome 硬件 AEC 正常工作的前提条件：
     * AEC算法需要扬声器输出（参考信号）与麦克风输入在同一采样率下才能正确对齐
     */
    async init() {
        if (!this.audioContext) {
            // ✅ 关键修复：不强制指定 sampleRate，使用系统默认（48kHz）
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.nativeSampleRate = this.audioContext.sampleRate;
            console.log(`[AudioManager] AudioContext 初始化，原生采样率: ${this.nativeSampleRate}Hz（AEC参考采样率）`);
            
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
     * 开始录音（非VAD模式）
     */
    async startRecording(onDataCallback) {
        await this.init();

        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('浏览器不支持录音功能或需要HTTPS连接');
            }

            // ✅ 关键修复：不约束 sampleRate，让浏览器选择原生采样率
            // Chrome AEC 需要麦克风和扬声器在同一原生采样率（48kHz）下才能正确消除回声
            // vad-processor.js 内部会自动将原生采样率降采样到 16kHz 输出给服务器
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            const processorUrl = new URL('./vad-processor.js', import.meta.url);
            await this.audioContext.audioWorklet.addModule(processorUrl);

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            const workletNode = new AudioWorkletNode(this.audioContext, 'vad-processor');
            
            workletNode.port.onmessage = (event) => {
                const { type, data } = event.data;
                if (type === 'audioData' && onDataCallback) {
                    onDataCallback(data);
                }
            };
            
            // targetSampleRate=16000 告知 worklet 需降采样到16kHz再输出PCM
            workletNode.port.postMessage({
                type: 'init',
                data: {
                    vadEnabled: false,
                    vadParams: null,
                    targetSampleRate: 16000
                }
            });

            source.connect(workletNode);
            // ✅ workletNode 不连接到 destination，避免麦克风信号从扬声器环回

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
            // ✅ 关键修复：不约束 sampleRate，使用系统原生采样率（48kHz）
            // 保证 Chrome AEC 能在原生采样率下正确对齐扬声器参考信号
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            const processorUrl = new URL('./vad-processor.js', import.meta.url);
            await this.audioContext.audioWorklet.addModule(processorUrl);

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            const workletNode = new AudioWorkletNode(this.audioContext, 'vad-processor');
            
            workletNode.port.onmessage = (event) => {
                const { type, data } = event.data;
                
                if (type === 'speechStart' && onSpeechStart) {
                    onSpeechStart();
                } else if (type === 'audioData' && onAudioData) {
                    onAudioData(data);
                } else if (type === 'speechEnd' && onSpeechEnd) {
                    onSpeechEnd();
                } else if (type === 'vadState') {
                    console.log('[AudioManager] VAD状态:', event.data);
                } else if (type === 'debug') {
                    console.debug('[AudioManager] VAD调试:', event.data.data);
                }
            };
            
            // targetSampleRate=16000 告知 worklet 降采样到16kHz输出
            workletNode.port.postMessage({
                type: 'init',
                data: {
                    vadEnabled: true,
                    vadParams: vadParams,
                    targetSampleRate: 16000
                }
            });

            source.connect(workletNode);
            // ✅ workletNode 不连接到 destination，避免麦克风信号从扬声器环回

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
            this.audioWorkletNode.port.postMessage({ type: 'stop' });
            
            setTimeout(() => {
                if (this.audioWorkletNode) {
                    try {
                        this.audioWorkletNode.disconnect();
                    } catch (error) {
                        // 忽略断开连接时的错误
                    }
                    this.audioWorkletNode = null;
                }
            }, 50);
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        this.vadEnabled = false;
        this.vadParams = null;
        this.vadState = {
            isSpeaking: false,
            silenceStart: null,
            speechStart: null,
            audioBuffer: []
        };
    }

    /**
     * 播放 PCM 音频（非流式场景）
     * 同样升采样到原生采样率，保持 AEC 参考信号一致性
     */
    async playPCM(pcmData, sampleRate = 16000) {
        await this.init();

        try {
            if (this.currentSource) {
                this.currentSource.stop();
                this.currentSource = null;
            }

            // 解码 Int16 PCM → Float32
            const pcmArray = new Int16Array(pcmData);
            const float32 = new Float32Array(pcmArray.length);
            for (let i = 0; i < pcmArray.length; i++) {
                float32[i] = pcmArray[i] / 32768;
            }

            // 升采样到原生采样率
            const float32Native = resampleLinear(float32, sampleRate, this.nativeSampleRate);

            const audioBuffer = this.audioContext.createBuffer(
                1,
                float32Native.length,
                this.nativeSampleRate
            );
            audioBuffer.getChannelData(0).set(float32Native);

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
        
        this.nativeSampleRate = null;
        this.streamingPlayer = null;
    }
}
