# MuseumAgent SDK V2.0 更新日志

## [2.0.0] - 2024-12-XX

### 🎉 重大更新

#### 新增功能
- ✅ **会话管理**：自动保存和恢复会话，支持加密存储
- ✅ **配置管理**：统一的配置持久化，支持热更新
- ✅ **工具函数库**：存储、安全、错误处理、日志等工具
- ✅ **多格式支持**：UMD、ESM 双格式，支持 Tree-shaking
- ✅ **构建系统**：Rollup 构建，生成压缩和未压缩版本

#### API 新增
- `client.saveSession()` - 保存会话
- `client.reconnectFromSavedSession()` - 从保存的会话恢复
- `client.updateConfig(key, value)` - 更新配置
- `client.updateConfigs(updates)` - 批量更新配置
- `client.resetConfig()` - 重置配置
- `client.disconnect(reason, clearSession)` - 断开连接（支持清除会话）

#### 导出新增
- `SessionManager` - 会话管理器
- `ConfigManager` - 配置管理器
- `setStorage`, `getStorage`, `removeStorage` - 存储工具
- `encryptData`, `decryptData`, `escapeHtml` - 安全工具
- `classifyError`, `formatError` - 错误处理工具
- `setLogLevel`, `debug`, `info`, `warn`, `error` - 日志工具
- `DEFAULT_CONFIG`, `STORAGE_KEYS`, `ERROR_TYPES`, `LOG_LEVELS` - 常量

#### 改进
- 📦 **构建产物**：生成 4 个版本（UMD/ESM × 压缩/未压缩）
- 🔒 **安全性**：会话数据加密存储
- 📝 **日志系统**：可配置的日志级别
- 🎯 **Tree-shaking**：支持按需引入，减小包体积
- 📖 **文档完善**：完整的 API 文档和使用示例

#### 架构优化
- 模块化设计，职责单一
- 纯函数工具，便于优化
- 零循环依赖
- 统一的导出接口

### 🔄 兼容性

- ✅ **向后兼容**：所有现有 API 保持不变
- ✅ **渐进增强**：新功能可选使用
- ✅ **零破坏性变更**：现有代码无需修改

### 📦 构建

```bash
npm install
npm run build
```

### 🚀 使用

#### 浏览器直接引入
```html
<script src="https://unpkg.com/museum-agent-client-sdk@2.0.0/dist/museum-agent-sdk.min.js"></script>
```

#### ES 模块引入
```javascript
import { MuseumAgentClient, Events } from 'museum-agent-client-sdk';
```

#### 按需引入
```javascript
import { setStorage, getStorage } from 'museum-agent-client-sdk';
```

---

## [1.0.0] - 2024-XX-XX

### 初始版本

- WebSocket 全双工通信
- 音频录制和播放
- VAD 语音检测
- 流式文本和语音响应
- 函数调用支持
- 打断机制
