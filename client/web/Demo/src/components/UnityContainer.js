/**
 * Unity 容器组件
 * 负责加载和管理 Unity WebGL 实例
 */

import { createElement } from '../utils/dom.js';
import { ControlButton } from './ControlButton.js';
import { FloatingPanel } from './FloatingPanel.js';
import { ChatWindow } from './ChatWindow.js';
import { SettingsPanel } from './SettingsPanel.js';

export class UnityContainer {
    constructor(container, client) {
        this.container = container;
        this.client = client;
        this.unityInstance = null;
        this.unityCanvas = null;
        this.controlButton = null;
        this.currentPanel = null;
        this.isLoading = false;
        
        this.init();
    }
    
    /**
     * 初始化
     */
    async init() {
        console.log('[UnityContainer] 初始化...');
        
        // ✅ 立即设置全局消息监听器（确保所有消息都被记录）
        this.setupGlobalMessageListener();
        
        // 创建 Unity 容器
        this.createUnityContainer();
        
        // 加载 Unity
        await this.loadUnity();
        
        // 创建控制按钮
        this.createControlButton();
        
        console.log('[UnityContainer] 初始化完成');
    }
    
    /**
     * ✅ 设置全局消息监听器（确保即使 ChatWindow 未打开也能记录消息）
     */
    setupGlobalMessageListener() {
        // 检查是否已经设置
        if (window._globalMessageListenerInitialized) {
            return;
        }
        
        console.log('[UnityContainer] 设置全局消息监听器');
        
        // 初始化全局消息历史
        if (!window._messageHistory) {
            window._messageHistory = [];
        }
        
        const { Events } = window.MuseumAgentSDK;
        
        // 监听消息发送（记录到全局历史）
        this.client.on(Events.MESSAGE_SENT, (data) => {
            const message = {
                id: data.id,
                type: 'sent',
                contentType: data.type === 'voice' ? 'voice' : 'text',
                content: data.content || '',
                timestamp: Date.now(),
                duration: data.type === 'voice' ? 0 : undefined,
                startTime: data.type === 'voice' ? data.startTime : undefined
            };
            
            // 检查是否已存在（避免重复）
            const exists = window._messageHistory.find(m => m.id === message.id);
            if (!exists) {
                window._messageHistory.push(message);
                console.log('[UnityContainer] 全局记录发送消息:', message.id);
            }
        });
        
        // 监听文本流（记录到全局历史）
        let globalCurrentTextMessage = null;
        this.client.on(Events.TEXT_CHUNK, (data) => {
            if (!globalCurrentTextMessage || globalCurrentTextMessage.id !== data.messageId) {
                // 新消息
                globalCurrentTextMessage = {
                    id: data.messageId,
                    type: 'received',
                    contentType: 'text',
                    content: data.chunk,
                    timestamp: Date.now(),
                    isStreaming: true
                };
                window._messageHistory.push(globalCurrentTextMessage);
                console.log('[UnityContainer] 全局记录接收文本消息:', globalCurrentTextMessage.id);
            } else {
                // 累加内容
                globalCurrentTextMessage.content += data.chunk;
            }
        });
        
        // 监听消息完成（标记流式消息完成）
        this.client.on(Events.MESSAGE_COMPLETE, (data) => {
            if (globalCurrentTextMessage && globalCurrentTextMessage.id === data.messageId) {
                globalCurrentTextMessage.isStreaming = false;
                globalCurrentTextMessage = null;
            }
        });
        
        // 监听语音流（记录到全局历史）
        let globalCurrentVoiceMessage = null;
        this.client.on(Events.VOICE_CHUNK, (data) => {
            const voiceMessageId = `${data.messageId}_voice`;
            
            if (!globalCurrentVoiceMessage || globalCurrentVoiceMessage.id !== voiceMessageId) {
                // 新消息
                globalCurrentVoiceMessage = {
                    id: voiceMessageId,
                    type: 'received',
                    contentType: 'voice',
                    content: '语音消息',
                    timestamp: Date.now(),
                    isStreaming: true,
                    duration: 0
                };
                window._messageHistory.push(globalCurrentVoiceMessage);
                console.log('[UnityContainer] 全局记录接收语音消息:', globalCurrentVoiceMessage.id);
            }
        });
        
        // 监听函数调用（记录到全局历史）
        this.client.on(Events.FUNCTION_CALL, (functionCall) => {
            const message = {
                id: `func_${Date.now()}_${Math.random()}`,
                type: 'received',
                contentType: 'function',
                content: functionCall,
                timestamp: Date.now()
            };
            window._messageHistory.push(message);
            console.log('[UnityContainer] 全局记录函数调用:', message.id);
        });
        
        // 监听录音完成（更新语音消息的时长和音频数据）
        this.client.on(Events.RECORDING_COMPLETE, (data) => {
            const message = window._messageHistory.find(m => m.id === data.id);
            if (message && message.contentType === 'voice') {
                message.duration = data.duration;
                message.audioData = data.audioData;
                console.log('[UnityContainer] 更新语音消息时长:', data.id, data.duration.toFixed(2) + 's');
            }
        });
        
        window._globalMessageListenerInitialized = true;
    }
    
    /**
     * 创建 Unity 容器
     */
    createUnityContainer() {
        // 清空容器
        this.container.innerHTML = '';
        this.container.className = 'unity-view';
        
        // 创建 Unity 容器
        const unityContainer = createElement('div', {
            id: 'unity-container',
            className: 'unity-container'
        });
        
        // 创建 Unity Canvas
        this.unityCanvas = createElement('canvas', {
            id: 'unity-canvas',
            className: 'unity-canvas'
        });
        this.unityCanvas.setAttribute('tabindex', '-1');
        
        unityContainer.appendChild(this.unityCanvas);
        
        // 创建加载提示
        const loadingBar = createElement('div', {
            id: 'unity-loading-bar',
            className: 'unity-loading-bar'
        });
        
        const loadingText = createElement('div', {
            className: 'unity-loading-text',
            textContent: '正在加载 Unity...'
        });
        
        const progressBarEmpty = createElement('div', {
            className: 'unity-progress-bar-empty'
        });
        
        const progressBarFull = createElement('div', {
            id: 'unity-progress-bar-full',
            className: 'unity-progress-bar-full'
        });
        
        progressBarEmpty.appendChild(progressBarFull);
        loadingBar.appendChild(loadingText);
        loadingBar.appendChild(progressBarEmpty);
        
        this.container.appendChild(unityContainer);
        this.container.appendChild(loadingBar);
    }
    
    /**
     * 加载 Unity
     */
    async loadUnity() {
        if (this.isLoading) {
            console.warn('[UnityContainer] Unity 正在加载中...');
            return;
        }
        
        this.isLoading = true;
        console.log('[UnityContainer] 开始加载 Unity...');
        
        try {
            // 动态加载 Unity loader
            await this.loadUnityLoader();
            
            // 配置 Unity
            const buildUrl = 'unity/Build';
            const config = {
                dataUrl: buildUrl + '/build.data.unityweb',
                frameworkUrl: buildUrl + '/build.framework.js.unityweb',
                codeUrl: buildUrl + '/build.wasm.unityweb',
                streamingAssetsUrl: 'unity/StreamingAssets',
                companyName: 'SoulFlaw',
                productName: 'Museum',
                productVersion: '0.1.0'
            };
            
            // 创建 Unity 实例
            const progressBarFull = document.getElementById('unity-progress-bar-full');
            
            this.unityInstance = await createUnityInstance(this.unityCanvas, config, (progress) => {
                if (progressBarFull) {
                    progressBarFull.style.width = (100 * progress) + '%';
                }
            });
            
            // 保存到全局变量（供 Unity 调用）
            window.unityInstance = this.unityInstance;
            
            // 隐藏加载提示
            const loadingBar = document.getElementById('unity-loading-bar');
            if (loadingBar) {
                loadingBar.style.display = 'none';
            }
            
            console.log('[UnityContainer] Unity 加载完成');
            
        } catch (error) {
            console.error('[UnityContainer] Unity 加载失败:', error);
            alert('Unity 加载失败: ' + error.message);
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * 加载 Unity Loader
     */
    loadUnityLoader() {
        return new Promise((resolve, reject) => {
            // 检查是否已加载
            if (window.createUnityInstance) {
                resolve();
                return;
            }
            
            // 动态加载脚本
            const script = document.createElement('script');
            script.src = 'unity/Build/build.loader.js';
            script.onload = () => {
                console.log('[UnityContainer] Unity Loader 加载完成');
                resolve();
            };
            script.onerror = () => {
                reject(new Error('无法加载 Unity Loader'));
            };
            
            document.body.appendChild(script);
        });
    }
    
    /**
     * 创建控制按钮
     */
    createControlButton() {
        this.controlButton = new ControlButton(this.client, {
            onMenuSelect: (action) => this.handleMenuSelect(action)
        });
    }
    
    /**
     * 处理菜单选择
     */
    handleMenuSelect(action) {
        console.log('[UnityContainer] 菜单选择:', action);
        
        if (action === 'settings') {
            this.showSettingsPanel();
        } else if (action === 'chat') {
            this.showChatPanel();
        }
    }
    
    /**
     * 显示设置面板
     */
    showSettingsPanel() {
        // 隐藏控制按钮
        this.controlButton.hide();
        
        // 创建设置面板
        this.currentPanel = new FloatingPanel(SettingsPanel, this.client, {
            title: '客户端配置',
            onClose: () => this.closePanel()
        });
        
        // ✅ 保存设置面板实例到全局变量（供 ChatWindow 访问）
        window._currentSettingsPanel = this.currentPanel.contentComponent;
    }
    
    /**
     * 显示聊天面板
     */
    showChatPanel() {
        // 隐藏控制按钮
        this.controlButton.hide();
        
        // 创建聊天面板
        this.currentPanel = new FloatingPanel(ChatWindow, this.client, {
            title: 'MuseumAgent 智能体',
            onClose: () => this.closePanel()
        });
    }
    
    /**
     * 关闭面板
     */
    closePanel() {
        if (this.currentPanel) {
            this.currentPanel.destroy();
            this.currentPanel = null;
        }
        
        // ✅ 清除全局设置面板引用
        window._currentSettingsPanel = null;
        
        // 显示控制按钮
        this.controlButton.show();
    }
    
    /**
     * 销毁
     */
    destroy() {
        console.log('[UnityContainer] 销毁组件');
        
        // 销毁控制按钮
        if (this.controlButton) {
            this.controlButton.destroy();
            this.controlButton = null;
        }
        
        // 销毁当前面板
        if (this.currentPanel) {
            this.currentPanel.destroy();
            this.currentPanel = null;
        }
        
        // 销毁 Unity 实例
        if (this.unityInstance) {
            this.unityInstance.Quit();
            this.unityInstance = null;
            window.unityInstance = null;
        }
        
        // 清空容器
        this.container.innerHTML = '';
        
        console.log('[UnityContainer] 组件已销毁');
    }
}

