/**
 * 错误处理工具（纯函数）
 * 提供统一的错误分类和格式化
 */

import { ERROR_TYPES } from '../constants.js';

/**
 * 分类错误
 * @param {Error} error - 错误对象
 * @returns {Object} 分类结果
 */
export function classifyError(error) {
    const message = error.message || '';
    
    // 网络错误
    if (message.includes('网络') || message.includes('连接') || message.includes('timeout') || message.includes('Network')) {
        return {
            type: ERROR_TYPES.NETWORK_ERROR,
            userMessage: '网络连接失败，请检查网络设置',
            recoverable: true
        };
    }
    
    // 认证错误
    if (message.includes('认证') || message.includes('登录') || message.includes('auth') || message.includes('Auth')) {
        return {
            type: ERROR_TYPES.AUTH_ERROR,
            userMessage: '认证失败，请重新登录',
            recoverable: false
        };
    }
    
    // 会话过期
    if (message.includes('会话') || message.includes('过期') || message.includes('session') || message.includes('Session')) {
        return {
            type: ERROR_TYPES.SESSION_EXPIRED,
            userMessage: '会话已过期，请重新登录',
            recoverable: false
        };
    }
    
    // 默认错误
    return {
        type: ERROR_TYPES.UNKNOWN_ERROR,
        userMessage: '操作失败：' + message,
        recoverable: false
    };
}

/**
 * 格式化错误信息
 * @param {Error} error - 错误对象
 * @param {string} context - 错误上下文
 * @returns {Object} 格式化后的错误信息
 */
export function formatError(error, context = '') {
    const classified = classifyError(error);
    return {
        ...classified,
        context,
        timestamp: Date.now(),
        originalError: error
    };
}

