/**
 * 聊天页面模块
 * 处理聊天消息、语音录制、VAD配置等功能
 */
class ChatPage {
    constructor() {
        this.init();
    }

    /**
     * 初始化聊天页面
     */
    init() {
        // 绑定事件
        this.bindEvents();
        
        // 初始化登出功能
        this.initLogoutFunctionality();
        
        // 更新会话ID
        this.updateSessionId();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 发送消息按钮
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        if (sendMessageBtn) {
            sendMessageBtn.addEventListener('click', () => this.sendMessage());
        }

        // 语音录制按钮
        const recordToggleBtn = document.getElementById('recordToggleBtn');
        if (recordToggleBtn) {
            recordToggleBtn.addEventListener('click', () => this.toggleRecording());
        }

        // 查询会话信息按钮
        const querySessionBtn = document.getElementById('querySessionBtn');
        if (querySessionBtn) {
            querySessionBtn.addEventListener('click', () => this.querySessionInfo());
        }

        // 清空日志按钮
        const clearLogBtn = document.getElementById('clearLogBtn');
        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => this.clearLog());
        }

        // 回车键发送消息
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }

    /**
     * 初始化登出功能
     */
    initLogoutFunctionality() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                // 清除本地存储的会话信息
                localStorage.removeItem('museumAgent_sessionId');
                localStorage.removeItem('museumAgent_serverUrl');
                
                // 如果app.js中存在客户端实例，则断开连接
                if (window.demoApp && window.demoApp.client) {
                    try {
                        window.demoApp.client.disconnectSession();
                    } catch(e) {
                        console.warn('断开连接时出错:', e);
                    }
                }
                
                // 切换回登录页面
                window.pageManager.switchToLoginPage();
            });
        }
    }

    /**
     * 更新会话ID显示
     */
    updateSessionId() {
        const savedSessionId = localStorage.getItem('museumAgent_sessionId');
        const sessionIdEl = document.getElementById('sessionId');
        if (savedSessionId && sessionIdEl) {
            sessionIdEl.value = savedSessionId;
            console.log('[初始化] 会话ID已更新:', savedSessionId);
        }
    }

    /**
     * 发送消息
     */
    sendMessage() {
        // 如果存在demoApp实例，则使用其发送消息功能
        if (window.demoApp && window.demoApp.handleSendMessage) {
            try {
                window.demoApp.handleSendMessage();
            } catch (error) {
                console.error('发送消息失败:', error);
            }
        } else {
            console.error('demoApp实例不存在或handleSendMessage方法未定义');
        }
    }

    /**
     * 切换录音状态
     */
    toggleRecording() {
        if (window.demoApp && window.demoApp.handleRecordToggle) {
            try {
                window.demoApp.handleRecordToggle();
            } catch (error) {
                console.error('切换录音状态失败:', error);
            }
        } else {
            console.error('录音功能未初始化');
        }
    }



    /**
     * 查询会话信息
     */
    querySessionInfo() {
        if (window.demoApp && window.demoApp.handleQuerySessionInfo) {
            try {
                window.demoApp.handleQuerySessionInfo();
            } catch (error) {
                console.error('查询会话信息失败:', error);
            }
        } else {
            console.error('demoApp实例不存在或handleQuerySessionInfo方法未定义');
        }
    }

    /**
     * 清空日志
     */
    clearLog() {
        const logContent = document.getElementById('logContent');
        if (logContent) {
            logContent.innerHTML = '';
        }
    }

    /**
     * 播放语音消息
     * @param {string} audioUrl 音频URL
     */
    async toggleVoiceMessage(audioUrl) {
        try {
            // 创建音频元素
            const audio = new Audio(audioUrl);
            
            // 播放音频
            await audio.play();
            console.log('音频播放成功');
        } catch (error) {
            console.error('播放音频失败:', error);
        }
    }

    /**
     * 更新VAD状态显示
     * @param {string} status VAD状态
     */
    updateVadStatus(status) {
        const vadStatusEl = document.getElementById('vadStatus');
        if (vadStatusEl) {
            vadStatusEl.className = `vad-status vad-${status}`;
            
            switch (status) {
                case 'active':
                    vadStatusEl.textContent = '🔊 语音检测中';
                    break;
                case 'inactive':
                    vadStatusEl.textContent = '🔇 未启动';
                    break;
                case 'speaking':
                    vadStatusEl.textContent = '🎤 正在说话';
                    break;
                case 'silence':
                    vadStatusEl.textContent = '🔇 静音';
                    break;
                default:
                    vadStatusEl.textContent = `🔄 ${status}`;
            }
        }
    }

    /**
     * 更新会话状态显示
     * @param {string} status 会话状态
     */
    updateSessionStatus(status) {
        const sessionStatusEl = document.getElementById('sessionStatus');
        if (sessionStatusEl) {
            sessionStatusEl.className = `status-badge status-${status}`;
            
            switch (status) {
                case 'online':
                    sessionStatusEl.textContent = '已连接';
                    break;
                case 'offline':
                    sessionStatusEl.textContent = '未连接';
                    break;
                case 'connecting':
                    sessionStatusEl.textContent = '连接中';
                    break;
                default:
                    sessionStatusEl.textContent = status;
            }
        }
    }

    /**
     * 添加消息到聊天历史
     * @param {string} message 消息内容
     * @param {string} sender 发送者 (user 或 agent)
     * @param {string} type 消息类型 (text 或 voice)
     */
    addMessageToHistory(message, sender, type = 'text') {
        const messageHistory = document.getElementById('messageHistory');
        if (!messageHistory) {
            return;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        if (type === 'text') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>${message}</p>
                </div>
            `;
        } else if (type === 'voice') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>🎤 语音消息</p>
                    <button class="btn btn-small btn-secondary play-voice-btn">播放</button>
                </div>
            `;
            
            // 添加播放按钮事件
            const playBtn = messageDiv.querySelector('.play-voice-btn');
            if (playBtn) {
                playBtn.addEventListener('click', () => this.toggleVoiceMessage(message));
            }
        }

        messageHistory.appendChild(messageDiv);
        messageHistory.scrollTop = messageHistory.scrollHeight;
    }
}

// 导出ChatPage类
export default ChatPage;