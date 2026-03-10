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

window.SwitchScreenMode = SwitchScreenMode;
console.log('[commonFunction] SwitchScreenMode 已注册到 window 对象');