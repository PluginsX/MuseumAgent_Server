/**
 * 页面管理器
 * 处理页面切换、模板加载和页面生命周期管理
 */
class PageManager {
    constructor() {
        this.isLoggedIn = false;
        this.currentPage = null;
        this.loginPage = null;
        this.chatPage = null;
    }

    /**
     * 初始化页面管理器
     */
    async init() {
        console.log('[PageManager] 初始化页面管理器，检查会话状态');
        
        // 检查浏览器缓存中是否有之前的会话缓存
        const savedSessionId = localStorage.getItem('museumAgent_sessionId');
        const savedUsername = localStorage.getItem('museumAgent_username');
        const savedPassword = localStorage.getItem('museumAgent_password');
        
        console.log('[PageManager] 会话缓存检查结果:', {
            savedSessionId: !!savedSessionId,
            savedUsername: !!savedUsername,
            savedPassword: !!savedPassword
        });
        
        // 如果没有会话缓存，直接跳转到登录页面
        if (!savedSessionId || !savedUsername || !savedPassword) {
            console.log('[PageManager] 没有会话缓存，跳转到登录页面');
            this.switchToLoginPage();
            return;
        }
        
        // 如果有会话缓存，创建临时客户端实例查询会话状态
        console.log('[PageManager] 有会话缓存，创建客户端实例查询会话状态');
        
        try {
            // 从localStorage获取服务器地址
            let serverUrl = localStorage.getItem('museumAgent_serverUrl') || 'http://localhost:8001';
            console.log('[PageManager] 使用的服务器地址:', serverUrl);
            
            // 创建临时客户端实例
            const tempClient = new MuseumAgentClient({
                baseUrl: serverUrl,
                timeout: 30000,
                autoReconnect: true,
                reconnectInterval: 5000,
                heartbeatInterval: 30000
            });
            
            // 设置会话ID
            tempClient.sessionId = savedSessionId;
            
            // 从localStorage加载认证数据
            tempClient.authData = {
                type: 'ACCOUNT',
                account: savedUsername,
                password: savedPassword
            };
            
            tempClient._lastRegisterData = {
                auth: tempClient.authData,
                platform: 'WEB',
                function_calling: [],
                require_tts: false
            };
            
            console.log('[PageManager] 临时客户端实例创建完成，开始查询会话状态');
            
            // 查询会话状态
            const sessionInfo = await tempClient.querySessionInfo([]);
            console.log('[PageManager] 会话状态查询成功:', sessionInfo);
            
            // 会话有效，跳转到聊天页面
            console.log('[PageManager] 会话有效，跳转到聊天页面');
            await this.switchToChatPage();
        } catch (error) {
            console.error('[PageManager] 会话状态查询失败:', error);
            
            // 会话无效，删除会话缓存，跳转到登录页面
            console.log('[PageManager] 会话无效，删除会话缓存，跳转到登录页面');
            
            // 删除会话缓存
            localStorage.removeItem('museumAgent_sessionId');
            localStorage.removeItem('museumAgent_username');
            localStorage.removeItem('museumAgent_password');
            
            // 跳转到登录页面
            this.switchToLoginPage();
        }
    }

    /**
     * 切换到登录页面
     */
    async switchToLoginPage() {
        try {
            // 移除当前页面
            this.removeCurrentPage();
            
            // 加载登录页面模板
            const loginTemplate = await this.loadTemplate('./templates/login-page.html');
            
            // 添加到DOM
            const body = document.body;
            body.insertAdjacentHTML('beforeend', loginTemplate);
            
            // 导入LoginPage类并创建实例
            const { default: LoginPage } = await import('../pages/login.js');
            this.loginPage = new LoginPage();
            this.currentPage = 'login';
            
            console.log('[PageManager] 切换到登录页面');
        } catch (error) {
            console.error('[PageManager] 切换到登录页面失败:', error);
        }
    }

    /**
     * 切换到聊天页面
     * @param {Object} registerData 注册会话的数据
     */
    async switchToChatPage(registerData = null) {
        try {
            // 移除当前页面
            this.removeCurrentPage();
            
            // 加载聊天页面模板
            const chatTemplate = await this.loadTemplate('./templates/chat-page.html');
            
            // 添加到DOM
            const body = document.body;
            body.insertAdjacentHTML('beforeend', chatTemplate);
            
            // 导入ChatPage类并创建实例
            const { default: ChatPage } = await import('../pages/chatPage.js');
            this.chatPage = new ChatPage();
            this.currentPage = 'chat';
            
            console.log('[PageManager] 切换到聊天页面');
            
            // 重新初始化app.js
            if (typeof MuseumAgentDemo !== 'undefined') {
                // 创建MuseumAgentDemo实例
                window.demoApp = new MuseumAgentDemo();
                console.log('[初始化] MuseumAgentDemo实例已创建');
                
                // 如果提供了注册数据，则执行会话注册
                if (registerData && window.demoApp && window.demoApp.client) {
                    try {
                        const result = await window.demoApp.client.registerSession(registerData);
                        console.log('会话注册成功:', result);
                    } catch (error) {
                        console.error('会话注册失败:', error);
                    }
                } else {
                    // 更新会话ID
                    const savedSessionId = localStorage.getItem('museumAgent_sessionId');
                    if (savedSessionId && window.demoApp.client) {
                        window.demoApp.client.sessionId = savedSessionId;
                        console.log('[初始化] 会话ID已更新:', savedSessionId);
                    }
                }
            }
            
            this.isLoggedIn = true;
        } catch (error) {
            console.error('[PageManager] 切换到聊天页面失败:', error);
        }
    }

    /**
     * 移除当前页面
     */
    removeCurrentPage() {
        if (this.currentPage === 'login') {
            const loginPage = document.getElementById('loginPage');
            if (loginPage) {
                loginPage.remove();
                this.loginPage = null;
            }
        } else if (this.currentPage === 'chat') {
            const chatPage = document.getElementById('chatPage');
            if (chatPage) {
                chatPage.remove();
                this.chatPage = null;
            }
        }
        this.currentPage = null;
    }

    /**
     * 加载模板文件
     * @param {string} templatePath 模板文件路径
     * @returns {Promise<string>} 模板内容
     */
    async loadTemplate(templatePath) {
        try {
            const response = await fetch(templatePath);
            if (!response.ok) {
                throw new Error(`加载模板失败: ${response.statusText}`);
            }
            return await response.text();
        } catch (error) {
            console.error('[PageManager] 加载模板失败:', error);
            throw error;
        }
    }

    /**
     * 获取当前页面实例
     * @returns {Object|null} 当前页面实例
     */
    getCurrentPage() {
        if (this.currentPage === 'login') {
            return this.loginPage;
        } else if (this.currentPage === 'chat') {
            return this.chatPage;
        }
        return null;
    }

    /**
     * 检查是否已登录
     * @returns {boolean} 是否已登录
     */
    getIsLoggedIn() {
        return this.isLoggedIn;
    }
}

// 导出PageManager类
export default PageManager;