#!/usr/bin/env node
"""
测试登录功能
测试从客户端服务器发送登录请求到主服务器
"""

const fetch = require('node-fetch');

async function testLogin() {
    console.log('开始测试登录功能...');
    
    try {
        // 测试从本地发送登录请求到主服务器
        console.log('测试1: 直接从本地发送登录请求');
        const response1 = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: '123', password: '123' })
        });
        
        console.log(`状态码: ${response1.status}`);
        const data1 = await response1.json();
        console.log(`响应:`, data1);
        
        // 测试模拟客户端服务器发送登录请求
        console.log('\n测试2: 模拟客户端服务器发送登录请求');
        const response2 = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:18000'
            },
            body: JSON.stringify({ username: '123', password: '123' })
        });
        
        console.log(`状态码: ${response2.status}`);
        const data2 = await response2.json();
        console.log(`响应:`, data2);
        
        console.log('\n登录功能测试完成！');
    } catch (error) {
        console.error('测试失败:', error);
    }
}

testLogin();