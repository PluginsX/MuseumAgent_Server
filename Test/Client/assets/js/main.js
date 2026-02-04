
/**
 * 博物馆智能体测试客户端
 * 模块化重构版本
 */

// ==================== 配置模块 ====================
const Config = {
    DEFAULT_SERVER_URL: 'https://localhost:8000',
    DEFAULT_TIMEOUT: 30,
    DEFAULT_CLIENT_TYPE: 'test',
    DEFAULT_SCENE_TYPE: 'public',
    HEARTBEAT_INTERVAL: 2 * 60 * 1000, // 2分钟
    STORAGE_KEY: 'museumAgentClientSettings'
};

// ==================== 状态管理模块 ====================
class StateManager {
    constructor() {
        this.isConnected = false;
        this.isProcessing = false;
        this.sessionId = null;
        this.sessionExpiryTime = null;
        this.heartbeatInterval = null;
    }

    setConnected(connected) {
        this.isConnected = connected;
        this.updateConnectionUI();
    }

    setProcessing(processing) {
        this.isProcessing = processing;
    }

    setSession(sessionId, expiryTime) {
        this.sessionId = sessionId;
        this.sessionExpiryTime = expiryTime;
        this.updateSessionUI();
    }

    clearSession() {
        this.sessionId = null;
        this.sessionExpiryTime = null;
        this.updateSessionUI();
    }

    updateConnectionUI() {
        const indicator = document.getElementById('connectionStatus');
        const text = document.getElementById('connectionText');
        
        if (indicator) {
            indicator.className = this.isConnected ? 'status-indicator status-connected' : 'status-indicator';
        }
        
        if (text) {
            text.textContent = this.isConnected ? '已连接' : '未连接';
            text.style.color = this.isConnected ? '#27ae60' : '#e74c3c';
        }
    }

    updateSessionUI() {
        const statusEl = document.getElementById('sessionStatus');
        const idEl = document.getElementById('sessionIdDisplay');
        const expiryEl = document.getElementById('sessionExpiry');
        const infoEl = document.getElementById('sessionInfo');
        
        if (statusEl) statusEl.textContent = this.sessionId ? '已注册' : '未注册';
        if (idEl) idEl.textContent = this.sessionId || '-';
        if (expiryEl) expiryEl.textContent = this.sessionExpiryTime ? this.sessionExpiryTime.toLocaleString() : '-';
        if (infoEl) infoEl.style.display = this.sessionId ? 'block' : 'none';
    }
}

// ==================== 配置管理模块 ====================
class ConfigManager {
    static saveSettings() {
        const settings = {
            serverUrl: this.getServerUrl(),
            timeout: this.getTimeout(),
            clientType: this.getClientType(),
            clientId: this.getClientId(),
            spiritId: this.getSpiritId(),
            sceneType: this.getSceneType(),
            functionMode: this.getFunctionMode(),
            functionDefinitions: document.getElementById('functionDefinitions').value
        };
        
        localStorage.setItem(Config.STORAGE_KEY, JSON.stringify(settings));
    }

    static loadSettings() {
        const saved = localStorage.getItem(Config.STORAGE_KEY);
        if (saved) {
            try {
                const settings = JSON.parse(saved);
                this.applySettings(settings);
            } catch (e) {
                console.error('加载设置失败:', e);
            }
        }
    }

    static applySettings(settings) {
        if (settings.serverUrl) document.getElementById('serverUrl').value = settings.serverUrl;
        if (settings.timeout) document.getElementById('timeout').value = settings.timeout;
        if (settings.clientType) document.getElementById('clientType').value = settings.clientType;
        if (settings.clientId) document.getElementById('clientId').value = settings.clientId;
        if (settings.spiritId) document.getElementById('spiritId').value = settings.spiritId;
        if (settings.sceneType) document.getElementById('sceneType').value = settings.sceneType;
        if (settings.functionMode) document.getElementById('functionModeToggle').value = settings.functionMode;
        if (settings.functionDefinitions) document.getElementById('functionDefinitions').value = settings.functionDefinitions;
        
        // 触发UI更新
        UIController.toggleFunctionMode();
    }

    // 获取配置值的静态方法
    static getServerUrl() {
        const serverUrlInput = document.getElementById('serverUrl');
        return serverUrlInput ? serverUrlInput.value.trim().replace(/\/$/, '') : Config.DEFAULT_SERVER_URL;
    }

    static getTimeout() {
        return parseInt(document.getElementById('timeout').value) || Config.DEFAULT_TIMEOUT;
    }

    static getClientType() {
        return document.getElementById('clientType').value || Config.DEFAULT_CLIENT_TYPE;
    }

    static getClientId() {
        const element = document.getElementById('clientId');
        return element.value || this.generateClientId();
    }

    static getSpiritId() {
        return document.getElementById('spiritId').value;
    }

    static getSceneType() {
        return document.getElementById('sceneType').value || Config.DEFAULT_SCENE_TYPE;
    }

    static getFunctionMode() {
        return document.getElementById('functionModeToggle').value;
    }

    static getFunctionDefinitions() {
        const functionDefTextarea = document.getElementById('functionDefinitions');
        return functionDefTextarea ? functionDefTextarea.value.trim() : '';
    }

    static generateClientId() {
        return 'client_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// ==================== UI控制器模块 ====================
class UIController {
    static addWelcomeMessage() {
        ChatManager.addBotMessage("欢迎使用博物馆智能体测试客户端！\n\n✨ 基于OpenAI Function Calling标准\n\n支持两种模式：\n• 普通对话模式：基础问答和咨询\n• 函数调用模式：支持复杂操作和精确控制\n\n功能特性：\n• 完全兼容OpenAI Function Calling标准\n• 支持动态函数定义配置\n• 会话管理机制\n• 实时心跳维持连接\n\n使用说明：\n1. 选择合适的模式（函数调用/普通对话）\n2. 如需函数调用，配置相应的函数定义\n3. 注册会话并开始对话\n\n示例问题：\n• '介绍一下蟠龙盖罍的历史背景'（普通对话）\n• '请移动到坐标(100, 200)'（函数调用）");
    }

    static addEventListeners() {
        // 回车发送消息
        const userInput = document.getElementById('userInput');
        if (userInput) {
            userInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    MessageController.sendMessage();
                }
            });
        }

        // 输入框变化时保存设置
        const inputs = ['serverUrl', 'timeout', 'clientType', 'clientId', 'spiritId', 'sceneType', 'functionDefinitions', 'functionModeToggle'];
        inputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', ConfigManager.saveSettings);
            }
        });
    }

    static toggleFunctionMode() {
        const mode = ConfigManager.getFunctionMode();
        const functionSection = document.getElementById('functionDefinitionSection');
        
        if (functionSection) {
            functionSection.classList.toggle('active', mode === 'with-functions');
        }
    }

    static updateOperationPresets() {
        // 可以根据客户端类型预设一些配置
        // 暂时留空，后续可扩展
    }

    static loadSampleFunctions() {
        const sampleFunctions = [
            {
                "name": "introduce_artifact",
                "description": "介绍指定文物的详细信息，包括历史背景、艺术特色等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "artifact_name": {
                            "type": "string",
                            "description": "文物名称"
                        }
                    },
                    "required": ["artifact_name"]
                }
            },
            {
                "name": "move_to_position",
                "description": "控制桌面宠物移动到指定坐标位置",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "number",
                            "description": "X坐标值"
                        },
                        "y": {
                            "type": "number",
                            "description": "Y坐标值"
                        }
                    },
                    "required": ["x", "y"]
                }
            },
            {
                "name": "show_emotion",
                "description": "表达指定的情绪状态",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "emotion": {
                            "type": "string",
                            "description": "情绪类型：happy, sad, angry, surprised, neutral",
                            "enum": ["happy", "sad", "angry", "surprised", "neutral"]
                        }
                    },
                    "required": ["emotion"]
                }
            }
        ];
        
        const functionDefTextarea = document.getElementById('functionDefinitions');
        if (functionDefTextarea) {
            functionDefTextarea.value = JSON.stringify(sampleFunctions, null, 2);
            Toast.show('已加载示例函数定义', 'success');
            ConfigManager.saveSettings();
        }
    }

    static clearChat() {
        if (confirm('确定要清空所有对话记录吗？')) {
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.innerHTML = '';
                this.addWelcomeMessage();
                Toast.show('对话已清空', 'info');
            }
        }
    }

    static sendExample(message) {
        const userInput = document.getElementById('userInput');
        if (userInput) {
            userInput.value = message;
            MessageController.sendMessage();
        }
    }

    static showLoading(buttonId, loadingText) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = true;
            button.originalText = button.textContent;
            button.textContent = loadingText;
        }
    }

    static hideLoading(buttonId, originalText) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = false;
            button.textContent = originalText || button.originalText || '';
        }
    }
}

// ==================== 网络请求模块 ====================
class NetworkManager {
    static async testConnection() {
        const serverUrl = ConfigManager.getServerUrl();
        Toast.show('正在测试连接...', 'info');
        
        try {
            console.log('正在连接到服务器:', serverUrl);
            
            const response = await fetch(`${serverUrl}/api/session/stats`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                signal: AbortSignal.timeout(5000)
            });
            
            console.log('服务器响应状态:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('服务器响应数据:', data);
                Toast.show(`连接成功！服务器正常运行，当前活跃会话数: ${data.active_sessions}`, 'success');
                stateManager.setConnected(true);
            } else {
                const errorText = await response.text();
                console.error('HTTP错误响应:', response.status, errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText.substring(0, 100)}`);
            }
        } catch (error) {
            console.error('连接测试失败:', error);
            let errorMessage = error.message;
            
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '网络连接失败，请检查服务器地址是否正确，服务器是否正在运行';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = '无法获取数据 - 请确认：1) 服务器正在运行；2) 浏览器没有阻止连接；3) 网络连接正常';
            } else if (error.message.includes('404')) {
                errorMessage = 'API端点不存在 (/api/session/stats)，请检查服务器API是否正确配置';
            } else if (error.message.includes('405')) {
                errorMessage = 'API方法不允许，请检查服务器端点配置';
            } else if (error.message.includes('NetworkError')) {
                errorMessage = '网络错误 - 请检查：1) 服务器是否运行；2) 网络连接；3) 防火墙设置';
            } else if (error.message.includes('403')) {
                errorMessage = '访问被禁止 - 可能是SSL证书或CORS问题';
            } else if (error.message.includes('401')) {
                errorMessage = '未授权访问 - 可能需要认证';
            }
            
            Toast.show(`连接失败: ${errorMessage}`, 'error');
            stateManager.setConnected(false);
        }
    }

    static async registerSession() {
        const mode = ConfigManager.getFunctionMode();
        let functions = null;

        if (mode === 'with-functions') {
            // 函数调用模式：获取函数定义
            const functionDefValue = ConfigManager.getFunctionDefinitions();
            
            if (functionDefValue) {
                try {
                    const parsedFunctions = JSON.parse(functionDefValue);
                    
                    // 验证是否为标准OpenAI Function Calling格式
                    if (Array.isArray(parsedFunctions)) {
                        functions = parsedFunctions;
                        // 验证每个函数定义的格式
                        for (let i = 0; i < functions.length; i++) {
                            const func = functions[i];
                            if (!func.name || !func.description || !func.parameters) {
                                throw new Error(`第${i+1}个函数定义缺少必要字段`);
                            }
                        }
                    } else {
                        throw new Error('函数定义必须是数组格式');
                    }
                } catch (e) {
                    Toast.show(`函数定义JSON格式错误: ${e.message}`, 'error');
                    return;
                }
            }
            // 注意：函数定义是可选的，即使为空也允许注册
        }
        // 普通对话模式：不提供函数定义

        UIController.showLoading('registerBtn', '注册中...');

        try {
            const registrationData = {
                client_metadata: {
                    client_id: ConfigManager.getClientId(),
                    client_type: ConfigManager.getClientType(),
                    client_version: "1.0.0",
                    platform: "web-test-client",
                    capabilities: {
                        max_concurrent_requests: 3,
                        supported_scenes: ["study", "leisure", "public"],
                        preferred_response_format: "json",
                        function_calling_supported: (mode === 'with-functions')
                    }
                },
                functions: (mode === 'with-functions' && functions) ? functions : []
            };

            const response = await fetch(`${ConfigManager.getServerUrl()}/api/session/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(registrationData),
                signal: AbortSignal.timeout(ConfigManager.getTimeout() * 1000)
            });

            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                } catch (e) {
                    errorMessage = `服务器返回错误: ${response.status} ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();

            stateManager.setSession(result.session_id, new Date(result.expires_at));
            stateManager.setConnected(true);
            NetworkManager.startHeartbeat();
            
            // 显示注册成功信息
            let successMessage = `✅ 会话注册成功!\n\n`;
            successMessage += `会话ID: ${result.session_id}\n`;
            successMessage += `过期时间: ${new Date(result.expires_at).toLocaleString()}\n`;
            successMessage += `支持功能: ${result.supported_features.join(', ')}\n`;
            
            if (mode === 'with-functions') {
                if (functions && functions.length > 0) {
                    successMessage += `\n已注册函数 (${functions.length}个):\n`;
                    functions.forEach((func, index) => {
                        successMessage += `  ${index + 1}. ${func.name}: ${func.description}\n`;
                    });
                    successMessage += `\n当前为函数调用模式，支持复杂操作。`;
                } else {
                    successMessage += `\n当前为函数调用模式，但未提供函数定义，将使用普通对话处理。`;
                }
            } else {
                successMessage += `\n当前为普通对话模式，适用于基础问答和咨询。`;
            }

            Toast.show('会话注册成功！', 'success');
            ChatManager.addBotMessage(successMessage);
        } catch (error) {
            console.error('注册会话失败:', error);
            
            let errorMessage = error.message;
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '网络连接失败，请检查服务器地址是否正确，服务器是否正在运行';
            } else if (error.message.includes('422') || error.message.includes('400')) {
                errorMessage = '请求格式错误，请检查配置信息是否正确';
            } else if (error.message.includes('404')) {
                errorMessage = '服务器接口不存在，请检查服务器地址和API路径';
            } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                errorMessage = '无法连接到服务器，请检查服务器是否正在运行以及网络连接';
            }
            
            Toast.show(`注册失败: ${errorMessage}`, 'error');
            ChatManager.addBotMessage(`❌ 会话注册失败: ${errorMessage}`);
        } finally {
            UIController.hideLoading('registerBtn', '注册会话');
        }
    }

    static startHeartbeat() {
        if (stateManager.heartbeatInterval) {
            clearInterval(stateManager.heartbeatInterval);
        }
        
        stateManager.heartbeatInterval = setInterval(async () => {
            if (stateManager.sessionId) {
                try {
                    const response = await fetch(`${ConfigManager.getServerUrl()}/api/session/heartbeat`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'session-id': stateManager.sessionId
                        },
                        signal: AbortSignal.timeout(5000)
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        console.warn('心跳失败:', response.status, errorData);
                        
                        // 如果心跳失败，可能意味着会话已失效，更新UI状态
                        stateManager.updateSessionUI();
                        stateManager.clearSession();
                        if (stateManager.heartbeatInterval) {
                            clearInterval(stateManager.heartbeatInterval);
                            stateManager.heartbeatInterval = null;
                        }
                    } else {
                        // 心跳成功，确保连接状态为已连接
                        stateManager.setConnected(true);
                    }
                } catch (error) {
                    console.warn('心跳请求异常:', error);
                    
                    if (error.name !== 'AbortError') {
                        stateManager.updateSessionUI();
                        stateManager.setConnected(false);
                    }
                }
            }
        }, Config.HEARTBEAT_INTERVAL);
    }

    static async unregisterSession() {
        if (!stateManager.sessionId) return;
        
        try {
            await fetch(`${ConfigManager.getServerUrl()}/api/session/unregister`, {
                method: 'DELETE',
                headers: {
                    'session-id': stateManager.sessionId
                }
            });
        } catch (error) {
            console.warn('会话注销失败:', error);
        } finally {
            stateManager.clearSession();
            if (stateManager.heartbeatInterval) {
                clearInterval(stateManager.heartbeatInterval);
                stateManager.heartbeatInterval = null;
            }
        }
    }

    static async processMessage(message) {
        stateManager.setProcessing(true);
        UIController.showLoading('sendBtn', '处理中...');
        
        try {
            const requestData = {
                user_input: message,
                client_type: ConfigManager.getClientType(),
                spirit_id: ConfigManager.getSpiritId(),
                scene_type: ConfigManager.getSceneType()
            };

            const headers = {
                'Content-Type': 'application/json',
            };
            
            if (stateManager.sessionId) {
                headers['session-id'] = stateManager.sessionId;
            }

            const response = await fetch(`${ConfigManager.getServerUrl()}/api/agent/parse`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestData),
                signal: AbortSignal.timeout(ConfigManager.getTimeout() * 1000)
            });

            const result = await response.json();

            if (response.ok) {
                NetworkManager.handleSuccessResponse(result);
            } else {
                if (response.status === 404 || response.status === 401) {
                    if (result.detail && (result.detail.includes('会话') || result.detail.includes('session') || result.detail.includes('Session'))) {
                        Toast.show('会话已失效，请重新注册', 'error');
                        stateManager.updateSessionUI();
                        stateManager.clearSession();
                        if (stateManager.heartbeatInterval) {
                            clearInterval(stateManager.heartbeatInterval);
                            stateManager.heartbeatInterval = null;
                        }
                    }
                }
                NetworkManager.handleErrorResponse(result, response.status);
            }

        } catch (error) {
            NetworkManager.handleNetworkError(error);
        } finally {
            stateManager.setProcessing(false);
            UIController.hideLoading('sendBtn', '发送');
        }
    }

    static handleSuccessResponse(result) {
        if (result.code === 200 && result.data) {
            const command = result.data;
            const rawResponse = JSON.stringify(command, null, 2);
            ChatManager.addBotMessage(rawResponse);
        } else {
            ChatManager.addBotMessage(`请求处理失败: ${result.msg || '未知错误'}`);
        }
    }

    static handleErrorResponse(result, status) {
        let errorMsg = `请求失败 (${status})`;
        
        if (result.msg) {
            errorMsg = result.msg;
        } else if (status === 404) {
            errorMsg = '未查询到相关文物数据';
        } else if (status === 400) {
            errorMsg = '请求参数错误';
        } else if (status === 401) {
            errorMsg = '接口认证失败';
        }

        ChatManager.addBotMessage(errorMsg);
    }

    static handleNetworkError(error) {
        if (error.name === 'AbortError') {
            ChatManager.addBotMessage('请求超时，请检查服务器地址和网络连接');
        } else {
            ChatManager.addBotMessage(`网络错误: ${error.message}`);
        }
    }
}

// ==================== 聊天管理模块 ====================
class ChatManager {
    static addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user';
        
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        messageElement.innerHTML = `
            <div class="message-header">
                <span>用户</span>
                <span>${timeStr}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message)}</div>
        `;
        
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.appendChild(messageElement);
            this.scrollToBottom();
        }
    }

    static addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot';
        
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        messageElement.innerHTML = `
            <div class="message-header">
                <span>智能体</span>
                <span>${timeStr}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message)}</div>
        `;
        
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.appendChild(messageElement);
            this.scrollToBottom();
        }
    }

    static addCommandDisplay(command) {
        const commandElement = document.createElement('div');
        commandElement.className = 'command-display';
        commandElement.innerHTML = `
            <strong>📋 完整响应字段：</strong><br>
            <pre>${JSON.stringify(command, null, 2)}</pre>
        `;
        
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.appendChild(commandElement);
            this.scrollToBottom();
        }
    }

    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
}

// ==================== Toast提示模块 ====================
class Toast {
    static show(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            z-index: 10000;
            min-width: 250px;
            max-width: 500px;
            word-wrap: break-word;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// ==================== 消息控制器模块 ====================
class MessageController {
    static async sendMessage() {
        const message = document.getElementById('userInput').value.trim();
        if (!message) {
            Toast.show('请输入消息内容', 'warning');
            return;
        }

        if (stateManager.isProcessing) {
            Toast.show('正在处理中，请稍候...', 'warning');
            return;
        }

        // 添加用户消息
        ChatManager.addUserMessage(message);
        document.getElementById('userInput').value = '';
        
        // 发送请求
        await NetworkManager.processMessage(message);
    }
}

// ==================== 拖拽调整面板宽度模块 ====================
class ResizeController {
    static init() {
        const leftDivider = document.getElementById('left-divider');
        const rightDivider = document.getElementById('right-divider');
        const leftPanel = document.querySelector('.left-panel');
        const centerPanel = document.querySelector('.center-panel');
        const rightPanel = document.querySelector('.right-panel');
        
        if (leftDivider && centerPanel) {
            leftDivider.addEventListener('mousedown', function(e) {
                e.preventDefault();
                
                leftDivider.classList.add('active');
                
                const startX = e.clientX;
                const startLeftWidth = leftPanel.offsetWidth;
                const startCenterWidth = centerPanel.offsetWidth;
                
                document.addEventListener('mousemove', mouseMoveHandlerLeft);
                document.addEventListener('mouseup', () => {
                    leftDivider.classList.remove('active');
                    document.removeEventListener('mousemove', mouseMoveHandlerLeft);
                }, { once: true });
                
                function mouseMoveHandlerLeft(e) {
                    const dx = e.clientX - startX;
                    
                    const newLeftWidth = Math.max(250, startLeftWidth + dx);
                    const newCenterWidth = Math.max(250, startCenterWidth - dx);
                    
                    leftPanel.style.flex = 'none';
                    leftPanel.style.width = newLeftWidth + 'px';
                    centerPanel.style.flex = 'none';
                    centerPanel.style.width = newCenterWidth + 'px';
                }
            });
        }
        
        if (rightDivider && rightPanel) {
            rightDivider.addEventListener('mousedown', function(e) {
                e.preventDefault();
                
                rightDivider.classList.add('active');
                
                const startX = e.clientX;
                const startCenterWidth = centerPanel.offsetWidth;
                const startRightWidth = rightPanel.offsetWidth;
                
                document.addEventListener('mousemove', mouseMoveHandlerRight);
                document.addEventListener('mouseup', () => {
                    rightDivider.classList.remove('active');
                    document.removeEventListener('mousemove', mouseMoveHandlerRight);
                }, { once: true });
                
                function mouseMoveHandlerRight(e) {
                    const dx = e.clientX - startX;
                    
                    const newCenterWidth = Math.max(250, startCenterWidth + dx);
                    const newRightWidth = Math.max(250, startRightWidth - dx);
                    
                    centerPanel.style.flex = 'none';
                    centerPanel.style.width = newCenterWidth + 'px';
                    rightPanel.style.flex = 'none';
                    rightPanel.style.width = newRightWidth + 'px';
                }
            });
        }
    }
}

// ==================== 全局状态管理器 ====================
const stateManager = new StateManager();

// ==================== 页面初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    // 初始化各个模块
    ConfigManager.loadSettings();
    UIController.updateOperationPresets();
    UIController.addEventListeners();
    UIController.addWelcomeMessage();
    UIController.toggleFunctionMode(); // 初始化模式切换
    ResizeController.init();
});

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    NetworkManager.unregisterSession();
});

// ==================== 导出全局函数供HTML调用 ====================
window.testConnection = NetworkManager.testConnection;
window.sendMessage = MessageController.sendMessage;
window.clearChat = UIController.clearChat;
window.sendExample = UIController.sendExample;
window.getCurrentServerUrl = ConfigManager.getServerUrl;
window.registerSession = NetworkManager.registerSession;
window.updateOperationPresets = UIController.updateOperationPresets;
window.toggleFunctionMode = UIController.toggleFunctionMode;
window.loadSampleFunctions = UIController.loadSampleFunctions;