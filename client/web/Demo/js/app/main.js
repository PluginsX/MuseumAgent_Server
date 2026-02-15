/**
 * 应用入口
 * 初始化整个应用，管理全局状态和模块
 */

// 导入PageManager类
import PageManager from './page-manager.js';

class MainApp {
    constructor() {
        this.init();
    }

    /**
     * 初始化应用
     */
    init() {
        console.log('[MainApp] 初始化应用...');
        
        // 创建页面管理器
        const pageManager = new PageManager();
        window.pageManager = pageManager;
        
        // 初始化页面管理器
        pageManager.init();
        
        // 全局辅助函数
        window.showHelp = this.showHelp;
        
        console.log('[MainApp] 应用初始化完成');
    }

    /**
     * 显示帮助信息
     */
    showHelp() {
        alert('欢迎使用MuseumAgent系统！\n\n账户登录：使用注册的用户名和密码登录\nAPI密钥登录：使用系统提供的API密钥登录\n\n如需帮助，请联系系统管理员。');
    }
}

// 当DOM加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 创建应用实例
    window.mainApp = new MainApp();
});

// 导出MainApp类（如果需要）
export default MainApp;