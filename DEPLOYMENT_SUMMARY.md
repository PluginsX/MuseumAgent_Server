# 部署方案修正总结

## 🎯 核心结论

**原方案存在严重错误！已全部修正。**

关键发现：由于 Nginx 的 `proxy_pass` 末尾带 `/`，会**自动移除路径前缀**，因此：

✅ **后端代码完全不需要修改！**  
✅ **不需要添加任何中间件！**  
✅ **不需要创建双路由！**

---

## ❌ 原方案的严重错误

### 错误 1：不必要的 Nginx 前缀处理中间件

**原方案说**：在 `api_gateway.py` 中添加中间件处理 `/mas/` 前缀

**实际情况**：
```nginx
location /mas/ {
    proxy_pass http://127.0.0.1:12301/;  # ← 末尾有 /
}
```

这个配置会自动将 `/mas/api/health` 转换为 `/api/health`，后端根本收不到 `/mas/` 前缀！

**结论**：❌ 添加中间件是**完全错误**的，会导致路由匹配失败！

---

### 错误 2：不必要的 WebSocket 双路由

**原方案说**：创建 `/ws/agent/stream` 和 `/mas/ws/agent/stream` 两个路由

**实际情况**：Nginx 已经移除了 `/mas/` 前缀，后端只会收到 `/ws/agent/stream`

**结论**：❌ `/mas/ws/agent/stream` 路由**永远不会被匹配到**，完全多余！

---

### 错误 3：本地开发端口不一致

**原方案**：vite.config.ts 代理到 `http://localhost:8001`

**实际情况**：配置文件中后端端口是 `12301`

**结论**：❌ 端口错误，本地开发时控制面板无法连接后端！

---

## ✅ 正确的部署方案

### 1. 后端代码：完全不需要修改！

```python
# src/gateway/api_gateway.py
# ❌ 不需要添加任何中间件
# ❌ 不需要处理 /mas/ 前缀
# ✅ 保持原样即可！
```

```python
# src/ws/agent_handler.py
# ❌ 不需要创建双路由
# ✅ 只需要标准路由 /ws/agent/stream
```

---

### 2. 前端代码：仅需修改 3 个文件

#### 修改 1：控制面板 API 基础路径

**文件**：`control-panel/src/utils/request.ts`

```typescript
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/Control',  // ← 修改这里
  timeout: 30000,
});
```

#### 修改 2：控制面板代理端口

**文件**：`control-panel/vite.config.ts`

```typescript
proxy: {
  '/api': { 
    target: 'http://localhost:12301',  // ← 修改为 12301
    changeOrigin: true,
  }
}
```

#### 修改 3：环境变量配置

**文件**：`control-panel/.env.production`（新建）

```env
VITE_API_BASE_URL=/Control
```

**文件**：`control-panel/.env.development`（新建）

```env
VITE_API_BASE_URL=
```

---

### 3. Nginx 配置：关键要点

```nginx
# 关键：proxy_pass 末尾必须有 /
location /mas/ {
    proxy_pass http://127.0.0.1:12301/;  # ← 末尾的 / 很重要！
    
    # WebSocket 支持（必需）
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # 流式传输优化（推荐）
    proxy_buffering off;
    proxy_read_timeout 300s;
}
```

---

## 📋 实际需要修改的文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `src/gateway/api_gateway.py` | ✅ 无需修改 | Nginx 已处理前缀 |
| `src/ws/agent_handler.py` | ✅ 无需修改 | Nginx 已处理前缀 |
| `client/web/Demo/src/app.js` | ✅ 已完成 | 自动推导地址 |
| `control-panel/src/utils/request.ts` | ✅ 已修改 | baseURL: '/Control' |
| `control-panel/vite.config.ts` | ✅ 已修改 | 端口改为 12301 |
| `control-panel/.env.production` | ✅ 已创建 | 生产环境配置 |
| `control-panel/.env.development` | ✅ 已创建 | 开发环境配置 |
| `server/nginx/html_www.soulflaw.com.conf` | ✅ 已更新 | 包含 Unity Addressables 配置 |

---

## 🚀 部署步骤（简化版）

### 步骤 1：准备控制面板

```bash
cd control-panel
npm install
npm run build
# 上传 dist 目录到服务器
```

### 步骤 2：部署后端服务

```bash
# 服务器上
cd /opt/MuseumAgent_Server
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置 systemd 服务
sudo systemctl enable museum-agent
sudo systemctl start museum-agent
```

### 步骤 3：上传 Unity Addressables 资源

```bash
# 确保完整上传 unity/ServerData/ 目录
# 包含所有 .bundle 文件和 catalog.json
```

### 步骤 4：配置 Nginx

```bash
# 在宝塔面板中编辑站点配置
# 复制 server/nginx/html_www.soulflaw.com.conf 的内容
# 注意：包含 Unity Addressables 资源配置
sudo nginx -t
sudo nginx -s reload
```

### 步骤 5：验证部署

```bash
# 测试后端
curl https://www.soulflaw.com/mas/health

# 测试 Unity 资源
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json
# 应该看到：Access-Control-Allow-Origin: *

# 测试控制面板
# 浏览器访问：https://www.soulflaw.com/Control/

# 测试 Demo
# 浏览器访问：https://www.soulflaw.com/
# 打开开发者工具，确认 Unity 资源加载正常
```

---

## 🔑 关键技术原理

### Nginx proxy_pass 路径转换规则

```nginx
# 规则 1：末尾有 / → 移除匹配的前缀
location /mas/ {
    proxy_pass http://127.0.0.1:12301/;
}
# /mas/api/health → /api/health ✅

# 规则 2：末尾无 / → 保留完整路径
location /mas/ {
    proxy_pass http://127.0.0.1:12301;
}
# /mas/api/health → /mas/api/health ❌
```

**我们使用规则 1，所以后端代码完全不需要修改！**

---

## 📊 对比总结

| 项目 | 原方案 | 正确方案 |
|------|--------|----------|
| 后端中间件 | ❌ 需要添加 | ✅ 不需要 |
| WebSocket 路由 | ❌ 需要双路由 | ✅ 单路由即可 |
| 代码修改量 | ❌ 多处修改 | ✅ 仅 3 个文件 |
| 复杂度 | ❌ 高 | ✅ 低 |
| 维护成本 | ❌ 高 | ✅ 低 |

---

## ✨ 最终效果

✅ **一套代码，零修改部署**  
✅ **本地开发和生产环境完全一致**  
✅ **Nginx 自动处理路径前缀**  
✅ **客户端自动推导服务端地址**  
✅ **WebSocket 和 HTTP 完美支持**

---

## 📚 完整文档

- **[UpGrade.md](./UpGrade.md)** - 完整的部署方案（2200+ 行）
- **[UNITY_ADDRESSABLES_CONFIG.md](./UNITY_ADDRESSABLES_CONFIG.md)** - Unity Addressables 资源配置专项文档

---

## 🎮 Unity Addressables 特别说明

本项目包含 Unity WebGL 客户端，使用 Addressables 系统动态加载资源。部署时需要特别注意：

### 关键配置

```nginx
location /unity/ServerData/ {
    alias /www/wwwroot/MuseumAgent_Client/Demo/unity/ServerData/;
    
    # 必需：CORS 配置
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    
    # 必需：OPTIONS 预检处理
    if ($request_method = 'OPTIONS') {
        return 204;
    }
    
    # 推荐：长期缓存
    expires 365d;
}
```

### 验证清单

- [ ] `unity/ServerData/` 目录完整上传
- [ ] 所有 .bundle 文件存在
- [ ] catalog.json 文件存在
- [ ] Nginx 配置包含 CORS 头
- [ ] 浏览器 Network 标签显示资源加载成功（200）
- [ ] 响应头包含 `Access-Control-Allow-Origin: *`

详细说明请查看：[UNITY_ADDRESSABLES_CONFIG.md](./UNITY_ADDRESSABLES_CONFIG.md)

---

**修正完成时间**：2026-03-09  
**修正者**：Kiro AI Assistant

