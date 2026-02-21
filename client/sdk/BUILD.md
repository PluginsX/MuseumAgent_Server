# MuseumAgent Client SDK - 构建指南

## 📦 构建步骤

### 1. 安装依赖

```bash
npm install
```

### 2. 开发模式（监视文件变化）

```bash
npm run dev
# 或
npm run watch
```

### 3. 生产构建

```bash
npm run build
```

### 4. 代码检查

```bash
npm run lint
```

### 5. 代码格式化

```bash
npm run format
```

## 📁 构建产物

构建后会在 `dist/` 目录生成以下文件：

```
dist/
├── museum-agent-sdk.js           # UMD 未压缩（调试用）
├── museum-agent-sdk.js.map       # Source Map
├── museum-agent-sdk.min.js       # UMD 压缩（生产用）
├── museum-agent-sdk.min.js.map   # Source Map
├── museum-agent-sdk.esm.js       # ESM 未压缩
├── museum-agent-sdk.esm.js.map   # Source Map
├── museum-agent-sdk.esm.min.js   # ESM 压缩
└── museum-agent-sdk.esm.min.js.map # Source Map
```

## 🚀 使用方式

### 浏览器直接引入（UMD）

```html
<!-- CDN 引入 -->
<script src="https://unpkg.com/museum-agent-client-sdk@2.0.0/dist/museum-agent-sdk.min.js"></script>

<script>
  const { MuseumAgentClient, Events } = MuseumAgentSDK;
  
  const client = new MuseumAgentClient({
    serverUrl: 'wss://example.com'
  });
</script>
```

### ES 模块引入

```javascript
import { MuseumAgentClient, Events } from 'museum-agent-client-sdk';

const client = new MuseumAgentClient({
  serverUrl: 'wss://example.com'
});
```

### 按需引入（Tree-shaking）

```javascript
// 只引入需要的工具函数
import { setStorage, getStorage } from 'museum-agent-client-sdk';
import { encryptData, decryptData } from 'museum-agent-client-sdk';
```

## 📝 注意事项

1. **开发时使用源码**：在开发 Demo 时，直接引入 `lib/index.js`，无需构建
2. **发布时使用构建产物**：发布到 NPM 或 CDN 时，使用 `dist/` 目录的文件
3. **Source Map**：构建产物包含 Source Map，便于调试
4. **Tree-shaking**：使用 ESM 版本可以实现按需引入，减小最终包体积

## 🔧 开发工作流

```bash
# 1. 修改源码（lib/ 目录）
# 2. 运行开发模式
npm run dev

# 3. 在 Demo 中测试（直接引入 lib/index.js）
# 4. 代码检查和格式化
npm run lint
npm run format

# 5. 生产构建
npm run build

# 6. 测试构建产物
# 7. 发布到 NPM
npm publish
```

