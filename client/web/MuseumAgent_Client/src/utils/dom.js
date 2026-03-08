/**
 * DOM 工具
 * 提供 DOM 操作的辅助函数
 */

/**
 * 创建元素
 */
export function createElement(tag, attributes = {}, children = []) {
    const element = document.createElement(tag);
    
    // 设置属性
    for (const [key, value] of Object.entries(attributes)) {
        if (key === 'className') {
            element.className = value;
        } else if (key === 'textContent') {
            element.textContent = value;
        } else if (key === 'innerHTML') {
            element.innerHTML = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(element.style, value);
        } else if (key.startsWith('on') && typeof value === 'function') {
            const eventName = key.substring(2).toLowerCase();
            element.addEventListener(eventName, value);
        } else if (key === 'value') {
            element.value = value;
        } else if (key === 'placeholder') {
            element.placeholder = value;
        } else if (key === 'rows') {
            element.rows = value;
        } else {
            element.setAttribute(key, value);
        }
    }
    
    // 添加子元素
    for (const child of children) {
        if (typeof child === 'string') {
            element.appendChild(document.createTextNode(child));
        } else if (child instanceof Node) {
            element.appendChild(child);
        }
    }
    
    return element;
}

/**
 * 查询元素
 */
export function $(selector, parent = document) {
    return parent.querySelector(selector);
}

/**
 * 查询所有元素
 */
export function $$(selector, parent = document) {
    return Array.from(parent.querySelectorAll(selector));
}

/**
 * 添加类名
 */
export function addClass(element, ...classNames) {
    element.classList.add(...classNames);
}

/**
 * 移除类名
 */
export function removeClass(element, ...classNames) {
    element.classList.remove(...classNames);
}

/**
 * 切换类名
 */
export function toggleClass(element, className) {
    element.classList.toggle(className);
}

/**
 * 显示元素
 */
export function show(element, display = 'block') {
    element.style.display = display;
}

/**
 * 隐藏元素
 */
export function hide(element) {
    element.style.display = 'none';
}

/**
 * 批量更新 DOM（减少重排）
 */
export function batchUpdate(callback) {
    requestAnimationFrame(() => {
        callback();
    });
}

/**
 * 防抖
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流
 */
export function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 格式化时间
 */
export function formatTime(timestamp) {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * 格式化时长
 */
export function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 滚动到底部
 */
export function scrollToBottom(element, smooth = true) {
    element.scrollTo({
        top: element.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
    });
}

/**
 * 复制到剪贴板
 */
export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (error) {
        console.error('[DOM] 复制失败:', error);
        return false;
    }
}

/**
 * 下载文件
 */
export function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * 显示通知
 */
export function showNotification(message, type = 'info', duration = 3000) {
    const notification = createElement('div', {
        className: `notification notification-${type}`,
        style: {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '4px',
            backgroundColor: type === 'error' ? '#f44336' : type === 'success' ? '#4caf50' : '#2196f3',
            color: 'white',
            boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
            zIndex: '10000',
            animation: 'slideIn 0.3s ease-out'
        }
    }, [message]);
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, duration);
}

