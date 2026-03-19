/**
 * VAD AudioWorklet 处理器 v2.0
 * 
 * 核心升级：
 * 1. 自适应噪声基线估计 —— 冷启动校准 + 实时慢速追踪，动态计算阈值
 * 2. 多特征融合检测 —— RMS能量 + 过零率(ZCR) + 人声频带能量比(FFT)
 * 3. 5状态机 + 连续帧防抖 —— 彻底消除瞬时噪声/碰撞音/咳嗽音误触发
 * 4. 完全向后兼容旧参数格式
 *
 * 运行于 AudioWorklet 独立线程，零外部依赖，O(n) 计算，适配移动端低端设备。
 */

'use strict';

// ─────────────────────────────────────────────
// 极简 256 点 FFT（Cooley-Tukey，原位运算）
// 仅用于人声频带能量比分析，计算量极小
// ─────────────────────────────────────────────
function fft256(re, im) {
    const n = 256;
    // Bit-reversal permutation
    for (let i = 1, j = 0; i < n; i++) {
        let bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) {
            let t = re[i]; re[i] = re[j]; re[j] = t;
            t = im[i]; im[i] = im[j]; im[j] = t;
        }
    }
    // Butterfly
    for (let len = 2; len <= n; len <<= 1) {
        const half = len >> 1;
        const ang = -Math.PI / half; // -2π/len
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

        // 噪声基线
        this.noiseEst    = 0.01;

        // 校准
        this.calFrames   = 0;
        this.calSum      = 0;
        this.calTarget   = 0;

        // 防抖计数
        this.speechCnt   = 0;  // 连续超阈值帧数
        this.silenceCnt  = 0;  // 连续低于阈值帧数

        // 时间戳（ms）
        this.speechStartMs  = 0;

        // 前填充环形缓冲
        this.preBuf      = [];
        this.preBufMax   = 0;

        // 后填充缓冲
        this.postBuf     = [];
        this.postBufMax  = 0;

        // 防抖目标帧数（由参数换算）
        this.confirmTarget = 3;
        this.silFrameTarget = 40;

        // FFT 累积缓冲（256 点）
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

        if (this.vadEnabled && data.vadParams) {
            this.p = this._norm(data.vadParams);

            // 每帧固定 128 样本
            const fd = (128 / sampleRate) * 1000; // 帧时长 ms

            this.calTarget      = Math.max(10, Math.ceil(this.p.calibrationDuration / fd));
            this.preBufMax      = Math.max(1,  Math.ceil(this.p.preSpeechPadding   / fd));
            this.postBufMax     = Math.max(1,  Math.ceil(this.p.postSpeechPadding  / fd));
            this.confirmTarget  = Math.max(1,  this.p.confirmFrames);
            this.silFrameTarget = Math.max(1,  Math.ceil(this.p.silenceDuration    / fd));

            this._reset();

            // ✅ autoNoiseAdaptation 关闭时：跳过校准，直接用手动阈值计算固定噪声基线
            if (this.p.autoNoiseAdaptation === false) {
                // 从手动阈值反推噪声基线：noise = minSpeechThreshold / speechRatio
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
        // 兼容旧版绝对阈值参数：若没有新参数则推算比率
        const speechRatio  = p.speechRatio  ?? (p.speechThreshold  ? null : 3.5);
        const silenceRatio = p.silenceRatio ?? (p.silenceThreshold ? null : 1.8);

        return {
            // ✅ 自动环境噪声适应开关（默认开启）
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

    /** 过零率（每帧过零次数，不归一化，直接与 zcrMin/zcrMax 比较） */
    _zcr(f32) {
        let c = 0;
        for (let i = 1; i < f32.length; i++) {
            if ((f32[i] >= 0) !== (f32[i-1] >= 0)) c++;
        }
        return c;
    }

    /**
     * 人声频带能量比（300-3400 Hz 占总能量的比例）
     * 使用累积 FFT 缓冲：当累积满 256 样本时计算一次，否则返回 -1（跳过检查）
     */
    _voiceBandRatio(f32) {
        // 累积样本到 FFT 缓冲
        const need = 256 - this.fftFill;
        const take = Math.min(need, f32.length);
        this.fftAccum.set(f32.subarray(0, take), this.fftFill);
        this.fftFill += take;

        if (this.fftFill < 256) return -1; // 数据不足，本帧跳过

        // 执行 FFT
        const re = new Float32Array(this.fftAccum); // 拷贝，避免污染
        const im = new Float32Array(256);
        fft256(re, im);

        // 计算各频带能量（只用前 128 个正频率 bin）
        // bin 分辨率 = sampleRate / 256
        const binRes = sampleRate / 256;
        let voiceE = 0, totalE = 0;
        for (let k = 1; k < 128; k++) {
            const freq = k * binRes;
            const mag2 = re[k]*re[k] + im[k]*im[k];
            totalE += mag2;
            if (freq >= 300 && freq <= 3400) voiceE += mag2;
        }

        // 重置 FFT 缓冲（滑动：保留后半段，下次继续累积）
        this.fftAccum.copyWithin(0, 128);
        this.fftFill = 128;

        return totalE > 1e-10 ? voiceE / totalE : -1;
    }

    // ── AudioWorklet 主入口 ───────────────────────
    process(inputs) {
        if (this.isStopped) return false;

        const ch = inputs[0]?.[0];
        if (!ch) return true;

        // 转 PCM Int16
        const pcm = new Int16Array(ch.length);
        for (let i = 0; i < ch.length; i++) {
            const s = ch[i] < -1 ? -1 : ch[i] > 1 ? 1 : ch[i];
            pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        if (this.vadEnabled && this.p) {
            this._vad(ch, pcm.buffer);
        } else {
            this.port.postMessage({ type: 'audioData', data: pcm.buffer }, [pcm.buffer]);
        }
        return true;
    }

    // ── VAD 主逻辑 ────────────────────────────────
    _vad(f32, pcmBuf) {
        const rms = this._rms(f32);
        const zcr = this._zcr(f32);
        const vbr = this._voiceBandRatio(f32); // -1 表示本帧数据不足，跳过频域检查
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
            // 校准完成：以均值作为噪声基线（加一点裕量避免过于敏感）
            this.noiseEst = (this.calSum / this.calFrames) * 1.1;
            // 保证噪声估计有下限
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
        // ✅ 仅在自动噪声适应开启时才动态更新噪声基线
        if (this.p.autoNoiseAdaptation !== false) {
            // 更新噪声基线（慢速追踪）
            this.noiseEst = this.noiseEst * (1 - this.p.noiseUpdateRate)
                          + rms            *      this.p.noiseUpdateRate;
            // 保证下限
            this.noiseEst = Math.max(this.noiseEst, this.p.minSilenceThreshold * 0.5);
        }

        // 维护前填充缓冲
        this._pushPre(pcmBuf);

        // 判断是否是人声（多特征融合）
        const isVoiceLike = this._isVoiceLike(rms, zcr, vbr);

        if (isVoiceLike) {
            this.speechCnt++;
            if (this.speechCnt >= this.confirmTarget) {
                // 连续 N 帧确认：进入 SPEAKING
                this.speechCnt  = 0;
                this.silenceCnt = 0;
                this.speechStartMs = nowMs;
                this.state = S.SPEAKING;

                // 发送语音开始事件
                this.port.postMessage({ type: 'speechStart' });

                // 发送前填充缓冲（包含语音起始前的音频，当前帧已在 _pushPre 中拷贝入 preBuf）
                for (const buf of this.preBuf) {
                    this.port.postMessage({ type: 'audioData', data: buf }, [buf]);
                }
                this.preBuf = [];
                // ✅ 不再单独发送 pcmBuf：当前帧已经作为拷贝存入 preBuf 并在上面发出，
                //    避免对同一个 ArrayBuffer 二次转移导致 DataCloneError
            }
        } else {
            // 不像人声：重置防抖计数
            this.speechCnt = 0;
        }
    }

    // ── 状态：SPEAKING ────────────────────────────
    _doSpeaking(f32, pcmBuf, rms, zcr, nowMs) {
        // 持续发送音频
        this.port.postMessage({ type: 'audioData', data: pcmBuf }, [pcmBuf]);

        const isSilent = rms < this._silenceThr();

        if (isSilent) {
            this.silenceCnt++;
            if (this.silenceCnt >= this.silFrameTarget) {
                // 持续静音达标：进入 ENDING（发送后填充）
                this.silenceCnt = 0;
                this.speechCnt  = 0;
                this.state      = S.ENDING;
                this.postBuf    = [];
            }
        } else {
            // 继续说话：重置静音计数
            this.silenceCnt = 0;
        }
    }

    // ── 状态：ENDING ──────────────────────────────
    _doEnding(f32, pcmBuf, rms, zcr, nowMs) {
        const isSilent = rms < this._silenceThr();

        if (!isSilent) {
            // 又检测到声音：返回 SPEAKING
            this.state      = S.SPEAKING;
            this.silenceCnt = 0;
            // 把后填充缓冲里的帧补发
            for (const buf of this.postBuf) {
                this.port.postMessage({ type: 'audioData', data: buf }, [buf]);
            }
            this.postBuf = [];
            this.port.postMessage({ type: 'audioData', data: pcmBuf }, [pcmBuf]);
            return;
        }

        // 仍然静音：累积后填充帧
        this.postBuf.push(pcmBuf);

        if (this.postBuf.length >= this.postBufMax) {
            // 后填充已满：语音真正结束
            const speechDurationMs = nowMs - this.speechStartMs;

            if (speechDurationMs >= this.p.minSpeechDuration) {
                // 发送后填充缓冲
                for (const buf of this.postBuf) {
                    this.port.postMessage({ type: 'audioData', data: buf }, [buf]);
                }
                // 发送语音结束事件
                this.port.postMessage({ type: 'speechEnd' });
            }
            // 不满足最短时长：静默丢弃（短暂噪声/咳嗽），不发 speechEnd

            // 回到 SILENCE
            this.postBuf    = [];
            this.speechCnt  = 0;
            this.silenceCnt = 0;
            this.state      = S.SILENCE;
        }
    }

    // ── 辅助：人声判断（多特征融合）─────────────
    /**
     * 综合 RMS、ZCR、频带能量比判断是否像人声
     * 任一特征明显排除则返回 false
     */
    _isVoiceLike(rms, zcr, vbr) {
        // 1. 能量必须超过动态语音阈值
        if (rms < this._speechThr()) return false;

        // 2. ZCR 过滤：
        //    - ZCR 极低（< zcrMin）：冲击音/碰撞噪声（单次爆破）
        //    - ZCR 极高（> zcrMax）：高频噪声/风噪
        if (zcr < this.p.zcrMin || zcr > this.p.zcrMax) return false;

        // 3. 频带能量比过滤（仅在 FFT 数据充足时检查）
        //    人声主要集中在 300-3400 Hz，该频带能量占比应 > voiceBandRatioMin
        if (vbr >= 0 && vbr < this.p.voiceBandRatioMin) return false;

        return true;
    }

    // ── 辅助：前填充环形缓冲 ─────────────────────
    // ✅ 修复 DataCloneError：存入前必须拷贝 ArrayBuffer，
    //    防止原始 pcmBuf 被 postMessage 转移后 preBuf 中留有 detached 引用
    _pushPre(pcmBuf) {
        this.preBuf.push(pcmBuf.slice(0));
        if (this.preBuf.length > this.preBufMax) {
            this.preBuf.shift(); // 丢弃最旧帧（环形）
        }
    }
}

registerProcessor('vad-processor', VADProcessor);
