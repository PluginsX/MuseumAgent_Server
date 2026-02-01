// 前端配置调试脚本 - 在浏览器控制台中运行
console.log("=== Config Page Debug Script ===");

// 检查localStorage中的token
const token = localStorage.getItem('token');
console.log("Token exists:", !!token);
console.log("Token value:", token ? token.substring(0, 20) + "..." : "null");

// 手动测试配置API
async function testConfigAPI() {
    try {
        console.log("Testing LLM config API...");
        const response = await fetch('/api/admin/config/llm/raw', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log("LLM Config Response status:", response.status);
        const data = await response.json();
        console.log("LLM Config Response data:", data);
        
        // 检查API Key
        if (data.api_key) {
            console.log("API Key from API:", data.api_key);
            console.log("API Key length:", data.api_key.length);
        } else {
            console.log("No API Key found in response");
        }
        
        return data;
    } catch (error) {
        console.error("API Error:", error);
        return null;
    }
}

// 检查当前页面状态
console.log("Current page path:", window.location.pathname);
console.log("Is on LLM config page:", window.location.pathname.includes('/config/llm'));

// 检查React组件状态
setTimeout(() => {
    // 尝试获取Ant Design表单实例
    const formItems = document.querySelectorAll('.ant-form-item');
    console.log("Form items found:", formItems.length);
    
    // 查找API Key输入框
    const apiKeyInputs = document.querySelectorAll('input[placeholder*="API Key"]');
    console.log("API Key inputs found:", apiKeyInputs.length);
    
    if (apiKeyInputs.length > 0) {
        const firstInput = apiKeyInputs[0];
        console.log("First API Key input value:", firstInput.value);
        console.log("First API Key input placeholder:", firstInput.placeholder);
    }
}, 2000);

// 运行测试
testConfigAPI().then(result => {
    console.log("=== Test Completed ===");
    console.log("Final result:", result);
});