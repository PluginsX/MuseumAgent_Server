# Unity WebGL 优化部署指南

## 📋 部署前检查清单

### 1. 备份现有配置
```bash
# 备份 Nginx 配置
cd /www/server/panel/vhost/nginx
cp html_www.soulflaw.com.conf html_www.soulflaw.com.conf.backup.$(date +%Y%m%d_%H%M%S)

# 备份服务器配置
cd /opt/MuseumAgent_Server
cp config/config.json config/config.json.backup.$(date +%Y%m%d_%H%M%S)
```

### 2. 检查 Unity 构建文件
```bash
cd /www/wwwroot/MuseumAgent_Client/unity/Build
ls -lh

# 应该看到以下文件：
# - build.loader.js
# - build.framework.js.unityweb
# - build.wasm.unityweb
# - build.data.unityweb
```

### 3. 验证文件压缩格式
```bash
# 检查文件头（Gzip 压缩的魔数是 1f8b）
xxd -l 2 -p build.wasm.unityweb
# 应该输出: 1f8b

# 如果输出是 ceb2，说明是 Brotli 压缩，需要修改 Nginx 配置
```

---

## 🚀 部署步骤

### 步骤1：更新 Nginx 配置

#### 1.1 上传优化后的配置文件
```bash
# 将本地的 html_www.soulflaw.com.conf 上传到服务器
scp server/nginx/html_www.soulflaw.com.conf root@your-server:/www/server/panel/vhost/nginx/
```

#### 1.2 测试 Nginx 配置
```bash
nginx -t

# 应该看到：
# nginx: the configuration file /www/server/nginx/conf/nginx.conf syntax is ok
# nginx: configuration file /www/server/nginx/conf/nginx.conf test is successful
```

#### 1.3 重载 Nginx
```bash
nginx -s reload

# 或使用宝塔面板重启 Nginx
```

---

### 步骤2：更新客户端代码

#### 2.1 重新构建 SDK
```bash
# 在本地开发机器上
cd client/sdk
npm run build

# 检查构建产物
ls -lh dist/
# 应该看到 museum-agent-sdk.min.js
```

#### 2.2 上传更新后的文件
```bash
# 上传 SDK
scp client/sdk/dist/museum-agent-sdk.min.js root@your-server:/www/wwwroot/MuseumAgent_Client/lib/
scp client/sdk/dist/museum-agent-sdk.min.js.map root@your-server:/www/wwwroot/MuseumAgent_Client/lib/

# 上传 UnityContainer.js
scp client/web/MuseumAgent_Client/src/components/UnityContainer.js root@your-server:/www/wwwroot/MuseumAgent_Client/src/components/
```

#### 2.3 检查文件权限
```bash
# 在服务器上执行
chown -R www:www /www/wwwroot/MuseumAgent_Client
chmod -R 755 /www/wwwroot/MuseumAgent_Client
```

---

### 步骤3：更新服务器配置

#### 3.1 确认配置文件
```bash
cat /opt/MuseumAgent_Server/config/config.json | grep -A 10 "session_management"

# 应该看到：
# "session_management": {
#   "session_timeout_minutes": 120,
#   "heartbeat_timeout_minutes": 10,
#   ...
# }
```

#### 3.2 重启服务器（如果需要）
```bash
# 如果修改了 Python 代码，需要重启服务器
cd /opt/MuseumAgent_Server
supervisorctl restart museum_agent

# 或使用宝塔面板重启
```

---

### 步骤4：运行部署检查脚本

```bash
# 上传检查脚本
scp check_deployment.sh root@your-server:/tmp/

# 在服务器上执行
chmod +x /tmp/check_deployment.sh
/tmp/check_deployment.sh

# 检查输出，确保所有检查通过
```

---

## ✅ 验证优化效果

### 1. 清除浏览器缓存
- 打开浏览器开发者工具（F12）
- 右键点击刷新按钮 → 选择"清空缓存并硬性重新加载"

### 2. 检查 Network 标签

#### 2.1 检查 Unity 文件
- 找到 `build.wasm.unityweb`
- 检查响应头：
  - ✅ `Content-Encoding: gzip`
  - ✅ `Cache-Control: public, max-age=31536000, immutable`
  - ✅ `Access-Control-Allow-Origin: *`
- 检查文件大小：应该是压缩后的大小（通常 10-20MB）
- 检查加载时间：应该在 30-60 秒内（取决于网速）

#### 2.2 检查 WebSocket 连接
- 找到 WebSocket 连接（ws:// 或 wss://）
- 检查状态：应该是 `101 Switching Protocols`
- 检查消息：应该能看到心跳消息（HEARTBEAT_REPLY）

### 3. 检查 Console 标签

#### 3.1 Unity 加载日志
```
[UnityContainer] 开始加载 Unity...
[UnityContainer] 发送保活心跳（Unity 加载中）
[UnityContainer] Unity 加载进度: 10%
[UnityContainer] 发送保活心跳（Unity 加载中）
[UnityContainer] Unity 加载进度: 50%
[UnityContainer] 发送保活心跳（Unity 加载中）
[UnityContainer] Unity 加载进度: 100%
[UnityContainer] Unity 加载完成
[UnityContainer] 已停止保活心跳
```

#### 3.2 会话状态
- Unity 加载完成后，不应该看到"会话已过期"的提示
- 应该能正常发送消息和接收回复

---

## 📊 性能对比

### 优化前
| 指标 | 数值 |
|------|------|
| Unity 加载时间 | 3-5 分钟 |
| build.wasm 大小 | 未压缩或压缩失败 |
| 会话状态 | 加载完成后过期 |
| 用户体验 | 极差 |

### 优化后
| 指标 | 数值 |
|------|------|
| Unity 加载时间 | 30-60 秒 |
| build.wasm 大小 | 正确压缩（10-20MB） |
| 会话状态 | 始终有效 |
| 用户体验 | 良好 |

---

## 🔧 故障排查

### 问题1：Unity 文件返回 404
**症状**：浏览器 Console 显示 404 错误

**排查步骤**：
```bash
# 1. 检查文件是否存在
ls -lh /www/wwwroot/MuseumAgent_Client/unity/Build/build.wasm.unityweb

# 2. 检查文件权限
ls -l /www/wwwroot/MuseumAgent_Client/unity/Build/

# 3. 检查 Nginx 配置
grep -A 10 "location.*unity/Build" /www/server/panel/vhost/nginx/html_www.soulflaw.com.conf

# 4. 检查 Nginx 错误日志
tail -f /www/wwwlogs/www.soulflaw.com.error.log
```

**解决方案**：
```bash
# 修复文件权限
chown -R www:www /www/wwwroot/MuseumAgent_Client/unity
chmod -R 755 /www/wwwroot/MuseumAgent_Client/unity
```

---

### 问题2：Unity 文件下载后无法解压
**症状**：浏览器 Console 显示解压错误

**排查步骤**：
```bash
# 1. 检查 Content-Encoding 头
curl -I https://www.soulflaw.com/unity/Build/build.wasm.unityweb | grep Content-Encoding

# 应该看到：Content-Encoding: gzip
```

**解决方案**：
- 确保 Nginx 配置中添加了 `add_header Content-Encoding gzip;`
- 重载 Nginx：`nginx -s reload`

---

### 问题3：会话仍然过期
**症状**：Unity 加载完成后提示"会话已过期"

**排查步骤**：
```bash
# 1. 检查浏览器 Console 是否有心跳日志
# 应该看到：[UnityContainer] 发送保活心跳（Unity 加载中）

# 2. 检查服务器日志
tail -f /opt/MuseumAgent_Server/logs/enhanced_museum_agent.log | grep HEARTBEAT

# 3. 检查 WebSocket 连接状态
# 在浏览器 Network 标签中，找到 WebSocket 连接，检查是否断开
```

**解决方案**：
```bash
# 1. 确认客户端代码已更新
grep -n "keepAliveInterval" /www/wwwroot/MuseumAgent_Client/src/components/UnityContainer.js

# 2. 确认 SDK 已更新
grep -o "heartbeatTimeout.*[0-9]*" /www/wwwroot/MuseumAgent_Client/lib/museum-agent-sdk.min.js

# 3. 清除浏览器缓存并重新加载
```

---

### 问题4：Unity 加载仍然很慢
**症状**：加载时间超过 2 分钟

**排查步骤**：
```bash
# 1. 检查文件大小
du -h /www/wwwroot/MuseumAgent_Client/unity/Build/*.unityweb

# 2. 检查网络速度
# 在浏览器 Network 标签中，查看下载速度

# 3. 检查服务器带宽
iftop -i eth0
```

**解决方案**：
1. **优化 Unity 构建**：
   - 减小纹理质量
   - 使用更高的压缩级别
   - 移除未使用的资源

2. **使用 CDN**：
   - 将 Unity 文件上传到 CDN
   - 修改客户端配置，从 CDN 加载

3. **启用 HTTP/2 服务器推送**：
```nginx
location / {
    http2_push /unity/Build/build.loader.js;
    http2_push /unity/Build/build.framework.js;
}
```

---

## 📈 进一步优化建议

### 1. 使用 CDN
```nginx
# 修改 UnityContainer.js，从 CDN 加载
const buildUrl = 'https://cdn.example.com/unity/Build';
```

### 2. 启用 Service Worker 缓存
```javascript
// 在 index.html 中添加
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
```

### 3. 预加载关键资源
```html
<!-- 在 index.html 中添加 -->
<link rel="preload" href="/unity/Build/build.loader.js" as="script">
<link rel="preload" href="/unity/Build/build.framework.js" as="script">
```

### 4. 使用 Addressables 延迟加载
- 将非必需资源移到 Addressables
- 在 Unity 场景加载完成后再加载

---

## 📞 技术支持

如果遇到问题，请提供以下信息：
1. 浏览器 Console 的完整日志
2. Network 标签的截图
3. 服务器日志：`/opt/MuseumAgent_Server/logs/enhanced_museum_agent.log`
4. Nginx 错误日志：`/www/wwwlogs/www.soulflaw.com.error.log`

---

## ✅ 部署完成检查清单

- [ ] Nginx 配置已更新并重载
- [ ] 客户端 SDK 已重新构建并上传
- [ ] UnityContainer.js 已更新
- [ ] 文件权限已正确设置
- [ ] 部署检查脚本全部通过
- [ ] Unity 文件 Content-Encoding 头正确
- [ ] Unity 加载时间在 1 分钟内
- [ ] 会话在 Unity 加载期间保持有效
- [ ] 用户可以正常使用智能体功能

---

**部署完成！** 🎉

