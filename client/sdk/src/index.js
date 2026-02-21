/**
 * MuseumAgent 客户端 SDK V2.0
 * 统一导出入口
 */

// 主 SDK 类
export { MuseumAgentClient, default } from './MuseumAgentSDK.js';

// 常量
export { Events, DEFAULT_CONFIG, STORAGE_KEYS, ERROR_TYPES, LOG_LEVELS } from './constants.js';

// 核心模块（高级用户可能需要）
export { EventBus } from './core/EventBus.js';
export { WebSocketClient } from './core/WebSocketClient.js';
export { SendManager } from './core/SendManager.js';
export { ReceiveManager } from './core/ReceiveManager.js';

// 管理器（高级用户可能需要）
export { AudioManager } from './managers/AudioManager.js';
export { SessionManager } from './managers/SessionManager.js';
export { ConfigManager } from './managers/ConfigManager.js';

// 工具函数（按需引入，支持 tree-shaking）
export {
    setStorage,
    getStorage,
    removeStorage,
    clearStorage,
    hasStorage
} from './utils/storage.js';

export {
    encryptData,
    decryptData,
    escapeHtml,
    sanitizeHtml,
    validateInput,
    generateSecureId
} from './utils/security.js';

export {
    classifyError,
    formatError
} from './utils/error.js';

export {
    setLogLevel,
    setLogPrefix,
    debug,
    info,
    warn,
    error
} from './utils/logger.js';

