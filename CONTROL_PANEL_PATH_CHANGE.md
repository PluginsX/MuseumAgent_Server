# 🔄 控制面板路径变更说明

## 📋 变更内容

根据你的需求，已将控制面板的访问路径从 `/Control/` 改为 `/mas/`。

---

## 🎯 新的访问路径

### 控制面板
- **旧路径**：`https://www.soulflaw.com/Control/`
- **新路径**：`https://www.soulflaw.com/mas/` ✅
- **说明**：现在直接访问 `/mas` 即可看到控制面板登录页面

### 智能体客户端服务
- **WebSocket**：`wss://www.soulflaw.com/agent/ws/`
- **API**：`https://www.soulflaw.com/agent/api/`
- **说明**：智能体服务改用独立的 `/agent/` 路径

### 其他服务（保持不变）
- **客户端页面**：`https://www.soulflaw.com/`
- **Unity 资源**：`https://www.soulflaw.com/unity/ServerData/`
- **SRS 服务**：`https://www.soulflaw.com/srs/`

---

## ✅ 已修改的文件

### 1. Nginx 配置
**文件**：`server/nginx/html_www.soulflaw.com.conf`

**主要变更**：
```nginx
# 控制面板现在通过 /mas/ 访问
location /mas/ {
    alias /www/wwwroot/MuseumAgent_Client/control-panel/dist/;
    try_files $uri $uri/ /mas/index.html;
}

# 控制面板 API
location /mas/api/ {
    proxy_pass http://127.0.0.1:12301/api/;
}

# 智能体客户端服务改用 /agent/ 路径
location /agent/ws/ {
    proxy_pass http://127.0.0.1:12301/ws/;
    # WebSocket 配置...
}

location /agent/api/ {
    proxy_pass http://127.0.0.1:12301/api/;
}

# 旧路径重定向（兼容性）
location /Control/ {
    return 301 /mas/;
}
```

### 2. 控制面板配置
**文件**：`control-panel/vite.config.ts`
```typescript
base: '/mas/',  // 从 /Control/ 改为 /mas/
```

**文件**：`control-panel/src/utils/request.ts`
```typescript
baseURL: import.meta.env.VITE_API_BASE_URL || '/mas',  // 从 /Control 改为 /mas
```

**文件**：`control-panel/.env.production`
```env
VITE_API_BASE_URL=/mas
```

### 3. 客户端配置
**文件**：`client/web/MuseumAgent_Client/src/app.js`
```javascript
function getAgentServerUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/agent/`;  // 从 /mas/ 改为 /agent/
}
```

---

## 🔑 Nginx 配置优先级

```
优先级从高到低：
1. /unity/ServerData/          → Unity Addressables 资源
2. /mas/api/                   → 控制面板 API（代理到后端）
3. /mas/internal/              → 控制面板内部 API
4. /mas/ws/                    → 控制面板 WebSocket（如需要）
5. /mas/                       → 控制面板静态文件
6. /agent/ws/                  → 智能体 WebSocket
7. /agent/api/                 → 智能体 API
8. /srs/                       → SRS 服务
9. /Control/                   → 重定向到 /mas/（兼容性）
10. /                          → 客户端静态文件
```

**关键点**：
- API 路径必须在静态文件路径之前配置（优先级更高）
- 这样 `/mas/api/xxx` 会被代理到后端，而不是尝试读取静态文件

---

## 🚀 部署步骤

### 1. 重新构建控制面板

```bash
cd control-panel
npm run build
```

### 2. 上传到服务器

```bash
# 上传新构建的 dist 目录
sudo cp -r dist /www/wwwroot/MuseumAgent_Client/control-panel/
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/control-panel/dist/
```

### 3. 更新 Nginx 配置

```bash
# 将新的配置文件内容复制到服务器
sudo nano /www/server/panel/vhost/nginx/html_www.soulflaw.com.conf

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo nginx -s reload
```

### 4. 更新客户端代码

```bash
# 上传更新后的 app.js
sudo cp client/web/MuseumAgent_Client/src/app.js /www/wwwroot/MuseumAgent_Client/src/
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/
```

---

## ✅ 验证部署

### 1. 验证控制面板

```bash
# 访问控制面板
curl -I https://www.soulflaw.com/mas/

# 应该返回 200 并看到 HTML 内容
```

**浏览器测试**：
1. 访问 `https://www.soulflaw.com/mas/`
2. 应该看到控制面板登录页面
3. 打开开发者工具，检查：
   - 静态资源（JS/CSS）正常加载
   - 路径都是 `/mas/assets/...`
   - 没有 404 错误

### 2. 验证 API 访问

```bash
# 测试登录 API
curl -X POST https://www.soulflaw.com/mas/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# 应该返回 JSON 响应
```

### 3. 验证验证码

**浏览器测试**：
1. 访问 `https://www.soulflaw.com/mas/`
2. 查看登录页面
3. 验证码图片应该正常显示
4. 验证码 API 路径应该是 `/mas/api/auth/captcha` 或类似

### 4. 验证客户端

```bash
# 访问客户端
curl -I https://www.soulflaw.com/

# 应该返回 200
```

**浏览器测试**：
1. 访问 `https://www.soulflaw.com/`
2. 客户端应该正常加载
3. WebSocket 应该连接到 `wss://www.soulflaw.com/agent/ws/...`

### 5. 验证兼容性重定向

```bash
# 访问旧路径
curl -I https://www.soulflaw.com/Control/

# 应该返回 301 重定向到 /mas/
```

---

## 🔍 故障排查

### 问题 1：控制面板 404

**检查**：
```bash
# 检查 dist 目录
ls -la /www/wwwroot/MuseumAgent_Client/control-panel/dist/

# 检查 Nginx 配置
sudo nginx -t

# 查看 Nginx 错误日志
tail -f /www/wwwlogs/www.soulflaw.com.error.log
```

**解决**：
- 确保 dist 目录存在且包含 index.html
- 确保 Nginx 配置中的 alias 路径正确
- 确保文件权限正确（www:www）

### 问题 2：API 请求 404

**检查**：
```bash
# 测试后端服务
curl http://127.0.0.1:12301/api/health

# 查看后端日志
sudo journalctl -u museum-agent -n 50
```

**解决**：
- 确保后端服务正在运行
- 确保 Nginx 的 proxy_pass 配置正确
- 确保 API 路径在静态文件路径之前配置

### 问题 3：验证码不显示

**检查**：
- 打开浏览器开发者工具 -> Network 标签
- 查看验证码请求的 URL
- 检查响应状态码和内容

**解决**：
- 确保验证码 API 路径正确（应该是 `/mas/api/...`）
- 确保后端验证码接口正常工作
- 检查 CORS 配置

### 问题 4：客户端 WebSocket 连接失败

**检查**：
```bash
# 测试 WebSocket
wscat -c wss://www.soulflaw.com/agent/ws/agent/stream
```

**解决**：
- 确保客户端代码已更新（使用 `/agent/` 路径）
- 确保 Nginx WebSocket 配置正确
- 检查防火墙设置

---

## 📊 路径对比表

| 服务 | 旧路径 | 新路径 | 说明 |
|------|--------|--------|------|
| 控制面板 | `/Control/` | `/mas/` | ✅ 已改变 |
| 控制面板 API | `/Control/api/` | `/mas/api/` | ✅ 已改变 |
| 智能体 WebSocket | `/mas/ws/` | `/agent/ws/` | ✅ 已改变 |
| 智能体 API | `/mas/api/` | `/agent/api/` | ✅ 已改变 |
| 客户端页面 | `/` | `/` | ⭕ 不变 |
| Unity 资源 | `/unity/ServerData/` | `/unity/ServerData/` | ⭕ 不变 |
| SRS 服务 | `/srs/` | `/srs/` | ⭕ 不变 |

---

## 🎯 总结

### 主要变更
1. ✅ 控制面板从 `/Control/` 迁移到 `/mas/`
2. ✅ 智能体服务从 `/mas/` 迁移到 `/agent/`
3. ✅ 添加了兼容性重定向（`/Control/` → `/mas/`）
4. ✅ 所有配置文件已更新

### 优势
- ✅ 更简洁的 URL（`/mas` 直接访问控制面板）
- ✅ 清晰的服务分离（控制面板和智能体服务独立）
- ✅ 保持向后兼容（旧路径自动重定向）

### 下一步
1. 重新构建控制面板
2. 部署到服务器
3. 验证所有功能正常

---

**变更时间**：2026-03-09  
**变更者**：Kiro AI Assistant

