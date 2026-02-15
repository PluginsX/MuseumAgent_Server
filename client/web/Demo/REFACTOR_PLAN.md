# 博物馆智能体 Web Demo 重构计划

## 重构目标

1. **完全符合通信协议** - 严格按照 `CommunicationProtocol_CS.md` 实现
2. **清晰的架构设计** - 模块化、职责分离、易维护
3. **高性能实现** - 优化音频处理、减少不必要的转换
4. **安全可靠** - 防止 XSS、加密敏感数据、完善错误处理
5. **良好的用户体验** - 流畅的交互、实时反馈

## 新架构设计

```
src/
├── core/                    # 核心层
│   ├── WebSocketClient.js   # WebSocket 客户端（严格遵循协议）
│   ├── StateManager.js      # 全局状态管理
│   └── EventBus.js          # 事件总线
├── services/                # 服务层
│   ├── AuthService.js       # 认证服务
│   ├── SessionService.js    # 会话管理
│   ├── MessageService.js    # 消息服务
│   └── AudioService.js      # 音频服务（录音+播放）
├── components/              # 组件层
│   ├── LoginForm.js         # 登录表单
│   ├── ChatWindow.js        # 聊天窗口
│   ├── MessageBubble.js     # 消息气泡
│   └── VoiceRecorder.js     # 语音录制器
├── utils/                   # 工具层
│   ├── security.js          # 安全工具（加密、XSS防护）
│   ├── audio.js             # 音频工具
│   └── dom.js               # DOM 工具
└── app.js                   # 应用入口
```

## 关键改进点

### 1. 通信协议完全符合

- ✅ 正确实现流式语音请求（起始帧 → 二进制帧 → 结束帧）
- ✅ 正确处理 RESPONSE（区分 text_stream_seq 和 voice_stream_seq）
- ✅ 统一音频格式（PCM 16kHz/16bit/单声道）
- ✅ 完善心跳机制

### 2. 架构优化

- ✅ 单一职责原则：每个模块只做一件事
- ✅ 依赖注入：模块间松耦合
- ✅ 事件驱动：通过 EventBus 通信
- ✅ 状态集中管理：StateManager 统一管理

### 3. 性能优化

- ✅ 音频处理使用 AudioWorklet（替代 ScriptProcessor）
- ✅ 减少数据转换（PCM 直接传输）
- ✅ DOM 操作批量化
- ✅ 内存及时释放

### 4. 安全加固

- ✅ 密码使用 Web Crypto API 加密存储
- ✅ 所有用户输入进行 XSS 过滤
- ✅ CSP 策略
- ✅ 完善的错误处理

## 实施步骤

1. ✅ 创建核心层（WebSocketClient, StateManager, EventBus）
2. ✅ 创建服务层（AuthService, SessionService, MessageService, AudioService）
3. ✅ 创建组件层（LoginForm, ChatWindow, MessageBubble, VoiceRecorder）
4. ✅ 创建工具层（security, audio, dom）
5. ✅ 集成测试
6. ✅ 性能优化
7. ✅ 文档完善

## 兼容性说明

- 不考虑旧版浏览器兼容性
- 最低要求：Chrome 90+, Firefox 88+, Safari 14+
- 使用现代 Web API（AudioWorklet, Web Crypto API）

## 预期效果

- 代码量减少 40%
- 性能提升 60%
- 内存占用减少 50%
- 维护成本降低 70%

