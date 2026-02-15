/**
 * 登录页面模块
 * 处理登录表单提交、服务器配置和登录状态管理
 */
class LoginPage {
    constructor() {
        this.isLoggedIn = false;
        this.init();
    }

    /**
     * 初始化登录页面
     */
    init() {
        // 绑定事件
        this.bindEvents();
        
        // 页面加载时，尝试从localStorage恢复服务器配置
        this.restoreServerConfig();
        
        // 检查登录状态
        this.checkLoginStatus();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 标签切换功能
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // 移除所有激活状态
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
                
                // 激活当前标签
                tab.classList.add('active');
                const tabId = tab.getAttribute('data-tab') + '-tab';
                document.getElementById(tabId).classList.add('active');
                
                // 隐藏错误消息
                this.hideError();
            });
        });

        // 登录表单提交处理
        const credentialsForm = document.getElementById('credentials-form');
        if (credentialsForm) {
            credentialsForm.addEventListener('submit', (e) => this.handleCredentialsLogin(e));
        }

        const apikeyForm = document.getElementById('apikey-form');
        if (apikeyForm) {
            apikeyForm.addEventListener('submit', (e) => this.handleApikeyLogin(e));
        }
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        const loadingEl = document.getElementById('loading');
        const loginBtnEl = document.getElementById('login-btn');
        const apikeyLoginBtnEl = document.getElementById('apikey-login-btn');
        
        if (loadingEl) {
            loadingEl.style.display = 'block';
        }
        if (loginBtnEl) {
            loginBtnEl.disabled = true;
        }
        if (apikeyLoginBtnEl) {
            apikeyLoginBtnEl.disabled = true;
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        const loadingEl = document.getElementById('loading');
        const loginBtnEl = document.getElementById('login-btn');
        const apikeyLoginBtnEl = document.getElementById('apikey-login-btn');
        
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
        if (loginBtnEl) {
            loginBtnEl.disabled = false;
        }
        if (apikeyLoginBtnEl) {
            apikeyLoginBtnEl.disabled = false;
        }
    }

    /**
     * 显示错误消息
     * @param {string} message 错误消息
     */
    showError(message) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        } else {
            console.error('错误消息元素不存在:', message);
        }
    }

    /**
     * 隐藏错误消息
     */
    hideError() {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.style.display = 'none';
        }
    }

    /**
     * 从localStorage恢复服务器配置
     */
    restoreServerConfig() {
        const savedServerUrl = localStorage.getItem('museumAgent_serverUrl');
        if (savedServerUrl) {
            try {
                const url = new URL(savedServerUrl);
                const serverHostEl = document.getElementById('server-host');
                const serverPortEl = document.getElementById('server-port');
                
                if (serverHostEl) {
                    serverHostEl.value = url.hostname;
                }
                if (serverPortEl) {
                    serverPortEl.value = url.port || '8001';
                }
            } catch (e) {
                console.warn('无法解析保存的服务器URL:', e);
            }
        }
    }

    /**
     * 检查登录状态
     */
    async checkLoginStatus() {
        const sessionId = localStorage.getItem('museumAgent_sessionId');
        if (sessionId) {
            // 如果已有会话，先验证会话有效性
            console.log('[登录状态] 发现已保存的会话ID，正在验证有效性...');
            
            try {
                // 构建服务器地址
                let serverUrl = localStorage.getItem('museumAgent_serverUrl');
                if (!serverUrl) {
                    serverUrl = 'http://localhost:8001'; // 默认服务器地址
                }
                
                // 创建临时客户端实例来验证会话
                const tempClient = new MuseumAgentClient({
                    baseUrl: serverUrl,
                    timeout: 30000
                });
                tempClient.sessionId = sessionId;
                
                // 尝试建立WebSocket连接并查询会话信息
                await tempClient.connectAgentStream();
                await tempClient.querySessionInfo();
                
                console.log('[登录状态] 会话验证成功，直接进入聊天页面');
                
                // 会话有效，切换到聊天页面
                window.pageManager.switchToChatPage();
            } catch (error) {
                console.error('[登录状态] 会话验证失败:', error.message);
                
                // 会话无效，清除本地存储
                localStorage.removeItem('museumAgent_sessionId');
                console.log('[登录状态] 会话已清除，显示登录页面');
            }
        }
    }

    /**
     * 处理账户登录
     * @param {Event} e 事件对象
     */
    async handleCredentialsLogin(e) {
        e.preventDefault();
        
        console.log('[登录] 用户点击登录按钮，尝试初始化AudioContext');
        // 用户交互：初始化Web Audio API，确保AudioContext从suspended状态恢复
        try {
            const tempAudioContext = new (window.AudioContext || window.webkitAudioContext)();
            if (tempAudioContext.state === 'suspended') {
                await tempAudioContext.resume();
                console.log('[登录] 临时AudioContext已恢复');
            }
            tempAudioContext.close();
            console.log('[登录] 用户交互确认，AudioContext可以正常工作');
        } catch (e) {
            console.warn('[登录] 初始化临时AudioContext失败:', e);
        }
        
        const usernameEl = document.getElementById('username');
        const passwordEl = document.getElementById('password');
        const serverHostEl = document.getElementById('server-host');
        const serverPortEl = document.getElementById('server-port');

        if (!usernameEl || !passwordEl || !serverHostEl || !serverPortEl) {
            this.showError('表单元素不存在');
            return;
        }

        const username = usernameEl.value;
        const password = passwordEl.value;
        const serverHost = serverHostEl.value;
        const serverPort = serverPortEl.value;

        if (!username || !password) {
            this.showError('请输入用户名和密码');
            return;
        }

        if (!serverHost || !serverPort) {
            this.showError('请输入服务器地址和端口');
            return;
        }

        this.showLoading();
        this.hideError();

        try {
            // 构建基础URL
            const baseUrl = `http://${serverHost}:${serverPort}`;
            
            const registerData = {
                auth: { type: 'ACCOUNT', account: username, password: password },
                platform: 'WEB',
                function_calling: [],
                require_tts: false,
                client_metadata: { scene_type: 'VISITOR_CENTER', spirit_id: 'default' }
            };

            // 登录成功后，保存必要的信息到localStorage
            if (window.authModule) {
                window.authModule.saveServerConfig(baseUrl);
            } else {
                localStorage.setItem('museumAgent_serverUrl', baseUrl);
            }
            // 保存用户名和密码
            localStorage.setItem('museumAgent_username', username);
            localStorage.setItem('museumAgent_password', password);
            console.log('[登录] 服务器地址已保存:', baseUrl);
            console.log('[登录] 登录凭证已保存');
            
            // 保存到authModule（如果存在）
            if (window.authModule) {
                window.authModule.username = username;
                window.authModule.password = password;
            }
            
            // 切换到聊天页面
            window.pageManager.switchToChatPage(registerData);
            
            this.hideLoading();
            
        } catch (error) {
            console.error('登录失败:', error);
            this.showError(error.message || '登录失败，请检查用户名密码和服务器配置');
            this.hideLoading();
        }
    }

    /**
     * 处理API密钥登录
     * @param {Event} e 事件对象
     */
    async handleApikeyLogin(e) {
        e.preventDefault();
        
        const apiKeyEl = document.getElementById('api-key');
        const usernameEl = document.getElementById('apikey-username');
        const serverHostEl = document.getElementById('server-host');
        const serverPortEl = document.getElementById('server-port');

        if (!apiKeyEl || !serverHostEl || !serverPortEl) {
            this.showError('表单元素不存在');
            return;
        }

        const apiKey = apiKeyEl.value;
        const username = usernameEl ? usernameEl.value : '';
        const serverHost = serverHostEl.value;
        const serverPort = serverPortEl.value;

        if (!apiKey) {
            this.showError('请输入API密钥');
            return;
        }

        if (!serverHost || !serverPort) {
            this.showError('请输入服务器地址和端口');
            return;
        }

        this.showLoading();
        this.hideError();

        try {
            // 构建基础URL
            const baseUrl = `http://${serverHost}:${serverPort}`;
            
            const registerData = {
                auth: { type: 'API_KEY', api_key: apiKey },
                platform: 'WEB',
                function_calling: [],
                require_tts: false,
                client_metadata: { scene_type: 'VISITOR_CENTER', spirit_id: 'default' }
            };

            // 登录成功后，保存必要的信息到localStorage
            if (window.authModule) {
                window.authModule.saveServerConfig(baseUrl);
            } else {
                localStorage.setItem('museumAgent_serverUrl', baseUrl);
            }
            // 保存用户名（如果有）
            if (username) {
                localStorage.setItem('museumAgent_username', username);
                console.log('[登录] 用户名已保存:', username);
            }
            
            // 切换到聊天页面
            window.pageManager.switchToChatPage(registerData);
            
            this.hideLoading();
            
        } catch (error) {
            console.error('API密钥登录失败:', error);
            this.showError(error.message || 'API密钥登录失败，请检查密钥和服务器配置');
            this.hideLoading();
        }
    }
}

// 导出LoginPage类
export default LoginPage;