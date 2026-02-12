// 检查登录状态的脚本
console.log('=== 检查登录状态 ===');
console.log('Token:', localStorage.getItem('token'));
console.log('LocalStorage 键:', Object.keys(localStorage));

// 测试API调用
const apiUrl = 'http://localhost:8000';

// 测试获取客户端列表
fetch(`${apiUrl}/api/admin/clients/connected`)
    .then(response => {
        console.log('获取客户端状态码:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('获取客户端成功:', data);
    })
    .catch(error => {
        console.log('获取客户端失败:', error);
    });

// 测试断开接口（使用一个假的session_id）
fetch(`${apiUrl}/api/admin/clients/session/test-session`, {
    method: 'DELETE'
})
    .then(response => {
        console.log('断开接口状态码:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('断开接口响应:', data);
    })
    .catch(error => {
        console.log('断开接口失败:', error);
    });
