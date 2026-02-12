/**
 * MuseumAgent Demo应用
 * 演示客户端库的使用方法
 */

class MuseumAgentDemo {
    constructor() {
        this.client = null;
        this.streamWs = null;
        this.ttsWs = null;
        this.streamBuffer = '';
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recordStartTime = 0;
        this.recordTimer = null;
        this.callStartTime = 0;
        this.callTimer = null;
        this.isInCall = false;
        
        this.init();
    }
    
    init() {
        const serverUrl = document.getElementById('serverUrl').value;
        this.client = new MuseumAgentClient({
            baseUrl: serverUrl,
            timeout: 30000,
            autoReconnect: true,
            reconnectInterval: 5000,
            heartbeatInterval: 30000
        });
        
        this.bindEvents();
        this.setupDragResize();
        this.log('info', 'Demo应用初始化完成');
    }
    
    bindEvents() {
        document.getElementById('loginBtn').addEventListener('click', () => this.handleLogin());
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());
        
        document.getElementById('registerSessionBtn').addEventListener('click', () => this.handleRegisterSession());
        document.getElementById('validateSessionBtn').addEventListener('click', () => this.handleValidateSession());
        document.getElementById('disconnectSessionBtn').addEventListener('click', () => this.handleDisconnectSession());
        
        document.getElementById('textInputBtn').addEventListener('click', () => this.switchInputMode('text'));
        document.getElementById('voiceInputBtn').addEventListener('click', () => this.switchInputMode('voice'));
        document.getElementById('callInputBtn').addEventListener('click', () => this.switchInputMode('call'));
        
        document.getElementById('sendMessageBtn').addEventListener('click', () => this.handleSendMessage());
        document.getElementById('startRecordBtn').addEventListener('click', () => this.handleStartRecord());
        document.getElementById('stopRecordBtn').addEventListener('click', () => this.handleStopRecord());
        
        document.getElementById('endCallBtn').addEventListener('click', () => this.handleEndCall());
        
        document.getElementById('clearLogBtn').addEventListener('click', () => this.clearLog());
        
        // 为chatInput添加键盘事件监听
        document.getElementById('chatInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        this.setupClientEventHandlers();
    }
    
    setupDragResize() {
        // 设置第一个拖拽手柄
        const resizeHandle1 = document.getElementById('resizeHandle1');
        const serverConfig = document.querySelector('.server-config');
        let isResizing1 = false;
        
        resizeHandle1.addEventListener('mousedown', (e) => {
            isResizing1 = true;
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });
        
        const handleMouseMove1 = (e) => {
            if (!isResizing1) return;
            
            const containerRect = document.querySelector('.main-container').getBoundingClientRect();
            const newWidth = e.clientX - containerRect.left;
            
            if (newWidth > 200 && newWidth < 500) {
                serverConfig.style.width = `${newWidth}px`;
            }
        };
        
        const handleMouseUp1 = () => {
            isResizing1 = false;
            document.body.style.cursor = '';
        };
        
        document.addEventListener('mousemove', handleMouseMove1);
        document.addEventListener('mouseup', handleMouseUp1);
        
        // 设置第二个拖拽手柄
        const resizeHandle2 = document.getElementById('resizeHandle2');
        const clientConfig = document.querySelector('.client-config');
        let isResizing2 = false;
        
        resizeHandle2.addEventListener('mousedown', (e) => {
            isResizing2 = true;
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });
        
        const handleMouseMove2 = (e) => {
            if (!isResizing2) return;
            
            const containerRect = document.querySelector('.main-container').getBoundingClientRect();
            const serverConfigWidth = serverConfig.offsetWidth;
            const newWidth = e.clientX - containerRect.left - serverConfigWidth - 5;
            
            if (newWidth > 200 && newWidth < 500) {
                clientConfig.style.width = `${newWidth}px`;
            }
        };
        
        const handleMouseUp2 = () => {
            isResizing2 = false;
            document.body.style.cursor = '';
        };
        
        document.addEventListener('mousemove', handleMouseMove2);
        document.addEventListener('mouseup', handleMouseUp2);
        
        // 设置第三个拖拽手柄（垂直方向）
        const resizeHandle3 = document.getElementById('resizeHandle3');
        const mainContainer = document.querySelector('.main-container');
        const logPanel = document.querySelector('.log-panel');
        let isResizing3 = false;
        
        resizeHandle3.addEventListener('mousedown', (e) => {
            isResizing3 = true;
            document.body.style.cursor = 'row-resize';
            e.preventDefault();
        });
        
        const handleMouseMove3 = (e) => {
            if (!isResizing3) return;
            
            const containerRect = document.querySelector('.container').getBoundingClientRect();
            const newHeight = containerRect.bottom - e.clientY;
            
            if (newHeight > 100 && newHeight < 400) {
                logPanel.style.height = `${newHeight}px`;
                logPanel.style.maxHeight = `${newHeight}px`;
                // 同时调整main-container的高度，实现挤压效果
                mainContainer.style.height = `calc(100vh - ${newHeight}px - 80px)`;
            }
        };
        
        const handleMouseUp3 = () => {
            isResizing3 = false;
            document.body.style.cursor = '';
        };
        
        document.addEventListener('mousemove', handleMouseMove3);
        document.addEventListener('mouseup', handleMouseUp3);
    }
    
    switchInputMode(mode) {
        const textInputBtn = document.getElementById('textInputBtn');
        const voiceInputBtn = document.getElementById('voiceInputBtn');
        const callInputBtn = document.getElementById('callInputBtn');
        const inputArea = document.querySelector('.input-area');
        const voiceRecorder = document.getElementById('voiceRecorder');
        const voiceCallOverlay = document.getElementById('voiceCallOverlay');
        
        // 移除所有按钮的active类
        textInputBtn.classList.remove('active');
        voiceInputBtn.classList.remove('active');
        callInputBtn.classList.remove('active');
        
        // 隐藏所有区域
        inputArea.style.display = 'none';
        voiceRecorder.style.display = 'none';
        voiceCallOverlay.style.display = 'none';
        
        if (mode === 'text') {
            textInputBtn.classList.add('active');
            inputArea.style.display = 'block';
        } else if (mode === 'voice') {
            voiceInputBtn.classList.add('active');
            voiceRecorder.style.display = 'block';
        } else if (mode === 'call') {
            callInputBtn.classList.add('active');
            this.handleStartCall();
        }
    }
    
    async handleStartCall() {
        this.log('info', '开始语音通话');
        
        if (!this.client.token) {
            this.log('warning', '请先登录');
            this.switchInputMode('text');
            return;
        }
        
        this.isInCall = true;
        this.callStartTime = Date.now();
        
        // 显示语音通话界面
        const voiceCallOverlay = document.getElementById('voiceCallOverlay');
        voiceCallOverlay.style.display = 'flex';
        
        // 开始计时
        this.startCallTimer();
        
        try {
            // 连接流式WebSocket
            if (!this.streamWs) {
                this.streamWs = await this.client.connectAgentStream();
            }
            
            // 开始录音
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.addEventListener('dataavailable', (event) => {
                this.audioChunks.push(event.data);
            });
            
            this.mediaRecorder.addEventListener('stop', () => {
                if (this.isInCall) {
                    // 发送音频数据
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                    this.sendCallAudio(audioBlob);
                    this.audioChunks = [];
                    // 继续录音
                    this.mediaRecorder.start();
                }
            });
            
            this.mediaRecorder.start();
            
            // 每3秒发送一次音频数据
            this.callAudioInterval = setInterval(() => {
                if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                    this.mediaRecorder.stop();
                }
            }, 3000);
            
        } catch (error) {
            this.log('error', `开始语音通话失败: ${error.message}`);
            this.handleEndCall();
        }
    }
    
    async sendCallAudio(audioBlob) {
        try {
            await this.client.sendAudioStream(
                this.streamWs,
                audioBlob,
                (chunk) => {
                    // 实时更新消息内容
                    const lastMessage = document.querySelector('.message.received:last-child .message-content');
                    if (lastMessage) {
                        lastMessage.textContent += chunk;
                    } else {
                        this.addMessage('received', chunk);
                    }
                },
                (data) => {
                    this.log('success', '音频流式生成完成');
                },
                { enableTTS: true }
            );
        } catch (error) {
            this.log('error', `发送通话音频失败: ${error.message}`);
        }
    }
    
    handleEndCall() {
        this.log('info', '结束语音通话');
        
        this.isInCall = false;
        
        // 停止计时
        if (this.callTimer) {
            clearInterval(this.callTimer);
            this.callTimer = null;
        }
        
        // 停止录音
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        // 停止音频发送间隔
        if (this.callAudioInterval) {
            clearInterval(this.callAudioInterval);
            this.callAudioInterval = null;
        }
        
        // 隐藏语音通话界面
        const voiceCallOverlay = document.getElementById('voiceCallOverlay');
        voiceCallOverlay.style.display = 'none';
        
        // 重置通话时长显示
        document.getElementById('callDuration').textContent = '00:00';
        
        // 切换回文本模式
        this.switchInputMode('text');
    }
    
    startCallTimer() {
        this.callTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.callStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            document.getElementById('callDuration').textContent = `${minutes}:${seconds}`;
        }, 1000);
    }
    
    setupClientEventHandlers() {
        this.client.on('login', (data) => {
            this.log('success', '登录成功');
            this.updateUIState(true);
            document.getElementById('loginStatus').textContent = '已登录';
            document.getElementById('loginStatus').className = 'status-badge status-online';
        });
        
        this.client.on('error', (data) => {
            this.log('error', `错误: ${data.type} - ${data.error?.message || JSON.stringify(data.error)}`);
        });
        
        this.client.on('session_registered', (data) => {
            this.log('success', `会话注册成功: ${data.session_id}`);
            document.getElementById('sessionId').textContent = data.session_id.substring(0, 8) + '...';
            document.getElementById('sessionStatus').textContent = '已连接';
            document.getElementById('sessionStatus').className = 'status-badge status-online';
        });
        
        this.client.on('session_disconnected', (data) => {
            this.log('info', '会话已断开');
            document.getElementById('sessionId').textContent = '-';
            document.getElementById('sessionStatus').textContent = '未连接';
            document.getElementById('sessionStatus').className = 'status-badge status-offline';
        });
        
        this.client.on('agent_response', (data) => {
            this.log('success', '收到智能体响应');
            this.addMessage('received', data.content || JSON.stringify(data));
        });
        
        this.client.on('ws_connected', (data) => {
            this.log('success', `WebSocket连接成功: ${data.type}`);
        });
        
        this.client.on('ws_disconnected', (data) => {
            this.log('info', `WebSocket连接断开: ${data.type}`);
        });
        
        this.client.on('stream_chunk', (data) => {
            this.streamBuffer += data.chunk;
            // 实时更新消息内容
            const lastMessage = document.querySelector('.message.received:last-child .message-content');
            if (lastMessage) {
                lastMessage.textContent = this.streamBuffer;
            }
            this.log('info', `收到流式数据块: ${data.chunk.length} 字符`);
        });
        
        this.client.on('stream_complete', (data) => {
            this.log('success', '流式生成完成');
            this.streamBuffer = '';
        });
        
        this.client.on('audio_chunk', (data) => {
            this.log('info', `收到音频数据块: ${data.size} 字节`);
        });
    }
    
    updateUIState(isLoggedIn) {
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        const sessionBtns = [
            'registerSessionBtn',
            'validateSessionBtn',
            'disconnectSessionBtn'
        ];
        
        if (isLoggedIn) {
            loginBtn.disabled = true;
            logoutBtn.disabled = false;
            sessionBtns.forEach(id => {
                document.getElementById(id).disabled = false;
            });
            document.getElementById('sendMessageBtn').disabled = false;
            document.getElementById('voiceInputBtn').disabled = false;
        } else {
            loginBtn.disabled = false;
            logoutBtn.disabled = true;
            sessionBtns.forEach(id => {
                document.getElementById(id).disabled = true;
            });
            document.getElementById('sendMessageBtn').disabled = true;
            document.getElementById('voiceInputBtn').disabled = true;
            document.getElementById('callInputBtn').disabled = true;
        }
    }
    
    async handleLogin() {
        const serverUrl = document.getElementById('serverUrl').value;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        if (!serverUrl || !username || !password) {
            this.log('warning', '请填写服务器地址、用户名和密码');
            return;
        }
        
        // 更新客户端配置
        this.client.config.baseUrl = serverUrl;
        
        this.log('info', `正在登录: ${username}`);
        
        try {
            await this.client.login(username, password);
        } catch (error) {
            this.log('error', `登录失败: ${error.message}`);
            document.getElementById('loginStatus').textContent = '登录失败';
            document.getElementById('loginStatus').className = 'status-badge status-offline';
        }
    }
    
    async handleLogout() {
        this.log('info', '正在登出');
        
        try {
            this.client.cleanup();
            this.updateUIState(false);
            document.getElementById('loginStatus').textContent = '未登录';
            document.getElementById('loginStatus').className = 'status-badge status-offline';
            this.log('success', '登出成功');
        } catch (error) {
            this.log('error', `登出失败: ${error.message}`);
        }
    }
    
    async handleRegisterSession() {
        const clientType = document.getElementById('clientType').value;
        const sceneType = document.getElementById('sceneType').value;
        const spiritId = document.getElementById('spiritId').value;
        
        this.log('info', '正在注册会话');
        
        try {
            await this.client.registerSession({
                client_type: clientType,
                scene_type: sceneType,
                spirit_id: spiritId
            });
        } catch (error) {
            this.log('error', `注册会话失败: ${error.message}`);
        }
    }
    
    async handleValidateSession() {
        this.log('info', '正在验证会话');
        
        try {
            const isValid = await this.client.validateSession();
            if (isValid) {
                this.log('success', '会话有效');
            } else {
                this.log('warning', '会话无效');
            }
        } catch (error) {
            this.log('error', `验证会话失败: ${error.message}`);
        }
    }
    
    async handleDisconnectSession() {
        this.log('info', '正在断开会话');
        
        try {
            await this.client.disconnectSession();
        } catch (error) {
            this.log('error', `断开会话失败: ${error.message}`);
        }
    }
    
    async handleSendMessage() {
        const chatInput = document.getElementById('chatInput').value;
        
        if (!chatInput) {
            this.log('warning', '请输入消息内容');
            return;
        }
        
        if (!this.client.token) {
            this.log('warning', '请先登录');
            return;
        }
        
        // 添加发送的消息到聊天窗
        this.addMessage('sent', chatInput);
        
        // 清空输入框
        document.getElementById('chatInput').value = '';
        
        const enableTTS = document.getElementById('enableTTS').checked;
        
        this.log('info', `正在发送消息: ${chatInput.substring(0, 50)}...`);
        
        try {
            // 使用流式对话
            if (!this.streamWs) {
                this.streamWs = await this.client.connectAgentStream();
            }
            
            await this.client.sendTextStream(
                this.streamWs,
                chatInput,
                (chunk) => {
                    // 实时更新消息内容
                    const lastMessage = document.querySelector('.message.received:last-child .message-content');
                    if (lastMessage) {
                        lastMessage.textContent += chunk;
                    } else {
                        this.addMessage('received', chunk);
                    }
                },
                (data) => {
                    this.log('success', '流式生成完成');
                },
                { enableTTS }
            );
        } catch (error) {
            this.log('error', `发送消息失败: ${error.message}`);
            this.addMessage('received', `错误: ${error.message}`);
        }
    }
    
    async handleStartRecord() {
        this.log('info', '开始录音');
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            this.recordStartTime = Date.now();
            
            // 开始计时
            this.startRecordTimer();
            
            this.mediaRecorder.addEventListener('dataavailable', (event) => {
                this.audioChunks.push(event.data);
            });
            
            this.mediaRecorder.addEventListener('stop', () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.handleAudioRecorded(audioBlob);
            });
            
            this.mediaRecorder.start();
            document.getElementById('startRecordBtn').disabled = true;
            document.getElementById('stopRecordBtn').disabled = false;
        } catch (error) {
            this.log('error', `开始录音失败: ${error.message}`);
        }
    }
    
    handleStopRecord() {
        this.log('info', '停止录音');
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            clearInterval(this.recordTimer);
            document.getElementById('startRecordBtn').disabled = false;
            document.getElementById('stopRecordBtn').disabled = true;
            document.getElementById('recordTime').textContent = '00:00';
        }
    }
    
    startRecordTimer() {
        this.recordTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.recordStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            document.getElementById('recordTime').textContent = `${minutes}:${seconds}`;
        }, 1000);
    }
    
    async handleAudioRecorded(audioBlob) {
        this.log('info', `录音完成: ${audioBlob.size} 字节`);
        
        // 添加发送的语音消息到聊天窗
        this.addMessage('sent', null, audioBlob);
        
        const enableTTS = document.getElementById('enableTTS').checked;
        
        try {
            if (!this.streamWs) {
                this.streamWs = await this.client.connectAgentStream();
            }
            
            await this.client.sendAudioStream(
                this.streamWs,
                audioBlob,
                (chunk) => {
                    // 实时更新消息内容
                    const lastMessage = document.querySelector('.message.received:last-child .message-content');
                    if (lastMessage) {
                        lastMessage.textContent += chunk;
                    } else {
                        this.addMessage('received', chunk);
                    }
                },
                (data) => {
                    this.log('success', '音频流式生成完成');
                },
                { enableTTS }
            );
        } catch (error) {
            this.log('error', `发送音频消息失败: ${error.message}`);
            this.addMessage('received', `错误: ${error.message}`);
        }
    }
    
    addMessage(type, content, audioData = null) {
        const messageHistory = document.getElementById('messageHistory');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        
        if (audioData) {
            // 语音消息
            const audioUrl = URL.createObjectURL(audioData);
            const audioId = `audio-${Date.now()}`;
            
            messageDiv.innerHTML = `
                ${type === 'received' ? '<div class="message-avatar"></div>' : ''}
                <div class="message-content">
                    <div class="voice-message">
                        <span class="voice-icon">🎤</span>
                        <span class="voice-duration">语音消息</span>
                        <button class="voice-play-btn" data-audio-id="${audioId}" data-audio-url="${audioUrl}">播放</button>
                    </div>
                </div>
                <div class="message-time">${timeString}</div>
                ${type === 'sent' ? '<div class="message-avatar"></div>' : ''}
            `;
            
            // 添加播放按钮事件
            const playBtn = messageDiv.querySelector('.voice-play-btn');
            playBtn.addEventListener('click', () => this.playVoiceMessage(playBtn, audioUrl));
        } else {
            // 文本消息
            messageDiv.innerHTML = `
                ${type === 'received' ? '<div class="message-avatar"></div>' : ''}
                <div class="message-content">${content}</div>
                <div class="message-time">${timeString}</div>
                ${type === 'sent' ? '<div class="message-avatar"></div>' : ''}
            `;
        }
        
        messageHistory.appendChild(messageDiv);
        messageHistory.scrollTop = messageHistory.scrollHeight;
    }
    
    playVoiceMessage(button, audioUrl) {
        const audio = new Audio(audioUrl);
        
        button.textContent = '停止';
        button.classList.add('playing');
        
        audio.play();
        
        audio.addEventListener('ended', () => {
            button.textContent = '播放';
            button.classList.remove('playing');
        });
        
        button.onclick = () => {
            if (audio.paused) {
                audio.play();
                button.textContent = '停止';
                button.classList.add('playing');
            } else {
                audio.pause();
                button.textContent = '播放';
                button.classList.remove('playing');
            }
        };
    }
    
    log(level, message) {
        const logContent = document.getElementById('logContent');
        const timestamp = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = `log-entry ${level}`;
        entry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span>${message}`;
        logContent.appendChild(entry);
        logContent.scrollTop = logContent.scrollHeight;
        
        console.log(`[${level.toUpperCase()}] ${message}`);
    }
    
    clearLog() {
        document.getElementById('logContent').innerHTML = '';
        this.log('info', '日志已清空');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.demo = new MuseumAgentDemo();
});
