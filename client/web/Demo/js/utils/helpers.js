/**
 * 工具函数模块
 */

/**
 * 格式化时间
 * @param {number} seconds - 秒数
 * @returns {string} - 格式化后的时间字符串
 */
export function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
    const remainingSeconds = (seconds % 60).toString().padStart(2, '0');
    return `${minutes}:${remainingSeconds}`;
}

/**
 * 截断文本
 * @param {string} text - 原始文本
 * @param {number} maxLength - 最大长度
 * @returns {string} - 截断后的文本
 */
export function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength) + '...';
}

/**
 * 检查是否是有效的URL
 * @param {string} url - URL字符串
 * @returns {boolean} - 是否是有效的URL
 */
export function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

/**
 * 生成唯一ID
 * @returns {string} - 唯一ID
 */
export function generateUniqueId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * 延迟执行
 * @param {number} ms - 延迟时间（毫秒）
 * @returns {Promise<void>}
 */
export function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 检查浏览器是否支持特定功能
 * @param {string} feature - 功能名称
 * @returns {boolean} - 是否支持
 */
export function isBrowserSupported(feature) {
    switch (feature) {
        case 'mediaRecorder':
            return 'MediaRecorder' in window;
        case 'getUserMedia':
            return 'getUserMedia' in navigator.mediaDevices;
        case 'websocket':
            return 'WebSocket' in window;
        default:
            return false;
    }
}

/**
 * 显示通知
 * @param {string} title - 通知标题
 * @param {string} message - 通知消息
 * @param {string} icon - 通知图标
 */
export function showNotification(title, message, icon = '') {
    if ('Notification' in window) {
        if (Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: icon
            });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(title, {
                        body: message,
                        icon: icon
                    });
                }
            });
        }
    }
}
