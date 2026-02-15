/**
 * MuseumAgent Demo应用
 * 整合所有模块，作为应用的入口点
 */

// 导入模块
import { authModule } from './modules/auth.js';
import { chatModule } from './modules/chat.js';
import { recorderModule } from './modules/recorder.js';
import { uiModule } from './modules/ui.js';
import { VADModule } from './modules/vad.js';
import { AudioModule } from './modules/audio.js';
import { delay } from './utils/helpers.js';

// 全局变量，用于在HTML中访问模块
window.chatModule = chatModule;

class MuseumAgentDemo {
    constructor() {
        this.client = null;
        this.isInCall = false;
        this.recordingMode = null; // null: 未录音, 'manual': 手动录音, 'auto': 自动检测
        this.callStartTime = 0;
        this.callTimer = null;
        
        // 累积状态，用于处理同时包含文本和函数调用的消息
        this.pendingMessage = {
            text: '',
            functionCall: null
        };
        
        // 音频模块
        this.audioModule = new AudioModule();
        
        // VAD 模块
        this.vadModule = new VADModule();

        this.init();
    }
    
    init() {
        // 初始化认证模块
        authModule.init();
        
        // 从localStorage获取服务器地址
                let serverUrl = authModule.baseUrl || 'http://localhost:8003';
                
                console.log('[初始化] 使用的服务器地址:', serverUrl);
        
        // 创建客户端实例
        this.client = new MuseumAgentClient({
            baseUrl: serverUrl,
            timeout: 30000,
            autoReconnect: true,
            reconnectInterval: 5000,
            heartbeatInterval: 30000
        });
        
        // 设置会话ID
        const savedSessionId = authModule.sessionId;
        if (savedSessionId) {
            this.client.sessionId = savedSessionId;
        }
        
        // 初始化录音模块
        recorderModule.init(this.client, this.vadModule);
        
        // 绑定VAD配置变化事件
        this.bindVADConfigEvents();
        
        // 初始化UI模块
        uiModule.init();
        
        // 绑定事件
        this.bindEvents();
        
        // 设置客户端事件处理器
        this.setupClientEventHandlers();
        
        console.log('[初始化] Demo应用初始化完成');
    }
    
    bindEvents() {
        // 发送消息按钮
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        if (sendMessageBtn) {
            sendMessageBtn.addEventListener('click', () => this.handleSendMessage());
        }
        
        // 录音切换按钮
        const recordToggleBtn = document.getElementById('recordToggleBtn');
        if (recordToggleBtn) {
            recordToggleBtn.addEventListener('click', () => this.handleRecordToggle());
        }
        
        // 清空日志按钮
        const clearLogBtn = document.getElementById('clearLogBtn');
        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => chatModule.clearLog());
        }
        
        // 会话信息查询按钮
        const querySessionBtn = document.getElementById('querySessionBtn');
        if (querySessionBtn) {
            querySessionBtn.addEventListener('click', () => this.handleQuerySessionInfo());
        }
        
        // 聊天输入框键盘事件
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });
        }
    }
    
    bindVADConfigEvents() {
        // VAD启用开关
        const vadEnabled = document.getElementById('vadEnabled');
        if (vadEnabled) {
            vadEnabled.addEventListener('change', (e) => {
                this.updateVADConfig();
                console.log('[VAD] VAD已', e.target.checked ? '启用' : '禁用');
            });
        }
        
        // VAD配置参数变化
        const vadConfigInputs = [
            'vadSilenceDuration',
            'vadPositiveThreshold',
            'vadNegativeThreshold',
            'vadPreSpeechPad',
            'vadRedemptionFrames',
            'vadMinSpeechFrames'
        ];
        
        vadConfigInputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    this.updateVADConfig();
                });
            }
        });
    }
    
    updateVADConfig() {
        const config = {
            enabled: document.getElementById('vadEnabled')?.checked || false,
            silenceDuration: parseInt(document.getElementById('vadSilenceDuration')?.value || '1000'),
            positiveSpeechThreshold: parseFloat(document.getElementById('vadPositiveThreshold')?.value || '0.5'),
            negativeSpeechThreshold: parseFloat(document.getElementById('vadNegativeThreshold')?.value || '0.35'),
            preSpeechPadFrames: parseInt(document.getElementById('vadPreSpeechPad')?.value || '1'),
            redemptionFrames: parseInt(document.getElementById('vadRedemptionFrames')?.value || '8'),
            minSpeechFrames: parseInt(document.getElementById('vadMinSpeechFrames')?.value || '3')
        };
        
        recorderModule.setVADConfig(config);
        
        // 保存VAD配置到localStorage
        localStorage.setItem('vadEnabled', config.enabled.toString());
        localStorage.setItem('vadSilenceDuration', config.silenceDuration.toString());
        localStorage.setItem('vadPositiveThreshold', config.positiveSpeechThreshold.toString());
        localStorage.setItem('vadNegativeThreshold', config.negativeSpeechThreshold.toString());
        localStorage.setItem('vadPreSpeechPadFrames', config.preSpeechPadFrames.toString());
        localStorage.setItem('vadRedemptionFrames', config.redemptionFrames.toString());
        localStorage.setItem('vadMinSpeechFrames', config.minSpeechFrames.toString());
        
        console.log('[VAD] 配置已更新:', config);
        console.log('[VAD] 配置已保存到localStorage');
    }
    
    setupClientEventHandlers() {
        this.client.on('login', (data) => {
            chatModule.log('success', '登录成功');
            uiModule.updateUIState(true);
        });
        
        this.client.on('error', (data) => {
            const errorMessage = data.error?.message || JSON.stringify(data.error);
            chatModule.log('error', `错误: ${data.type} - ${errorMessage}`);
            
            // 处理会话无效错误
            if (data.type === 'stream' && data.error?.error_code === 'SESSION_INVALID') {
                chatModule.log('error', '会话已失效，请重新登录');
                // 清理会话状态
                authModule.clearSession();
                this.client.sessionId = null;
                // 更新UI显示
                chatModule.updateSessionStatus('disconnected', null);
                // 可以在这里添加重定向到登录页面的逻辑
            }
        });
        
        this.client.on('session_registered', (data) => {
            let sessionId = this.client.sessionId;
            
            if (sessionId && typeof sessionId === 'string') {
                chatModule.log('success', `会话注册成功: ${sessionId}`);
                // 更新UI显示
                chatModule.updateSessionStatus('connected', sessionId);
                // 保存会话ID
                authModule.saveSessionId(sessionId);
                chatModule.log('info', '会话ID已保存到本地存储');
            } else {
                chatModule.log('error', '会话注册成功但未返回session_id');
                console.error('[Session] 会话注册成功但未返回session_id:', data);
            }
        });
        
        this.client.on('session_disconnected', (data) => {
            chatModule.log('info', '会话已断开');
            // 更新UI显示
            chatModule.updateSessionStatus('disconnected', null);
            // 清除本地存储中的会话ID
            authModule.clearSession();
            this.client.sessionId = null;
            chatModule.log('info', '会话ID已从本地存储清除');
        });
        
        // 不需要再处理agent_response事件，因为已经在sendTextRequest的onChunk回调中处理了
        // this.client.on('agent_response', (data) => {
        //     chatModule.log('success', '收到智能体响应');
        //     chatModule.addMessage('received', data.content || JSON.stringify(data));
        // });
        
        this.client.on('ws_connected', (data) => {
            chatModule.log('success', `WebSocket连接成功: ${data.type}`);
        });
        
        this.client.on('ws_disconnected', (data) => {
            chatModule.log('info', `WebSocket连接断开: ${data.type}`);
        });
        
        // 不需要再处理stream_chunk事件，因为已经在sendTextRequest的onChunk回调中处理了
        // this.client.on('stream_chunk', (data) => {
        //     // 实时更新消息内容
        //     const lastMessage = document.querySelector('.message.received:last-child .message-content');
        //     if (lastMessage) {
        //         lastMessage.textContent += data.chunk;
        //     } else {
        //         chatModule.addMessage('received', data.chunk);
        //     }
        //     chatModule.log('info', `收到流式数据块: ${data.chunk.length} 字符`);
        // });

        this.client.on('audio_chunk', (data) => {
            const receiveTime = performance.now();
            chatModule.log('info', `收到音频数据块: ${data.size} 字节, seq: ${data.voice_stream_seq || 0}`);
            console.log('[audio_chunk] 事件触发，data:', data, '接收时间:', receiveTime);

            // 如果是第一个音频块，创建语音消息元素
            if (!this.voiceMessageDiv) {
                console.log('[audio_chunk] 创建语音消息气泡');
                // 直接创建一个新的语音消息气泡，不要修改已有的文本消息气泡
                // 创建一个最小的有效WAV文件(包含44字节WAV头 + 0字节数据)
                const minimalWavHeader = new Uint8Array([
                    // RIFF header (12 bytes)
                    0x52, 0x49, 0x46, 0x46, // "RIFF"
                    0x24, 0x00, 0x00, 0x00, // file size - 8
                    0x57, 0x41, 0x56, 0x45, // "WAVE"
                    // fmt sub-chunk (24 bytes)
                    0x66, 0x6D, 0x74, 0x20, // "fmt "
                    0x10, 0x00, 0x00, 0x00, // chunk size
                    0x01, 0x00, // audio format (PCM)
                    0x01, 0x00, // channels (1)
                    0x40, 0x3D, 0x00, 0x00, // sample rate (16000)
                    0x80, 0x7A, 0x00, 0x00, // byte rate (32000)
                    0x02, 0x00, // block align (2)
                    0x10, 0x00, // bits per sample (16)
                    // data sub-chunk header (8 bytes)
                    0x64, 0x61, 0x74, 0x61, // "data"
                    0x00, 0x00, 0x00, 0x00  // data size (0)
                ]);
                const minimalBlob = new Blob([minimalWavHeader.buffer], { type: 'audio/wav' });
                this.voiceMessageDiv = chatModule.addMessage('received', null, minimalBlob, 0);
                console.log('[audio_chunk] 语音消息气泡已创建:', this.voiceMessageDiv);
                // 显示"播放中..."而不是实时计数
                const durationElement = this.voiceMessageDiv.querySelector('.voice-duration');
                if (durationElement) {
                    durationElement.textContent = '播放中...';
                }
            }

            // 检查是否启用了自动播放语音消息
            const autoPlayVoiceCheckbox = document.getElementById('autoPlayVoice');
            const shouldAutoPlay = autoPlayVoiceCheckbox ? autoPlayVoiceCheckbox.checked : false;

            // 如果有音频数据且启用了自动播放，立即播放（流式播放）
            if (data.audioData && shouldAutoPlay) {
                // 缓存音频数据用于后续完整时长计算
                this.audioModule.audioChunks.push(data.audioData);

                // 立即播放当前音频片段（流式播放 - 使用预调度优化）
                const playStartTime = performance.now();
                this.audioModule._playAudioChunkImmediately(data.audioData);
                const playScheduleTime = performance.now() - playStartTime;
                console.log('[audio_chunk] 音频片段已调度播放，调度耗时:', playScheduleTime.toFixed(2), 'ms');

                // 检测是否是最后一个音频块（voice_stream_seq: -1）
                if (data.voice_stream_seq === -1) {
                    console.log('[audio_chunk] 检测到音频流结束信号，自动处理完整音频');
                    // 延迟一点处理，确保所有音频数据都已接收
                    setTimeout(async () => {
                        if (this.audioModule.audioChunks.length > 0 && this.voiceMessageDiv) {
                            await this.audioModule._finalizeAudio(this.voiceMessageDiv);
                        }
                    }, 100);
                }
            } else if (data.audioData) {
                // 缓存音频数据用于后续完整时长计算，但不自动播放
                this.audioModule.audioChunks.push(data.audioData);
                console.log('[audio_chunk] 音频数据已缓存，但未自动播放（自动播放已禁用）');

                // 检测是否是最后一个音频块（voice_stream_seq: -1）
                if (data.voice_stream_seq === -1) {
                    console.log('[audio_chunk] 检测到音频流结束信号，处理完整音频');
                    // 延迟一点处理，确保所有音频数据都已接收
                    setTimeout(async () => {
                        if (this.audioModule.audioChunks.length > 0 && this.voiceMessageDiv) {
                            await this.audioModule._finalizeAudio(this.voiceMessageDiv);
                        }
                    }, 100);
                }
            } else {
                chatModule.log('info', '收到空音频数据块，但已创建语音消息气泡');
            }
        });
        
        this.client.on('audio_complete', async (data) => {
            console.log('[audio_complete] 事件触发');
            // 如果还没有创建语音消息气泡（可能只收到了audio_complete消息而没有收到audio_chunk消息），则创建它
            if (!this.voiceMessageDiv) {
                console.log('[audio_complete] 创建语音消息气泡');
                // 添加语音回复到聊天窗，初始时长为0
                // 创建一个最小的有效WAV文件(包含44字节WAV头 + 0字节数据)
                const minimalWavHeader = new Uint8Array([
                    // RIFF header (12 bytes)
                    0x52, 0x49, 0x46, 0x46, // "RIFF"
                    0x24, 0x00, 0x00, 0x00, // file size - 8
                    0x57, 0x41, 0x56, 0x45, // "WAVE"
                    // fmt sub-chunk (24 bytes)
                    0x66, 0x6D, 0x74, 0x20, // "fmt "
                    0x10, 0x00, 0x00, 0x00, // chunk size
                    0x01, 0x00, // audio format (PCM)
                    0x01, 0x00, // channels (1)
                    0x40, 0x3D, 0x00, 0x00, // sample rate (16000)
                    0x80, 0x7A, 0x00, 0x00, // byte rate (32000)
                    0x02, 0x00, // block align (2)
                    0x10, 0x00, // bits per sample (16)
                    // data sub-chunk header (8 bytes)
                    0x64, 0x61, 0x74, 0x61, // "data"
                    0x00, 0x00, 0x00, 0x00  // data size (0)
                ]);
                const minimalBlob = new Blob([minimalWavHeader.buffer], { type: 'audio/wav' });
                this.voiceMessageDiv = chatModule.addMessage('received', null, minimalBlob, 0);
                console.log('[audio_complete] 语音消息气泡已创建:', this.voiceMessageDiv);
            }

            if (data.audioData) {
                chatModule.log('info', `收到完整音频数据: ${data.audioData.size} 字节`);
                // 如果有完整的音频数据，添加到缓存中
                this.audioModule.audioChunks.push(data.audioData);
            } else {
                chatModule.log('info', '音频流传输完成');
            }

            // 停止音频时长计时器
            if (this.audioModule.audioTimer) {
                clearInterval(this.audioModule.audioTimer);
                this.audioModule.audioTimer = null;
            }

            // 处理所有音频数据块，缓存PCM数据
            await this.audioModule._processAudioChunks();

            // 处理完整的音频数据
            await this.audioModule._finalizeAudio(this.voiceMessageDiv);
        });

        // 监听流式生成完成事件，触发音频处理
        this.client.on('stream_complete', async (data) => {
            console.log('[stream_complete] 事件触发，检查是否有音频数据');
            // 如果有缓存的音频数据块，处理它们
            if (this.audioModule.audioChunks.length > 0 && this.voiceMessageDiv) {
                chatModule.log('info', `发现 ${this.audioModule.audioChunks.length} 个音频数据块，开始处理`);

                // 停止音频时长计时器
                if (this.audioModule.audioTimer) {
                    clearInterval(this.audioModule.audioTimer);
                    this.audioModule.audioTimer = null;
                }

                // 处理所有音频数据块
                await this.audioModule._processAudioChunks();

                // 处理完整的音频数据
                await this.audioModule._finalizeAudio(this.voiceMessageDiv);
            }
        });
        
        this.client.on('function_call', (data) => {
            const params = data.function.parameters ?? data.function.arguments ?? {};
            chatModule.log('info', `收到函数调用: ${data.function.name}(${JSON.stringify(params)})`);
            const functionName = data.function.name;
            const args = params;
            let formattedArgs = '';
            
            if (args && typeof args === 'object' && Object.keys(args).length > 0) {
                // 如果有参数，格式化为逗号分隔的键值对
                formattedArgs = '(' + Object.entries(args).map(([key, value]) => 
                    `${key}=${typeof value === 'string' ? `"${value}"` : value}`
                ).join(', ') + ')';
            } else {
                // 如果没有参数，显示空括号
                formattedArgs = '()';
            }
            
            const functionCallDisplay = `[${functionName}${formattedArgs}]`;
            chatModule.addMessage('received', functionCallDisplay, null, null, {isFunctionCall: true});
        });
    }
    
    /**
     * 初始化Web Audio API
     */
    _initWebAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('[WebAudio] AudioContext创建成功，采样率:', this.audioContext.sampleRate);
        } catch (error) {
            console.error('[WebAudio] 初始化失败:', error);
        }
    }

    /**
     * 播放PCM音频（核心方法）
     * @param {ArrayBuffer} pcmData - PCM原始二进制数据
     * @param {Object} config - PCM参数
     */
    async _playPCM(pcmData, config = {}) {
        return new Promise((resolve, reject) => {
            try {
                const { sampleRate = 16000, bitDepth = 16, channels = 1 } = config;
                
                console.log('[WebAudio] 开始播放PCM，参数:', { sampleRate, bitDepth, channels });
                
                // 1. 停止当前播放（避免重复叠加）
                if (this.currentSource) {
                    this.currentSource.stop();
                    this.currentSource.disconnect();
                    this.currentSource = null;
                }
                
                // 2. 初始化音频上下文
                if (!this.audioContext) {
                    this._initWebAudio();
                }
                
                if (this.audioContext && this.audioContext.state === 'suspended') {
                    this.audioContext.resume().then(() => {
                        this._continuePlayPCM(pcmData, config, resolve, reject);
                    }).catch(err => {
                        console.error('[WebAudio] AudioContext恢复失败:', err);
                        reject(err);
                    });
                } else {
                    this._continuePlayPCM(pcmData, config, resolve, reject);
                }
            } catch (error) {
                console.error('[WebAudio] 播放PCM失败:', error);
                this.isPlaying = false;
                reject(error);
            }
        });
    }

    /**
     * 继续播放PCM音频（内部方法）
     */
    _continuePlayPCM(pcmData, config, resolve, reject) {
        try {
            const { sampleRate = 16000, bitDepth = 16, channels = 1 } = config;
            
            // 3. 将PCM数据转换为AudioBuffer可识别的格式
            const sampleCount = pcmData.byteLength / (bitDepth / 8);
            const audioBuffer = this.audioContext.createBuffer(
                channels,
                sampleCount,
                sampleRate
            );
            
            // 4. 将PCM数据填充到AudioBuffer（关键：用Int16Array解析）
            const pcmArray = new Int16Array(pcmData);
            for (let channel = 0; channel < channels; channel++) {
                const channelData = audioBuffer.getChannelData(channel);
                for (let i = 0; i < sampleCount; i++) {
                    channelData[i] = pcmArray[i] / 32768;
                }
            }
            
            // 5. 创建音频源并播放（避免重复）
            this.currentSource = this.audioContext.createBufferSource();
            this.currentSource.buffer = audioBuffer;
            this.currentSource.connect(this.audioContext.destination);
            
            this.currentSource.onended = () => {
                console.log('[WebAudio] 音频播放完成');
                this.isPlaying = false;
                this.currentSource = null;
                resolve();
            };
            
            this.isPlaying = true;
            this.currentSource.start();
            console.log('[WebAudio] 开始播放音频');
            
        } catch (error) {
            console.error('[WebAudio] 播放PCM失败:', error);
            this.isPlaying = false;
            reject(error);
        }
    }

    /**
     * 播放完整的PCM音频数据
     */
    async _playPcmAudio() {
        if (this.allPcmChunks.length === 0 || this.isPlaying) {
            return;
        }
        
        try {
            // 合并所有PCM数据块
            const totalLength = this.allPcmChunks.reduce((sum, chunk) => sum + chunk.length, 0);
            const combinedPcm = new Uint8Array(totalLength);
            let offset = 0;
            for (const chunk of this.allPcmChunks) {
                combinedPcm.set(chunk, offset);
                offset += chunk.length;
            }
            
            console.log('[WebAudio] 合并PCM数据，总长度:', combinedPcm.length, 'bytes');
            
            // 播放PCM音频
            await this._playPCM(combinedPcm.buffer, {
                sampleRate: 16000,
                bitDepth: 16,
                channels: 1
            });
            
        } catch (error) {
            console.error('[WebAudio] 播放音频失败:', error);
            this.isPlaying = false;
        }
    }

    /**
     * 处理音频数据块，直接缓存
     */
    async _processAudioChunks() {
        const validAudioChunks = this.audioChunks.filter(chunk => chunk !== null);

        console.log('[WebAudio] 开始处理音频数据块，有效数据块数量:', validAudioChunks.length);

        if (validAudioChunks.length === 0) {
            console.log('[WebAudio] 没有有效音频数据块，跳过处理');
            return;
        }

        try {
            // 直接缓存音频数据块，不进行任何转换
            console.log('[WebAudio] 音频数据块已缓存，等待处理');
            console.log('[WebAudio] 音频数据块详情:', validAudioChunks.map(chunk => ({
                size: chunk.size,
                type: chunk.type
            })));
        } catch (error) {
            console.error('[WebAudio] 处理音频数据块失败:', error);
        }
    }
    
    /**
     * 处理完整的音频数据（立即执行，不延迟）
     */
    async _finalizeAudio() {
        // 检查是否已经处理过音频数据
        if (this._audioProcessing) {
            console.log('[WebAudio] 音频数据已经在处理中，跳过重复处理');
            return;
        }

        this._audioProcessing = true;

        try {
            // 立即处理音频数据，不使用异步延迟
            if (this.audioChunks.length > 0) {
                console.log('[WebAudio] 开始处理音频数据，数据块数量:', this.audioChunks.length);

                // 合并所有音频数据块
                const totalSize = this.audioChunks.reduce((sum, chunk) => sum + chunk.size, 0);
                console.log('[WebAudio] 总音频数据大小:', totalSize, 'bytes');

                // 读取所有音频数据块并合并为Uint8Array
                const audioArrays = await Promise.all(
                    this.audioChunks.map(async (chunk) => {
                        const arrayBuffer = await chunk.arrayBuffer();
                        return new Uint8Array(arrayBuffer);
                    })
                );

                const combinedAudio = new Uint8Array(totalSize);
                let offset = 0;
                for (const arr of audioArrays) {
                    combinedAudio.set(arr, offset);
                    offset += arr.length;
                }

                console.log('[WebAudio] PCM音频数据已合并，大小:', combinedAudio.length, 'bytes');

                // 可选：移除过长的静音片段（如果需要更紧凑的播放）
                const removeExcessiveSilence = false; // 设为 true 启用静音移除
                let processedAudio = combinedAudio;
                
                if (removeExcessiveSilence) {
                    console.log('[WebAudio] 开始移除过长静音片段...');
                    processedAudio = this._removeSilence(combinedAudio, 0.2); // 移除超过200ms的静音
                    console.log('[WebAudio] 静音移除完成，原始大小:', combinedAudio.length, '处理后:', processedAudio.length);
                }

                // 服务端现在统一发送裸PCM格式（16kHz/16bit/单声道）
                // 直接创建PCM Blob，无需WAV封装
                const audioBlob = new Blob([processedAudio.buffer], { type: 'audio/pcm' });
                
                // PCM时长 = 数据大小 / (采样率 * 声道数 * 每样本字节数)
                // 16-bit PCM, 16kHz, 单声道: 每秒 = 16000 * 1 * 2 = 32000 字节
                const duration = Math.round(processedAudio.length / 32000);
                console.log('[WebAudio] PCM音频信息:', { dataSize: processedAudio.length, duration, sampleRate: 16000, channels: 1 });

                console.log('[WebAudio] 创建PCM Blob，大小:', audioBlob.size, 'bytes', '类型:', audioBlob.type, '时长:', duration, 's');

                // 更新语音消息的时长
                if (this.voiceMessageDiv) {
                    const durationElement = this.voiceMessageDiv.querySelector('.voice-duration');
                    if (durationElement) {
                        const minutes = Math.floor(duration / 60).toString().padStart(2, '0');
                        const seconds = (duration % 60).toString().padStart(2, '0');
                        durationElement.textContent = `${minutes}:${seconds}`;
                        console.log('[WebAudio] 更新语音消息时长:', durationElement.textContent);
                    }
                }

                // 更新语音消息的音频数据
                if (this.voiceMessageDiv) {
                    const voiceMessage = this.voiceMessageDiv.querySelector('.voice-message');
                    if (voiceMessage) {
                        // 保存旧的URL，等新的URL设置成功后再清理
                        const oldAudioUrl = voiceMessage.dataset.audioUrl;

                        // 更新语音消息的data-audio-url和data-audio-id属性
                        const audioUrl = URL.createObjectURL(audioBlob);
                        const audioId = `audio-${Date.now()}`;
                        voiceMessage.dataset.audioUrl = audioUrl;
                        voiceMessage.dataset.audioId = audioId;
                        console.log('[WebAudio] 语音消息音频数据已更新（可反复播放）:', { audioUrl, audioId, blobSize: audioBlob.size });

                        // 将完整的音频Blob存储到语音消息对象中，供点击事件使用
                        voiceMessage._fullAudioBlob = audioBlob;
                        console.log('[WebAudio] 完整音频Blob已存储到语音消息元素，支持点击反复播放');

                        // 延迟清理旧的音频URL（确保新的URL已经设置成功）
                        if (oldAudioUrl && oldAudioUrl !== audioUrl) {
                            setTimeout(() => {
                                try {
                                    URL.revokeObjectURL(oldAudioUrl);
                                    console.log('[WebAudio] 清理旧的音频URL:', oldAudioUrl);
                                } catch (error) {
                                    console.error('[WebAudio] 清理旧URL失败:', error);
                                }
                            }, 100);
                        }
                    }
                }
            } else {
                console.log('[WebAudio] 没有音频数据可处理');
            }

        } catch (error) {
            console.error('[WebAudio] 处理音频数据失败:', error);
        } finally {
            // 清理资源
            this._cleanupAudioResources();
            this._audioProcessing = false;
            console.log('[WebAudio] 音频处理完成，资源已清理');
        }
    }

    /**
     * 立即播放音频片段（流式播放 - 优化版）
     * @param {Blob} audioChunk - 音频片段
     */
    async _playAudioChunkImmediately(audioChunk) {
        try {
            const chunkReceiveTime = performance.now();
            
            // 将音频片段加入播放队列
            this._audioQueue.push(audioChunk);
            console.log('[WebAudio] 音频片段加入播放队列，队列长度:', this._audioQueue.length, 
                       '片段大小:', audioChunk.size, 'bytes');

            // 如果没有正在播放，立即开始播放队列
            if (!this._isPlayingQueue) {
                const playStartTime = performance.now();
                const queueDelay = playStartTime - chunkReceiveTime;
                console.log('[WebAudio] 启动播放队列，队列延迟:', queueDelay.toFixed(2), 'ms');
                
                // 不使用 await，让播放在后台进行，避免阻塞后续音频片段的接收
                this._playAudioQueue().catch(error => {
                    console.error('[WebAudio] 播放队列失败:', error);
                });
            } else {
                console.log('[WebAudio] 播放队列正在运行，音频片段已加入队列等待播放');
            }
        } catch (error) {
            console.error('[WebAudio] 播放音频片段失败:', error);
        }
    }

    /**
     * 播放音频队列（边解码边播放，PCM优化版）
     * 收到PCM数据后立即解码并播放，无需等待所有片段
     */
    async _playAudioQueue() {
        if (this._isPlayingQueue) {
            return;
        }

        this._isPlayingQueue = true;

        // 初始化AudioContext
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('[WebAudio] 初始化AudioContext，采样率:', this.audioContext.sampleRate);
        }

        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
            console.log('[WebAudio] 恢复AudioContext');
        }

        console.log('[WebAudio] 开始播放音频队列（PCM流式模式），初始队列长度:', this._audioQueue.length);

        // 初始化播放调度时间
        let nextStartTime = this.audioContext.currentTime + 0.05; // 50ms初始缓冲
        const sources = [];
        
        // 持续处理队列中的PCM音频片段
        while (this._audioQueue.length > 0) {
            const audioChunk = this._audioQueue.shift();
            console.log('[WebAudio] 处理PCM片段，剩余队列:', this._audioQueue.length);
            
            try {
                // 立即解码PCM数据（无需等待）
                const decodeStartTime = performance.now();
                const audioBuffer = await this._decodeAudioChunk(audioChunk);
                const decodeTime = performance.now() - decodeStartTime;
                
                if (!audioBuffer) {
                    console.warn('[WebAudio] PCM片段解码失败，跳过');
                    continue;
                }
                
                console.log('[WebAudio] PCM片段解码完成，耗时:', decodeTime.toFixed(2), 'ms，时长:', audioBuffer.duration.toFixed(3), 's');
                
                // 创建音频源并立即调度
                const source = this.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                
                const gainNode = this.audioContext.createGain();
                gainNode.gain.value = 1.0;
                source.connect(gainNode);
                gainNode.connect(this.audioContext.destination);
                
                // 计算播放时间（确保无缝衔接）
                const startTime = Math.max(nextStartTime, this.audioContext.currentTime);
                nextStartTime = startTime + audioBuffer.duration;
                
                // 开始播放
                source.start(startTime);
                sources.push({ source, gainNode, startTime, duration: audioBuffer.duration });
                
                console.log('[WebAudio] PCM片段已调度播放，开始时间:', startTime.toFixed(3), '下一片段时间:', nextStartTime.toFixed(3));
                
            } catch (error) {
                console.error('[WebAudio] 处理PCM片段失败:', error);
            }
        }

        // 等待所有音频播放完成
        if (sources.length > 0) {
            const lastSource = sources[sources.length - 1];
            const totalDuration = (lastSource.startTime + lastSource.duration - this.audioContext.currentTime) * 1000;
            
            console.log('[WebAudio] 所有音频片段已调度，共', sources.length, '个片段，总时长:', (totalDuration / 1000).toFixed(3), 's');
            
            // 等待播放完成
            await new Promise(resolve => {
                setTimeout(() => {
                    console.log('[WebAudio] 音频队列播放完成');
                    // 清理资源
                    sources.forEach(({ source, gainNode }) => {
                        try {
                            gainNode.disconnect();
                        } catch (e) {
                            // 忽略断开连接时的错误
                        }
                    });
                    resolve();
                }, Math.max(totalDuration + 100, 100)); // 至少等待100ms
            });
        }

        this._isPlayingQueue = false;
        console.log('[WebAudio] 播放队列已结束');
    }

    /**
     * 解码音频片段（统一PCM解码逻辑）
     * @param {Blob} audioChunk - 音频片段（裸PCM格式）
     * @returns {Promise<AudioBuffer>} - 解码后的AudioBuffer
     */
    async _decodeAudioChunk(audioChunk) {
        const startTime = performance.now();
        const arrayBuffer = await audioChunk.arrayBuffer();
        const readTime = performance.now() - startTime;
        
        if (arrayBuffer.byteLength < 4) {
            console.warn('[WebAudio] 音频数据太小，跳过');
            return null;
        }

        // 服务端现在统一发送裸PCM格式（16kHz/16bit/单声道）
        // 直接使用PCM解码，无需检测WAV头
        let audioBuffer;
        const decodeStartTime = performance.now();
        
        try {
            audioBuffer = await this._createAudioBufferFromPCM(arrayBuffer);
            const decodeTime = performance.now() - decodeStartTime;
            console.log('[WebAudio] PCM解码完成，大小:', arrayBuffer.byteLength, 'bytes，时长:', audioBuffer.duration.toFixed(3), 's，耗时:', decodeTime.toFixed(2), 'ms');
        } catch (error) {
            console.error('[WebAudio] PCM解码失败:', error);
            return null;
        }

        // 验证音频内容（快速检查）
        if (audioBuffer) {
            const channelData = audioBuffer.getChannelData(0);
            let nonZeroCount = 0;
            const checkSamples = Math.min(100, channelData.length);
            for (let i = 0; i < checkSamples; i++) {
                if (Math.abs(channelData[i]) > 0.001) {
                    nonZeroCount++;
                }
            }
            
            if (nonZeroCount === 0) {
                console.warn('[WebAudio] 警告：音频片段可能是静音（前', checkSamples, '个样本全为0）');
            }
        }

        return audioBuffer;
    }

    /**
     * 播放单个音频片段（已废弃，保留用于兼容）
     * @deprecated 请使用预调度播放模式
     */
    async _playSingleAudioChunk(audioChunk) {
        console.warn('[WebAudio] _playSingleAudioChunk已废弃，请使用预调度播放模式');
        const audioBuffer = await this._decodeAudioChunk(audioChunk);
        if (!audioBuffer) return;

        return new Promise((resolve) => {
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            const gainNode = this.audioContext.createGain();
            gainNode.gain.value = 1.0;
            source.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            source.onended = () => {
                gainNode.disconnect();
                resolve();
            };
            
            source.start();
            
            setTimeout(() => {
                gainNode.disconnect();
                resolve();
            }, audioBuffer.duration * 1000 + 50);
        });
    }

    /**
     * 移除PCM数据中过长的静音片段
     * @param {Uint8Array} pcmData - PCM数据
     * @param {number} maxSilenceDuration - 最大允许的静音时长（秒）
     * @returns {Uint8Array} - 处理后的PCM数据
     */
    _removeSilence(pcmData, maxSilenceDuration = 0.2) {
        const sampleRate = 16000;
        const bytesPerSample = 2;
        const silenceThreshold = 100; // 振幅阈值
        const maxSilenceSamples = Math.floor(maxSilenceDuration * sampleRate);
        
        const dataView = new DataView(pcmData.buffer, pcmData.byteOffset, pcmData.byteLength);
        const totalSamples = Math.floor(pcmData.length / bytesPerSample);
        
        // 第一遍：标记需要保留的样本
        const keepSamples = new Array(totalSamples).fill(false);
        let consecutiveSilent = 0;
        let silentStart = -1;
        
        for (let i = 0; i < totalSamples; i++) {
            const sample = dataView.getInt16(i * bytesPerSample, true);
            const isSilent = Math.abs(sample) < silenceThreshold;
            
            if (isSilent) {
                if (silentStart === -1) {
                    silentStart = i;
                }
                consecutiveSilent++;
            } else {
                // 遇到非静音样本
                if (silentStart !== -1) {
                    // 决定是否保留这段静音
                    const silentDuration = consecutiveSilent;
                    if (silentDuration <= maxSilenceSamples) {
                        // 保留短静音
                        for (let j = silentStart; j < i; j++) {
                            keepSamples[j] = true;
                        }
                    } else {
                        // 只保留最大允许长度的静音
                        const keepStart = i - maxSilenceSamples;
                        for (let j = keepStart; j < i; j++) {
                            keepSamples[j] = true;
                        }
                    }
                    silentStart = -1;
                    consecutiveSilent = 0;
                }
                keepSamples[i] = true;
            }
        }
        
        // 第二遍：构建新的PCM数据
        const keptSamples = keepSamples.filter(k => k).length;
        const newPcmData = new Uint8Array(keptSamples * bytesPerSample);
        const newDataView = new DataView(newPcmData.buffer);
        
        let writeIndex = 0;
        for (let i = 0; i < totalSamples; i++) {
            if (keepSamples[i]) {
                const sample = dataView.getInt16(i * bytesPerSample, true);
                newDataView.setInt16(writeIndex * bytesPerSample, sample, true);
                writeIndex++;
            }
        }
        
        const removedSamples = totalSamples - keptSamples;
        const removedDuration = removedSamples / sampleRate;
        console.log('[WebAudio] 静音移除统计:', {
            '原始样本数': totalSamples,
            '保留样本数': keptSamples,
            '移除样本数': removedSamples,
            '移除时长': removedDuration.toFixed(3) + 's'
        });
        
        return newPcmData;
    }

    /**
     * 从PCM数据创建AudioBuffer
     * @param {ArrayBuffer} pcmData - PCM数据
     * @returns {Promise<AudioBuffer>} - AudioBuffer
     */
    async _createAudioBufferFromPCM(pcmData) {
        const sampleRate = 16000;
        const numChannels = 1;
        const bytesPerSample = 2; // 16-bit PCM
        const frameCount = Math.floor(pcmData.byteLength / (numChannels * bytesPerSample));

        console.log('[WebAudio] PCM参数:', {
            sampleRate,
            numChannels,
            bytesPerSample,
            frameCount,
            dataLength: pcmData.byteLength
        });

        if (frameCount === 0) {
            throw new Error('无效的PCM数据，帧数为0');
        }

        const audioBuffer = this.audioContext.createBuffer(numChannels, frameCount, sampleRate);
        const channelData = audioBuffer.getChannelData(0);

        const dataView = new DataView(pcmData);
        let nonZeroSamples = 0;
        let maxSample = 0;
        let silentSegments = []; // 记录静音片段
        let currentSilentStart = -1;
        const silenceThreshold = 0.001; // 静音阈值

        for (let i = 0; i < frameCount; i++) {
            // 读取16位PCM数据
            const sample = dataView.getInt16(i * bytesPerSample, true);
            // 转换为浮点数（范围：-1.0 到 1.0）
            channelData[i] = sample / 32768;

            // 统计非零样本
            if (sample !== 0) {
                nonZeroSamples++;
            }
            if (Math.abs(channelData[i]) > maxSample) {
                maxSample = Math.abs(channelData[i]);
            }

            // 检测静音片段
            if (Math.abs(channelData[i]) < silenceThreshold) {
                if (currentSilentStart === -1) {
                    currentSilentStart = i;
                }
            } else {
                if (currentSilentStart !== -1) {
                    const silentDuration = (i - currentSilentStart) / sampleRate;
                    if (silentDuration > 0.1) { // 只记录超过100ms的静音
                        silentSegments.push({
                            start: currentSilentStart / sampleRate,
                            end: i / sampleRate,
                            duration: silentDuration
                        });
                    }
                    currentSilentStart = -1;
                }
            }
        }

        // 处理末尾的静音
        if (currentSilentStart !== -1) {
            const silentDuration = (frameCount - currentSilentStart) / sampleRate;
            if (silentDuration > 0.1) {
                silentSegments.push({
                    start: currentSilentStart / sampleRate,
                    end: frameCount / sampleRate,
                    duration: silentDuration
                });
            }
        }

        console.log('[WebAudio] PCM转换完成，时长:', audioBuffer.duration.toFixed(3), 's');
        console.log('[WebAudio] PCM数据分析 - 非零样本数:', nonZeroSamples, '/', frameCount, '最大振幅:', maxSample.toFixed(4));
        
        if (silentSegments.length > 0) {
            console.warn('[WebAudio] ⚠️ 检测到', silentSegments.length, '个静音片段（>100ms）:');
            silentSegments.forEach((seg, idx) => {
                console.warn(`  [${idx + 1}] ${seg.start.toFixed(3)}s - ${seg.end.toFixed(3)}s (时长: ${seg.duration.toFixed(3)}s)`);
            });
        }

        return audioBuffer;
    }

    /**
     * 按顺序播放所有音频片段（已废弃，保留用于兼容）
     * @param {Array<Blob>} audioChunks - 音频片段数组
     * @deprecated 请使用_playAudioQueue和_playSingleAudioChunk
     */
    async _playAllAudioChunks(audioChunks) {
        console.warn('[WebAudio] _playAllAudioChunks已废弃，请使用流式播放');
        // 此方法已不再使用
    }

    /**
     * 播放单个音频片段（已废弃）
     * @deprecated 请使用_playSingleAudioChunk
     */
    async _playSingleChunk(chunk) {
        console.warn('[WebAudio] _playSingleChunk已废弃，请使用_playSingleAudioChunk');
        // 此方法已不再使用
    }

    /**
     * 使用Web Audio API播放PCM音频数据
     * @param {Blob} audioBlob - 音频数据
     * @deprecated 此方法已弃用，请使用流式播放
     */
    async _playAudio(audioBlob) {
        // 此方法已不再使用，保留是为了兼容性
        console.warn('[WebAudio] _playAudio已弃用，请使用流式播放');
    }
    
    /**
     * 播放WAV格式的音频
     * @param {Blob} wavBlob - WAV格式的音频数据
     */
    async _playWavAudio(wavBlob) {
        return new Promise((resolve, reject) => {
            try {
                console.log('[WebAudio] 开始播放WAV音频，Blob大小:', wavBlob.size, 'bytes');
                
                const audioElement = document.createElement('audio');
                const audioUrl = URL.createObjectURL(wavBlob);
                audioElement.src = audioUrl;
                
                console.log('[WebAudio] 音频元素已创建，src:', audioUrl);
                
                audioElement.oncanplaythrough = () => {
                    console.log('[WebAudio] 音频可以播放，开始播放');
                    audioElement.play().then(() => {
                        console.log('[WebAudio] 音频播放开始');
                    }).catch(error => {
                        console.error('[WebAudio] 音频播放失败:', error);
                        URL.revokeObjectURL(audioUrl);
                        reject(error);
                    });
                };
                
                audioElement.onended = () => {
                    console.log('[WebAudio] 音频播放完成');
                    URL.revokeObjectURL(audioUrl);
                    resolve();
                };
                
                audioElement.onerror = (error) => {
                    console.error('[WebAudio] 音频加载失败:', error);
                    console.error('[WebAudio] 错误详情:', error.target.error);
                    URL.revokeObjectURL(audioUrl);
                    reject(error);
                };
                
                // 测试音频元素的属性
                console.log('[WebAudio] 音频元素属性:', {
                    src: audioElement.src,
                    readyState: audioElement.readyState,
                    networkState: audioElement.networkState,
                    preload: audioElement.preload,
                    autoplay: audioElement.autoplay,
                    loop: audioElement.loop,
                    muted: audioElement.muted,
                    volume: audioElement.volume
                });
                
                // 尝试加载音频
                audioElement.load();
                console.log('[WebAudio] 音频元素已加载');
                
            } catch (error) {
                console.error('[WebAudio] 创建音频元素失败:', error);
                reject(error);
            }
        });
    }
    
    /**
     * 创建WAV格式的Blob
     * @param {Uint8Array} pcmData - PCM数据
     * @param {number} sampleRate - 采样率
     * @param {number} numChannels - 声道数
     * @returns {Blob} - WAV格式的Blob
     */
    _createWavBlob(pcmData, sampleRate, numChannels) {
        console.log('[WebAudio] 创建WAV Blob，PCM数据长度:', pcmData.length, 'bytes', '采样率:', sampleRate, '声道数:', numChannels);

        const bytesPerSample = 2; // 16-bit
        const blockAlign = numChannels * bytesPerSample;
        const byteRate = sampleRate * blockAlign;
        const dataSize = pcmData.length;
        const totalSize = 36 + dataSize;
        const buffer = new ArrayBuffer(44 + dataSize);
        const view = new DataView(buffer);

        console.log('[WebAudio] WAV文件参数:', {
            bytesPerSample,
            blockAlign,
            byteRate,
            dataSize,
            totalSize,
            sampleRate,
            numChannels
        });

        // RIFF header
        this._writeString(view, 0, 'RIFF');
        view.setUint32(4, totalSize, true); // Little-endian
        this._writeString(view, 8, 'WAVE');
        console.log('[WebAudio] RIFF header 已写入');

        // fmt sub-chunk
        this._writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true); // Sub-chunk1 size (16 for PCM)
        view.setUint16(20, 1, true); // Audio format (1 for PCM)
        view.setUint16(22, numChannels, true); // Number of channels
        view.setUint32(24, sampleRate, true); // Sample rate
        view.setUint32(28, byteRate, true); // Byte rate
        view.setUint16(32, blockAlign, true); // Block align
        view.setUint16(34, 16, true); // Bits per sample
        console.log('[WebAudio] fmt chunk 已写入');

        // data sub-chunk
        this._writeString(view, 36, 'data');
        view.setUint32(40, dataSize, true); // Sub-chunk2 size
        console.log('[WebAudio] data chunk 已写入');

        // Write PCM data
        const uint8Array = new Uint8Array(buffer, 44);
        uint8Array.set(pcmData);
        console.log('[WebAudio] PCM数据已写入');

        // 验证WAV头是否正确
        const verifySampleRate = view.getUint32(24, true);
        const verifyNumChannels = view.getUint16(22, true);
        console.log('[WebAudio] WAV头验证 - 采样率:', verifySampleRate, '声道数:', verifyNumChannels);

        const wavBlob = new Blob([buffer], { type: 'audio/wav' });
        console.log('[WebAudio] WAV Blob 创建完成，大小:', wavBlob.size, 'bytes');

        return wavBlob;
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
     * 清理音频相关资源
     */
    _cleanupAudioResources() {
        // 停止当前播放
        if (this.currentSource) {
            try {
                this.currentSource.stop();
                this.currentSource.disconnect();
            } catch (e) {
                // 忽略停止时的错误
            }
            this.currentSource = null;
        }
        
        // 停止音频时长计时器
        if (this.audioTimer) {
            clearInterval(this.audioTimer);
            this.audioTimer = null;
        }
        
        // 清理音频URL
        if (this.currentAudioUrl) {
            URL.revokeObjectURL(this.currentAudioUrl);
            this.currentAudioUrl = null;
        }
        
        // 清理音频对象
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        
        // 清理音频数据
        if (!this._audioProcessing) {
            this.audioChunks = [];
        }
        this.audioDuration = 0;
        this.audioStartTime = 0;
        
        // 清理语音消息元素引用
        this.voiceMessageDiv = null;
        
        // 重置播放状态
        this.isPlaying = false;
        
        console.log('[WebAudio] 音频资源已清理');
    }
    
    async handleSendMessage() {
        // 获取聊天输入框元素
        const chatInput = document.getElementById('chatInput');
        const enableTTSCheckbox = document.getElementById('enableTTS');
        
        // 检查输入框是否存在
        if (!chatInput) {
            chatModule.log('error', '聊天输入框元素不存在');
            return;
        }
        
        // 获取输入框的值并去除首尾空白
        const messageText = chatInput.value.trim();
        
        // 检查输入值是否为空
        if (!messageText) {
            chatModule.log('warning', '请输入消息内容');
            return;
        }
        
        // 检查会话状态
        if (!this.client.sessionId) {
            chatModule.log('warning', '请先登录');
            uiModule.switchInputMode('text');
            return;
        }
        
        const enableTTS = enableTTSCheckbox ? enableTTSCheckbox.checked : false;
        
        // 添加发送的消息到聊天窗
        chatModule.addMessage('sent', messageText);
        
        // 清空输入框
        chatInput.value = '';
        
        chatModule.log('info', `正在发送消息: ${messageText.substring(0, 50)}...`);
        
        try {
            // 确保WebSocket连接存在
            const ws = await this.client.ensureWebSocketConnection();
            
            // 为当前请求创建一个消息缓冲区和消息元素引用
            let currentMessageDiv = null;
            let messageBuffer = '';
            
            await this.client.sendTextRequest(
                ws,
                messageText,
                (chunk) => {
                    // 将数据块添加到缓冲区
                    messageBuffer += chunk;
                    
                    // 如果还没有创建消息元素，创建一个
                    if (!currentMessageDiv) {
                        currentMessageDiv = chatModule.addMessage('received', messageBuffer);
                    } else {
                        // 更新现有的消息元素
                        const messageContent = currentMessageDiv.querySelector('.message-content');
                        if (messageContent) {
                            messageContent.textContent = messageBuffer;
                        }
                    }
                },
                (data) => {
                    chatModule.log('success', '流式生成完成');
                },
                { enableTTS }
            );
        } catch (error) {
            chatModule.log('error', `发送消息失败: ${error.message}`);
            chatModule.addMessage('received', `错误: ${error.message}`);
        }
    }
    
    /**
     * 检查会话状态并验证有效性
     * @returns {boolean} - 会话是否有效
     */
    async _checkSessionStatus() {
        // 检查会话状态
        if (!this.client || !this.client.sessionId) {
            chatModule.log('error', '会话未注册，请先登录');
            // 显示登录模态框
            document.getElementById('loginModal').style.display = 'block';
            return false;
        }
        
        // 验证会话是否有效
        try {
            await this.client.querySessionInfo([]);
            return true;
        } catch (error) {
            chatModule.log('error', '会话已过期，请重新登录');
            // 显示登录模态框
            document.getElementById('loginModal').style.display = 'block';
            return false;
        }
    }
    
    /**
     * 停止录音
     * @param {HTMLElement} btn - 按钮元素
     * @param {string} mode - 录音模式
     * @returns {Promise<Blob|null>} - 音频数据
     */
    async _stopRecording(btn, mode) {
        try {
            const audioBlob = await recorderModule.stopRecording();
            
            // 重置按钮状态
            if (mode === 'manual') {
                btn.textContent = '开始语音';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-primary');
            } else if (mode === 'auto') {
                btn.textContent = '自动检测';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-secondary');
                chatModule.log('info', '自动检测已停止');
            }
            
            // 重置录音时间
            const recordTimeSpan = document.getElementById('recordTime');
            if (recordTimeSpan) {
                recordTimeSpan.textContent = '00:00';
            }
            
            // 如果成功创建了音频文件，添加到消息列表
            if (audioBlob && mode === 'manual') {
                console.log('添加语音消息到消息列表');
                // 计算录音时长
                const duration = Math.floor((Date.now() - recorderModule.getRecordStartTime()) / 1000);
                // 添加语音消息到聊天窗口
                chatModule.addMessage('sent', null, audioBlob, duration);
            }
            
            // 更新状态
            this.recordingMode = null;
            
            return audioBlob;
        } catch (error) {
            console.error(`停止录音失败: ${error}`, error);
            
            // 重置按钮状态
            if (mode === 'manual') {
                btn.textContent = '开始语音';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-primary');
            } else if (mode === 'auto') {
                btn.textContent = '自动检测';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-secondary');
            }
            
            // 重置录音时间
            const recordTimeSpan = document.getElementById('recordTime');
            if (recordTimeSpan) {
                recordTimeSpan.textContent = '00:00';
            }
            
            // 更新状态
            this.recordingMode = null;
            
            return null;
        }
    }
    
    /**
     * 开始录音
     * @param {HTMLElement} btn - 按钮元素
     * @param {string} mode - 录音模式
     * @returns {Promise<boolean>} - 是否成功开始录音
     */
    async _startRecording(btn, mode) {
        // 检查会话状态
        if (!await this._checkSessionStatus()) {
            return false;
        }
        
        try {
            // 配置VAD
            if (mode === 'manual') {
                recorderModule.setVADConfig({ enabled: false });
            } else if (mode === 'auto') {
                recorderModule.setVADConfig({ enabled: true });
            }
            
            // 开始录音
            await recorderModule.startRecording();
            
            // 更新按钮状态
            if (mode === 'manual') {
                btn.textContent = '停止语音';
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-danger');
            } else if (mode === 'auto') {
                btn.textContent = '停止检测';
                btn.classList.remove('btn-secondary');
                btn.classList.add('btn-danger');
                chatModule.log('info', '自动检测已开始，正在等待语音...');
            }
            
            // 更新状态
            this.recordingMode = mode;
            
            return true;
        } catch (error) {
            console.error(`开始录音失败: ${error.message}`, error);
            chatModule.log('error', `开始录音失败: ${error.message}`);
            
            // 重置按钮状态
            if (mode === 'manual') {
                btn.textContent = '开始语音';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-primary');
            } else if (mode === 'auto') {
                btn.textContent = '自动检测';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-secondary');
            }
            
            // 重置录音时间
            const recordTimeSpan = document.getElementById('recordTime');
            if (recordTimeSpan) {
                recordTimeSpan.textContent = '00:00';
            }
            
            return false;
        }
    }
    
    async handleRecordToggle() {
        const recordToggleBtn = document.getElementById('recordToggleBtn');
        
        if (!recordToggleBtn) {
            chatModule.log('error', '语音按钮不存在');
            return;
        }
        
        if (this.recordingMode) {
            // 停止录音
            await this._stopRecording(recordToggleBtn, this.recordingMode);
        } else {
            // 获取VAD配置
            const vadEnabled = localStorage.getItem('vadEnabled') === 'true';
            
            // 根据VAD配置决定录音模式
            const mode = vadEnabled ? 'auto' : 'manual';
            
            // 开始录音
            await this._startRecording(recordToggleBtn, mode);
        }
    }
    
    async handleQuerySessionInfo() {
        if (!this.client.sessionId) {
            chatModule.log('warning', '请先登录');
            return;
        }
        
        chatModule.log('info', '查询会话信息');
        
        try {
            const sessionInfo = await this.client.querySessionInfo();
            chatModule.log('success', `会话信息查询成功: ${JSON.stringify(sessionInfo)}`);
            
            // 更新UI显示
            if (sessionInfo.session_data) {
                const sessionIdElement = document.getElementById('sessionId');
                if (sessionIdElement) {
                    sessionIdElement.textContent = this.client.sessionId.substring(0, 8) + '...';
                }
                
                // 处理服务器返回的会话信息格式
                const sessionData = sessionInfo.session_data.data || sessionInfo.session_data;
                
                if (sessionData.login_time) {
                    chatModule.log('info', `会话创建时间: ${new Date(sessionData.login_time).toLocaleString()}`);
                }
                if (sessionData.remaining_seconds) {
                    chatModule.log('info', `剩余超时时间: ${sessionData.remaining_seconds} 秒`);
                }
                if (sessionData.username) {
                    chatModule.log('info', `用户名: ${sessionData.username}`);
                }
                if (sessionData.active !== undefined) {
                    chatModule.log('info', `会话状态: ${sessionData.active ? '活跃' : '已过期'}`);
                }
            }
        } catch (error) {
            chatModule.log('error', `查询会话信息失败: ${error.message}`);
        }
    }
    
    async handleStartCall() {
        chatModule.log('info', '开始语音通话');
        
        if (!this.client.sessionId) {
            chatModule.log('warning', '请先登录');
            uiModule.switchInputMode('text');
            return;
        }
        
        this.isInCall = true;
        this.callStartTime = Date.now();
        
        // 显示语音通话界面
        const voiceCallOverlay = document.getElementById('voiceCallOverlay');
        if (voiceCallOverlay) {
            voiceCallOverlay.style.display = 'flex';
        }
        
        // 开始计时
        this.startCallTimer();
        
        try {
            // 连接流式WebSocket
            const streamWs = await this.client.connectAgentStream();
            
            // 开始录音
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            const audioChunks = [];
            
            mediaRecorder.addEventListener('dataavailable', (event) => {
                audioChunks.push(event.data);
            });
            
            mediaRecorder.addEventListener('stop', () => {
                if (this.isInCall) {
                    // 发送音频数据
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    this.sendCallAudio(audioBlob, streamWs);
                    audioChunks.length = 0;
                    // 继续录音
                    mediaRecorder.start();
                }
            });
            
            mediaRecorder.start();
            
            // 每3秒发送一次音频数据
            this.callAudioInterval = setInterval(() => {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                }
            }, 3000);
            
        } catch (error) {
            chatModule.log('error', `开始语音通话失败: ${error.message}`);
            this.handleEndCall();
        }
    }
    
    async sendCallAudio(audioBlob, streamWs) {
        try {
            await this.client.sendVoiceRequest(
                streamWs,
                audioBlob,
                (chunk) => {
                    // 实时更新消息内容
                    const lastMessage = document.querySelector('.message.received:last-child .message-content');
                    if (lastMessage) {
                        lastMessage.textContent += chunk;
                    } else {
                        chatModule.addMessage('received', chunk);
                    }
                },
                (data) => {
                    chatModule.log('success', '音频流式生成完成');
                },
                { enableTTS: true }
            );
        } catch (error) {
            chatModule.log('error', `发送通话音频失败: ${error.message}`);
        }
    }
    
    handleEndCall() {
        chatModule.log('info', '结束语音通话');
        
        this.isInCall = false;
        
        // 停止计时
        if (this.callTimer) {
            clearInterval(this.callTimer);
            this.callTimer = null;
        }
        
        // 停止录音和音频发送
        if (this.callAudioInterval) {
            clearInterval(this.callAudioInterval);
            this.callAudioInterval = null;
        }
        
        // 隐藏语音通话界面
        const voiceCallOverlay = document.getElementById('voiceCallOverlay');
        if (voiceCallOverlay) {
            voiceCallOverlay.style.display = 'none';
        }
        
        // 重置通话时长显示
        const callDuration = document.getElementById('callDuration');
        if (callDuration) {
            callDuration.textContent = '00:00';
        }
        
        // 切换回文本模式
        uiModule.switchInputMode('text');
    }
    
    startCallTimer() {
        this.callTimer = setInterval(() => {
            const callDuration = document.getElementById('callDuration');
            if (callDuration) {
                const elapsed = Math.floor((Date.now() - this.callStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
                const seconds = (elapsed % 60).toString().padStart(2, '0');
                callDuration.textContent = `${minutes}:${seconds}`;
            }
        }, 1000);
    }
}

// 导出MuseumAgentDemo类
export default MuseumAgentDemo;

// 当DOM加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否已登录
    if (window.isLoggedIn) {
        // 如果已登录，创建应用实例
        window.demoApp = new MuseumAgentDemo();
    }
});

// 全局函数，用于在HTML中调用
window.createChatPage = function() {
    // 移除登录页面
    const loginPage = document.getElementById('loginPage');
    if (loginPage) {
        loginPage.remove();
    }

    // 创建聊天页面DOM结构
    const chatPage = document.createElement('div');
    chatPage.className = 'app-container active';
    chatPage.id = 'chatPage';
    
    chatPage.innerHTML = `
        <header class="app-header">
            <h1>MuseumAgent 客户端</h1>
            <p class="subtitle">博物馆智能体Web客户端 <button id="logoutBtn" class="btn" style="display: inline-block; width: auto; padding: 4px 12px; font-size: 12px; margin-left: 10px;">登出</button></p>
        </header>

        <div class="main-container">
            <div class="config-panel client-config">
            <h2>1. 客户端配置</h2>
            <div class="config-content">
                <div class="form-group">
                    <label for="clientType">客户端类型:</label>
                    <input type="text" id="clientType" placeholder="输入客户端类型" value="web">
                </div>
                <div class="form-group">
                    <label for="sceneType">场景类型:</label>
                    <input type="text" id="sceneType" placeholder="输入场景类型" value="public">
                </div>
                <div class="form-group">
                    <label for="spiritId">精灵ID:</label>
                    <input type="text" id="spiritId" placeholder="输入精灵ID">
                </div>
                <div class="form-group">
                    <label for="enableTTS">启用语音播报:</label>
                    <input type="checkbox" id="enableTTS" checked>
                </div>
                <div class="form-group">
                    <label for="autoPlayVoice">自动播放语音消息:</label>
                    <input type="checkbox" id="autoPlayVoice" checked>
                </div>
                <div class="form-group">
                    <label for="sessionId">会话ID:</label>
                    <input type="text" id="sessionId" placeholder="会话ID" readonly>
                </div>
                <div class="form-group">
                    <label for="sessionStatus">会话状态:</label>
                    <span id="sessionStatus" class="status-badge status-offline">未连接</span>
                </div>
                <div class="form-group">
                    <button id="querySessionBtn" class="btn btn-primary">查询会话信息</button>
                </div>
            </div>
        </div>

            <div class="resize-handle" id="resizeHandle1"></div>

            <div class="config-panel functions-config">
                <h2>2. 函数定义</h2>
                <div class="config-content">
                    <div class="form-group full-width">
                        <label for="functions">客户端支持的函数定义 (JSON格式):</label>
                        <textarea id="functions" class="functions-input" placeholder='
                        [
                            {
                                "name": "FunctionsName",// 函数名称
                                "description": "FunctionDescription",// 函数描述
                                "parameters": // 参数定义
                                {
                                    "type": "object",// 参数类型为对象
                                    "properties": // 参数属性定义
                                    {
                                        "property_name": // 属性名称
                                        {
                                            "type": "string",// 属性类型为字符串
                                            "description": "property_description" // 属性描述
                                        }
                                    },
                                    "required": // 必须参数
                                    [
                                        "property_name"// 必须参数property_name
                                    ]
                                }
                            }
                        ]'>
                        [
                            {
                                "name": "play_emotion",
                                "description": "播放电子宠物的表情",
                                "parameters": {
                                "type": "object",
                                "properties": {
                                    "emotion_name": {
                                    "type": "string",
                                    "description": "表情名称，如：happy、sad、angry、surprised、excited等"
                                    }
                                },
                                "required": ["emotion_name"]
                                }
                            },
                            {
                                "name": "move_to",
                                "description": "移动电子宠物到指定位置",
                                "parameters": {
                                "type": "object",
                                "properties": {
                                    "x": {
                                    "type": "number",
                                    "description": "X坐标"
                                    },
                                    "y": {
                                    "type": "number",
                                    "description": "Y坐标"
                                    },
                                    "z": {
                                    "type": "number",
                                    "description": "Z坐标"
                                    }
                                },
                                "required": ["x", "y", "z"]
                                }
                            },
                            {
                                "name": "play_animation",
                                "description": "播放电子宠物的动画",
                                "parameters": {
                                "type": "object",
                                "properties": {
                                    "animation_name": {
                                    "type": "string",
                                    "description": "动画名称，如：walk、run、jump、dance、wave等"
                                    }
                                },
                                "required": ["animation_name"]
                                }
                            },
                            {
                                "name": "sleep",
                                "description": "让电子宠物进入睡眠状态",
                                "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                                }
                            },
                            {
                                "name": "wake_up",
                                "description": "唤醒电子宠物",
                                "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                                }
                            }
                        ]</textarea>
                    </div>
                </div>
            </div>

            <div class="resize-handle" id="resizeHandle2"></div>

            <div class="chat-panel">
                <h2>3. 聊天窗</h2>
                <div class="chat-container">
                    <div class="message-history" id="messageHistory">
                        <!-- 消息历史记录 -->
                    </div>
                    <div class="message-input">

                        <div class="input-area">
                            <textarea id="chatInput" placeholder="输入消息..."></textarea>
                        </div>
                        <div class="input-controls">
                            <button id="sendMessageBtn" class="btn btn-primary">发送</button>
                            <div class="voice-actions">
                                <button id="recordToggleBtn" class="btn btn-primary">开始语音</button>
                                <span id="recordTime" class="record-time">00:00</span>
                            </div>
                        </div>
                        <div class="voice-recorder" id="voiceRecorder" style="display: none;">
                            <!-- 保留原始语音录音器结构，确保现有功能正常工作 -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="resize-handle resize-handle-vertical" id="resizeHandle3"></div>

        <div class="log-panel">
            <div class="log-header">
                <h2>控制台</h2>
                <button id="clearLogBtn" class="btn btn-small btn-secondary">清空</button>
            </div>
            <div id="logContent" class="log-content"></div>
        </div>
    `;
    
    // 添加聊天页面到DOM
    document.body.appendChild(chatPage);
    
    // 初始化登出功能
    initLogoutFunctionality();
    
    // 设置登录状态
    window.isLoggedIn = true;
    
    // 创建应用实例
    window.demoApp = new MuseumAgentDemo();
};

// 初始化登出功能
function initLogoutFunctionality() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            // 清除本地存储的会话信息
            authModule.clearSession();
            
            // 如果app.js中存在客户端实例，则断开连接
            if (window.demoApp && window.demoApp.client) {
                try {
                    window.demoApp.client.disconnectSession();
                } catch(e) {
                    console.warn('断开连接时出错:', e);
                }
            }
            
            // 移除聊天页面
            const chatPage = document.getElementById('chatPage');
            if (chatPage) {
                chatPage.remove();
            }
            
            // 重新加载页面以显示登录页面
            window.location.reload();
        });
    }
}

