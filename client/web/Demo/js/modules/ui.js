/**
 * UI模块
 * 处理界面布局、拖拽调整等功能
 */
class UIModule {
    constructor() {
        this.isResizing1 = false;
        this.isResizing2 = false;
        this.isResizing3 = false;
    }

    /**
     * 初始化UI模块
     */
    init() {
        this.setupDragResize();
        this.setupEventListeners();
        this.adjustLayout();
    }

    /**
     * 调整页面布局
     */
    adjustLayout() {
        const mainContainer = document.querySelector('.main-container');
        const logPanel = document.querySelector('.log-panel');
        
        if (mainContainer && logPanel) {
            // 确保main-container和log-panel的高度正确计算
            const logPanelHeight = logPanel.offsetHeight;
            mainContainer.style.height = `calc(100vh - ${logPanelHeight}px - 80px)`;
        }
    }

    /**
     * 设置拖拽调整功能
     */
    setupDragResize() {
        // 设置第一个拖拽手柄
        const resizeHandle1 = document.getElementById('resizeHandle1');
        const clientConfig = document.querySelector('.client-config');
        if (resizeHandle1 && clientConfig) {
            resizeHandle1.addEventListener('mousedown', (e) => {
                this.isResizing1 = true;
                document.body.style.cursor = 'col-resize';
                e.preventDefault();
            });
        }

        // 设置第二个拖拽手柄
        const resizeHandle2 = document.getElementById('resizeHandle2');
        const functionsConfig = document.querySelector('.functions-config');
        if (resizeHandle2 && functionsConfig) {
            resizeHandle2.addEventListener('mousedown', (e) => {
                this.isResizing2 = true;
                document.body.style.cursor = 'col-resize';
                e.preventDefault();
            });
        }

        // 设置第三个拖拽手柄（垂直方向）
        const resizeHandle3 = document.getElementById('resizeHandle3');
        const mainContainer = document.querySelector('.main-container');
        const logPanel = document.querySelector('.log-panel');
        if (resizeHandle3 && mainContainer && logPanel) {
            resizeHandle3.addEventListener('mousedown', (e) => {
                this.isResizing3 = true;
                document.body.style.cursor = 'row-resize';
                e.preventDefault();
            });
        }

        // 全局鼠标移动事件
        document.addEventListener('mousemove', (e) => {
            this.handleMouseMove(e);
        });

        // 全局鼠标释放事件
        document.addEventListener('mouseup', () => {
            this.handleMouseUp();
        });
    }

    /**
     * 处理鼠标移动事件
     * @param {MouseEvent} e - 鼠标事件
     */
    handleMouseMove(e) {
        // 处理第一个拖拽手柄
        if (this.isResizing1) {
            const mainContainer = document.querySelector('.main-container');
            const clientConfig = document.querySelector('.client-config');
            if (mainContainer && clientConfig) {
                const containerRect = mainContainer.getBoundingClientRect();
                const newWidth = e.clientX - containerRect.left;
                
                if (newWidth > 200 && newWidth < 500) {
                    clientConfig.style.width = `${newWidth}px`;
                }
            }
        }

        // 处理第二个拖拽手柄
        if (this.isResizing2) {
            const mainContainer = document.querySelector('.main-container');
            const clientConfig = document.querySelector('.client-config');
            const functionsConfig = document.querySelector('.functions-config');
            if (mainContainer && clientConfig && functionsConfig) {
                const mainContainerRect = mainContainer.getBoundingClientRect();
                const clientConfigWidth = clientConfig.offsetWidth;
                const newWidth = e.clientX - mainContainerRect.left - clientConfigWidth;
                
                if (newWidth > 200 && newWidth < 500) {
                    functionsConfig.style.width = `${newWidth}px`;
                }
            }
        }

        // 处理第三个拖拽手柄（垂直方向）
        if (this.isResizing3) {
            const mainContainer = document.querySelector('.main-container');
            const logPanel = document.querySelector('.log-panel');
            if (mainContainer && logPanel) {
                const containerRect = document.body.getBoundingClientRect();
                const newHeight = containerRect.bottom - e.clientY;
                
                if (newHeight > 100 && newHeight < 400) {
                    logPanel.style.height = `${newHeight}px`;
                    logPanel.style.maxHeight = `${newHeight}px`;
                    // 同时调整main-container的高度，实现挤压效果
                    mainContainer.style.height = `calc(100vh - ${newHeight}px - 80px)`;
                }
            }
        }
    }

    /**
     * 处理鼠标释放事件
     */
    handleMouseUp() {
        if (this.isResizing1 || this.isResizing2 || this.isResizing3) {
            this.isResizing1 = false;
            this.isResizing2 = false;
            this.isResizing3 = false;
            document.body.style.cursor = '';
        }
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 添加窗口大小变化事件监听器
        window.addEventListener('resize', () => {
            this.adjustLayout();
        });
    }

    /**
     * 切换输入模式
     * @param {string} mode - 输入模式
     */
    switchInputMode(mode) {
        const inputArea = document.querySelector('.input-area');
        const voiceActions = document.querySelector('.voice-actions');
        
        // 检查所有元素是否存在
        if (!inputArea || !voiceActions) {
            return;
        }
        
        // 默认显示所有区域
        inputArea.style.display = 'block';
        voiceActions.style.display = 'flex';
    }

    /**
     * 显示错误消息
     * @param {string} message - 错误消息
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
     * 更新UI状态
     * @param {boolean} isConnected - 是否已连接
     */
    updateUIState(isConnected) {
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        const recordToggleBtn = document.getElementById('recordToggleBtn');
        
        if (sendMessageBtn) {
            sendMessageBtn.disabled = !isConnected;
        }
        
        if (recordToggleBtn) {
            recordToggleBtn.disabled = !isConnected;
        }
    }
}

// 导出单例实例
export const uiModule = new UIModule();
