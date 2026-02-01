// 前端调试脚本 - 在浏览器控制台中运行
console.log("=== Embedding Stats Debug Script ===");

// 检查localStorage中的token
const token = localStorage.getItem('token');
console.log("Token exists:", !!token);
console.log("Token value:", token ? token.substring(0, 20) + "..." : "null");

// 检查API基础配置
console.log("Base URL:", import.meta.env.VITE_API_URL || '');
console.log("Base URL (alternative):", window.location.origin);

// 手动测试stats API
async function testStatsAPI() {
    try {
        console.log("Testing stats API...");
        const response = await fetch('/api/admin/embedding/stats', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log("Response status:", response.status);
        const data = await response.json();
        console.log("Response data:", data);
        console.log("Total vectors:", data.total_vectors);
        
        return data;
    } catch (error) {
        console.error("API Error:", error);
        return null;
    }
}

// 检查当前页面状态
console.log("Current page path:", window.location.pathname);
console.log("Is on Control panel:", window.location.pathname.includes('/Control'));

// 运行测试
testStatsAPI().then(result => {
    console.log("=== Test Completed ===");
    console.log("Final result:", result);
});