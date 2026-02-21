/**
 * 存储工具函数（纯函数，无状态）
 * 提供统一的 localStorage 操作接口
 */

const DEFAULT_PREFIX = 'museumAgent_';

/**
 * 保存数据到 localStorage
 * @param {string} key - 键名
 * @param {*} value - 值（会自动序列化）
 * @param {string} prefix - 键名前缀
 * @returns {boolean} 是否成功
 */
export function setStorage(key, value, prefix = DEFAULT_PREFIX) {
    try {
        const fullKey = prefix + key;
        const serialized = JSON.stringify(value);
        localStorage.setItem(fullKey, serialized);
        return true;
    } catch (error) {
        console.error('[Storage] 保存失败:', error);
        return false;
    }
}

/**
 * 从 localStorage 读取数据
 * @param {string} key - 键名
 * @param {*} defaultValue - 默认值
 * @param {string} prefix - 键名前缀
 * @returns {*} 读取的值或默认值
 */
export function getStorage(key, defaultValue = null, prefix = DEFAULT_PREFIX) {
    try {
        const fullKey = prefix + key;
        const serialized = localStorage.getItem(fullKey);
        return serialized ? JSON.parse(serialized) : defaultValue;
    } catch (error) {
        console.error('[Storage] 读取失败:', error);
        return defaultValue;
    }
}

/**
 * 删除数据
 * @param {string} key - 键名
 * @param {string} prefix - 键名前缀
 */
export function removeStorage(key, prefix = DEFAULT_PREFIX) {
    const fullKey = prefix + key;
    localStorage.removeItem(fullKey);
}

/**
 * 清空所有数据（按前缀）
 * @param {string} prefix - 键名前缀
 */
export function clearStorage(prefix = DEFAULT_PREFIX) {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
        if (key.startsWith(prefix)) {
            localStorage.removeItem(key);
        }
    });
}

/**
 * 检查是否存在
 * @param {string} key - 键名
 * @param {string} prefix - 键名前缀
 * @returns {boolean} 是否存在
 */
export function hasStorage(key, prefix = DEFAULT_PREFIX) {
    const fullKey = prefix + key;
    return localStorage.getItem(fullKey) !== null;
}

