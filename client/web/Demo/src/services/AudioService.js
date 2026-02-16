/**
 * 音频服务
 * 统一处理音频录制和播放，使用 AudioWorklet 提升性能
 */

import { eventBus, Events } from '../core/EventBus.js';
import { stateManager } from '../core/StateManager.js';

export class AudioService {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.audioWorkletNode = null;
        this.isRecording = false;
        
        // VAD相关
        this.vadEnabled = false;
        this.vadParams = null;
        this.vadState = {
            isSpeaking: false,
            silenceStart: null,
            speechStart: null,
            audioBuffer: []
        };
        
        // 播放相关
        this.playbackQueue = [];
        this.isPlaying = false;
        this.currentSource = null;
        this.currentPlayingMessageId = null; // 当前正在播放的消息ID
        
        // 流式播放器（单例，始终存在）
        this.streamingPlayer = null;
        
        // 自动初始化
        this.autoInit();
    }
    
    /**
     * 自动初始化（客户端启动时调用）
     * 注意：AudioContext 必须在用户交互后才能创建，所以这里只是尝试初始化
     */
    async autoInit() {
        // 不在这里初始化，等待用户第一次交互（点击话筒或发送消息）
        console.log('[AudioService] 等待用户交互后初始化 AudioContext');
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
            
            // 创建流式播放器（单例）
            this.streamingPlayer = new StreamingAudioPlayer(this.audioContext);
            
            console.log('[AudioService] 初始化成功，采样率:', this.audioContext.sampleRate);
            console.log('[AudioService] 流式播放器已就绪');
        }
        
        // 如果 AudioContext 被挂起，尝试恢复
        if (this.audioContext && this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
            console.log('[AudioService] AudioContext 已恢复');
        }
    }

    /**
     * 开始录音（使用 AudioWorklet）
     */
    async startRecording(onDataCallback) {
        await this.init();

        try {
            // 获取麦克风权限
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // 创建音频源
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // 使用 ScriptProcessor（AudioWorklet 需要单独的 processor 文件）
            // 生产环境建议使用 AudioWorklet
            const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
            
            processor.onaudioprocess = (e) => {
                if (!this.isRecording) return;

                const inputData = e.inputBuffer.getChannelData(0);
                
                // 转换为 Int16 PCM
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                // 回调音频数据（不启用VAD时直接发送）
                if (onDataCallback) {
                    onDataCallback(pcmData.buffer);
                }

                eventBus.emit(Events.RECORDING_DATA, pcmData.buffer);
            };

            source.connect(processor);
            processor.connect(this.audioContext.destination);

            this.audioWorkletNode = processor;
            this.isRecording = true;
            this.vadEnabled = false;

            stateManager.setState('recording.isRecording', true);
            eventBus.emit(Events.RECORDING_START);

            console.log('[AudioService] 录音已开始（不启用VAD）');

        } catch (error) {
            console.error('[AudioService] 录音启动失败:', error);
            eventBus.emit(Events.RECORDING_ERROR, error);
            throw error;
        }
    }

    /**
     * 开始录音（启用VAD）
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
            // 获取麦克风权限
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // 创建音频源
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // 使用 ScriptProcessor
            const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
            
            processor.onaudioprocess = (e) => {
                if (!this.isRecording) return;

                const inputData = e.inputBuffer.getChannelData(0);
                
                // 转换为 Int16 PCM
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                // VAD处理
                this._processVAD(inputData, pcmData.buffer);

                eventBus.emit(Events.RECORDING_DATA, pcmData.buffer);
            };

            source.connect(processor);
            processor.connect(this.audioContext.destination);

            this.audioWorkletNode = processor;
            this.isRecording = true;

            stateManager.setState('recording.isRecording', true);
            eventBus.emit(Events.RECORDING_START);

            console.log('[AudioService] 录音已开始（启用VAD）', vadParams);

        } catch (error) {
            console.error('[AudioService] 录音启动失败:', error);
            eventBus.emit(Events.RECORDING_ERROR, error);
            throw error;
        }
    }

    /**
     * VAD处理逻辑
     * VAD只控制何时开始/停止发送语音消息，不控制话筒开关
     */
    _processVAD(floatData, pcmBuffer) {
        if (!this.vadEnabled) {
            console.log('[AudioService] VAD未启用，跳过处理');
            return;
        }
        
        // 计算音频能量（RMS）
        let sum = 0;
        for (let i = 0; i < floatData.length; i++) {
            sum += floatData[i] * floatData[i];
        }
        const rms = Math.sqrt(sum / floatData.length);

        const now = Date.now();
        
        // 调试：每100帧输出一次能量值
        if (!this._vadDebugCounter) this._vadDebugCounter = 0;
        this._vadDebugCounter++;
        if (this._vadDebugCounter % 100 === 0) {
            console.log('[AudioService] VAD能量值:', rms.toFixed(4), '阈值:', this.vadParams.speechThreshold);
        }

        // 检测语音开始
        if (!this.vadState.isSpeaking) {
            if (rms > this.vadParams.speechThreshold) {
                // 语音开始
                this.vadState.isSpeaking = true;
                this.vadState.speechStart = now;
                this.vadState.silenceStart = null;
                
                console.log('[AudioService] VAD: 检测到语音开始，RMS:', rms.toFixed(4), '创建新的语音消息');
                
                // 触发语音开始回调（创建新的语音消息气泡）
                if (this.vadState.speechStartCallback) {
                    this.vadState.speechStartCallback();
                }
                
                // 添加预填充（之前缓存的音频）
                const paddingFrames = Math.floor(this.vadParams.preSpeechPadding / (4096 / 16));
                const startIndex = Math.max(0, this.vadState.audioBuffer.length - paddingFrames);
                for (let i = startIndex; i < this.vadState.audioBuffer.length; i++) {
                    if (this.vadState.audioDataCallback) {
                        this.vadState.audioDataCallback(this.vadState.audioBuffer[i]);
                    }
                }
                
                // 发送当前帧
                if (this.vadState.audioDataCallback) {
                    this.vadState.audioDataCallback(pcmBuffer);
                }
            } else {
                // 缓存静音帧（用于预填充）
                this.vadState.audioBuffer.push(pcmBuffer);
                if (this.vadState.audioBuffer.length > 10) {
                    this.vadState.audioBuffer.shift();
                }
            }
        } else {
            // 正在说话
            if (rms < this.vadParams.silenceThreshold) {
                // 检测到静音
                if (!this.vadState.silenceStart) {
                    this.vadState.silenceStart = now;
                }
                
                // 检查静音持续时间
                const silenceDuration = now - this.vadState.silenceStart;
                if (silenceDuration >= this.vadParams.silenceDuration) {
                    // 语音结束
                    const speechDuration = now - this.vadState.speechStart;
                    
                    // 检查最小语音时长
                    if (speechDuration >= this.vadParams.minSpeechDuration) {
                        // 添加后填充
                        const paddingFrames = Math.floor(this.vadParams.postSpeechPadding / (4096 / 16));
                        for (let i = 0; i < paddingFrames && i < this.vadState.audioBuffer.length; i++) {
                            if (this.vadState.audioDataCallback) {
                                this.vadState.audioDataCallback(this.vadState.audioBuffer[i]);
                            }
                        }
                        
                        console.log('[AudioService] VAD: 检测到语音结束，时长:', (speechDuration / 1000).toFixed(2), '秒');
                        console.log('[AudioService] VAD: 结束本次语音消息发送，继续监听下一次语音');
                        
                        // 触发语音结束回调（结束本次语音消息发送）
                        if (this.vadState.speechEndCallback) {
                            this.vadState.speechEndCallback();
                        }
                    } else {
                        console.log('[AudioService] VAD: 语音时长不足，忽略:', (speechDuration / 1000).toFixed(2), '秒');
                    }
                    
                    // 重置VAD状态，准备检测下一次语音
                    // 注意：不关闭话筒，继续监听
                    this.vadState.isSpeaking = false;
                    this.vadState.speechStart = null;
                    this.vadState.silenceStart = null;
                    this.vadState.audioBuffer = [];
                    return;
                }
                
                // 继续发送当前帧（后填充）
                if (this.vadState.audioDataCallback) {
                    this.vadState.audioDataCallback(pcmBuffer);
                }
                this.vadState.audioBuffer.push(pcmBuffer);
            } else {
                // 继续说话
                this.vadState.silenceStart = null;
                
                // 发送当前帧
                if (this.vadState.audioDataCallback) {
                    this.vadState.audioDataCallback(pcmBuffer);
                }
            }
        }
    }

    /**
     * 停止录音
     */
    stopRecording() {
        this.isRecording = false;

        if (this.audioWorkletNode) {
            this.audioWorkletNode.disconnect();
            this.audioWorkletNode = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        stateManager.setState('recording.isRecording', false);
        eventBus.emit(Events.RECORDING_STOP);

        console.log('[AudioService] 录音已停止');
    }

    /**
     * 播放 PCM 音频（优化版）
     */
    async playPCM(pcmData, sampleRate = 16000) {
        await this.init();

        try {
            // 停止当前播放
            if (this.currentSource) {
                this.currentSource.stop();
                this.currentSource = null;
            }

            // 创建 AudioBuffer
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

            // 创建音频源
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            this.currentSource = source;
            this.isPlaying = true;

            stateManager.setState('audio.isPlaying', true);
            eventBus.emit(Events.AUDIO_PLAY_START);

            return new Promise((resolve, reject) => {
                source.onended = () => {
                    this.isPlaying = false;
                    this.currentSource = null;
                    stateManager.setState('audio.isPlaying', false);
                    eventBus.emit(Events.AUDIO_PLAY_END);
                    resolve();
                };

                source.start();
            });

        } catch (error) {
            console.error('[AudioService] 播放失败:', error);
            eventBus.emit(Events.AUDIO_PLAY_ERROR, error);
            throw error;
        }
    }

    /**
     * 开始播放新的流式消息
     */
    async startStreamingMessage(messageId) {
        // 确保初始化（用户交互后可以成功）
        try {
            await this.init();
            console.log('[AudioService] AudioContext 状态:', this.audioContext?.state);
            console.log('[AudioService] 流式播放器状态:', this.streamingPlayer ? '已就绪' : '未初始化');
        } catch (error) {
            console.error('[AudioService] 初始化失败:', error);
            return false;
        }
        
        if (!this.streamingPlayer) {
            console.error('[AudioService] 流式播放器未初始化');
            return false;
        }
        
        // 停止当前正在播放的其他消息
        if (this.currentPlayingMessageId && this.currentPlayingMessageId !== messageId) {
            console.log('[AudioService] 停止当前播放:', this.currentPlayingMessageId);
            this.streamingPlayer.stop();
        }
        
        // 开始新消息
        this.streamingPlayer.startMessage(messageId);
        this.currentPlayingMessageId = messageId;
        
        console.log('[AudioService] 开始流式播放消息:', messageId);
        return true;
    }
    
    /**
     * 添加音频块到流式播放器
     */
    async addStreamingChunk(messageId, pcmData) {
        // 如果播放器未初始化，尝试初始化
        if (!this.streamingPlayer) {
            try {
                console.log('[AudioService] 流式播放器未初始化，尝试初始化...');
                await this.init();
                console.log('[AudioService] 初始化完成，AudioContext:', this.audioContext?.state, '播放器:', this.streamingPlayer ? '已就绪' : '未初始化');
            } catch (error) {
                console.error('[AudioService] 初始化失败:', error);
                return;
            }
        }
        
        if (!this.streamingPlayer) {
            console.error('[AudioService] 流式播放器仍未初始化');
            return;
        }
        
        this.streamingPlayer.addChunk(messageId, pcmData);
    }
    
    /**
     * 结束流式消息
     */
    endStreamingMessage(messageId) {
        if (!this.streamingPlayer) {
            return;
        }
        
        this.streamingPlayer.endMessage(messageId);
        
        // 如果是当前播放的消息，清除ID
        if (this.currentPlayingMessageId === messageId) {
            this.currentPlayingMessageId = null;
        }
        
        console.log('[AudioService] 流式消息结束:', messageId);
    }
    
    /**
     * 停止流式播放
     */
    stopStreamingPlayback() {
        if (!this.streamingPlayer) {
            return;
        }
        
        this.streamingPlayer.stop();
        this.currentPlayingMessageId = null;
        
        console.log('[AudioService] 停止流式播放');
    }

    /**
     * 停止播放
     */
    stopPlayback() {
        if (this.currentSource) {
            this.currentSource.stop();
            this.currentSource = null;
        }

        this.isPlaying = false;
        this.currentPlayingMessageId = null;
        stateManager.setState('audio.isPlaying', false);
        eventBus.emit(Events.AUDIO_PLAY_END);
    }

    /**
     * 创建 WAV 文件（用于下载或显示）
     */
    createWAV(pcmData, sampleRate = 16000) {
        const numChannels = 1;
        const bitsPerSample = 16;
        const byteRate = sampleRate * numChannels * bitsPerSample / 8;
        const blockAlign = numChannels * bitsPerSample / 8;
        const dataSize = pcmData.byteLength;

        const buffer = new ArrayBuffer(44 + dataSize);
        const view = new DataView(buffer);

        // RIFF header
        this._writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + dataSize, true);
        this._writeString(view, 8, 'WAVE');

        // fmt chunk
        this._writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, byteRate, true);
        view.setUint16(32, blockAlign, true);
        view.setUint16(34, bitsPerSample, true);

        // data chunk
        this._writeString(view, 36, 'data');
        view.setUint32(40, dataSize, true);

        // PCM data
        new Uint8Array(buffer, 44).set(new Uint8Array(pcmData));

        return new Blob([buffer], { type: 'audio/wav' });
    }

    /**
     * 写入字符串到 DataView
     */
    _writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }

    /**
     * 清理资源
     */
    cleanup() {
        this.stopRecording();
        this.stopPlayback();
        this.stopStreamingPlayback();

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        this.streamingPlayer = null;
    }
}

/**
 * 流式音频播放器
 * 实现真正的边接收边播放，无需等待所有数据
 * 
 * 设计原则：
 * 1. 单例模式：全局唯一实例，客户端启动时初始化
 * 2. 始终待命：随时准备接收和播放音频
 * 3. 多消息支持：可以同时管理多个消息的播放
 */
class StreamingAudioPlayer {
    constructor(audioContext) {
        this.audioContext = audioContext;
        this.sampleRate = 16000;
        
        // 当前播放的消息
        this.currentMessageId = null;
        this.isPlaying = false;
        this.isStopped = false;
        
        // 音频队列
        this.audioQueue = [];
        this.isProcessing = false;
        
        // 播放时间跟踪
        this.nextStartTime = 0;
        this.startTime = 0;
        
        console.log('[StreamingAudioPlayer] 播放器已初始化，随时待命');
    }
    
    /**
     * 开始播放新消息
     */
    startMessage(messageId) {
        // 如果正在播放其他消息，先停止
        if (this.currentMessageId && this.currentMessageId !== messageId) {
            console.log('[StreamingAudioPlayer] 停止当前播放:', this.currentMessageId);
            this.stop();
        }
        
        this.currentMessageId = messageId;
        this.isPlaying = false;
        this.isStopped = false;
        this.audioQueue = [];
        this.isProcessing = false;
        this.nextStartTime = 0;
        
        console.log('[StreamingAudioPlayer] 开始播放新消息:', messageId);
    }
    
    /**
     * 添加音频块（实时接收）
     */
    addChunk(messageId, pcmData) {
        // 检查是否是当前消息
        if (messageId !== this.currentMessageId) {
            console.log('[StreamingAudioPlayer] 忽略非当前消息的音频块:', messageId);
            return;
        }
        
        if (this.isStopped) {
            console.log('[StreamingAudioPlayer] 已停止，忽略音频块');
            return;
        }
        
        console.log('[StreamingAudioPlayer] 接收音频块:', pcmData.byteLength, '字节');
        this.audioQueue.push(pcmData);
        
        // 如果还没开始播放，立即开始
        if (!this.isPlaying) {
            this.start();
        }
        
        // 处理队列
        this.processQueue();
    }
    
    /**
     * 开始播放
     */
    start() {
        if (this.isPlaying || this.isStopped) return;
        
        this.isPlaying = true;
        this.startTime = this.audioContext.currentTime;
        this.nextStartTime = this.startTime;
        
        console.log('[StreamingAudioPlayer] 开始播放，当前时间:', this.startTime.toFixed(3));
    }
    
    /**
     * 处理音频队列
     */
    async processQueue() {
        if (this.isProcessing || this.isStopped) return;
        
        this.isProcessing = true;
        
        while (this.audioQueue.length > 0 && !this.isStopped) {
            const pcmData = this.audioQueue.shift();
            
            try {
                // 创建 AudioBuffer
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
                
                // 创建音频源并调度播放
                const source = this.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(this.audioContext.destination);
                
                // 计算播放时间（无缝衔接）
                const now = this.audioContext.currentTime;
                const startTime = Math.max(now, this.nextStartTime);
                
                source.start(startTime);
                
                // 更新下一个音频块的开始时间
                this.nextStartTime = startTime + audioBuffer.duration;
                
                console.log('[StreamingAudioPlayer] 播放音频块，时长:', audioBuffer.duration.toFixed(3), '秒，开始时间:', startTime.toFixed(3));
                
            } catch (error) {
                console.error('[StreamingAudioPlayer] 播放音频块失败:', error);
            }
        }
        
        this.isProcessing = false;
    }
    
    /**
     * 标记消息流结束
     */
    endMessage(messageId) {
        if (messageId !== this.currentMessageId) {
            return;
        }
        
        console.log('[StreamingAudioPlayer] 消息流结束:', messageId);
        // 处理剩余的音频块
        this.processQueue();
        
        // 不清空状态，等待下一个消息
    }
    
    /**
     * 停止播放
     */
    stop() {
        if (this.isStopped) return;
        
        this.isStopped = true;
        this.isPlaying = false;
        this.audioQueue = [];
        this.currentMessageId = null;
        
        console.log('[StreamingAudioPlayer] 停止播放');
    }
    
    /**
     * 重置播放器（准备播放新消息）
     */
    reset() {
        this.stop();
        this.isStopped = false;
        console.log('[StreamingAudioPlayer] 播放器已重置，准备接收新消息');
    }
}

// 创建全局单例
export const audioService = new AudioService();

