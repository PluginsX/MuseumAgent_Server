/**
 * 认证服务
 * 处理登录、登出、会话管理
 */

import { eventBus, Events } from '../core/EventBus.js';
import { stateManager } from '../core/StateManager.js';
import { encryptData, decryptData } from '../utils/security.js';

export class AuthService {
    constructor() {
        this.storageKey = 'museumAgent_auth';
    }

    /**
     * 登录（账户密码）
     */
    async loginWithCredentials(username, password, serverUrl) {
        try {
            const authData = {
                type: 'ACCOUNT',
                account: username,
                password: password
            };

            // 保存认证信息（加密存储）
            await this._saveAuth({
                username,
                password: await encryptData(password),
                serverUrl,
                authType: 'ACCOUNT'
            });

            // 更新状态
            stateManager.updateState('auth', {
                isAuthenticated: true,
                username,
                serverUrl
            });

            eventBus.emit(Events.AUTH_LOGIN_SUCCESS, { username, serverUrl });

            return authData;

        } catch (error) {
            console.error('[AuthService] 登录失败:', error);
            eventBus.emit(Events.AUTH_LOGIN_FAILED, error);
            throw error;
        }
    }

    /**
     * 登录（API Key）
     */
    async loginWithApiKey(apiKey, serverUrl) {
        try {
            const authData = {
                type: 'API_KEY',
                api_key: apiKey
            };

            // 保存认证信息（加密存储）
            await this._saveAuth({
                apiKey: await encryptData(apiKey),
                serverUrl,
                authType: 'API_KEY'
            });

            // 更新状态
            stateManager.updateState('auth', {
                isAuthenticated: true,
                serverUrl
            });

            eventBus.emit(Events.AUTH_LOGIN_SUCCESS, { serverUrl });

            return authData;

        } catch (error) {
            console.error('[AuthService] API Key 登录失败:', error);
            eventBus.emit(Events.AUTH_LOGIN_FAILED, error);
            throw error;
        }
    }

    /**
     * 登出
     */
    logout() {
        this._clearAuth();
        stateManager.reset();
        eventBus.emit(Events.AUTH_LOGOUT);
    }

    /**
     * 恢复会话（从本地存储）
     */
    async restoreSession() {
        try {
            const authData = await this._loadAuth();
            if (!authData) return null;

            // 解密密码
            if (authData.authType === 'ACCOUNT') {
                const password = await decryptData(authData.password);
                return {
                    type: 'ACCOUNT',
                    account: authData.username,
                    password: password
                };
            } else if (authData.authType === 'API_KEY') {
                const apiKey = await decryptData(authData.apiKey);
                return {
                    type: 'API_KEY',
                    api_key: apiKey
                };
            }

            return null;

        } catch (error) {
            console.error('[AuthService] 恢复会话失败:', error);
            return null;
        }
    }

    /**
     * 获取服务器 URL
     */
    getServerUrl() {
        const authData = localStorage.getItem(this.storageKey);
        if (authData) {
            try {
                const data = JSON.parse(authData);
                return data.serverUrl;
            } catch (error) {
                return null;
            }
        }
        return null;
    }

    /**
     * 保存认证信息
     */
    async _saveAuth(data) {
        localStorage.setItem(this.storageKey, JSON.stringify(data));
    }

    /**
     * 加载认证信息
     */
    async _loadAuth() {
        const data = localStorage.getItem(this.storageKey);
        if (data) {
            try {
                return JSON.parse(data);
            } catch (error) {
                return null;
            }
        }
        return null;
    }

    /**
     * 清除认证信息
     */
    _clearAuth() {
        localStorage.removeItem(this.storageKey);
    }
}

// 创建全局单例
export const authService = new AuthService();

