// 测试前端代码的脚本
console.log('=== 测试前端代码 ===');

// 检查是否加载了必要的组件
console.log('Modal:', typeof Modal);
console.log('message:', typeof message);
console.log('api:', typeof api);

// 检查disconnectClient函数
if (typeof disconnectClient === 'function') {
    console.log('disconnectClient 函数存在');
} else {
    console.log('disconnectClient 函数不存在');
}

// 测试事件绑定
const disconnectButtons = document.querySelectorAll('button.ant-btn-dangerous');
console.log('断开按钮数量:', disconnectButtons.length);

disconnectButtons.forEach((button, index) => {
    console.log(`按钮 ${index} 文本:`, button.textContent.trim());
    console.log(`按钮 ${index} 点击事件:`, button.onclick);
});

// 测试Modal.confirm
if (typeof Modal !== 'undefined' && typeof Modal.confirm === 'function') {
    console.log('Modal.confirm 函数存在');
    // 测试Modal.confirm是否能正常调用
    try {
        const modal = Modal.confirm({
            title: '测试确认对话框',
            content: '这是一个测试对话框',
            okText: '确定',
            cancelText: '取消',
            onOk: () => {
                console.log('用户点击了确定');
            },
            onCancel: () => {
                console.log('用户点击了取消');
            }
        });
        console.log('Modal.confirm 调用成功');
        // 关闭测试模态框
        setTimeout(() => {
            modal.destroy();
        }, 1000);
    } catch (error) {
        console.log('Modal.confirm 调用失败:', error);
    }
} else {
    console.log('Modal.confirm 函数不存在');
}
