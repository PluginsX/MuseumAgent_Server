/**
 * VAD (Voice Activity Detection) 模块
 * 使用 Silero VAD 进行轻量级语音活动检测
 * 仅在检测到语音时采集音频，节省流量和性能
 */

class VADModule {
    constructor() {
        this.vadProcessor = null;
        this.isEnabled = false;
        this.isVoiceActive = false;
        this.silenceTimer = null;
        
        // 默认配置
        this.config = {
            enabled: true,                    // 是否启用VAD
            silenceDuration: 1000,            // 静音多久后停止采集（毫秒）
            positiveSpeechThreshold: 0.5,     // 语音检测阈值（0-1，越高越严格）
            negativeSpeechThreshold: 0.35,    // 静音检测阈值（0-1，越低越严格）
            preSpeechPadFrames: 1,            // 语音前保留帧数
            redemptionFrames: 8,              // 容错帧数（避免短暂静音误判）
            frameSamples: 1536,               // 每帧样本数（16kHz下约96ms）
            minSpeechFrames: 3                // 最小语音帧数（避免误触发）
        };
        
        // 回调函数
        this.onVoiceStart = null;
        this.onVoiceEnd = null;
        this.onVoiceActivity = null;
        
        // 统计信息
        this.stats = {
            totalFrames: 0,
            voiceFrames: 0,
            silenceFrames: 0,
            activations: 0
        };
    }
    
    /**
     * 初始化VAD模块
     * @param {MediaStream} audioStream - 音频流
     * @param {Object} config - 配置参数
     */
    async init(audioStream, config = {}) {
        // 合并配置
        this.config = { ...this.config, ...config };
        
        if (!this.config.enabled) {
            console.log('[VAD] VAD已禁用，跳过初始化');
            return;
        }
        
        console.log('[VAD] 开始初始化VAD模块...', this.config);
        
        try {
            // 动态加载VAD库（CDN）
            if (!window.vad) {
                console.log('[VAD] 加载VAD库...');
                await this._loadVADLibrary();
            }
            
            // 创建VAD处理器
            const myvad = await window.vad.MicVAD.new({
                positiveSpeechThreshold: this.config.positiveSpeechThreshold,
                negativeSpeechThreshold: this.config.negativeSpeechThreshold,
                preSpeechPadFrames: this.config.preSpeechPadFrames,
                redemptionFrames: this.config.redemptionFrames,
                frameSamples: this.config.frameSamples,
                minSpeechFrames: this.config.minSpeechFrames,
                
                // 语音开始回调
                onSpeechStart: () => {
                    console.log('[VAD] 检测到语音开始');
                    this.isVoiceActive = true;
                    this.stats.activations++;
                    
                    // 清除静音计时器
                    if (this.silenceTimer) {
                        clearTimeout(this.silenceTimer);
                        this.silenceTimer = null;
                    }
                    
                    // 触发回调
                    if (this.onVoiceStart) {
                        this.onVoiceStart();
                    }
                },
                
                // 语音结束回调
                onSpeechEnd: () => {
                    console.log('[VAD] 检测到语音结束，启动静音计时器');
                    
                    // 启动静音计时器
                    this.silenceTimer = setTimeout(() => {
                        console.log('[VAD] 静音超时，停止采集');
                        this.isVoiceActive = false;
                        
                        // 触发回调
                        if (this.onVoiceEnd) {
                            this.onVoiceEnd();
                        }
                    }, this.config.silenceDuration);
                },
                
                // 帧处理回调
                onFrameProcessed: (probabilities) => {
                    this.stats.totalFrames++;
                    
                    // 统计语音/静音帧
                    if (probabilities.isSpeech) {
                        this.stats.voiceFrames++;
                    } else {
                        this.stats.silenceFrames++;
                    }
                    
                    // 触发活动回调
                    if (this.onVoiceActivity) {
                        this.onVoiceActivity(probabilities);
                    }
                },
                
                // 使用提供的音频流
                stream: audioStream
            });
            
            this.vadProcessor = myvad;
            this.isEnabled = true;
            
            console.log('[VAD] VAD模块初始化成功');
            
        } catch (error) {
            console.error('[VAD] VAD初始化失败:', error);
            this.isEnabled = false;
            throw error;
        }
    }
    
    /**
     * 动态加载ONNX Runtime库
     */
    async _loadONNXRuntime() {
        return new Promise((resolve, reject) => {
            // 检查是否已加载
            if (window.ort) {
                console.log('[VAD] ONNX Runtime库已加载');
                resolve();
                return;
            }
            
            // 创建script标签
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.14.0/dist/ort.min.js';
            script.async = true;
            
            script.onload = () => {
                console.log('[VAD] ONNX Runtime库加载成功');
                resolve();
            };
            
            script.onerror = () => {
                console.error('[VAD] ONNX Runtime库加载失败');
                reject(new Error('Failed to load ONNX Runtime library'));
            };
            
            document.head.appendChild(script);
        });
    }
    
    /**
     * 动态加载VAD库
     */
    async _loadVADLibrary() {
        return new Promise((resolve, reject) => {
            // 检查是否已加载
            if (window.vad) {
                resolve();
                return;
            }
            
            // 先加载ONNX Runtime库
            this._loadONNXRuntime().then(() => {
                // 创建script标签
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.7/dist/bundle.min.js';
                script.async = true;
                
                script.onload = () => {
                    console.log('[VAD] VAD库加载成功');
                    resolve();
                };
                
                script.onerror = () => {
                    console.error('[VAD] VAD库加载失败');
                    reject(new Error('Failed to load VAD library'));
                };
                
                document.head.appendChild(script);
            }).catch(error => {
                console.error('[VAD] 加载ONNX Runtime库失败:', error);
                reject(error);
            });
        });
    }
    
    /**
     * 启动VAD检测
     */
    start() {
        if (!this.isEnabled || !this.vadProcessor) {
            console.warn('[VAD] VAD未启用或未初始化');
            return;
        }
        
        console.log('[VAD] 启动VAD检测');
        this.vadProcessor.start();
    }
    
    /**
     * 暂停VAD检测
     */
    pause() {
        if (!this.vadProcessor) return;
        
        console.log('[VAD] 暂停VAD检测');
        this.vadProcessor.pause();
        
        // 清除静音计时器
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
    }
    
    /**
     * 销毁VAD模块
     */
    destroy() {
        if (this.vadProcessor) {
            console.log('[VAD] 销毁VAD模块');
            this.vadProcessor.destroy();
            this.vadProcessor = null;
        }
        
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
        
        this.isEnabled = false;
        this.isVoiceActive = false;
    }
    
    /**
     * 更新配置
     * @param {Object} newConfig - 新配置
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        console.log('[VAD] 配置已更新:', this.config);
    }
    
    /**
     * 获取统计信息
     */
    getStats() {
        return {
            ...this.stats,
            voiceRatio: this.stats.totalFrames > 0 
                ? (this.stats.voiceFrames / this.stats.totalFrames * 100).toFixed(2) + '%'
                : '0%'
        };
    }
    
    /**
     * 重置统计信息
     */
    resetStats() {
        this.stats = {
            totalFrames: 0,
            voiceFrames: 0,
            silenceFrames: 0,
            activations: 0
        };
    }
}

// 导出模块
export { VADModule };

