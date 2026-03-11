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
 * 优化移动端视频播放兼容性
 * 彻底禁用画中画和悬浮播放功能
 * 适用于 Unity WebGL 项目中的 HTML5 Video 元素
 */
export function optimizeMobileVideoPlayback(canvas) {
    if (!canvas) return;
    
    // 查找 canvas 内的所有 video 元素
    const videos = canvas.querySelectorAll('video');
    
    videos.forEach(video => {
        console.log('[optimizeMobileVideoPlayback] 彻底禁用画中画/悬浮播放:', video);
        
        // ========================================
        // ✅ 第一部分：API 级别禁用（最优先）
        // ========================================
        
        // 1. 禁用 Picture-in-Picture API
        if (video.disablePictureInPicture !== undefined) {
            video.disablePictureInPicture = true;
            console.log('[optimizeMobileVideoPlayback] ✓ disablePictureInPicture = true');
        }
        
        // 2. 阻止 requestPictureInPicture 方法调用
        if ('requestPictureInPicture' in video) {
            const originalRequestPiP = video.requestPictureInPicture.bind(video);
            video.requestPictureInPicture = async () => {
                console.error('[optimizeMobileVideoPlayback] ⛔ 画中画功能已被禁用！');
                throw new Error('[Unity WebGL] 画中画功能已被禁用，视频必须在 Unity 内部播放');
            };
            console.log('[optimizeMobileVideoPlayback] ✓ requestPictureInPicture 已拦截');
        }
        
        // ========================================
        // ✅ 第二部分：HTML 属性级别禁用
        // ========================================
        
        // 3. 强制内联播放（所有浏览器）
        video.setAttribute('playsinline', '1');
        video.setAttribute('webkit-playsinline', '1');
        video.setAttribute('x5-playsinline', '1');
        console.log('[optimizeMobileVideoPlayback] ✓ playsinline 属性已设置');
        
        // 4. 禁止 X5 内核的悬浮播放（小米、QQ 浏览器等）
        video.setAttribute('x5-video-player-type', 'inline');
        video.setAttribute('x5-video-player-fullscreen', 'false');
        video.setAttribute('x5-video-fullscreen-orientation', 'portrait');
        console.log('[optimizeMobileVideoPlayback] ✓ X5 悬浮播放已禁用');
        
        // 5. 移除所有可能触发悬浮的属性
        video.removeAttribute('x5-video-airplay');
        video.removeAttribute('disablepictureinpicture');
        console.log('[optimizeMobileVideoPlayback] ✓ 已清理悬浮相关属性');
        
        // ========================================
        // ✅ 第三部分：事件级别拦截
        // ========================================
        
        // 6. 阻止右键菜单（防止手动触发画中画）
        video.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('[optimizeMobileVideoPlayback] ⛔ 右键菜单已阻止');
            return false;
        }, true);  // 使用捕获阶段
        
        // 7. 拦截 enterpictureinpicture 事件
        video.addEventListener('enterpictureinpicture', (e) => {
            console.error('[optimizeMobileVideoPlayback] ⚠️ 检测到画中画模式被触发！');
            e.preventDefault();
            e.stopPropagation();
            // 立即退出画中画
            if (document.pictureInPictureElement) {
                document.exitPictureInPicture().catch(() => {});
            }
            alert('⛔ 画中画功能已被禁用\n视频必须在 Unity 内部完整播放');
            return false;
        }, true);
        
        // 8. 阻止离开画中画时的某些行为
        video.addEventListener('leavepictureinpicture', (e) => {
            console.log('[optimizeMobileVideoPlayback] ℹ️ 画中画模式已退出');
        }, true);
        
        // 9. 阻止触摸长按触发菜单
        video.addEventListener('touchstart', (e) => {
            e.preventDefault();
        }, { passive: false });
        
        // 10. 阻止双击缩放
        video.addEventListener('dblclick', (e) => {
            e.preventDefault();
        });
        
        // ========================================
        // ✅ 第四部分：CSS 样式级别锁定
        // ========================================
        
        // 11. 强制设置 CSS 样式（最高优先级）
        Object.assign(video.style, {
            // 防止层叠上下文变化
            '-webkit-backface-visibility': 'hidden !important',
            'backface-visibility': 'hidden !important',
            
            // 固定位置，防止被抽离
            'position': 'static !important',
            'top': '0 !important',
            'left': '0 !important',
            'right': 'auto !important',
            'bottom': 'auto !important',
            'margin': '0 !important',
            'padding': '0 !important',
            
            // 禁止变换
            'transform': 'none !important',
            '-webkit-transform': 'none !important',
            '-moz-transform': 'none !important',
            '-o-transform': 'none !important',
            
            // 层级锁定在 Unity Canvas 内
            'z-index': 'auto !important',
            
            // 防止 GPU 加速导致的问题
            'will-change': 'auto !important',
            
            // 禁止动画
            'animation': 'none !important',
            '-webkit-animation': 'none !important',
            
            // 确保显示正常
            'display': 'block !important',
            'opacity': '1 !important',
            'visibility': 'visible !important',
            
            // 禁止选择
            'user-select': 'none !important',
            '-webkit-user-select': 'none !important',
            '-moz-user-select': 'none !important',
            '-ms-user-select': 'none !important',
            
            // 禁止拖拽
            'pointer-events': 'auto !important',
            '-webkit-touch-callout': 'none !important',
            
            // 禁止图片替换
            '-webkit-user-modify': 'read-only !important',
            
            // 禁止滚动
            'overflow': 'hidden !important',
            
            // 禁止内容溢出
            'max-width': '100% !important',
            'max-height': '100% !important',
            
            // 强制不透明
            'filter': 'none !important',
            '-webkit-filter': 'none !important',
            
            // 禁止混合模式
            'mix-blend-mode': 'normal !important',
            
            // 禁止遮罩
            '-webkit-mask': 'none !important',
            'mask': 'none !important',
            
            // 禁止阴影
            'box-shadow': 'none !important',
            '-webkit-box-shadow': 'none !important',
            
            // 禁止边框
            'border': 'none !important',
            '-webkit-border-radius': '0 !important',
            'border-radius': '0 !important',
            
            // 禁止 outline
            'outline': 'none !important',
            
            // 禁止 focus 效果
            ':focus': {
                'outline': 'none !important'
            }
        });
        
        console.log('[optimizeMobileVideoPlayback] ✓ CSS 样式已锁定');
    });
    
    // ========================================
    // ✅ 第五部分：Canvas 容器级别保护
    // ========================================
    
    // 12. 为整个 canvas 容器添加保护样式
    Object.assign(canvas.style, {
        '-webkit-transform': 'translateZ(0) !important',
        'transform': 'translateZ(0) !important',
        'contain': 'layout style paint size !important',
        'overflow': 'hidden !important',
        'position': 'relative !important',
        'width': '100% !important',
        'height': '100% !important',
        'max-width': '100% !important',
        'max-height': '100% !important',
        'min-width': '100% !important',
        'min-height': '100% !important',
        'margin': '0 !important',
        'padding': '0 !important',
        'border': 'none !important',
        'z-index': '1 !important'
    });
    
    console.log('[optimizeMobileVideoPlayback] ✓ Canvas 容器已锁定');
    console.log('[optimizeMobileVideoPlayback] 🎯 视频优化完成，共处理', videos.length, '个视频元素');
    console.log('[optimizeMobileVideoPlayback] ⚠️ 画中画和悬浮播放功能已彻底禁用');
}

/**
 * 检测设备类型并应用相应优化
 */
export function detectAndOptimizeForDevice() {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    
    // 检测 Android 设备
    const isAndroid = /android/i.test(userAgent);
    // 检测 iOS 设备
    const isIOS = /iPad|iPhone|iPod/.test(userAgent) && !(window.MSStream);
    // 检测小米浏览器（X5 内核）
    const isMiBrowser = /miuibrowser|x5browser|micromessenger/i.test(userAgent);
    // 检测微信内置浏览器
    const isWeChat = /micromessenger/i.test(userAgent);
    
    console.log('[detectAndOptimizeForDevice] 设备检测:', {
        isAndroid,
        isIOS,
        isMiBrowser,
        isWeChat,
        userAgent
    });
    
    // 获取 Unity Canvas
    const unityCanvas = document.getElementById('unity-canvas');
    
    if (unityCanvas) {
        if (isAndroid || isIOS) {
            console.log('[detectAndOptimizeForDevice] 检测到移动设备，应用优化...');
            optimizeMobileVideoPlayback(unityCanvas);
            
            // 针对小米浏览器的特殊处理
            if (isMiBrowser) {
                console.log('[detectAndOptimizeForDevice] 检测到小米浏览器，应用 X5 特殊处理...');
                
                // 添加 X5 特定的 meta 标签
                let x5Meta = document.querySelector('meta[name="x5-video-player-type"]');
                if (!x5Meta) {
                    x5Meta = document.createElement('meta');
                    x5Meta.name = 'x5-video-player-type';
                    x5Meta.content = 'inline';
                    document.head.appendChild(x5Meta);
                }
                
                x5Meta = document.querySelector('meta[name="x5-video-player-fullscreen"]');
                if (!x5Meta) {
                    x5Meta = document.createElement('meta');
                    x5Meta.name = 'x5-video-player-fullscreen';
                    x5Meta.content = 'false';
                    document.head.appendChild(x5Meta);
                }
                
                x5Meta = document.querySelector('meta[name="x5-playsinline"]');
                if (!x5Meta) {
                    x5Meta = document.createElement('meta');
                    x5Meta.name = 'x5-playsinline';
                    x5Meta.content = 'true';
                    document.head.appendChild(x5Meta);
                }
            }
        }
    }
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

