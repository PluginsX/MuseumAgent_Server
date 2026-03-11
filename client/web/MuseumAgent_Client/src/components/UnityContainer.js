/**
 * Unity 容器组件
 * ✅ 重构版本：精简职责，只负责 Unity + ControlButton + 面板调度
 * 不再处理消息记录和配置管理（由 AgentController 统一管理）
 */

import { createElement, detectAndOptimizeForDevice } from '../utils/dom.js';
import { ControlButton } from './ControlButton.js';
import { FloatingPanel } from './FloatingPanel.js';
import { detectDeviceEnvironment } from '../commonFunction.js';

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
        
        // ✅ 初始化设备环境信息
        this.deviceInfo = detectDeviceEnvironment();
        console.log('[UnityContainer] 设备信息:', this.deviceInfo);
        
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
        // 只在非 web-mode 下阻止键盘事件
        this.unityCanvas.addEventListener('keydown', (e) => {
            // 如果处于 web-mode，允许键盘事件正常传播
            if (document.body.classList.contains('web-mode')) {
                return;
            }
            // 如果当前焦点是输入框或textarea，不处理键盘事件
            if (document.activeElement.tagName === 'INPUT' || 
                document.activeElement.tagName === 'TEXTAREA' ||
                document.activeElement.isContentEditable) {
                return;
            }
            // 如果事件目标在输入框或textarea内，不处理键盘事件
            if (e.target.tagName === 'INPUT' || 
                e.target.tagName === 'TEXTAREA' ||
                e.target.isContentEditable ||
                e.target.closest('input') ||
                e.target.closest('textarea')) {
                return;
            }
            // 如果当前焦点不在 canvas 上，阻止事件继续传播
            if (document.activeElement !== this.unityCanvas) {
                e.stopPropagation();
                return;
            }
        }, true);  // 使用捕获阶段
        
        unityContainer.appendChild(this.unityCanvas);
        
        // ✅ 移动端视频优化：在 canvas 创建后立即应用
        if (this.unityCanvas) {
            detectAndOptimizeForDevice();
        }
        
        // ✅ 禁用右键菜单和文本选择（Unity 主界面）
        this.setupUnityViewInteractions();
        
        // 创建加载提示
        const loadingBar = createElement('div', {
            id: 'unity-loading-bar',
            className: 'unity-loading-bar'
        });
        
        const loadingText = createElement('div', {
            className: 'unity-loading-text',
            textContent: '加载中请稍等...'
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
     * 设置 Unity 视图的交互限制（禁用右键、选择等）
     * 只在非 web-mode 下生效
     */
    setupUnityViewInteractions() {
        console.log('[UnityContainer] 设置 Unity 视图交互限制...');
        
        // 获取整个文档 body
        const doc = document.body;
        
        // 1. 全局阻止右键菜单（只在非 web-mode 下阻止）
        doc.addEventListener('contextmenu', (e) => {
            // 如果处于 web-mode，允许右键菜单
            if (doc.classList.contains('web-mode')) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            console.log('[UnityContainer] ⛔ 右键菜单已阻止（Unity 模式）');
            return false;
        }, true);  // 使用捕获阶段，确保优先级最高
        
        // 2. 阻止所有元素的默认拖拽行为（只在非 web-mode 下阻止）
        const allElements = doc.querySelectorAll('*');
        allElements.forEach(el => {
            el.addEventListener('dragstart', (e) => {
                // 如果处于 web-mode，允许拖拽
                if (doc.classList.contains('web-mode')) {
                    return;
                }
                e.preventDefault();
                e.stopPropagation();
                return false;
            }, true);
            
            el.addEventListener('drop', (e) => {
                // 如果处于 web-mode，允许拖放
                if (doc.classList.contains('web-mode')) {
                    return;
                }
                e.preventDefault();
                e.stopPropagation();
                return false;
            }, true);
        });
        
        // 3. 阻止文本选择和复制（只在非 web-mode 下阻止）
        doc.addEventListener('selectstart', (e) => {
            // 如果处于 web-mode，允许文本选择
            if (doc.classList.contains('web-mode')) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            console.log('[UnityContainer] ⛔ 文本选择已阻止（Unity 模式）');
            return false;
        }, true);
        
        doc.addEventListener('copy', (e) => {
            // 如果处于 web-mode，允许复制
            if (doc.classList.contains('web-mode')) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            console.log('[UnityContainer] ⛔ 复制已阻止（Unity 模式）');
            return false;
        }, true);
        
        doc.addEventListener('cut', (e) => {
            // 如果处于 web-mode，允许剪切
            if (doc.classList.contains('web-mode')) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            console.log('[UnityContainer] ⛔ 剪切已阻止（Unity 模式）');
            return false;
        }, true);
        
        // 4. 阻止长按触发菜单（移动端）（只在非 web-mode 下阻止）
        let touchTimer = null;
        doc.addEventListener('touchstart', (e) => {
            // 如果处于 web-mode，允许长按
            if (doc.classList.contains('web-mode')) {
                return;
            }
            touchTimer = setTimeout(() => {
                console.log('[UnityContainer] ⛔ 长按已阻止（Unity 模式）');
                e.preventDefault();
            }, 500);  // 500ms 后触发
        }, { passive: false });
        
        doc.addEventListener('touchend', () => {
            if (touchTimer) {
                clearTimeout(touchTimer);
                touchTimer = null;
            }
        });
        
        doc.addEventListener('touchmove', (e) => {
            // 如果处于 web-mode，允许触摸滚动
            if (doc.classList.contains('web-mode')) {
                return;
            }
            e.preventDefault();  // 阻止滚动
        }, { passive: false });
        
        console.log('[UnityContainer] ✓ Unity 视图交互限制设置完成');
    }
    
    /**
     * 恢复正常的网页交互（聊天/配置页面）
     */
    restoreNormalInteractions() {
        console.log('[UnityContainer] 恢复正常的网页交互...');
        
        const doc = document.body;
        
        // 移除所有阻止事件监听器
        // 注意：由于我们使用了捕获阶段和匿名函数，这里需要重新添加允许的事件
        
        // 1. 允许右键菜单（通过移除阻止监听器）
        // 由于我们无法直接移除匿名监听器，我们通过检查当前视图类型来控制行为
        
        // 2. 允许文本选择和复制
        // 这些现在由 CSS 控制（.chat-view 类）
        
        console.log('[UnityContainer] ✓ 正常交互已恢复');
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
        
        // ✅ 关键修复：在 Unity 加载期间保持心跳
        const keepAliveInterval = setInterval(() => {
            if (this.client && this.client.wsClient && this.client.wsClient.isConnected()) {
                console.log('[UnityContainer] 发送保活心跳（Unity 加载中）');
                // 发送一个轻量级的心跳消息
                this.client.wsClient.send({
                    version: '1.0',
                    msg_type: 'HEARTBEAT_REPLY',
                    session_id: this.client.sessionId,
                    payload: { 
                        client_status: 'LOADING_UNITY',
                        progress: 'loading'
                    },
                    timestamp: Date.now()
                });
            }
        }, 30000);  // 每 30 秒发送一次心跳
        
        try {
            // 动态加载 Unity loader
            console.log('[UnityContainer] 开始加载 Unity Loader...');
            await this.loadUnityLoader();
            console.log('[UnityContainer] Unity Loader 加载完成');
            
            // 配置 Unity
            const buildUrl = 'unity/Build';
            const config = {
                dataUrl: buildUrl + '/build.data.unityweb',
                frameworkUrl: buildUrl + '/build.framework.js.unityweb',
                codeUrl: buildUrl + '/build.wasm.unityweb',
                streamingAssetsUrl: 'unity/StreamingAssets',
                companyName: 'SoulFlaw',
                productName: 'Museum',
                productVersion: '0.1.0',
                // ✅ 启用压缩支持
                compressionFormat: 'br'  // 或 'gzip'，取决于你的构建设置
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
            
            // ✅ Unity 加载完成后再次应用移动端优化
            if (this.unityCanvas) {
                console.log('[UnityContainer] Unity 加载完成，再次应用移动端视频优化...');
                detectAndOptimizeForDevice();
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
            // ✅ 清理保活定时器
            clearInterval(keepAliveInterval);
            console.log('[UnityContainer] 已停止保活心跳');
            
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
        
        // ✅ 使用设备信息决定显示模式（仅作为预设，用户可随时切换）
        const useWindowMode = this.deviceInfo.shouldUseWindowMode;
        
        // 创建浮动面板包装
        this.currentPanel = new FloatingPanel(settingsPanel, {
            title: '客户端配置',
            deviceInfo: this.deviceInfo,
            useWindowMode: useWindowMode,
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
        
        // ✅ 使用设备信息决定显示模式（仅作为预设，用户可随时切换）
        const useWindowMode = this.deviceInfo.shouldUseWindowMode;
        
        // 创建浮动面板包装
        this.currentPanel = new FloatingPanel(chatWindow, {
            title: 'MuseumAgent 智能体',
            deviceInfo: this.deviceInfo,
            useWindowMode: useWindowMode,
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
