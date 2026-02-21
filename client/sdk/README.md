# MuseumAgent Client SDK

[![npm version](https://img.shields.io/npm/v/museum-agent-client-sdk.svg)](https://www.npmjs.com/package/museum-agent-client-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MuseumAgent 通用 Web 客户端 SDK - 全新架构，发送接收完全解耦，支持会话管理和配置持久化。

## 📦 项目位置

**独立 SDK 仓库**：`client/sdk/`

此 SDK 已从 Demo 项目中完全分离，可以独立开发、构建和发布。

---

## ✨ 特性

- 🚀 **全双工通信**：发送和接收完全解耦，异步并行运行
- 🔄 **会话管理**：自动保存和恢复会话，支持加密存储
- ⚙️ **配置管理**：统一的配置持久化，支持热更新
- 🎤 **音频处理**：内置录音、播放、VAD 语音检测
- 🔌 **零依赖**：纯原生 JavaScript 实现，无外部依赖
- 📦 **多格式支持**：UMD、ESM 双格式，支持 Tree-shaking
- 🔒 **安全可靠**：内置加密工具和错误处理
- 📝 **完整日志**：可配置的日志级别和输出

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
```

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

## 🔄 更新到 Demo

### 自动更新（推荐）

```bash
# Windows
update-demo.bat

# 自动执行：
# 1. 构建 SDK
# 2. 复制到 Demo
# 3. 验证文件
```

### 手动更新

```bash
# 1. 构建
npm run build

# 2. 复制
cp dist/museum-agent-sdk.min.js ../web/Demo/lib/
cp dist/museum-agent-sdk.min.js.map ../web/Demo/lib/
```

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

### 开发流程

```bash
# 1. 修改源码
vim src/managers/SessionManager.js

# 2. 开发模式（自动构建）
npm run dev

# 3. 测试
# 在 Demo 中测试或创建测试文件

# 4. 构建生产版本
npm run build

# 5. 更新到 Demo
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
# 上传 dist/ 目录到 CDN
# 然后在项目中引用
<script src="https://cdn.example.com/museum-agent-sdk@2.0.0/museum-agent-sdk.min.js"></script>
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

- **Demo 项目**：`../web/Demo/` - 使用本 SDK 的示例应用
- **项目结构说明**：`../PROJECT_STRUCTURE.md` - 完整的项目结构文档
