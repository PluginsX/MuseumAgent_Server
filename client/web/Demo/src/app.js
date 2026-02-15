/**
 * 应用入口
 * 管理应用生命周期和路由
 */

import { eventBus, Events } from './core/EventBus.js';
import { stateManager } from './core/StateManager.js';
import { authService } from './services/AuthService.js';
import { messageService } from './services/MessageService.js';
import { LoginForm } from './components/LoginForm.js';
import { ChatWindow } from './components/ChatWindow.js';
import { createElement, $, showNotification } from './utils/dom.js';

class App {
    constructor() {
        this.container = null;
        this.currentView = null;
        
        this.init();
    }

    /**
     * 初始化应用
     */
    async init() {
        console.log('[App] 初始化应用...');

        // 创建容器
        this.container = $('#app');
        if (!this.container) {
            console.log('[App] 创建 #app 容器');
            this.container = createElement('div', { id: 'app' });
            document.body.appendChild(this.container);
        }
        console.log('[App] 容器已准备:', this.container);

        // 设置样式
        this.setupStyles();

        // 绑定全局事件
        this.bindGlobalEvents();

        // 尝试恢复会话
        const authData = await authService.restoreSession();
        if (authData) {
            console.log('[App] 发现已保存的会话，尝试恢复...');
            try {
                const serverUrl = authService.getServerUrl();
                await this.showChatView(serverUrl, authData);
                showNotification('会话已恢复', 'success');
            } catch (error) {
                console.error('[App] 恢复会话失败:', error);
                this.showLoginView();
            }
        } else {
            console.log('[App] 没有已保存的会话，显示登录界面');
            this.showLoginView();
        }

        console.log('[App] 应用初始化完成');
    }

    /**
     * 设置全局样式
     */
    setupStyles() {
        // CSS 已通过外部文件引入，这里不需要额外设置
        console.log('[App] 样式已加载');
    }

    /**
     * 绑定全局事件
     */
    bindGlobalEvents() {
        // 登录成功
        eventBus.on(Events.AUTH_LOGIN_SUCCESS, async (data) => {
            console.log('[App] 收到登录成功事件:', data);
            const serverUrl = authService.getServerUrl();
            const authData = await authService.restoreSession();
            
            console.log('[App] serverUrl:', serverUrl);
            console.log('[App] authData:', authData);
            
            if (authData && serverUrl) {
                await this.showChatView(serverUrl, authData);
            } else {
                console.error('[App] 缺少必要的登录信息');
            }
        });

        // 登出
        eventBus.on(Events.AUTH_LOGOUT, () => {
            this.showLoginView();
        });

        // 会话过期
        eventBus.on(Events.SESSION_EXPIRED, () => {
            showNotification('会话已过期，请重新登录', 'error');
            authService.logout();
        });

        // 连接错误
        eventBus.on(Events.CONNECTION_ERROR, (error) => {
            showNotification('连接错误: ' + error.message, 'error');
        });

        // 显示错误
        eventBus.on(Events.UI_SHOW_ERROR, (message) => {
            showNotification(message, 'error');
        });

        // 显示成功
        eventBus.on(Events.UI_SHOW_SUCCESS, (message) => {
            showNotification(message, 'success');
        });
    }

    /**
     * 显示登录视图
     */
    showLoginView() {
        console.log('[App] 显示登录视图');
        this.container.innerHTML = '';
        this.container.style.display = 'flex';
        this.container.style.alignItems = 'center';
        this.container.style.justifyContent = 'center';
        this.currentView = new LoginForm(this.container);
        console.log('[App] 登录视图已创建');
    }

    /**
     * 显示聊天视图
     */
    async showChatView(serverUrl, authData) {
        console.log('[App] 显示聊天视图, serverUrl:', serverUrl, 'authData:', authData);
        
        // 初始化消息服务（先连接）
        try {
            console.log('[App] 初始化消息服务...');
            await messageService.init(serverUrl, authData);
            console.log('[App] 消息服务初始化成功！！！');
        } catch (error) {
            console.error('[App] 初始化失败:', error);
            showNotification('连接失败: ' + error.message, 'error');
            this.showLoginView();
            return;
        }
        
        console.log('[App] 开始创建聊天界面 DOM...');
        
        // 清空容器并重置样式
        this.container.innerHTML = '';
        this.container.style.display = 'block';
        this.container.style.alignItems = '';
        this.container.style.justifyContent = '';
        this.container.style.height = '100vh';
        this.container.style.width = '100vw';

        console.log('[App] 容器已清空，开始创建 chatView...');

        // 创建聊天视图容器
        const chatView = createElement('div', { className: 'chat-view' });
        console.log('[App] chatView 已创建:', chatView);

        // 头部
        const header = createElement('div', { className: 'chat-header' });
        console.log('[App] header 已创建:', header);
        
        const title = createElement('h1', { textContent: 'MuseumAgent 智能体' });
        console.log('[App] title 已创建:', title);
        
        // 创建登出按钮
        const logoutButton = createElement('button', {
            className: 'logout-button',
            textContent: '登出'
        });
        console.log('[App] logoutButton 已创建:', logoutButton);

        // 创建设置按钮
        const settingsButton = createElement('button', {
            className: 'settings-button',
            textContent: '⚙️'
        });
        console.log('[App] settingsButton 已创建:', settingsButton);

        // 绑定事件
        logoutButton.addEventListener('click', async () => {
            await messageService.disconnect();
            authService.logout();
        });

        // 绑定设置按钮事件
        settingsButton.addEventListener('click', () => {
            if (window.settingsPanel) {
                window.settingsPanel.toggle();
            } else {
                // 动态导入SettingsPanel
                import('./components/SettingsPanel.js').then(({ SettingsPanel }) => {
                    window.settingsPanel = new SettingsPanel();
                    window.settingsPanel.toggle();
                });
            }
        });

        // 创建按钮容器，用于对齐和布局
        const buttonContainer = createElement('div', {
            className: 'header-button-container'
        });
        buttonContainer.appendChild(settingsButton);
        buttonContainer.appendChild(logoutButton);

        header.appendChild(title);
        header.appendChild(buttonContainer);
        console.log('[App] header 子元素已添加');

        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .chat-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 10px 20px;
                background-color: #f0f0f0;
                border-bottom: 1px solid #ddd;
            }
            
            .chat-header h1 {
                margin: 0;
                font-size: 18px;
                color: #333;
            }
            
            .header-button-container {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .logout-button,
            .settings-button {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .logout-button {
                background-color: #dc3545;
                color: white;
            }
            
            .logout-button:hover {
                background-color: #c82333;
            }
            
            .settings-button {
                background-color: #6c757d;
                color: white;
                font-size: 16px;
                padding: 8px;
                width: 36px;
            }
            
            .settings-button:hover {
                background-color: #5a6268;
            }
        `;
        document.head.appendChild(style);

        // 聊天窗口容器
        const chatContainer = createElement('div', {
            className: 'chat-container'
        });
        console.log('[App] chatContainer 已创建:', chatContainer);

        chatView.appendChild(header);
        chatView.appendChild(chatContainer);
        console.log('[App] chatView 子元素已添加');
        
        this.container.appendChild(chatView);
        console.log('[App] chatView 已添加到 container');
        console.log('[App] container.children:', this.container.children);

        // 创建聊天窗口组件
        console.log('[App] 创建聊天窗口组件...');
        this.currentView = new ChatWindow(chatContainer);
        
        console.log('[App] 聊天窗口创建完成');
        console.log('[App] messageContainer:', chatContainer.querySelector('.message-container'));
        console.log('[App] inputContainer:', chatContainer.querySelector('.input-container'));
        
        showNotification('连接成功', 'success');
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

export default App;

