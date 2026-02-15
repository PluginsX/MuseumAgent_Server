/**
 * 认证模块
 * 处理登录、会话管理等功能
 */
class AuthModule {
    constructor() {
        this.baseUrl = null;
        this.sessionId = null;
    }

    /**
     * 初始化认证模块
     */
    init() {
        this.loadSavedConfig();
    }

    /**
     * 加载保存的服务器配置
     */
    loadSavedConfig() {
        const savedServerUrl = localStorage.getItem('museumAgent_serverUrl');
        if (savedServerUrl) {
            try {
                const url = new URL(savedServerUrl);
                // 添加空值检查
                const serverHostElement = document.getElementById('server-host');
                const serverPortElement = document.getElementById('server-port');
                if (serverHostElement) {
                    serverHostElement.value = url.hostname;
                }
                if (serverPortElement) {
                    serverPortElement.value = url.port || '8001';
                }
                this.baseUrl = savedServerUrl;
            } catch (e) {
                console.warn('无法解析保存的服务器URL:', e);
            }
        }

        const savedSessionId = localStorage.getItem('museumAgent_sessionId');
        if (savedSessionId) {
            this.sessionId = savedSessionId;
        }
    }

    /**
     * 构建服务器基础URL
     * @param {string} host - 服务器地址
     * @param {string} port - 服务器端口
     * @returns {string} - 完整的服务器URL
     */
    buildServerUrl(host, port) {
        return `http://${host}:${port}`;
    }

    /**
     * 保存服务器配置
     * @param {string} url - 服务器URL
     */
    saveServerConfig(url) {
        localStorage.setItem('museumAgent_serverUrl', url);
        this.baseUrl = url;
        console.log('[认证] 服务器地址已保存:', url);
    }

    /**
     * 保存会话ID
     * @param {string} sessionId - 会话ID
     * @param {Object} credentials - 登录凭证
     */
    saveSessionId(sessionId, credentials = null) {
        localStorage.setItem('museumAgent_sessionId', sessionId);
        this.sessionId = sessionId;
        console.log('[认证] 会话ID已保存:', sessionId);
        
        // 保存登录凭证
        if (credentials && credentials.username && credentials.password) {
            localStorage.setItem('museumAgent_username', credentials.username);
            localStorage.setItem('museumAgent_password', credentials.password);
            console.log('[认证] 登录凭证已保存');
        }
    }

    /**
     * 清除会话信息
     */
    clearSession() {
        localStorage.removeItem('museumAgent_sessionId');
        localStorage.removeItem('museumAgent_serverUrl');
        localStorage.removeItem('museumAgent_username');
        localStorage.removeItem('museumAgent_password');
        this.sessionId = null;
        this.baseUrl = null;
        console.log('[认证] 会话信息已清除');
    }

    /**
     * 准备登录数据
     * @param {string} type - 登录类型 (ACCOUNT 或 API_KEY)
     * @param {Object} credentials - 登录凭证
     * @returns {Object} - 登录数据
     */
    /**
     * 构建 REGISTER payload（协议：platform, function_calling）
     */
    prepareLoginData(type, credentials) {
        const loginData = {
            auth: { type },
            platform: 'WEB',
            function_calling: [],
            require_tts: false,
            client_metadata: { scene_type: 'VISITOR_CENTER', spirit_id: 'default' }
        };

        if (type === "ACCOUNT") {
            loginData.auth.account = credentials.username;
            loginData.auth.password = credentials.password;
        } else if (type === "API_KEY") {
            loginData.auth.api_key = credentials.apiKey;
        }

        return loginData;
    }

    /**
     * 检查登录状态
     * @returns {boolean} - 是否已登录
     */
    isLoggedIn() {
        return !!this.sessionId;
    }

    /**
     * 获取当前会话ID
     * @returns {string|null} - 会话ID
     */
    getSessionId() {
        return this.sessionId;
    }

    /**
     * 获取服务器URL
     * @returns {string|null} - 服务器URL
     */
    getServerUrl() {
        return this.baseUrl;
    }
}

// 导出单例实例
export const authModule = new AuthModule();
