/**
 * 日志工具（纯函数）
 * 提供可配置的日志输出
 */

import { LOG_LEVELS } from '../constants.js';

let currentLevel = LOG_LEVELS.INFO;
let prefix = '[MuseumAgent]';

/**
 * 设置日志级别
 * @param {string|number} level - 日志级别
 */
export function setLogLevel(level) {
    if (typeof level === 'string') {
        currentLevel = LOG_LEVELS[level.toUpperCase()] ?? LOG_LEVELS.INFO;
    } else {
        currentLevel = level;
    }
}

/**
 * 设置日志前缀
 * @param {string} newPrefix - 新的前缀
 */
export function setLogPrefix(newPrefix) {
    prefix = newPrefix;
}

/**
 * 调试日志
 * @param {...any} args - 日志参数
 */
export function debug(...args) {
    if (currentLevel <= LOG_LEVELS.DEBUG) {
        console.debug(prefix, ...args);
    }
}

/**
 * 信息日志
 * @param {...any} args - 日志参数
 */
export function info(...args) {
    if (currentLevel <= LOG_LEVELS.INFO) {
        console.info(prefix, ...args);
    }
}

/**
 * 警告日志
 * @param {...any} args - 日志参数
 */
export function warn(...args) {
    if (currentLevel <= LOG_LEVELS.WARN) {
        console.warn(prefix, ...args);
    }
}

/**
 * 错误日志
 * @param {...any} args - 日志参数
 */
export function error(...args) {
    if (currentLevel <= LOG_LEVELS.ERROR) {
        console.error(prefix, ...args);
    }
}

// 导出日志级别常量
export { LOG_LEVELS };

