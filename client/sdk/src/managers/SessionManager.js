/**
 * 会话管理器
 * 负责会话的保存、加载、验证和清除
 */

import { getStorage, setStorage, removeStorage } from '../utils/storage.js';
import { encryptData, decryptData } from '../utils/security.js';
import { STORAGE_KEYS } from '../constants.js';
import { info, warn } from '../utils/logger.js';

export class SessionManager {
    constructor() {
        this.currentSession = null;
    }
    
    /**
     * 保存会话（加密存储）
     * @param {string} serverUrl - 服务器地址
     * @param {Object} authData - 认证数据
     * @param {string} sessionId - 会话 ID
     * @returns {Promise<boolean>} 是否成功
     */
    async saveSession(serverUrl, authData, sessionId) {
        try {
            const sessionData = {
                serverUrl,
                authData,
                sessionId,
                timestamp: Date.now()
            };
            
            const encrypted = await encryptData(JSON.stringify(sessionData));
            setStorage(STORAGE_KEYS.SESSION, encrypted);
            this.currentSession = sessionData;
            
            info('[SessionManager] 会话已保存');
            return true;
        } catch (error) {
            warn('[SessionManager] 保存会话失败:', error);
            return false;
        }
    }
    
    /**
     * 加载会话（解密）
     * @returns {Promise<Object|null>} 会话数据或 null
     */
    async loadSession() {
        try {
            const encrypted = getStorage(STORAGE_KEYS.SESSION);
            if (!encrypted) {
                return null;
            }
            
            const decrypted = await decryptData(encrypted);
            const sessionData = JSON.parse(decrypted);
            
            // 检查是否过期（24小时）
            if (!this.isSessionValid(sessionData)) {
                this.clearSession();
                return null;
            }
            
            this.currentSession = sessionData;
            info('[SessionManager] 会话已加载');
            return sessionData;
        } catch (error) {
            warn('[SessionManager] 加载会话失败:', error);
            this.clearSession();
            return null;
        }
    }
    
    /**
     * 清除会话
     */
    clearSession() {
        removeStorage(STORAGE_KEYS.SESSION);
        this.currentSession = null;
        info('[SessionManager] 会话已清除');
    }
    
    /**
     * 检查会话是否有效
     * @param {Object} session - 会话数据
     * @returns {boolean} 是否有效
     */
    isSessionValid(session) {
        if (!session || !session.timestamp) {
            return false;
        }
        
        const maxAge = 24 * 60 * 60 * 1000; // 24小时
        return Date.now() - session.timestamp < maxAge;
    }
    
    /**
     * 获取当前会话
     * @returns {Object|null} 当前会话数据
     */
    getCurrentSession() {
        return this.currentSession;
    }
}

