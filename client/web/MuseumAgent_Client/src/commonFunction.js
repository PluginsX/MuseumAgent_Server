/**
 * 设备/平台信息采集
 * 返回设备类型、屏幕方向、尺寸等信息
 */
export function detectDeviceEnvironment() {
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;
    const pixelRatio = window.devicePixelRatio || 1;
    const touchEnabled = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    // 设备类型判断
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTablet = (screenWidth >= 768 && screenWidth <= 1024 && touchEnabled) || 
                     (screenWidth >= 768 && screenWidth <= 1024 && /iPad|Android|Tablet/i.test(navigator.userAgent));
    const isDesktop = !isMobile && !isTablet;
    
    // 屏幕方向
    const isPortrait = screenHeight > screenWidth;
    const orientation = isPortrait ? 'portrait' : 'landscape';
    const orientationAngle = isPortrait ? 90 : 0;
    
    // 响应式断点
    const isExtraSmall = screenWidth < 480;
    const isSmall = screenWidth >= 480 && screenWidth < 768;
    const isMedium = screenWidth >= 768 && screenWidth < 1024;
    const isLarge = screenWidth >= 1024 && screenWidth < 1440;
    const isExtraLarge = screenWidth >= 1440;
    
    // 触摸质量
    const maxTouchPoints = navigator.maxTouchPoints || 0;
    const touchPrecision = pixelRatio > 2 ? 'high' : (pixelRatio > 1 ? 'medium' : 'low');
    
    return {
        // 基础信息
        screenWidth,
        screenHeight,
        pixelRatio,
        touchEnabled,
        
        // 设备类型
        isMobile,
        isTablet,
        isDesktop,
        
        // 屏幕方向
        orientation,
        isPortrait,
        orientationAngle,
        
        // 响应式断点
        isExtraSmall,
        isSmall,
        isMedium,
        isLarge,
        isExtraLarge,
        
        // 触摸质量
        maxTouchPoints,
        touchPrecision,
        
        // 综合判断
        isMobileDevice: isMobile || isTablet,
        isTouchDevice: touchEnabled,
        
        // 用于判断是否使用窗口模式（仅作为预设）
        shouldUseWindowMode: isDesktop || (isTablet && !isPortrait)
    };
}

/**
 * 切换全屏
 * 全局函数，可在浏览器控制台直接调用
 * 支持：Chrome、Firefox、Safari、Edge、IE
 */
function SwitchScreenMode() {
    const doc = document.documentElement;
    
    if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement && !document.msFullscreenElement) {
        const requestFullscreen = doc.requestFullscreen || doc.webkitRequestFullscreen || doc.mozRequestFullScreen || doc.msRequestFullscreen;
        
        if (requestFullscreen) {
            requestFullscreen.call(doc).catch(err => {
                console.error('[SwitchScreenMode] 进入全屏失败:', err);
            });
        }
    } else {
        const exitFullscreen = document.exitFullscreen || document.webkitExitFullscreen || document.mozCancelFullScreen || document.msExitFullscreen;
        
        if (exitFullscreen) {
            exitFullscreen.call(document).catch(err => {
                console.error('[SwitchScreenMode] 退出全屏失败:', err);
            });
        }
    }
}

// 挂载到全局
window.detectDeviceEnvironment = detectDeviceEnvironment;
window.SwitchScreenMode = SwitchScreenMode;

// 自动检测并输出
console.log('[DeviceDetector] 设备环境信息:', detectDeviceEnvironment());
console.log('[commonFunction] SwitchScreenMode 已注册到 window 对象');
