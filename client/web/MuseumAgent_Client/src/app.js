/**
 * MuseumAgent Demo - 应用入口
 * ✅ 重构版本：引入 AgentController，实现 Agent-First 架构
 * 使用 MuseumAgentSDK 构建产物（UMD 格式）
 */

// 从全局变量获取 SDK
const { MuseumAgentClient, Events } = window.MuseumAgentSDK;

import { LoginForm } from './components/LoginForm.js';
import { UnityContainer } from './components/UnityContainer.js';
import { AgentController } from './AgentController.js';
import { createElement, $, showNotification } from './utils/dom.js';

/**
 * 自动推导智能体服务端地址
 * 自适应本地开发环境和线上部署环境：
 * - 本地环境（localhost / 127.0.0.1）：直接连接本地智能体服务器 ws://localhost:12301
 *   最终 WebSocket 路径：ws://localhost:12301/ws/agent/stream
 * - 线上环境：通过 Nginx 反代路径 /agent 访问
 *   最终 WebSocket 路径：wss://host/agent/ws/agent/stream
 * @returns {string} WebSocket 服务端地址（baseUrl，WebSocketClient 会自动拼接 /ws/agent/stream）
 */
function getAgentServerUrl() {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0';

    if (isLocal) {
        // 本地开发环境：直接连接智能体服务器（端口 12301），跳过前端静态服务器（端口 12302）
        // WebSocketClient 会自动拼接 /ws/agent/stream，最终：ws://localhost:12301/ws/agent/stream
        return 'ws://localhost:12301';
    }

    // 线上环境：通过 Nginx 反代，路径 /agent/ws/ 转发到 127.0.0.1:12301/ws/
    // WebSocketClient 会自动拼接 /ws/agent/stream，最终：wss://host/agent/ws/agent/stream
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/agent`;
}

class App {
    constructor() {
        this.container = null;
        this.currentView = null;
        this.client = null;
        this.agentController = null;
        
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
        
        // 清理错误的 localStorage 缓存（修复路径问题）
        this.cleanupInvalidSession();

        // 尝试从保存的会话恢复
        const client = new MuseumAgentClient({
            serverUrl: getAgentServerUrl(),
            functionCalling: this.getPetFunctions()
        });
        
        const restored = await client.reconnectFromSavedSession();
        if (restored) {
            console.log('[App] 会话恢复成功');
            this.client = client;
            
            // 创建 AgentController
            this.agentController = new AgentController(this.client);
            console.log('[App] AgentController 已创建');
            
            this.showUnityView();
            showNotification('会话已恢复', 'success');
        } else {
            console.log('[App] 没有保存的会话，显示登录页面');
            this.showLoginView();
        }

        console.log('[App] 应用初始化完成');
    }
    
    /**
     * ✅ 清理无效的会话缓存
     * 修复：如果保存的 serverUrl 是 /mas/（控制面板路径），则清除缓存
     */
    cleanupInvalidSession() {
        try {
            const savedSession = localStorage.getItem('museumAgentSession');
            if (savedSession) {
                const session = JSON.parse(savedSession);
                // 检查是否是错误的控制面板路径
                if (session.serverUrl && session.serverUrl.includes('/mas')) {
                    console.warn('[App] 检测到错误的 serverUrl (包含 /mas)，清除缓存');
                    localStorage.removeItem('museumAgentSession');
                    showNotification('检测到旧版本缓存，已自动清理', 'info');
                }
            }
        } catch (error) {
            console.error('[App] 清理会话缓存失败:', error);
        }
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
        
        // ✅ 创建 AgentController（登录成功后立即创建）
        this.agentController = new AgentController(this.client);
        console.log('[App] AgentController 已创建');
        
        // 显示 Unity 界面
        this.showUnityView();
    }

    /**
     * ✅ 显示 Unity 视图（传入 AgentController）
     */
    showUnityView() {
        console.log('[App] 显示 Unity 视图');
        
        this.cleanupCurrentView();
        
        // 清空容器
        this.container.innerHTML = '';
        this.container.style.display = 'block';
        this.container.style.alignItems = '';
        this.container.style.justifyContent = '';
        this.container.style.height = '100vh';
        this.container.style.width = '100vw';
        this.container.style.overflow = 'hidden';

        // ✅ 创建 Unity 容器组件（传入 AgentController）
        this.currentView = new UnityContainer(this.container, this.client, this.agentController);
        
        console.log('[App] Unity 视图创建完成');
    }

    /**
     * 登出（清理 AgentController）
     */
    async logout() {
        console.log('[App] 登出');
        
        // 销毁 AgentController
        if (this.agentController) {
            this.agentController.destroy();
            this.agentController = null;
        }
        
        // 断开连接并清除保存的会话
        if (this.client) {
            await this.client.disconnect('用户登出', true);
            this.client.cleanup();
            this.client = null;
        }
        
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
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

// UnityAgentBridge对象，用于接收Unity的调用
window.UnityAgentBridge = {
    // 存储Unity实例
    unityInstance: null,
    
    // 注册Unity实例到JS环境
    registerUnityInstance: function(gameObjectName) {
        console.log('[UnityAgentBridge] 注册Unity实例:', gameObjectName);
        this.unityInstance = window.unityInstance;
        console.log('[UnityAgentBridge] Unity实例已注册:', this.unityInstance ? '成功' : '失败');
    },
    
    // 接收Unity发送的上下文更新
    updateContext: function(contextJson) {
        console.log('[UnityAgentBridge] 接收上下文更新:', contextJson);
        try {
            // 解析上下文数据
            const contextData = JSON.parse(contextJson);
            console.log('[UnityAgentBridge] 解析后的上下文数据:', contextData);
            
            // 更新智能体客户端的上下文
            if (window.app && window.app.client) {
                console.log('[UnityAgentBridge] 更新智能体客户端上下文');
                try {
                    // 调用SDK的updateContext方法
                    window.app.client.updateContext(contextData);
                    console.log('[UnityAgentBridge] 上下文更新成功');
                } catch (error) {
                    console.error('[UnityAgentBridge] 更新上下文失败:', error);
                }
            } else {
                console.warn('[UnityAgentBridge] 智能体客户端未初始化');
            }
        } catch (error) {
            console.error('[UnityAgentBridge] 解析上下文数据失败:', error);
        }
    },
    
    // 接收Unity回传的函数执行结果
    notifyFunctionResult: function(resultJson) {
        console.log('[UnityAgentBridge] 接收函数执行结果:', resultJson);
        try {
            // 解析结果数据
            const resultData = JSON.parse(resultJson);
            console.log('[UnityAgentBridge] 解析后的函数执行结果:', resultData);
            
            // 处理函数执行结果
            if (window.app && window.app.client) {
                console.log('[UnityAgentBridge] 处理函数执行结果');
                // 这里需要根据智能体客户端的API来处理函数执行结果
                // 暂时打印日志，后续根据实际API进行修改
            } else {
                console.warn('[UnityAgentBridge] 智能体客户端未初始化');
            }
        } catch (error) {
            console.error('[UnityAgentBridge] 解析函数执行结果失败:', error);
        }
    },
    
    // 接收Unity转发的用户消息
    forwardUserMessage: function(message) {
        console.log('[UnityAgentBridge] 接收转发的用户消息:', message);
        try {
            // 处理转发的用户消息
            if (window.app && window.app.client) {
                console.log('[UnityAgentBridge] 发送用户消息');
                // 使用 sendText 方法替代不存在的 sendMessage 方法
                window.app.client.sendText(message);
            } else {
                console.warn('[UnityAgentBridge] 智能体客户端未初始化');
            }
        } catch (error) {
            console.error('[UnityAgentBridge] 处理用户消息失败:', error);
        }
    }
};

export default App;
