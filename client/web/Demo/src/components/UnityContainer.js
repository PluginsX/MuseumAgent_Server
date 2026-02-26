/**
 * Unity 容器组件
 * ✅ 重构版本：精简职责，只负责 Unity + ControlButton + 面板调度
 * 不再处理消息记录和配置管理（由 AgentController 统一管理）
 */

import { createElement } from '../utils/dom.js';
import { ControlButton } from './ControlButton.js';
import { FloatingPanel } from './FloatingPanel.js';

export class UnityContainer {
    constructor(container, client, agentController) {
        this.container = container;
        this.client = client;
        this.agentController = agentController;  // ✅ 引用 AgentController
        
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
        
        // 创建 Unity 容器
        this.createUnityContainer();
        
        // 加载 Unity
        await this.loadUnity();
        
        // 创建控制按钮
        this.createControlButton();
        
        console.log('[UnityContainer] 初始化完成');
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
        
        // ✅ 阻止 Unity Canvas 捕获键盘事件（除非它有焦点）
        this.unityCanvas.addEventListener('keydown', (e) => {
            // 如果当前焦点不在 canvas 上，不处理键盘事件
            if (document.activeElement !== this.unityCanvas) {
                return;
            }
        }, true);  // 使用捕获阶段
        
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
            console.log('[UnityContainer] 开始加载 Unity Loader...');
            await this.loadUnityLoader();
            console.log('[UnityContainer] Unity Loader 加载完成');
            
            // 配置 Unity
            const buildUrl = 'unity/Build';
            const config = {
                dataUrl: buildUrl + '/build.data',
                frameworkUrl: buildUrl + '/build.framework.js',
                codeUrl: buildUrl + '/build.wasm',
                streamingAssetsUrl: 'unity/StreamingAssets',
                companyName: 'SoulFlaw',
                productName: 'Museum',
                productVersion: '0.1.0'
            };
            
            // 获取当前页面的协议和域名，用于构建完整的URL
            const currentOrigin = window.location.origin;
            console.log('[UnityContainer] 当前页面Origin:', currentOrigin);
            
            // 配置Addressable系统的基础URL
            // 这样Unity就能正确解析ServerData中的bundle文件路径
            const addressablesBaseUrl = currentOrigin + '/unity/ServerData/WebGL/';
            console.log('[UnityContainer] Addressables基础URL:', addressablesBaseUrl);
            
            // 将Addressables配置添加到Unity配置中
            config.addressablesBaseUrl = addressablesBaseUrl;
            
            // 配置StreamingAssets的基础URL
            const streamingAssetsBaseUrl = currentOrigin + '/unity/StreamingAssets/';
            config.streamingAssetsBaseUrl = streamingAssetsBaseUrl;
            
            console.log('[UnityContainer] Unity 配置:', config);
            
            // 创建 Unity 实例
            const progressBarFull = document.getElementById('unity-progress-bar-full');
            console.log('[UnityContainer] 开始创建 Unity 实例...');
            
            this.unityInstance = await createUnityInstance(this.unityCanvas, config, (progress) => {
                console.log('[UnityContainer] Unity 加载进度:', Math.round(progress * 100) + '%');
                if (progressBarFull) {
                    progressBarFull.style.width = (100 * progress) + '%';
                }
            });
            
            // 保存到全局变量（供 Unity 调用）
            window.unityInstance = this.unityInstance;
            console.log('[UnityContainer] Unity 实例已保存到全局变量:', window.unityInstance ? '成功' : '失败');
            
            // 配置Addressable系统的远程加载路径
            if (this.unityInstance) {
                console.log('[UnityContainer] 配置Addressable系统...');
                try {
                    // 调用Unity的Addressable系统配置方法
                    // 注意：这需要在Unity项目中实现相应的C#方法
                    this.unityInstance.SendMessage('AddressablesManager', 'SetRemoteLoadPath', addressablesBaseUrl);
                    console.log('[UnityContainer] Addressable系统配置完成');
                } catch (error) {
                    console.warn('[UnityContainer] 配置Addressable系统失败:', error);
                    console.warn('[UnityContainer] 可能是因为Unity场景中没有AddressablesManager对象');
                }
            }
            
            // 隐藏加载提示
            const loadingBar = document.getElementById('unity-loading-bar');
            if (loadingBar) {
                loadingBar.style.display = 'none';
                console.log('[UnityContainer] 加载提示已隐藏');
            }
            
            console.log('[UnityContainer] Unity 加载完成，实例状态:', this.unityInstance ? '已创建' : '未创建');
            
            // 尝试调用 Unity 的 RegisterToJS 方法
            if (this.unityInstance) {
                console.log('[UnityContainer] 尝试调用 Unity 的 RegisterToJS 方法...');
                try {
                    this.unityInstance.SendMessage('AgentBridge', 'RegisterToJS');
                    console.log('[UnityContainer] 已调用 Unity 的 RegisterToJS 方法');
                } catch (error) {
                    console.warn('[UnityContainer] 调用 RegisterToJS 方法失败:', error);
                    console.warn('[UnityContainer] 可能是因为 Unity 场景中没有 AgentBridge 对象，或对象名称不正确');
                }
            }
            
        } catch (error) {
            console.error('[UnityContainer] Unity 加载失败:', error);
            console.error('[UnityContainer] 错误详情:', error.stack);
            alert('Unity 加载失败: ' + error.message);
        } finally {
            this.isLoading = false;
            console.log('[UnityContainer] Unity 加载过程结束，isLoading:', this.isLoading);
        }
    }
    
    /**
     * 加载 Unity Loader
     */
    loadUnityLoader() {
        return new Promise((resolve, reject) => {
            // 检查是否已加载
            if (window.createUnityInstance) {
                console.log('[UnityContainer] Unity Loader 已加载，直接使用');
                resolve();
                return;
            }
            
            console.log('[UnityContainer] 开始加载 Unity Loader...');
            
            // 动态加载脚本
            const script = document.createElement('script');
            script.src = 'unity/Build/build.loader.js';
            console.log('[UnityContainer] Unity Loader 脚本路径:', script.src);
            
            script.onload = () => {
                console.log('[UnityContainer] Unity Loader 加载完成');
                console.log('[UnityContainer] createUnityInstance 函数是否存在:', typeof window.createUnityInstance === 'function');
                resolve();
            };
            
            script.onerror = () => {
                console.error('[UnityContainer] Unity Loader 加载失败');
                reject(new Error('无法加载 Unity Loader'));
            };
            
            script.onabort = () => {
                console.error('[UnityContainer] Unity Loader 加载被中止');
                reject(new Error('Unity Loader 加载被中止'));
            };
            
            console.log('[UnityContainer] 正在添加 Unity Loader 脚本到文档...');
            document.body.appendChild(script);
            console.log('[UnityContainer] Unity Loader 脚本已添加到文档');
        });
    }
    
    /**
     * 创建控制按钮
     */
    createControlButton() {
        this.controlButton = new ControlButton(this.client, this.agentController, {
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
     * ✅ 显示设置面板（通过 AgentController 获取单例）
     */
    showSettingsPanel() {
        // 隐藏控制按钮
        this.controlButton.hide();
        
        // ✅ 通过 AgentController 获取 SettingsPanel 单例
        const settingsPanel = this.agentController.getSettingsPanel();
        
        // 创建浮动面板包装
        this.currentPanel = new FloatingPanel(settingsPanel, {
            title: '客户端配置',
            onClose: () => this.closePanel()
        });
    }
    
    /**
     * ✅ 显示聊天面板（通过 AgentController 获取单例）
     */
    showChatPanel() {
        // 隐藏控制按钮
        this.controlButton.hide();
        
        // ✅ 通过 AgentController 获取 ChatWindow 单例
        const chatWindow = this.agentController.getChatWindow();
        
        // 创建浮动面板包装
        this.currentPanel = new FloatingPanel(chatWindow, {
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
