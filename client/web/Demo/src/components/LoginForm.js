/**
 * 登录表单组件
 */

import { createElement, $, showNotification } from '../utils/dom.js';
import { validateInput } from '../utils/security.js';
import { authService } from '../services/AuthService.js';
import { eventBus, Events } from '../core/EventBus.js';

export class LoginForm {
    constructor(container) {
        this.container = container;
        this.currentTab = 'account';
        
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        this.render();
        this.bindEvents();
    }

    /**
     * 渲染
     */
    render() {
        this.container.innerHTML = '';
        
        const formContainer = createElement('div', {
            className: 'login-form-container'
        });

        // 标题
        const title = createElement('h2', {
            textContent: 'MuseumAgent 登录'
        });

        // 标签页
        const tabs = createElement('div', {
            className: 'tabs'
        });

        const accountTab = this.createTab('account', '账户登录');
        const apiKeyTab = this.createTab('apikey', 'API密钥');

        tabs.appendChild(accountTab);
        tabs.appendChild(apiKeyTab);

        // 表单内容
        const formContent = createElement('div', { className: 'form-content' });
        
        // 服务器配置
        const serverConfig = this.createServerConfig();
        
        // 账户登录表单
        const accountForm = this.createAccountForm();
        
        // API密钥登录表单
        const apiKeyForm = this.createApiKeyForm();
        apiKeyForm.style.display = 'none';

        formContent.appendChild(accountForm);
        formContent.appendChild(apiKeyForm);

        formContainer.appendChild(title);
        formContainer.appendChild(tabs);
        formContainer.appendChild(serverConfig);
        formContainer.appendChild(formContent);

        this.container.appendChild(formContainer);
    }

    /**
     * 创建标签页
     */
    createTab(id, text) {
        const tab = createElement('div', {
            className: `tab ${id === this.currentTab ? 'active' : ''}`,
            textContent: text,
            'data-tab': id
        });

        return tab;
    }

    /**
     * 创建服务器配置
     */
    createServerConfig() {
        const container = createElement('div', {
            className: 'server-config'
        });

        const label = createElement('label', {
            textContent: '服务器地址'
        });

        const inputGroup = createElement('div', {
            className: 'server-input-group'
        });

        const hostInput = createElement('input', {
            type: 'text',
            id: 'server-host',
            placeholder: 'localhost',
            value: 'localhost'
        });

        const portInput = createElement('input', {
            type: 'text',
            id: 'server-port',
            placeholder: '8001',
            value: '8001'
        });

        inputGroup.appendChild(hostInput);
        inputGroup.appendChild(portInput);
        container.appendChild(label);
        container.appendChild(inputGroup);

        return container;
    }

    /**
     * 创建账户登录表单
     */
    createAccountForm() {
        const form = createElement('form', {
            id: 'account-form',
            className: 'login-form'
        });

        const usernameGroup = this.createFormGroup('用户名', 'text', 'username', 'admin');
        const passwordGroup = this.createFormGroup('密码', 'password', 'password', 'admin123');

        const submitButton = createElement('button', {
            type: 'submit',
            textContent: '登录'
        });

        form.appendChild(usernameGroup);
        form.appendChild(passwordGroup);
        form.appendChild(submitButton);

        return form;
    }

    /**
     * 创建API密钥登录表单
     */
    createApiKeyForm() {
        const form = createElement('form', {
            id: 'apikey-form',
            className: 'login-form'
        });

        const apiKeyGroup = this.createFormGroup('API密钥', 'text', 'api-key', '');

        const submitButton = createElement('button', {
            type: 'submit',
            textContent: '登录'
        });

        form.appendChild(apiKeyGroup);
        form.appendChild(submitButton);

        return form;
    }

    /**
     * 创建表单组
     */
    createFormGroup(label, type, id, placeholder) {
        const group = createElement('div', {
            className: 'form-group'
        });

        const labelElement = createElement('label', {
            textContent: label,
            htmlFor: id
        });

        const input = createElement('input', {
            type: type,
            id: id,
            placeholder: placeholder
        });

        group.appendChild(labelElement);
        group.appendChild(input);

        return group;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 标签页切换
        const tabs = this.container.querySelectorAll('.tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchTab(tab.dataset.tab);
            });
        });

        // 账户登录
        const accountForm = $('#account-form', this.container);
        if (accountForm) {
            accountForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleAccountLogin();
            });
        }

        // API密钥登录
        const apiKeyForm = $('#apikey-form', this.container);
        if (apiKeyForm) {
            apiKeyForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleApiKeyLogin();
            });
        }
    }

    /**
     * 切换标签页
     */
    switchTab(tabId) {
        this.currentTab = tabId;

        // 更新标签样式
        const tabs = this.container.querySelectorAll('.tab');
        tabs.forEach(tab => {
            if (tab.dataset.tab === tabId) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        // 切换表单
        const accountForm = $('#account-form', this.container);
        const apiKeyForm = $('#apikey-form', this.container);

        if (tabId === 'account') {
            accountForm.style.display = 'block';
            apiKeyForm.style.display = 'none';
        } else {
            accountForm.style.display = 'none';
            apiKeyForm.style.display = 'block';
        }
    }

    /**
     * 处理账户登录
     */
    async handleAccountLogin() {
        const username = $('#username', this.container).value.trim();
        const password = $('#password', this.container).value;
        const host = $('#server-host', this.container).value.trim();
        const port = $('#server-port', this.container).value.trim();

        // 验证
        if (!username || !password) {
            showNotification('请输入用户名和密码', 'error');
            return;
        }

        if (!host || !port) {
            showNotification('请输入服务器地址', 'error');
            return;
        }

        const serverUrl = `ws://${host}:${port}`;

        try {
            showNotification('正在登录...', 'info', 1000);
            await authService.loginWithCredentials(username, password, serverUrl);
            // authService 内部已经触发了 AUTH_LOGIN_SUCCESS 事件，不需要再次触发
        } catch (error) {
            showNotification('登录失败: ' + error.message, 'error');
        }
    }

    /**
     * 处理API密钥登录
     */
    async handleApiKeyLogin() {
        const apiKey = $('#api-key', this.container).value.trim();
        const host = $('#server-host', this.container).value.trim();
        const port = $('#server-port', this.container).value.trim();

        // 验证
        if (!apiKey) {
            showNotification('请输入API密钥', 'error');
            return;
        }

        if (!host || !port) {
            showNotification('请输入服务器地址', 'error');
            return;
        }

        const serverUrl = `ws://${host}:${port}`;

        try {
            showNotification('正在登录...', 'info', 1000);
            await authService.loginWithApiKey(apiKey, serverUrl);
            // authService 内部已经触发了 AUTH_LOGIN_SUCCESS 事件，不需要再次触发
        } catch (error) {
            showNotification('登录失败: ' + error.message, 'error');
        }
    }
}

