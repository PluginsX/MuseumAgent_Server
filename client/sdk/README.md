# MuseumAgent Client SDK

[![npm version](https://img.shields.io/npm/v/museum-agent-client-sdk.svg)](https://www.npmjs.com/package/museum-agent-client-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MuseumAgent 通用 Web 客户端 SDK - 全新架构，发送接收完全解耦，支持会话管理和配置持久化。

## 📦 项目位置

**独立 SDK 仓库**：`client/sdk/`

此 SDK 已从 MuseumAgent_Client 项目中完全分离，可以独立开发、构建和发布。

---

## ✨ 特性

- 🚀 **全双工通信**：发送和接收完全解耦，异步并行运行
- 🔄 **会话管理**：自动保存和恢复会话，支持加密存储
- ⚙️ **配置管理**：统一的配置持久化，支持热更新
- 🎤 **音频处理**：内置录音、播放、VAD 语音检测（基于 AudioWorklet）
- 🔌 **零依赖**：纯原生 JavaScript 实现，无外部依赖
- 📦 **多格式支持**：UMD、ESM 双格式，支持 Tree-shaking
- 🔒 **安全可靠**：内置加密工具和错误处理
- 📝 **完整日志**：可配置的日志级别和输出
- ⚡ **高性能**：AudioWorklet 独立线程处理音频，不阻塞主线程

---

## 🚀 快速开始

### 安装依赖

```bash
npm install
```

### 构建

```bash
# 开发模式（监视文件变化）
npm run dev

# 生产构建
npm run build
```

### 构建产物

```
dist/
├── museum-agent-sdk.js           # UMD 未压缩 (96KB)
├── museum-agent-sdk.min.js       # UMD 压缩 (34KB) ⭐
├── museum-agent-sdk.esm.js       # ESM 未压缩 (85KB)
└── museum-agent-sdk.esm.min.js   # ESM 压缩 (34KB)

src/managers/
└── vad-processor.js              # AudioWorklet 处理器 (5KB) ⚠️ 必需
```

**注意**：`vad-processor.js` 是 AudioWorklet 处理器，必须与 SDK 一起部署。

---

## 📖 使用方式

### 浏览器直接引入（UMD）

```html
<script src="./dist/museum-agent-sdk.min.js"></script>

<script>
  const { MuseumAgentClient, Events } = MuseumAgentSDK;
  
  const client = new MuseumAgentClient({
    serverUrl: 'wss://your-server.com'
  });
  
  // 尝试恢复会话
  const restored = await client.reconnectFromSavedSession();
  
  if (!restored) {
    await client.connect(authData);
    await client.saveSession();
  }
</script>
```

**重要**：确保 `vad-processor.js` 与 SDK 在同一目录或可访问路径。

### ES 模块引入

```javascript
import { MuseumAgentClient, Events } from 'museum-agent-client-sdk';

const client = new MuseumAgentClient({
  serverUrl: 'wss://your-server.com'
});
```

### 按需引入（Tree-shaking）

```javascript
import { setStorage, getStorage } from 'museum-agent-client-sdk';
import { encryptData, decryptData } from 'museum-agent-client-sdk';
```

---

## 🔄 更新到 MuseumAgent_Client

### 自动更新（推荐）

```bash
# Windows
update-demo.bat

# 自动执行：
# 1. 构建 SDK
# 2. 复制到 Demo（包括 AudioWorklet 处理器）
# 3. 验证文件
```

### 手动更新

```bash
# 1. 构建
npm run build

# 2. 复制所有必需文件
cp dist/museum-agent-sdk.min.js ../web/MuseumAgent_Client/lib/
cp dist/museum-agent-sdk.min.js.map ../web/MuseumAgent_Client/lib/
cp src/managers/vad-processor.js ../web/MuseumAgent_Client/lib/
```

**注意**：必须同时复制 `vad-processor.js`，否则录音功能将无法工作。

---

## 📚 API 文档

详细的 API 文档请查看：[完整 API 文档](./API.md)

### 核心 API

```javascript
// 创建客户端
const client = new MuseumAgentClient(config);

// 会话管理
await client.saveSession();
await client.reconnectFromSavedSession();

// 连接和断开
await client.connect(authData);
await client.disconnect(reason, clearSession);

// 发送消息
await client.sendText(text, options);
await client.startRecording(options);
await client.stopRecording();

// 配置管理
client.updateConfig(key, value);
client.updateConfigs(updates);
client.resetConfig();

// 事件监听
client.on(Events.TEXT_CHUNK, callback);
client.off(Events.TEXT_CHUNK, callback);
```

---

## 🛠️ 开发指南

### 项目结构

```
sdk/
├── src/                  # 源码
│   ├── core/            # 核心模块
│   ├── managers/        # 管理器
│   │   ├── AudioManager.js      # 音频管理器
│   │   ├── SessionManager.js    # 会话管理器
│   │   ├── ConfigManager.js     # 配置管理器
│   │   └── vad-processor.js     # AudioWorklet 处理器 ⚠️
│   ├── utils/           # 工具函数
│   ├── constants.js     # 常量定义
│   ├── MuseumAgentSDK.js # 主 SDK 类
│   └── index.js         # 入口文件
│
├── dist/                 # 构建产物
├── node_modules/         # 依赖
├── package.json          # NPM 配置
├── rollup.config.js     # 构建配置
└── README.md            # 本文档
```

**⚠️ 重要**：`vad-processor.js` 是 AudioWorklet 处理器，必须作为独立文件部署。

### 开发流程

```bash
# 1. 修改源码
vim src/managers/SessionManager.js

# 2. 开发模式（自动构建）
npm run dev

# 3. 测试
# 在 MuseumAgent_Client 中测试或创建测试文件

# 4. 构建生产版本
npm run build

# 5. 更新到 MuseumAgent_Client
update-demo.bat

# 6. 提交代码
git add .
git commit -m "feat: 添加新功能"
```

---

## 📦 发布

### 发布到 NPM

```bash
# 1. 更新版本
npm version patch  # 2.0.0 -> 2.0.1
npm version minor  # 2.0.1 -> 2.1.0
npm version major  # 2.1.0 -> 3.0.0

# 2. 构建
npm run build

# 3. 发布
npm publish
```

### 发布到 CDN

```bash
# 上传 dist/ 目录和 vad-processor.js 到 CDN
# 确保两个文件在同一目录或相对路径正确

# 然后在项目中引用
<script src="https://cdn.example.com/museum-agent-sdk@2.0.0/museum-agent-sdk.min.js"></script>
<!-- vad-processor.js 会自动从相对路径加载 -->
```

**注意**：部署时必须包含以下文件：
- `museum-agent-sdk.min.js` - 主 SDK
- `vad-processor.js` - AudioWorklet 处理器（必需）
- `museum-agent-sdk.min.js.map` - Source Map（可选）

---

## 🌐 浏览器兼容性

### ✅ 完全支持

| 浏览器 | 最低版本 | 推荐版本 | 说明 |
|--------|---------|---------|------|
| Chrome | 66+ | 90+ | 完全支持，性能最佳 |
| Edge | 79+ | 90+ | 基于 Chromium，与 Chrome 一致 |
| Firefox | 76+ | 100+ | 完全支持 |
| Safari (macOS) | 14.1+ | 16.0+ | 完全支持 |
| Safari (iOS) | 14.5+ | 16.0+ | 完全支持，需 HTTPS |
| Opera | 53+ | 最新 | 基于 Chromium |

**全球覆盖率：~94%**

### 核心技术依赖

- **WebSocket**：双向通信
- **Web Audio API**：音频处理
- **AudioWorkletNode**：音频处理（关键）⚠️
- **MediaDevices.getUserMedia**：麦克风访问
- **localStorage**：数据持久化
- **ES6+**：async/await, Promise, class 等

### ⚠️ 部分支持

- **Safari 14.0 及以下**：不支持 AudioWorklet，录音功能无法使用
- **旧版 Android 浏览器**：可能不支持

### ❌ 不支持

- **Internet Explorer**：完全不支持（已停止维护）
- **Chrome < 66**：缺少 AudioWorklet 支持
- **Firefox < 76**：缺少 AudioWorklet 支持

### 兼容性检测

```javascript
function checkBrowserCompatibility() {
    const issues = [];
    
    if (!window.WebSocket) {
        issues.push('WebSocket 不支持');
    }
    
    if (!window.AudioContext && !window.webkitAudioContext) {
        issues.push('Web Audio API 不支持');
    }
    
    if (!navigator.mediaDevices?.getUserMedia) {
        issues.push('麦克风访问不支持');
    }
    
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    if (!audioContext.audioWorklet) {
        issues.push('AudioWorklet 不支持（录音功能无法使用）');
    }
    
    return {
        compatible: issues.length === 0,
        issues: issues
    };
}

// 使用
const result = checkBrowserCompatibility();
if (!result.compatible) {
    console.warn('浏览器兼容性问题：', result.issues);
}
```

---

## 🧪 测试

```bash
# 代码检查
npm run lint

# 代码格式化
npm run format
```

---

## 📄 许可证

MIT License

---

## 📮 联系方式

- GitHub: https://github.com/your-org/museum-agent
- Email: support@museum-agent.com

---

## 🎯 相关项目

- **MuseumAgent_Client 项目**：`../web/MuseumAgent_Client/` - 使用本 SDK 的示例应用
- **项目结构说明**：`../PROJECT_STRUCTURE.md` - 完整的项目结构文档
