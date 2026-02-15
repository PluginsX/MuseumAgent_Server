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
            
            console.log('[AudioService] 初始化成功，采样率:', this.audioContext.sampleRate);
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
    async startRecordingWithVAD(vadParams, onDataCallback) {
        await this.init();

        this.vadParams = vadParams;
        this.vadEnabled = true;
        this.vadState = {
            isSpeaking: false,
            silenceStart: null,
            speechStart: null,
            audioBuffer: []
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
                this._processVAD(inputData, pcmData.buffer, onDataCallback);

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
     */
    _processVAD(floatData, pcmBuffer, onDataCallback) {
        // 计算音频能量（RMS）
        let sum = 0;
        for (let i = 0; i < floatData.length; i++) {
            sum += floatData[i] * floatData[i];
        }
        const rms = Math.sqrt(sum / floatData.length);

        const now = Date.now();

        // 检测语音开始
        if (!this.vadState.isSpeaking) {
            if (rms > this.vadParams.speechThreshold) {
                // 语音开始
                this.vadState.isSpeaking = true;
                this.vadState.speechStart = now;
                this.vadState.silenceStart = null;
                
                // 添加预填充（之前缓存的音频）
                const paddingFrames = Math.floor(this.vadParams.preSpeechPadding / (4096 / 16));
                const startIndex = Math.max(0, this.vadState.audioBuffer.length - paddingFrames);
                for (let i = startIndex; i < this.vadState.audioBuffer.length; i++) {
                    if (onDataCallback) {
                        onDataCallback(this.vadState.audioBuffer[i]);
                    }
                }
                
                // 发送当前帧
                if (onDataCallback) {
                    onDataCallback(pcmBuffer);
                }
                
                console.log('[AudioService] VAD: 检测到语音开始');
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
                            if (onDataCallback) {
                                onDataCallback(this.vadState.audioBuffer[i]);
                            }
                        }
                        
                        console.log('[AudioService] VAD: 检测到语音结束，时长:', (speechDuration / 1000).toFixed(2), '秒');
                    }
                    
                    // 重置状态
                    this.vadState.isSpeaking = false;
                    this.vadState.speechStart = null;
                    this.vadState.silenceStart = null;
                    this.vadState.audioBuffer = [];
                }
                
                // 继续发送当前帧（后填充）
                if (onDataCallback) {
                    onDataCallback(pcmBuffer);
                }
                this.vadState.audioBuffer.push(pcmBuffer);
            } else {
                // 继续说话
                this.vadState.silenceStart = null;
                
                // 发送当前帧
                if (onDataCallback) {
                    onDataCallback(pcmBuffer);
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
     * 流式播放音频（边接收边播放）
     */
    async playStreamPCM(pcmChunks) {
        await this.init();

        // 合并所有 PCM 数据
        const totalLength = pcmChunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
        const combined = new Uint8Array(totalLength);
        
        let offset = 0;
        for (const chunk of pcmChunks) {
            combined.set(new Uint8Array(chunk), offset);
            offset += chunk.byteLength;
        }

        return this.playPCM(combined.buffer);
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

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }
}

// 创建全局单例
export const audioService = new AudioService();

