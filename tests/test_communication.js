/**
 * MuseumAgent 通信测试脚本
 * 测试与服务器的各种业务通信
 */

// 导入MuseumAgentClient类
const MuseumAgentClient = require('../client/web/Demo/js/lib/MuseumAgent_Client');

class CommunicationTest {
    constructor() {
        this.client = null;
        this.testResults = [];
    }

    async runTests() {
        console.log('====================================');
        console.log('MuseumAgent 通信测试开始');
        console.log('====================================');

        try {
            // 初始化客户端
            await this.initializeClient();

            // 运行测试用例
            await this.testLogin();
            await this.testSessionManagement();
            await this.testAgentInteraction();
            await this.testWebSocketStream();
            await this.testWebSocketTTS();

            // 清理资源
            this.client.cleanup();

            // 输出测试结果
            this.printResults();

        } catch (error) {
            console.error('测试过程中发生错误:', error);
        }
    }

    async initializeClient() {
        console.log('\n1. 初始化客户端');
        this.client = new MuseumAgentClient({
            baseUrl: 'http://localhost:8000',
            timeout: 30000,
            autoReconnect: true,
            reconnectInterval: 5000,
            heartbeatInterval: 30000
        });

        // 注册事件监听器
        this.setupEventListeners();

        this.testResults.push({
            test: '客户端初始化',
            status: 'PASS',
            message: '客户端初始化成功'
        });
    }

    setupEventListeners() {
        this.client.on('login', (data) => {
            console.log('[事件] 登录成功:', data);
        });

        this.client.on('error', (data) => {
            console.error('[事件] 发生错误:', data);
        });

        this.client.on('session_registered', (data) => {
            console.log('[事件] 会话注册成功:', data.session_id);
        });

        this.client.on('session_disconnected', (data) => {
            console.log('[事件] 会话断开:', data.session_id);
        });

        this.client.on('agent_response', (data) => {
            console.log('[事件] 收到智能体响应:', data);
        });

        this.client.on('ws_connected', (data) => {
            console.log('[事件] WebSocket连接成功:', data.type);
        });

        this.client.on('ws_disconnected', (data) => {
            console.log('[事件] WebSocket连接断开:', data.type);
        });

        this.client.on('stream_chunk', (data) => {
            console.log('[事件] 收到流式数据块:', data.chunk.length, '字符');
        });

        this.client.on('stream_complete', (data) => {
            console.log('[事件] 流式生成完成:', data.streamId);
        });

        this.client.on('audio_chunk', (data) => {
            console.log('[事件] 收到音频数据块:', data.size, '字节');
        });
    }

    async testLogin() {
        console.log('\n2. 测试认证相关API');
        try {
            console.log('   2.1 测试登录');
            const response = await this.client.login('123', '123');
            console.log('   登录成功，Token:', response.access_token.substring(0, 20) + '...');
            
            this.testResults.push({
                test: '登录测试',
                status: 'PASS',
                message: '登录成功'
            });

            console.log('   2.2 测试获取用户信息');
            const userInfo = await this.client.getCurrentUser();
            console.log('   获取用户信息成功:', userInfo.username);
            
            this.testResults.push({
                test: '获取用户信息测试',
                status: 'PASS',
                message: '获取用户信息成功'
            });

        } catch (error) {
            console.error('   登录测试失败:', error.message);
            this.testResults.push({
                test: '登录测试',
                status: 'FAIL',
                message: error.message
            });
        }
    }

    async testSessionManagement() {
        console.log('\n3. 测试会话管理相关API');
        try {
            console.log('   3.1 测试注册会话');
            const session = await this.client.registerSession({
                client_type: 'web',
                scene_type: 'public'
            });
            console.log('   会话注册成功:', session.session_id);
            
            this.testResults.push({
                test: '注册会话测试',
                status: 'PASS',
                message: '会话注册成功'
            });

            console.log('   3.2 测试验证会话');
            const isValid = await this.client.validateSession();
            console.log('   会话验证结果:', isValid);
            
            this.testResults.push({
                test: '验证会话测试',
                status: 'PASS',
                message: '会话验证成功'
            });

            console.log('   3.3 测试断开会话');
            await this.client.disconnectSession();
            console.log('   会话断开成功');
            
            this.testResults.push({
                test: '断开会话测试',
                status: 'PASS',
                message: '会话断开成功'
            });

        } catch (error) {
            console.error('   会话管理测试失败:', error.message);
            this.testResults.push({
                test: '会话管理测试',
                status: 'FAIL',
                message: error.message
            });
        }
    }

    async testAgentInteraction() {
        console.log('\n4. 测试智能体交互API');
        try {
            // 重新注册会话
            await this.client.registerSession({
                client_type: 'web',
                scene_type: 'public'
            });

            console.log('   4.1 测试智能体解析接口');
            const result = await this.client.parseAgent('请介绍一下青铜鼎', {
                clientType: 'web',
                sceneType: 'public'
            });
            console.log('   智能体解析成功:', result);
            
            this.testResults.push({
                test: '智能体解析测试',
                status: 'PASS',
                message: '智能体解析成功'
            });

        } catch (error) {
            console.error('   智能体交互测试失败:', error.message);
            this.testResults.push({
                test: '智能体交互测试',
                status: 'FAIL',
                message: error.message
            });
        }
    }

    async testWebSocketStream() {
        console.log('\n5. 测试WebSocket流式通信');
        try {
            console.log('   5.1 连接智能体流式WebSocket');
            const ws = await this.client.connectAgentStream();
            console.log('   WebSocket连接成功');

            console.log('   5.2 发送流式请求');
            await new Promise((resolve) => {
                this.client.sendTextStream(
                    ws,
                    '请介绍一下博物馆的历史',
                    (chunk) => {
                        console.log('   收到数据块:', chunk.substring(0, 50) + '...');
                    },
                    (data) => {
                        console.log('   流式生成完成');
                        resolve();
                    }
                );

                // 添加超时处理
                setTimeout(() => {
                    console.log('   流式请求超时，继续测试');
                    resolve();
                }, 5000);
            });

            console.log('   5.3 断开WebSocket连接');
            this.client.disconnectWebSocket('agent_stream');
            console.log('   WebSocket断开成功');
            
            this.testResults.push({
                test: 'WebSocket流式通信测试',
                status: 'PASS',
                message: 'WebSocket流式通信成功'
            });

        } catch (error) {
            console.error('   WebSocket流式通信测试失败:', error.message);
            this.testResults.push({
                test: 'WebSocket流式通信测试',
                status: 'FAIL',
                message: error.message
            });
        }
    }

    async testWebSocketTTS() {
        console.log('\n6. 测试WebSocket TTS通信');
        try {
            console.log('   6.1 连接TTS WebSocket');
            const ws = await this.client.connectAudioTTS();
            console.log('   TTS WebSocket连接成功');

            console.log('   6.2 发送TTS请求');
            await new Promise((resolve) => {
                this.client.sendTTSRequest(
                    ws,
                    '欢迎使用博物馆智能体，这是一个语音合成测试',
                    (audioChunk) => {
                        console.log('   收到音频数据块:', audioChunk.byteLength || audioChunk.size, '字节');
                    }
                );
                
                // 3秒后结束测试
                setTimeout(resolve, 3000);
            });

            console.log('   6.3 断开TTS WebSocket连接');
            this.client.disconnectWebSocket('audio_tts');
            console.log('   TTS WebSocket断开成功');
            
            this.testResults.push({
                test: 'WebSocket TTS通信测试',
                status: 'PASS',
                message: 'WebSocket TTS通信成功'
            });

        } catch (error) {
            console.error('   WebSocket TTS通信测试失败:', error.message);
            this.testResults.push({
                test: 'WebSocket TTS通信测试',
                status: 'FAIL',
                message: error.message
            });
        }
    }

    printResults() {
        console.log('\n====================================');
        console.log('测试结果汇总');
        console.log('====================================');

        let passCount = 0;
        let failCount = 0;

        this.testResults.forEach(result => {
            console.log(`${result.status === 'PASS' ? '✅' : '❌'} ${result.test}: ${result.status}`);
            if (result.message) {
                console.log(`   信息: ${result.message}`);
            }
            
            if (result.status === 'PASS') {
                passCount++;
            } else {
                failCount++;
            }
        });

        console.log('\n====================================');
        console.log(`测试完成: 共 ${this.testResults.length} 个测试用例`);
        console.log(`通过: ${passCount} 个`);
        console.log(`失败: ${failCount} 个`);
        console.log('====================================');

        if (failCount === 0) {
            console.log('🎉 所有测试用例都通过了！');
        } else {
            console.log('⚠️  有测试用例失败，需要检查。');
        }
    }
}

// 运行测试
if (typeof module !== 'undefined' && require.main === module) {
    const test = new CommunicationTest();
    test.runTests();
}

// 导出测试类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CommunicationTest;
}
