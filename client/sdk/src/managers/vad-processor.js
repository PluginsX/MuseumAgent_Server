/**
 * VAD AudioWorklet 处理器 v2.1
 *
 * 核心升级（v2.1）：
 * 0. 内置降采样器 —— 支持任意输入采样率（如48kHz）自动降采样到16kHz再处理
 *    这是 AEC 修复的关键配套：AudioContext 运行在系统原生采样率（48kHz），
 *    Chrome 硬件 AEC 能在 48kHz 下正确对齐参考信号；
 *    本处理器负责将 48kHz 麦克风信号降采样到 16kHz，再做 VAD 和 PCM 输出。
 *
 * 原有功能保持不变：
 * 1. 自适应噪声基线估计 —— 冷启动校准 + 实时慢速追踪，动态计算阈值
 * 2. 多特征融合检测 —— RMS能量 + 过零率(ZCR) + 人声频带能量比(FFT)
 * 3. 5状态机 + 连续帧防抖 —— 彻底消除瞬时噪声/碰撞音/咳嗽音误触发
 * 4. 完全向后兼容旧参数格式
 *
 * 运行于 AudioWorklet 独立线程，零外部依赖，O(n) 计算。
 */

'use strict';

// ─────────────────────────────────────────────
// 极简 256 点 FFT（Cooley-Tukey，原位运算）
// 仅用于人声频带能量比分析，计算量极小
// ─────────────────────────────────────────────
function fft256(re, im) {
    const n = 256;
    for (let i = 1, j = 0; i < n; i++) {
        let bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) {
            let t = re[i]; re[i] = re[j]; re[j] = t;
            t = im[i]; im[i] = im[j]; im[j] = t;
        }
    }
    for (let len = 2; len <= n; len <<= 1) {
        const half = len >> 1;
        const ang = -Math.PI / half;
        const wBaseRe = Math.cos(ang);
        const wBaseIm = Math.sin(ang);
        for (let i = 0; i < n; i += len) {
            let wRe = 1, wIm = 0;
            for (let k = 0; k < half; k++) {
                const uRe = re[i + k],       uIm = im[i + k];
                const vRe = re[i+k+half]*wRe - im[i+k+half]*wIm;
                const vIm = re[i+k+half]*wIm + im[i+k+half]*wRe;
                re[i+k]      = uRe + vRe;  im[i+k]      = uIm + vIm;
                re[i+k+half] = uRe - vRe;  im[i+k+half] = uIm - vIm;
                const nwRe = wRe*wBaseRe - wIm*wBaseIm;
                wIm = wRe*wBaseIm + wIm*wBaseRe;
                wRe = nwRe;
            }
        }
    }
}

// ─────────────────────────────────────────────
// 流式线性插值降采样器（AudioWorklet 线程内）
// 将任意输入采样率降采样到 targetRate，跨帧追踪相位保证连续性
// ─────────────────────────────────────────────
class Downsampler {
    /**
     * @param {number} inputRate  - 输入采样率（如 48000）
     * @param {number} outputRate - 目标采样率（如 16000）
     */
    constructor(inputRate, outputRate) {
        this.ratio = inputRate / outputRate;  // 每个输出样本对应的输入样本数（如 3.0）
        this.phase = 0;                       // 当前输入序列中的浮点位置（跨帧持续累积）
        this.lastSample = 0;                  // 上一帧最后一个样本，用于跨帧插值
    }

    /**
     * 处理一帧输入，返回降采样后的 Float32Array
     * @param {Float32Array} input
     * @returns {Float32Array}
     */
    process(input) {
        const ratio = this.ratio;
        const outLen = Math.ceil((input.length - this.phase) / ratio) + 2;
        const output = new Float32Array(outLen);
        let outIdx = 0;

        while (this.phase < input.length) {
            const idx = Math.floor(this.phase);
            const frac = this.phase - idx;
            // 取当前位置前后两个样本做线性插值
            // idx=0 时 prev 使用上一帧最后样本实现跨帧连续
            const prev = idx > 0 ? input[idx - 1] : this.lastSample;
            const curr = input[idx] !== undefined ? input[idx] : prev;
            const next = input[idx + 1] !== undefined ? input[idx + 1] : curr;
            // 在 curr 和 next 之间插值
            output[outIdx++] = curr + frac * (next - curr);
            this.phase += ratio;
        }

        // 保存本帧最后一个样本，供下帧跨帧插值
        this.lastSample = input[input.length - 1] || 0;
        // 将 phase 减去已消耗的输入长度，保留小数余数给下帧
        this.phase -= input.length;

        return output.subarray(0, outIdx);
    }
}

// ─────────────────────────────────────────────
// VAD 状态枚举
// ─────────────────────────────────────────────
const S = { IDLE: 0, CALIBRATING: 1, SILENCE: 2, SPEAKING: 3, ENDING: 4 };

// ─────────────────────────────────────────────
// 主处理器
// ─────────────────────────────────────────────
class VADProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.vadEnabled  = false;
        this.isStopped   = false;
        this.p           = null;   // 规范化后的参数
        this.state       = S.IDLE;

        // ✅ v2.1：降采样器（当 sampleRate !== targetSampleRate 时启用）
        this.downsampler      = null;
        this.targetSampleRate = 16000;  // 输出PCM采样率，始终为16kHz

        // 噪声基线
        this.noiseEst    = 0.01;

        // 校准
        this.calFrames   = 0;
        this.calSum      = 0;
        this.calTarget   = 0;

        // 防抖计数
        this.speechCnt   = 0;
        this.silenceCnt  = 0;

        // 时间戳（ms）
        this.speechStartMs  = 0;

        // 前填充环形缓冲
        this.preBuf      = [];
        this.preBufMax   = 0;

        // 后填充缓冲
        this.postBuf     = [];
        this.postBufMax  = 0;

        // 防抖目标帧数（由参数换算）
        this.confirmTarget  = 3;
        this.silFrameTarget = 40;

        // FFT 累积缓冲（256 点，基于 targetSampleRate=16kHz）
        this.fftAccum    = new Float32Array(256);
        this.fftFill     = 0;

        // 调试日志节流
        this._lastDbg    = 0;

        this.port.onmessage = ({ data: { type, data } }) => {
            if (type === 'init') this._init(data);
            else if (type === 'stop') this._stop();
        };
    }

    // ── 初始化 ──────────────────────────────────
    _init(data) {
        this.isStopped  = false;
        this.vadEnabled = !!data.vadEnabled;

        // ✅ v2.1：读取目标采样率，按需初始化降采样器
        this.targetSampleRate = data.targetSampleRate || 16000;
        if (sampleRate !== this.targetSampleRate) {
            this.downsampler = new Downsampler(sampleRate, this.targetSampleRate);
        } else {
            this.downsampler = null;
        }

        if (this.vadEnabled && data.vadParams) {
            this.p = this._norm(data.vadParams);

            // 帧时长基于 targetSampleRate（16kHz），每帧128样本经降采样后约8ms
            // 若无降采样（native=16k），则仍是 128/16000*1000 ≈ 8ms
            const fd = (128 / this.targetSampleRate) * 1000;

            this.calTarget      = Math.max(10, Math.ceil(this.p.calibrationDuration / fd));
            this.preBufMax      = Math.max(1,  Math.ceil(this.p.preSpeechPadding   / fd));
            this.postBufMax     = Math.max(1,  Math.ceil(this.p.postSpeechPadding  / fd));
            this.confirmTarget  = Math.max(1,  this.p.confirmFrames);
            this.silFrameTarget = Math.max(1,  Math.ceil(this.p.silenceDuration    / fd));

            this._reset();

            if (this.p.autoNoiseAdaptation === false) {
                const derivedNoise = this.p.minSpeechThreshold / this.p.speechRatio;
                this.noiseEst = Math.max(derivedNoise, this.p.minSilenceThreshold * 0.5);
                this.state = S.SILENCE;
                this.port.postMessage({
                    type     : 'vadState',
                    state    : 'ready',
                    noiseEst : +this.noiseEst.toFixed(6),
                    speechThr: +this._speechThr().toFixed(6),
                    note     : 'auto-noise-adaptation disabled, using fixed thresholds'
                });
            } else {
                this.state = S.CALIBRATING;
                this.port.postMessage({ type: 'vadState', state: 'calibrating' });
            }
        } else {
            this.state = S.IDLE;
        }
    }

    // ── 停止 ────────────────────────────────────
    _stop() {
        this.isStopped  = true;
        this.vadEnabled = false;
        this.state      = S.IDLE;
        this._reset();
    }

    // ── 参数规范化（兼容新旧格式）────────────────
    _norm(p) {
        const speechRatio  = p.speechRatio  ?? (p.speechThreshold  ? null : 3.5);
        const silenceRatio = p.silenceRatio ?? (p.silenceThreshold ? null : 1.8);

        return {
            autoNoiseAdaptation : p.autoNoiseAdaptation !== false,
            calibrationDuration : p.calibrationDuration  ?? 1500,
            speechRatio         : speechRatio             ?? 3.5,
            silenceRatio        : silenceRatio            ?? 1.8,
            minSpeechThreshold  : p.minSpeechThreshold    ?? (p.speechThreshold  ?? 0.010),
            minSilenceThreshold : p.minSilenceThreshold   ?? (p.silenceThreshold ?? 0.004),
            silenceDuration     : p.silenceDuration       ?? 800,
            minSpeechDuration   : p.minSpeechDuration     ?? 200,
            confirmFrames       : p.confirmFrames         ?? 3,
            preSpeechPadding    : p.preSpeechPadding      ?? 300,
            postSpeechPadding   : p.postSpeechPadding     ?? 300,
            zcrMin              : p.zcrMin                ?? 3,
            zcrMax              : p.zcrMax                ?? 60,
            voiceBandRatioMin   : p.voiceBandRatioMin     ?? 0.20,
            noiseUpdateRate     : p.noiseUpdateRate       ?? 0.015,
        };
    }

    // ── 重置运行状态 ─────────────────────────────
    _reset() {
        this.calFrames   = 0;
        this.calSum      = 0;
        this.speechCnt   = 0;
        this.silenceCnt  = 0;
        this.speechStartMs = 0;
        this.preBuf      = [];
        this.postBuf     = [];
        this.fftAccum.fill(0);
        this.fftFill     = 0;
    }

    // ── 阈值计算 ─────────────────────────────────
    _speechThr() {
        return Math.max(this.p.minSpeechThreshold,
                        this.noiseEst * this.p.speechRatio);
    }
    _silenceThr() {
        return Math.max(this.p.minSilenceThreshold,
                        this.noiseEst * this.p.silenceRatio);
    }

    // ── 特征提取 ─────────────────────────────────
    /** RMS 均方根能量 */
    _rms(f32) {
        let s = 0;
        for (let i = 0; i < f32.length; i++) s += f32[i] * f32[i];
        return Math.sqrt(s / f32.length);
    }

    /** 过零率（每帧过零次数） */
    _zcr(f32) {
        let c = 0;
        for (let i = 1; i < f32.length; i++) {
            if ((f32[i] >= 0) !== (f32[i-1] >= 0)) c++;
        }
        return c;
    }

    /**
     * 人声频带能量比（300-3400 Hz 占总能量的比例）
     * 基于 targetSampleRate(16kHz) 域的数据计算，FFT bin分辨率 = 16000/256 = 62.5Hz
     */
    _voiceBandRatio(f32) {
        const need = 256 - this.fftFill;
        const take = Math.min(need, f32.length);
        this.fftAccum.set(f32.subarray(0, take), this.fftFill);
        this.fftFill += take;

        if (this.fftFill < 256) return -1;

        const re = new Float32Array(this.fftAccum);
        const im = new Float32Array(256);
        fft256(re, im);

        // bin分辨率基于 targetSampleRate
        const binRes = this.targetSampleRate / 256;
        let voiceE = 0, totalE = 0;
        for (let k = 1; k < 128; k++) {
            const freq = k * binRes;
            const mag2 = re[k]*re[k] + im[k]*im[k];
            totalE += mag2;
            if (freq >= 300 && freq <= 3400) voiceE += mag2;
        }

        this.fftAccum.copyWithin(0, 128);
        this.fftFill = 128;

        return totalE > 1e-10 ? voiceE / totalE : -1;
    }

    // ── AudioWorklet 主入口 ───────────────────────
    process(inputs) {
        if (this.isStopped) return false;

        const ch = inputs[0]?.[0];
        if (!ch) return true;

        // ✅ v2.1：若已初始化降采样器，先将原生采样率数据降采样到 targetSampleRate(16kHz)
        // 后续所有处理（VAD特征计算、PCM输出）均基于降采样后的16kHz数据
        const f32 = this.downsampler ? this.downsampler.process(ch) : ch;

        // 将 Float32 转为 PCM Int16（基于16kHz数据）
        const pcm = new Int16Array(f32.length);
        for (let i = 0; i < f32.length; i++) {
            const s = f32[i] < -1 ? -1 : f32[i] > 1 ? 1 : f32[i];
            pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        if (this.vadEnabled && this.p) {
            this._vad(f32, pcm.buffer);
        } else {
            this.port.postMessage({ type: 'audioData', data: pcm.buffer }, [pcm.buffer]);
        }
        return true;
    }

    // ── VAD 主逻辑 ────────────────────────────────
    _vad(f32, pcmBuf) {
        const rms = this._rms(f32);
        const zcr = this._zcr(f32);
        const vbr = this._voiceBandRatio(f32);
        const nowMs = currentTime * 1000;

        // 节流调试日志（每 2.5 秒一次）
        if (nowMs - this._lastDbg > 2500) {
            this._lastDbg = nowMs;
            this.port.postMessage({
                type: 'debug',
                data: {
                    state      : ['IDLE','CAL','SIL','SPK','END'][this.state],
                    rms        : +rms.toFixed(5),
                    zcr,
                    vbr        : vbr < 0 ? 'n/a' : +vbr.toFixed(3),
                    noise      : +this.noiseEst.toFixed(5),
                    spThr      : +this._speechThr().toFixed(5),
                    silThr     : +this._silenceThr().toFixed(5),
                    nativeSR   : sampleRate,
                    targetSR   : this.targetSampleRate,
                }
            });
        }

        switch (this.state) {
            case S.CALIBRATING: this._doCalibrate(f32, pcmBuf, rms, nowMs); break;
            case S.SILENCE:     this._doSilence(f32, pcmBuf, rms, zcr, vbr, nowMs); break;
            case S.SPEAKING:    this._doSpeaking(f32, pcmBuf, rms, zcr, nowMs); break;
            case S.ENDING:      this._doEnding(f32, pcmBuf, rms, zcr, nowMs); break;
        }
    }

    // ── 状态：CALIBRATING ────────────────────────
    _doCalibrate(f32, pcmBuf, rms, nowMs) {
        this.calSum += rms;
        this.calFrames++;
        this._pushPre(pcmBuf);

        if (this.calFrames >= this.calTarget) {
            this.noiseEst = (this.calSum / this.calFrames) * 1.1;
            this.noiseEst = Math.max(this.noiseEst, this.p.minSilenceThreshold * 0.5);

            this.state = S.SILENCE;
            this.port.postMessage({
                type    : 'vadState',
                state   : 'ready',
                noiseEst: +this.noiseEst.toFixed(6),
                speechThr: +this._speechThr().toFixed(6),
            });
        }
    }

    // ── 状态：SILENCE ─────────────────────────────
    _doSilence(f32, pcmBuf, rms, zcr, vbr, nowMs) {
        if (this.p.autoNoiseAdaptation !== false) {
            this.noiseEst = this.noiseEst * (1 - this.p.noiseUpdateRate)
                          + rms            *      this.p.noiseUpdateRate;
            this.noiseEst = Math.max(this.noiseEst, this.p.minSilenceThreshold * 0.5);
        }

        this._pushPre(pcmBuf);

        const isVoiceLike = this._isVoiceLike(rms, zcr, vbr);

        if (isVoiceLike) {
            this.speechCnt++;
            if (this.speechCnt >= this.confirmTarget) {
                this.speechCnt  = 0;
                this.silenceCnt = 0;
                this.speechStartMs = nowMs;
                this.state = S.SPEAKING;

                this.port.postMessage({ type: 'speechStart' });

                for (const buf of this.preBuf) {
                    this.port.postMessage({ type: 'audioData', data: buf }, [buf]);
                }
                this.preBuf = [];
            }
        } else {
            this.speechCnt = 0;
        }
    }

    // ── 状态：SPEAKING ────────────────────────────
    _doSpeaking(f32, pcmBuf, rms, zcr, nowMs) {
        this.port.postMessage({ type: 'audioData', data: pcmBuf }, [pcmBuf]);

        const isSilent = rms < this._silenceThr();

        if (isSilent) {
            this.silenceCnt++;
            if (this.silenceCnt >= this.silFrameTarget) {
                this.silenceCnt = 0;
                this.speechCnt  = 0;
                this.state      = S.ENDING;
                this.postBuf    = [];
            }
        } else {
            this.silenceCnt = 0;
        }
    }

    // ── 状态：ENDING ──────────────────────────────
    _doEnding(f32, pcmBuf, rms, zcr, nowMs) {
        const isSilent = rms < this._silenceThr();

        if (!isSilent) {
            this.state      = S.SPEAKING;
            this.silenceCnt = 0;
            for (const buf of this.postBuf) {
                this.port.postMessage({ type: 'audioData', data: buf }, [buf]);
            }
            this.postBuf = [];
            this.port.postMessage({ type: 'audioData', data: pcmBuf }, [pcmBuf]);
            return;
        }

        this.postBuf.push(pcmBuf);

        if (this.postBuf.length >= this.postBufMax) {
            const speechDurationMs = nowMs - this.speechStartMs;

            if (speechDurationMs >= this.p.minSpeechDuration) {
                for (const buf of this.postBuf) {
                    this.port.postMessage({ type: 'audioData', data: buf }, [buf]);
                }
                this.port.postMessage({ type: 'speechEnd' });
            }

            this.postBuf    = [];
            this.speechCnt  = 0;
            this.silenceCnt = 0;
            this.state      = S.SILENCE;
        }
    }

    // ── 辅助：人声判断（多特征融合）─────────────
    _isVoiceLike(rms, zcr, vbr) {
        if (rms < this._speechThr()) return false;
        if (zcr < this.p.zcrMin || zcr > this.p.zcrMax) return false;
        if (vbr >= 0 && vbr < this.p.voiceBandRatioMin) return false;
        return true;
    }

    // ── 辅助：前填充环形缓冲 ─────────────────────
    _pushPre(pcmBuf) {
        this.preBuf.push(pcmBuf.slice(0));
        if (this.preBuf.length > this.preBufMax) {
            this.preBuf.shift();
        }
    }
}

registerProcessor('vad-processor', VADProcessor);
