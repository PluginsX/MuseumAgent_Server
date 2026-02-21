# MuseumAgent 项目结构说明

## 📦 新的项目结构（方案 A：完全分离）

```
MuseumAgent_Server/
├── client/
│   ├── sdk/                          # 📦 SDK 库（独立开发）
│   │   ├── src/                     # 源码
│   │   │   ├── core/               # 核心模块
│   │   │   │   ├── EventBus.js
│   │   │   │   ├── WebSocketClient.js
│   │   │   │   ├── SendManager.js
│   │   │   │   └── ReceiveManager.js
│   │   │   ├── managers/           # 管理器
│   │   │   │   ├── AudioManager.js
│   │   │   │   ├── SessionManager.js
│   │   │   │   └── ConfigManager.js
│   │   │   ├── utils/              # 工具函数
│   │   │   │   ├── storage.js
│   │   │   │   ├── security.js
│   │   │   │   ├── error.js
│   │   │   │   └── logger.js
│   │   │   ├── constants.js        # 常量定义
│   │   │   ├── MuseumAgentSDK.js  # 主 SDK 类
│   │   │   └── index.js            # 入口文件
│   │   │
│   │   ├── dist/                    # 构建产物
│   │   │   ├── museum-agent-sdk.js           # UMD 未压缩
│   │   │   ├── museum-agent-sdk.min.js       # UMD 压缩 ⭐
│   │   │   ├── museum-agent-sdk.esm.js       # ESM 未压缩
│   │   │   └── museum-agent-sdk.esm.min.js   # ESM 压缩
│   │   │
│   │   ├── node_modules/            # 依赖
│   │   ├── package.json             # NPM 配置
│   │   ├── rollup.config.js        # 构建配置
│   │   ├── .eslintrc.js            # ESLint 配置
│   │   ├── .prettierrc             # Prettier 配置
│   │   ├── .gitignore              # Git 忽略
│   │   ├── README.md                # SDK 文档
│   │   ├── BUILD.md                 # 构建指南
│   │   └── CHANGELOG.md             # 更新日志
│   │
│   └── web/
│       └── Demo/                     # 🎨 Demo 项目（使用构建产物）
│           ├── lib/
│           │   ├── museum-agent-sdk.min.js      # ✅ SDK 构建产物
│           │   └── museum-agent-sdk.min.js.map  # Source Map
│           │
│           ├── src/                 # 应用代码
│           │   ├── components/
│           │   │   ├── LoginForm.js
│           │   │   ├── ChatWindow.js
│           │   │   ├── MessageBubble.js
│           │   │   └── SettingsPanel.js
│           │   ├── utils/
│           │   │   ├── dom.js
│           │   │   └── audioPlayer.js
│           │   ├── app.js
│           │   └── styles.css
│           │
│           ├── res/                 # 资源文件
│           ├── index.html           # 入口页面
│           ├── ssl_server.py        # 开发服务器
│           ├── start.bat            # 启动脚本
│           └── README.md            # Demo 说明
```

---

## 🎯 核心改进

### 1. SDK 完全独立 ✅

**位置：** `client/sdk/`

**特点：**
- ✅ 独立的 Git 仓库（可选）
- ✅ 独立的 package.json
- ✅ 独立的构建系统
- ✅ 可以发布到 NPM

**开发流程：**
```bash
# 进入 SDK 目录
cd client/sdk

# 安装依赖
npm install

# 开发模式（监视文件变化）
npm run dev

# 生产构建
npm run build

# 发布到 NPM（可选）
npm publish
```

### 2. Demo 只使用构建产物 ✅

**位置：** `client/web/Demo/`

**特点：**
- ✅ 只包含一个 SDK 文件（34KB）
- ✅ 使用 UMD 格式（浏览器直接引入）
- ✅ 无需构建工具
- ✅ 可以独立部署

**使用方式：**
```html
<!-- index.html -->
<script src="./lib/museum-agent-sdk.min.js"></script>
<script type="module" src="./src/app.js"></script>
```

```javascript
// src/app.js
const { MuseumAgentClient, Events } = window.MuseumAgentSDK;

const client = new MuseumAgentClient({
  serverUrl: 'wss://your-server.com'
});
```

---

## 🔄 工作流程

### 场景 1：开发 SDK

```bash
# 1. 进入 SDK 目录
cd client/sdk

# 2. 修改源码
vim src/managers/SessionManager.js

# 3. 构建
npm run build

# 4. 复制到 Demo（自动化脚本）
cp dist/museum-agent-sdk.min.js ../web/Demo/lib/
cp dist/museum-agent-sdk.min.js.map ../web/Demo/lib/

# 5. 测试 Demo
cd ../web/Demo
python ssl_server.py
```

### 场景 2：开发 Demo

```bash
# 1. 确保 SDK 已构建
cd client/sdk
npm run build

# 2. 复制到 Demo
cp dist/museum-agent-sdk.min.js ../web/Demo/lib/

# 3. 开发 Demo
cd ../web/Demo
vim src/components/NewComponent.js

# 4. 测试
python ssl_server.py
```

### 场景 3：发布 SDK

```bash
# 1. 更新版本
cd client/sdk
npm version patch  # 2.0.0 -> 2.0.1

# 2. 构建
npm run build

# 3. 发布到 NPM
npm publish

# 4. Demo 更新 SDK
# 方式 A：从 NPM 下载
npm install museum-agent-client-sdk@latest
cp node_modules/museum-agent-client-sdk/dist/museum-agent-sdk.min.js ../web/Demo/lib/

# 方式 B：从 CDN 引用
# 修改 Demo 的 index.html
<script src="https://unpkg.com/museum-agent-client-sdk@2.0.1/dist/museum-agent-sdk.min.js"></script>
```

---

## 📋 自动化脚本

### 创建 SDK 更新脚本

**client/sdk/update-demo.bat**
```batch
@echo off
echo 正在构建 SDK...
call npm run build

echo 正在复制到 Demo...
copy /Y dist\museum-agent-sdk.min.js ..\web\Demo\lib\museum-agent-sdk.min.js
copy /Y dist\museum-agent-sdk.min.js.map ..\web\Demo\lib\museum-agent-sdk.min.js.map

echo SDK 已更新到 Demo！
pause
```

**使用方法：**
```bash
cd client/sdk
update-demo.bat
```

---

## 🎯 优势对比

| 特性 | 旧结构（耦合） | 新结构（分离） |
|-----|-------------|-------------|
| SDK 独立性 | ❌ 与 Demo 耦合 | ✅ 完全独立 |
| Demo 体积 | 大（所有源码） | 小（单个文件 34KB） |
| 开发效率 | 中等 | 高（各自独立） |
| 部署便利性 | 复杂 | 简单 |
| 可维护性 | 中等 | 优秀 |
| 可扩展性 | 受限 | 优秀 |
| NPM 发布 | 困难 | 容易 |
| CDN 支持 | ❌ | ✅ |

---

## 📖 文档位置

### SDK 文档
- **API 文档**：`client/sdk/README.md`
- **构建指南**：`client/sdk/BUILD.md`
- **更新日志**：`client/sdk/CHANGELOG.md`

### Demo 文档
- **使用说明**：`client/web/Demo/README.md`
- **项目结构**：本文档

---

## 🚀 快速开始

### 首次设置

```bash
# 1. 安装 SDK 依赖
cd client/sdk
npm install

# 2. 构建 SDK
npm run build

# 3. 复制到 Demo
cp dist/museum-agent-sdk.min.js ../web/Demo/lib/
cp dist/museum-agent-sdk.min.js.map ../web/Demo/lib/

# 4. 启动 Demo
cd ../web/Demo
python ssl_server.py

# 5. 访问
# https://localhost:8443
```

### 日常开发

**开发 SDK：**
```bash
cd client/sdk
npm run dev  # 监视模式
# 修改源码后自动构建
```

**开发 Demo：**
```bash
cd client/web/Demo
python ssl_server.py
# 修改应用代码后刷新浏览器
```

---

## 💡 最佳实践

### 1. SDK 版本管理

使用语义化版本：
- **Patch（2.0.0 -> 2.0.1）**：Bug 修复
- **Minor（2.0.1 -> 2.1.0）**：新功能（向后兼容）
- **Major（2.1.0 -> 3.0.0）**：破坏性变更

### 2. Demo 更新 SDK

**开发阶段：**
- 手动复制构建产物
- 使用自动化脚本

**生产阶段：**
- 从 NPM 安装
- 从 CDN 引用

### 3. Git 管理

**选项 A：单仓库（当前）**
```
MuseumAgent_Server/
├── client/sdk/
└── client/web/Demo/
```

**选项 B：多仓库（推荐长期）**
```
museum-agent-sdk/          # SDK 独立仓库
museum-agent-demo/         # Demo 独立仓库
```

---

## 🎉 总结

**新结构的核心优势：**

1. ✅ **SDK 完全独立**：可以独立开发、测试、发布
2. ✅ **Demo 轻量化**：只包含一个 SDK 文件（34KB）
3. ✅ **开发效率高**：各自独立，互不干扰
4. ✅ **部署简单**：Demo 可以直接部署，无需构建
5. ✅ **易于维护**：职责清晰，代码分离
6. ✅ **可扩展性强**：可以创建多个 Demo 项目

**下一步：**
- 创建自动化更新脚本
- 考虑发布 SDK 到 NPM
- 创建更多示例项目

