/**
 * VAD AudioWorklet 处理器
 * 在独立线程中处理音频数据，避免阻塞主线程
 */

class VADProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        
        // VAD 参数（从主线程接收）
        this.vadParams = null;
        this.vadEnabled = false;
        
        // ✅ 停止标志
        this.isStopped = false;
        
        // VAD 状态
        this.isSpeaking = false;
        this.silenceStart = null;
        this.speechStart = null;
        this.audioBuffer = [];
        
        // 监听来自主线程的消息
        this.port.onmessage = (event) => {
            const { type, data } = event.data;
            
            if (type === 'init') {
                this.vadParams = data.vadParams;
                this.vadEnabled = data.vadEnabled;
                this.isStopped = false;
            } else if (type === 'stop') {
                // ✅ 设置停止标志，停止处理音频
                this.isStopped = true;
                this.vadEnabled = false;
                this.isSpeaking = false;
                this.audioBuffer = [];
            }
        };
    }
    
    process(inputs, outputs, parameters) {
        // ✅ 如果已停止，返回 false 终止处理器
        if (this.isStopped) {
            return false;
        }
        
        const input = inputs[0];
        if (!input || !input[0]) {
            return true;
        }
        
        const inputData = input[0]; // Float32Array
        
        // 转换为 PCM Int16
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // 发送音频数据到主线程
        if (this.vadEnabled) {
            this._processVAD(inputData, pcmData.buffer);
        } else {
            // 非 VAD 模式，直接发送
            this.port.postMessage({
                type: 'audioData',
                data: pcmData.buffer
            }, [pcmData.buffer]);
        }
        
        return true;
    }
    
    _processVAD(floatData, pcmBuffer) {
        // 计算 RMS
        let sum = 0;
        for (let i = 0; i < floatData.length; i++) {
            sum += floatData[i] * floatData[i];
        }
        const rms = Math.sqrt(sum / floatData.length);
        
        const now = currentTime * 1000; // 转换为毫秒
        const frameDuration = (floatData.length / sampleRate) * 1000; // 帧时长（毫秒）
        
        if (!this.isSpeaking) {
            // 计算前缓存需要的最大帧数
            const prePaddingMaxFrames = Math.ceil(this.vadParams.preSpeechPadding / frameDuration);
            
            // 持续缓存音频数据（用于前填充）
            this.audioBuffer.push(pcmBuffer);
            if (this.audioBuffer.length > prePaddingMaxFrames) {
                this.audioBuffer.shift();
            }
            
            // 检测到语音开始
            if (rms > this.vadParams.speechThreshold) {
                this.isSpeaking = true;
                this.speechStart = now;
                this.silenceStart = null;
                
                // 通知主线程：语音开始
                this.port.postMessage({
                    type: 'speechStart'
                });
                
                // 发送前缓存数据
                for (const buffer of this.audioBuffer) {
                    this.port.postMessage({
                        type: 'audioData',
                        data: buffer
                    }, [buffer]);
                }
                
                // 清空缓存（已发送）
                this.audioBuffer = [];
            }
        } else {
            // 语音进行中
            const postPaddingMaxFrames = Math.ceil(this.vadParams.postSpeechPadding / frameDuration);
            
            // 持续缓存音频数据（用于后填充）
            this.audioBuffer.push(pcmBuffer);
            if (this.audioBuffer.length > postPaddingMaxFrames) {
                const oldBuffer = this.audioBuffer.shift();
                // 发送旧的缓存数据
                this.port.postMessage({
                    type: 'audioData',
                    data: oldBuffer
                }, [oldBuffer]);
            }
            
            if (rms < this.vadParams.silenceThreshold) {
                // 静音
                if (!this.silenceStart) {
                    this.silenceStart = now;
                }
                
                const silenceDuration = now - this.silenceStart;
                if (silenceDuration >= this.vadParams.silenceDuration) {
                    const speechDuration = now - this.speechStart;
                    
                    if (speechDuration >= this.vadParams.minSpeechDuration) {
                        // 发送后缓存数据
                        for (const buffer of this.audioBuffer) {
                            this.port.postMessage({
                                type: 'audioData',
                                data: buffer
                            }, [buffer]);
                        }
                        
                        // 通知主线程：语音结束
                        this.port.postMessage({
                            type: 'speechEnd'
                        });
                    }
                    
                    // 重置状态
                    this.isSpeaking = false;
                    this.speechStart = null;
                    this.silenceStart = null;
                    this.audioBuffer = [];
                }
            } else {
                // 继续说话
                this.silenceStart = null;
            }
        }
    }
}

registerProcessor('vad-processor', VADProcessor);

