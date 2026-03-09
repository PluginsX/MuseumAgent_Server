# MuseumAgent 客户端性能优化方案
# 解决 Unity 加载慢和会话过期问题

## 问题诊断总结

### 问题1：Unity 加载缓慢（3-5分钟）
**根本原因**：
1. ✅ Unity 文件已使用 Gzip 压缩（.unityweb 后缀）
2. ❌ Nginx 配置中缺少正确的 Content-Encoding 头
3. ❌ 浏览器无法识别文件已压缩，尝试再次解压导致失败或加载缓慢
4. ❌ 缺少合理的缓存策略

**影响**：
- build.wasm.unityweb：可能 10-20MB（压缩后）
- build.data.unityweb：可能 20-50MB（压缩后）
- 总下载时间：3-5分钟（取决于网速）

### 问题2：Unity 加载期间会话过期
**根本原因**：
1. ✅ Unity 加载阻塞主线程（3-5分钟）
2. ❌ 客户端心跳超时设置过短（2分钟）
3. ❌ Unity 加载期间无法发送心跳回复
4. ❌ 服务器检测到心跳超时，主动释放会话

**影响**：
- Unity 加载完成后提示"会话已过期，请重新登录"
- 用户体验极差

---

## 优化方案

### 方案1：优化 Nginx 配置（关键）

#### 1.1 修改 html_www.soulflaw.com.conf

**优化点**：
1. ✅ 为 .unityweb 文件添加正确的 Content-Encoding: gzip 头
2. ✅ 增加超时时间，支持慢速网络
3. ✅ 优化缓存策略
4. ✅ 增加 WebSocket 心跳超时时间

**修改后的配置**：见下方完整配置文件

#### 1.2 验证 Nginx 主配置

**检查点**：
1. ✅ Gzip 模块已启用
2. ✅ 压缩级别合理（5）
3. ✅ 包含 application/wasm 和 application/octet-stream 类型
4. ⚠️ 建议禁用全局 Gzip 动态压缩（Unity 文件已预压缩）

---

### 方案2：优化客户端代码（已完成）

#### 2.1 UnityContainer.js
✅ 已添加 Unity 加载期间的保活心跳（每30秒）
✅ 已修复 Unity 文件路径（添加 .unityweb 后缀）
✅ 已添加压缩格式配置（compressionFormat: 'gzip'）

#### 2.2 WebSocketClient.js
✅ 已增加心跳超时时间（从 2 分钟增加到 10 分钟）

#### 2.3 strict_session_manager.py
✅ 已修复 is_disconnected() 方法的硬编码超时
✅ 已优化会话清理逻辑，只清理真正过期的会话

---

### 方案3：Unity 构建优化建议

#### 3.1 检查 Unity 构建设置
1. 打开 Unity → File → Build Settings → Player Settings
2. 找到 Publishing Settings
3. 确认以下设置：
   - ✅ Compression Format: Gzip（已确认）
   - ✅ Data caching: 启用
   - ✅ Decompression Fallback: 启用

#### 3.2 减小构建体积
1. 纹理压缩：使用 ASTC 或 ETC2 格式
2. 音频压缩：使用 Vorbis 格式
3. 代码剥离：启用 Managed Stripping Level
4. 使用 Addressables：延迟加载非必需资源

---

## 部署步骤

### 步骤1：备份现有配置
```bash
cd /www/server/panel/vhost/nginx
cp html_www.soulflaw.com.conf html_www.soulflaw.com.conf.backup
```

### 步骤2：更新 Nginx 配置
1. 使用下方优化后的配置替换现有配置
2. 测试配置：`nginx -t`
3. 重载 Nginx：`nginx -s reload`

### 步骤3：重新构建客户端 SDK
```bash
cd /path/to/client/sdk
npm run build
```

### 步骤4：更新客户端代码
```bash
cd /path/to/client/web/MuseumAgent_Client
# 复制更新后的文件到服务器
```

### 步骤5：验证优化效果
1. 清除浏览器缓存
2. 打开开发者工具 → Network 标签
3. 访问客户端页面
4. 检查：
   - Unity 文件的 Content-Encoding 头是否为 gzip
   - 文件大小是否正确（压缩后）
   - 加载时间是否缩短
   - 会话是否保持有效

---

## 预期效果

### 优化前
- Unity 加载时间：3-5 分钟
- 会话状态：加载完成后过期
- 用户体验：极差

### 优化后
- Unity 加载时间：30-60 秒（取决于网速）
- 会话状态：始终有效
- 用户体验：良好

---

## 监控与调试

### 1. 检查 Unity 文件下载
```bash
# 检查文件大小
curl -I https://www.soulflaw.com/unity/Build/build.wasm

# 检查 Content-Encoding 头
curl -I https://www.soulflaw.com/unity/Build/build.wasm | grep Content-Encoding

# 应该看到：Content-Encoding: gzip
```

### 2. 检查 WebSocket 连接
```bash
# 查看 Nginx 日志
tail -f /www/wwwlogs/www.soulflaw.com.log

# 查看服务器日志
tail -f /opt/MuseumAgent_Server/logs/enhanced_museum_agent.log
```

### 3. 浏览器开发者工具
- Network 标签：检查文件大小和加载时间
- Console 标签：检查心跳日志
- Application 标签：检查 localStorage 中的会话数据

---

## 故障排查

### 问题1：Unity 文件返回 404
**原因**：文件路径不正确
**解决**：检查 Nginx alias 路径是否正确

### 问题2：Unity 文件下载后无法解压
**原因**：Content-Encoding 头不正确
**解决**：确保 Nginx 配置中添加了 `add_header Content-Encoding gzip;`

### 问题3：会话仍然过期
**原因**：心跳未正常发送
**解决**：
1. 检查浏览器 Console 是否有心跳日志
2. 检查服务器日志是否收到心跳
3. 确认 WebSocket 连接未断开

### 问题4：Unity 加载仍然很慢
**原因**：网络带宽不足或文件过大
**解决**：
1. 使用 CDN 加速
2. 进一步优化 Unity 构建体积
3. 使用 Addressables 延迟加载

---

## 附加优化建议

### 1. 启用 HTTP/2
```nginx
listen 443 ssl http2;  # 已启用
```

### 2. 启用 QUIC（HTTP/3）
```nginx
listen 443 quic;  # 已启用
```

### 3. 使用 CDN
- 将 Unity Build 文件上传到 CDN
- 修改客户端配置，从 CDN 加载

### 4. 预加载关键资源
```html
<link rel="preload" href="/unity/Build/build.loader.js" as="script">
<link rel="preload" href="/unity/Build/build.framework.js" as="script">
```

### 5. 使用 Service Worker 缓存
```javascript
// 缓存 Unity 文件到本地
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('unity-cache').then((cache) => {
      return cache.addAll([
        '/unity/Build/build.loader.js',
        '/unity/Build/build.framework.js',
        '/unity/Build/build.wasm',
        '/unity/Build/build.data'
      ]);
    })
  );
});
```

---

## 总结

通过以上优化，可以将 Unity 加载时间从 **3-5 分钟** 缩短到 **30-60 秒**，并确保会话在加载期间始终有效。

关键优化点：
1. ✅ Nginx 正确配置 Content-Encoding: gzip
2. ✅ 客户端在 Unity 加载期间保持心跳
3. ✅ 增加心跳超时时间
4. ✅ 优化缓存策略

如有问题，请参考故障排查部分或联系技术支持。

