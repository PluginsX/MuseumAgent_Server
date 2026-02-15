// 调试脚本 - 在浏览器控制台运行

console.log('=== 开始调试 ===');

// 1. 检查 DOM 结构
console.log('1. 检查 #app 容器:');
const app = document.getElementById('app');
console.log('app 元素:', app);
console.log('app.innerHTML 长度:', app ? app.innerHTML.length : 'null');
console.log('app.children:', app ? app.children : 'null');

// 2. 检查子元素
if (app && app.children.length > 0) {
    console.log('2. app 的第一个子元素:');
    const firstChild = app.children[0];
    console.log('className:', firstChild.className);
    console.log('style:', firstChild.style.cssText);
    console.log('children:', firstChild.children);
    
    // 3. 检查聊天视图
    const chatView = document.querySelector('.chat-view');
    console.log('3. .chat-view 元素:', chatView);
    if (chatView) {
        console.log('chatView.style:', chatView.style.cssText);
        console.log('chatView.children:', chatView.children);
    }
    
    // 4. 检查聊天容器
    const chatContainer = document.querySelector('.chat-container');
    console.log('4. .chat-container 元素:', chatContainer);
    if (chatContainer) {
        console.log('chatContainer.style:', chatContainer.style.cssText);
        console.log('chatContainer.children:', chatContainer.children);
    }
    
    // 5. 检查消息容器
    const messageContainer = document.querySelector('.message-container');
    console.log('5. .message-container 元素:', messageContainer);
    if (messageContainer) {
        console.log('messageContainer.style:', messageContainer.style.cssText);
    }
    
    // 6. 检查输入容器
    const inputContainer = document.querySelector('.input-container');
    console.log('6. .input-container 元素:', inputContainer);
    if (inputContainer) {
        console.log('inputContainer.style:', inputContainer.style.cssText);
    }
} else {
    console.log('2. app 容器为空或没有子元素！');
}

// 7. 检查登录表单
const loginForm = document.querySelector('.login-form-container');
console.log('7. 登录表单:', loginForm);
console.log('登录表单是否可见:', loginForm ? window.getComputedStyle(loginForm).display : 'null');

console.log('=== 调试结束 ===');

