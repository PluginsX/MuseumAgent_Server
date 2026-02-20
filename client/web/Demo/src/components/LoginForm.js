/**
 * 登录表单组件
 * 基于 MuseumAgentSDK 客户端库开发
 */

import { createElement } from '../utils/dom.js';

export class LoginForm {
    constructor(container, onLogin) {
        this.container = container;
        this.onLogin = onLogin;
        this.render();
    }

    render() {
        // 创建表单容器
        const formContainer = createElement('div', { className: 'login-container' });

        // 标题
        const title = createElement('h1', { 
            className: 'login-title',
            textContent: 'MuseumAgent' 
        });

        const subtitle = createElement('p', { 
            className: 'login-subtitle',
            textContent: '智能体客户端' 
        });

        // 服务器地址输入
        const serverInput = createElement('input', {
            type: 'text',
            className: 'login-input',
            placeholder: '服务器地址',
            value: 'ws://localhost:8001'
        });
        
        // 认证方式选择
        const authTypeContainer = createElement('div', { className: 'auth-type-container' });
        
        const accountRadio = createElement('input', {
            type: 'radio',
            name: 'authType',
            value: 'ACCOUNT',
            id: 'authTypeAccount',
            checked: true
        });

        const accountLabel = createElement('label', {
            htmlFor: 'authTypeAccount',
            textContent: '账户密码'
        });

        const apiKeyRadio = createElement('input', {
            type: 'radio',
            name: 'authType',
            value: 'API_KEY',
            id: 'authTypeApiKey'
        });

        const apiKeyLabel = createElement('label', {
            htmlFor: 'authTypeApiKey',
            textContent: 'API Key'
        });

        authTypeContainer.appendChild(accountRadio);
        authTypeContainer.appendChild(accountLabel);
        authTypeContainer.appendChild(apiKeyRadio);
        authTypeContainer.appendChild(apiKeyLabel);

        // 账户密码输入（默认显示）
        const accountContainer = createElement('div', { 
            className: 'auth-input-container',
            id: 'accountContainer'
        });

        const usernameInput = createElement('input', {
            type: 'text',
            className: 'login-input',
            placeholder: '用户名',
            value: '123'
        });

        const passwordInput = createElement('input', {
            type: 'password',
            className: 'login-input',
            placeholder: '密码',
            value: '123'
        });

        accountContainer.appendChild(usernameInput);
        accountContainer.appendChild(passwordInput);

        // API Key 输入（默认隐藏）
        const apiKeyContainer = createElement('div', { 
            className: 'auth-input-container',
            id: 'apiKeyContainer',
            style: 'display: none;'
        });

        const apiKeyInput = createElement('input', {
            type: 'text',
            className: 'login-input',
            placeholder: 'API Key'
        });

        apiKeyContainer.appendChild(apiKeyInput);

        // 登录按钮
        const loginButton = createElement('button', {
            className: 'login-button',
            textContent: '连接'
        });

        // 状态提示
        const statusText = createElement('p', {
            className: 'login-status',
            textContent: ''
        });

        // 切换认证方式
        const toggleAuthType = () => {
            const authType = document.querySelector('input[name="authType"]:checked').value;
            if (authType === 'ACCOUNT') {
                accountContainer.style.display = 'flex';
                apiKeyContainer.style.display = 'none';
            } else {
                accountContainer.style.display = 'none';
                apiKeyContainer.style.display = 'flex';
            }
        };

        accountRadio.addEventListener('change', toggleAuthType);
        apiKeyRadio.addEventListener('change', toggleAuthType);

        // 登录处理
        const handleLogin = async () => {
            const serverUrl = serverInput.value.trim();
            const authType = document.querySelector('input[name="authType"]:checked').value;

            if (!serverUrl) {
                statusText.textContent = '请输入服务器地址';
                statusText.style.color = '#e74c3c';
            return;
        }

            let authData;
            if (authType === 'ACCOUNT') {
                const username = usernameInput.value.trim();
                const password = passwordInput.value.trim();

                if (!username || !password) {
                    statusText.textContent = '请输入用户名和密码';
                    statusText.style.color = '#e74c3c';
            return;
        }

                authData = {
                    type: 'ACCOUNT',
                    account: username,
                    password: password
                };
            } else {
                const apiKey = apiKeyInput.value.trim();

        if (!apiKey) {
                    statusText.textContent = '请输入 API Key';
                    statusText.style.color = '#e74c3c';
            return;
        }

                authData = {
                    type: 'API_KEY',
                    api_key: apiKey
                };
        }

            // 显示连接中状态
            loginButton.disabled = true;
            loginButton.textContent = '连接中...';
            statusText.textContent = '正在连接服务器...';
            statusText.style.color = '#3498db';

            try {
                await this.onLogin(serverUrl, authData);
        } catch (error) {
                loginButton.disabled = false;
                loginButton.textContent = '连接';
                statusText.textContent = '连接失败: ' + error.message;
                statusText.style.color = '#e74c3c';
            }
        };

        loginButton.addEventListener('click', handleLogin);

        // 回车登录
        const handleKeyPress = (e) => {
            if (e.key === 'Enter') {
                handleLogin();
            }
        };

        serverInput.addEventListener('keypress', handleKeyPress);
        usernameInput.addEventListener('keypress', handleKeyPress);
        passwordInput.addEventListener('keypress', handleKeyPress);
        apiKeyInput.addEventListener('keypress', handleKeyPress);

        // 组装表单
        formContainer.appendChild(title);
        formContainer.appendChild(subtitle);
        formContainer.appendChild(serverInput);
        formContainer.appendChild(authTypeContainer);
        formContainer.appendChild(accountContainer);
        formContainer.appendChild(apiKeyContainer);
        formContainer.appendChild(loginButton);
        formContainer.appendChild(statusText);

        this.container.appendChild(formContainer);
        }

    destroy() {
        this.container.innerHTML = '';
    }
}
