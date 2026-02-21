/**
 * 配置管理器
 * 负责配置的保存、加载、更新和重置
 */

import { getStorage, setStorage, removeStorage } from '../utils/storage.js';
import { STORAGE_KEYS, DEFAULT_CONFIG } from '../constants.js';
import { info } from '../utils/logger.js';

export class ConfigManager {
    constructor(customDefaults = {}) {
        this.defaults = { ...DEFAULT_CONFIG, ...customDefaults };
        this.current = { ...this.defaults };
    }
    
    /**
     * 加载配置（合并默认值和保存的配置）
     * @returns {Object} 配置对象
     */
    load() {
        const saved = getStorage(STORAGE_KEYS.CONFIG);
        if (saved) {
            this.current = { ...this.defaults, ...saved };
            info('[ConfigManager] 配置已加载');
        }
        return this.current;
    }
    
    /**
     * 保存配置
     * @param {Object} config - 配置对象（可选，默认保存当前配置）
     */
    save(config = this.current) {
        this.current = config;
        setStorage(STORAGE_KEYS.CONFIG, config);
        info('[ConfigManager] 配置已保存');
    }
    
    /**
     * 更新单个配置项
     * @param {string} key - 配置键
     * @param {*} value - 配置值
     */
    update(key, value) {
        this.current[key] = value;
        this.save();
    }
    
    /**
     * 批量更新配置
     * @param {Object} updates - 要更新的配置项
     */
    updateMultiple(updates) {
        Object.assign(this.current, updates);
        this.save();
    }
    
    /**
     * 获取配置项
     * @param {string} key - 配置键
     * @returns {*} 配置值
     */
    get(key) {
        return this.current[key];
    }
    
    /**
     * 获取所有配置
     * @returns {Object} 配置对象副本
     */
    getAll() {
        return { ...this.current };
    }
    
    /**
     * 重置为默认值
     */
    reset() {
        this.current = { ...this.defaults };
        removeStorage(STORAGE_KEYS.CONFIG);
        info('[ConfigManager] 配置已重置');
    }
    
    /**
     * 获取差异（用于增量更新）
     * @param {Object} newConfig - 新配置
     * @returns {Object} 差异对象
     */
    getDiff(newConfig) {
        const diff = {};
        for (const key in newConfig) {
            if (JSON.stringify(newConfig[key]) !== JSON.stringify(this.current[key])) {
                diff[key] = newConfig[key];
            }
        }
        return diff;
    }
}

