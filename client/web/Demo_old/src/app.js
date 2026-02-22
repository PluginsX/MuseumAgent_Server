/**
 * MuseumAgent Demo - 应用入口
 * 使用 MuseumAgentSDK 构建产物（UMD 格式）
 */

// 从全局变量获取 SDK
const { MuseumAgentClient, Events } = window.MuseumAgentSDK;

import { LoginForm } from './components/LoginForm.js';
import { ChatWindow } from './components/ChatWindow.js';
import { createElement, $, showNotification } from './utils/dom.js';

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

        // ✅ 尝试从保存的会话恢复
        const client = new MuseumAgentClient({
            serverUrl: 'wss://museum.soulflaw.com:12301',
            functionCalling: this.getPetFunctions()
        });
        
        const restored = await client.reconnectFromSavedSession();
        if (restored) {
            console.log('[App] 会话恢复成功');
            this.client = client;
            this.showChatView();
            showNotification('会话已恢复', 'success');
        } else {
            console.log('[App] 没有保存的会话，显示登录页面');
            this.showLoginView();
        }

        console.log('[App] 应用初始化完成');
    }
    
    /**
     * 获取宠物函数配置
     */
    getPetFunctions() {
        return [
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
                throw error; // 重新抛出错误，让LoginForm处理
            }
        });
    }

    /**
     * 连接并显示聊天界面
     */
    async connectAndShowChat(serverUrl, authData) {
        console.log('[App] 连接服务器...');
        
        // 创建客户端（使用库默认的最佳VAD参数）
        this.client = new MuseumAgentClient({
            serverUrl: serverUrl,
            requireTTS: true,
            enableSRS: true,
            autoPlay: true,  // 默认开启自动播放
            vadEnabled: true,
            functionCalling: this.getPetFunctions()
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
        
        // ✅ 保存会话（自动加密）
        await this.client.saveSession();
        console.log('[App] 会话已保存');
        
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
                    // ✅ 将设置面板引用传递给客户端（用于差异配置更新）
                    this.client.setSettingsPanel(window.settingsPanel);
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

        // 全屏按钮
        const fullscreenButton = createElement('button', {
            className: 'fullscreen-button',
            textContent: '◱'
        });
        fullscreenButton.addEventListener('click', () => {
            this.toggleFullscreen();
        });

        buttonContainer.appendChild(settingsButton);
        buttonContainer.appendChild(logoutButton);
        buttonContainer.appendChild(fullscreenButton);
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
        
        // 断开连接并清除保存的会话
        if (this.client) {
            await this.client.disconnect('用户登出', true);  // ✅ 第二个参数 true 表示清除会话
            this.client.cleanup();
            this.client = null;
        }
        
        // 显示登录界面
        this.showLoginView();
    }

    /**
     * 切换全屏
     */
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            // 进入全屏
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            } else if (document.documentElement.webkitRequestFullscreen) {
                document.documentElement.webkitRequestFullscreen();
            } else if (document.documentElement.msRequestFullscreen) {
                document.documentElement.msRequestFullscreen();
            }
        } else {
            // 退出全屏
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        }
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
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

export default App;
