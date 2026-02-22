/**
 * 全局音频播放器管理器
 * 确保同一时间只有一个语音消息在播放
 */

class GlobalAudioPlayer {
    constructor() {
        this.currentAudio = null;
        this.currentBubble = null;
        this.isPlaying = false;
    }

    /**
     * 播放音频
     * @param {ArrayBuffer|Blob} audioData - 音频数据
     * @param {Object} bubble - 消息气泡实例
     * @param {Function} onEnd - 播放结束回调
     */
    async play(audioData, bubble, onEnd) {
        // 如果正在播放其他音频，先停止
        if (this.isPlaying && this.currentBubble !== bubble) {
            this.stop();
        }

        // 如果是同一个气泡，切换播放/暂停
        if (this.currentBubble === bubble && this.isPlaying) {
            this.stop();
            return;
        }

        try {
            // 创建音频对象
            let audioBlob;
            if (audioData instanceof Blob) {
                audioBlob = audioData;
            } else if (audioData instanceof ArrayBuffer) {
                // 将 PCM 数据转换为 WAV 格式
                const wavData = this.pcmToWav(audioData, 16000, 16, 1);
                audioBlob = new Blob([wavData], { type: 'audio/wav' });
            } else {
                throw new Error('不支持的音频数据格式');
            }

            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            // 设置当前播放状态
            this.currentAudio = audio;
            this.currentBubble = bubble;
            this.isPlaying = true;

            // 监听播放结束
            audio.onended = () => {
                this.cleanup();
                if (onEnd) onEnd();
            };

            // 监听播放错误
            audio.onerror = (e) => {
                console.error('[AudioPlayer] 播放失败:', e);
                this.cleanup();
                if (onEnd) onEnd();
            };

            // 开始播放
            await audio.play();
            console.log('[AudioPlayer] 开始播放音频');

        } catch (error) {
            console.error('[AudioPlayer] 播放音频失败:', error);
            this.cleanup();
            throw error;
        }
    }

    /**
     * 将 PCM 数据转换为 WAV 格式
     * @param {ArrayBuffer} pcmData - PCM 音频数据
     * @param {number} sampleRate - 采样率
     * @param {number} bitsPerSample - 位深度
     * @param {number} numChannels - 声道数
     * @returns {ArrayBuffer} WAV 格式音频数据
     */
    pcmToWav(pcmData, sampleRate, bitsPerSample, numChannels) {
        const dataLength = pcmData.byteLength;
        const buffer = new ArrayBuffer(44 + dataLength);
        const view = new DataView(buffer);

        // WAV 文件头
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };

        writeString(0, 'RIFF');
        view.setUint32(4, 36 + dataLength, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true); // fmt chunk size
        view.setUint16(20, 1, true); // PCM format
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numChannels * bitsPerSample / 8, true); // byte rate
        view.setUint16(32, numChannels * bitsPerSample / 8, true); // block align
        view.setUint16(34, bitsPerSample, true);
        writeString(36, 'data');
        view.setUint32(40, dataLength, true);

        // 复制 PCM 数据
        const pcmView = new Uint8Array(pcmData);
        const wavView = new Uint8Array(buffer);
        wavView.set(pcmView, 44);

        return buffer;
    }

    /**
     * 停止播放
     */
    stop() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
        }
        this.cleanup();
    }

    /**
     * 清理资源
     */
    cleanup() {
        if (this.currentAudio) {
            const url = this.currentAudio.src;
            this.currentAudio.onended = null;
            this.currentAudio.onerror = null;
            this.currentAudio = null;
            
            // 释放 Blob URL
            if (url && url.startsWith('blob:')) {
                URL.revokeObjectURL(url);
            }
        }

        if (this.currentBubble && this.currentBubble.setPlayingState) {
            this.currentBubble.setPlayingState(false);
        }

        this.currentBubble = null;
        this.isPlaying = false;
    }

    /**
     * 检查是否正在播放指定气泡的音频
     */
    isPlayingBubble(bubble) {
        return this.isPlaying && this.currentBubble === bubble;
    }
}

// 创建全局单例
const globalAudioPlayer = new GlobalAudioPlayer();

export default globalAudioPlayer;

