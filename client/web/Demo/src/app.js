/**
 * MuseumAgent Demo - 应用入口
 * 基于 MuseumAgentSDK 客户端库开发
 */

import { MuseumAgentClient, Events } from '../lib/MuseumAgentSDK.js';
import { LoginForm } from './components/LoginForm.js';
import { ChatWindow } from './components/ChatWindow.js';
import { createElement, $, showNotification } from './utils/dom.js';
import { encryptData, decryptData } from './utils/security.js';

class App {
    constructor() {
        this.container = null;
        this.currentView = null;
        this.client = null;
        
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
            this.container = createElement('div', { id: 'app' });
            document.body.appendChild(this.container);
        }

        // 直接显示登录页面（不尝试恢复会话）
        // 因为 WebSocket 会话是临时的，关闭浏览器后会话就失效了
        this.showLoginView();

        console.log('[App] 应用初始化完成');
    }

    /**
     * 显示登录视图
     */
    showLoginView() {
        console.log('[App] 显示登录视图');
        
        this.cleanupCurrentView();
        
        this.container.innerHTML = '';
        this.container.style.display = 'flex';
        this.container.style.alignItems = 'center';
        this.container.style.justifyContent = 'center';
        
        this.currentView = new LoginForm(this.container, async (serverUrl, authData) => {
            // 登录回调
            try {
                await this.connectAndShowChat(serverUrl, authData);
                showNotification('登录成功', 'success');
            } catch (error) {
                console.error('[App] 登录失败:', error);
                showNotification('登录失败: ' + error.message, 'error');
            }
        });
    }

    /**
     * 连接并显示聊天界面
     */
    async connectAndShowChat(serverUrl, authData) {
        console.log('[App] 连接服务器...');
        
        // 桌面智能宠物预设函数定义
        const petFunctions = [
            {
                name: "move_to_position",
                description: "移动宠物到屏幕指定位置",
                parameters: {
                    type: "object",
                    properties: {
                        x: { type: "number", description: "X坐标（像素）" },
                        y: { type: "number", description: "Y坐标（像素）" },
                        duration: { type: "number", description: "移动持续时间（毫秒）" }
                    },
                    required: ["x", "y"]
                }
            },
            {
                name: "play_animation",
                description: "播放宠物动画",
                parameters: {
                    type: "object",
                    properties: {
                        animation: {
                            type: "string",
                            enum: ["idle", "walk", "run", "jump", "sit", "sleep", "happy", "sad", "angry"],
                            description: "动画类型"
                        },
                        loop: { type: "boolean", description: "是否循环播放" }
                    },
                    required: ["animation"]
                }
            },
            {
                name: "show_emotion",
                description: "显示宠物情绪表情",
                parameters: {
                    type: "object",
                    properties: {
                        emotion: {
                            type: "string",
                            enum: ["happy", "sad", "angry", "surprised", "confused", "love"],
                            description: "情绪类型"
                        },
                        duration: { type: "number", description: "持续时间（毫秒）" }
                    },
                    required: ["emotion"]
                }
            },
            {
                name: "speak_text",
                description: "让宠物说话（显示气泡文字）",
                parameters: {
                    type: "object",
                    properties: {
                        text: { type: "string", description: "要说的文字内容" },
                        duration: { type: "number", description: "显示持续时间（毫秒）" }
                    },
                    required: ["text"]
                }
            },
            {
                name: "change_size",
                description: "改变宠物大小",
                parameters: {
                    type: "object",
                    properties: {
                        scale: { type: "number", description: "缩放比例（0.5-2.0）" }
                    },
                    required: ["scale"]
                }
            }
        ];

        // 创建客户端（使用灵敏的VAD参数）
        this.client = new MuseumAgentClient({
            serverUrl: serverUrl,
            requireTTS: true,
            enableSRS: true,
            autoPlay: false,  // 默认关闭自动播放，用户可以在设置中开启
            vadEnabled: true,
            functionCalling: petFunctions,
            vadParams: {
                silenceThreshold: 0.005,      // 更低的静音阈值，更灵敏
                silenceDuration: 500,          // 更短的静音持续时间，快速响应
                speechThreshold: 0.015,        // 更低的语音阈值，更容易触发
                minSpeechDuration: 150,        // 更短的最小语音时长
                preSpeechPadding: 100,         // 更短的前置填充
                postSpeechPadding: 200         // 更短的后置填充
            }
        });

        // 监听会话过期
        this.client.on(Events.SESSION_EXPIRED, () => {
            showNotification('会话已过期，请重新登录', 'error');
            this.logout();
        });

        // 监听连接错误
        this.client.on(Events.CONNECTION_ERROR, (error) => {
            showNotification('连接错误: ' + error.message, 'error');
        });

        // 连接
        await this.client.connect(authData);
        
        // 显示聊天界面
        this.showChatView();
    }

    /**
     * 显示聊天视图
     */
    showChatView() {
        console.log('[App] 显示聊天视图');
        
        // 清空容器
        this.container.innerHTML = '';
        this.container.style.display = 'block';
        this.container.style.alignItems = '';
        this.container.style.justifyContent = '';
        this.container.style.height = '100vh';
        this.container.style.width = '100vw';

        // 创建聊天视图
        const chatView = createElement('div', { className: 'chat-view' });

        // 头部
        const header = createElement('div', { className: 'chat-header' });
        const title = createElement('h1', { textContent: 'MuseumAgent 智能体' });
        
        // 按钮容器
        const buttonContainer = createElement('div', { className: 'header-button-container' });
        
        // 设置按钮
        const settingsButton = createElement('button', {
            className: 'settings-button',
            textContent: '⚙️'
        });
        settingsButton.addEventListener('click', () => {
            if (window.settingsPanel) {
                window.settingsPanel.toggle();
            } else {
                import('./components/SettingsPanel.js').then(({ SettingsPanel }) => {
                    window.settingsPanel = new SettingsPanel(this.client);
                    window.settingsPanel.toggle();
                });
            }
        });
        
        // 登出按钮
        const logoutButton = createElement('button', {
            className: 'logout-button',
            textContent: '登出'
        });
        logoutButton.addEventListener('click', () => {
            this.logout();
        });

        buttonContainer.appendChild(settingsButton);
        buttonContainer.appendChild(logoutButton);
        header.appendChild(title);
        header.appendChild(buttonContainer);

        // 聊天容器
        const chatContainer = createElement('div', { className: 'chat-container' });

        chatView.appendChild(header);
        chatView.appendChild(chatContainer);
        this.container.appendChild(chatView);

        // 创建聊天窗口组件
        this.currentView = new ChatWindow(chatContainer, this.client);
        
        console.log('[App] 聊天窗口创建完成');
    }

    /**
     * 登出
     */
    async logout() {
        console.log('[App] 登出');
        
        // 断开连接
        if (this.client) {
            await this.client.disconnect();
            this.client.cleanup();
            this.client = null;
        }
        
        // 清除保存的认证信息
        this.clearAuthData();
        
        // 显示登录界面
        this.showLoginView();
    }

    /**
     * 清理当前视图
     */
    cleanupCurrentView() {
        if (this.currentView && typeof this.currentView.destroy === 'function') {
            this.currentView.destroy();
        }
        this.currentView = null;
    }

    /**
     * 保存认证信息
     */
    async saveAuthData(serverUrl, authData) {
        const data = {
            serverUrl,
            authData: {
                type: authData.type,
                account: authData.account,
                password: authData.password ? await encryptData(authData.password) : undefined,
                api_key: authData.api_key ? await encryptData(authData.api_key) : undefined
            }
        };
        localStorage.setItem('museumAgent_auth', JSON.stringify(data));
    }

    /**
     * 加载认证信息
     */
    loadAuthData() {
        const data = localStorage.getItem('museumAgent_auth');
        if (!data) return null;
        
        try {
            return JSON.parse(data);
        } catch (error) {
            return null;
        }
    }

    /**
     * 清除认证信息
     */
    clearAuthData() {
        localStorage.removeItem('museumAgent_auth');
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

export default App;
