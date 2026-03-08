# MuseumAgent 服务端部署升级方案

> 本文档详细规划博物馆智能体服务端从本地开发环境到阿里云生产环境的完整部署方案。

---

## ⚠️ 原方案问题分析与修正

### 🔴 严重问题清单

#### 问题 1：Nginx 前缀处理中间件**完全错误**
**错误原因**：
- Nginx 反向代理 `proxy_pass http://127.0.0.1:12301/` 末尾有 `/`，会**自动移除** `/mas/` 前缀
- 后端收到的请求路径已经是 `/api/xxx` 或 `/ws/xxx`，**不会**包含 `/mas/`
- 添加中间件处理 `/mas/` 前缀是**多余且错误**的，会导致路由匹配失败

**正确理解**：
```
客户端请求：https://www.soulflaw.com/mas/api/health
    ↓
Nginx 接收：/mas/api/health
    ↓
proxy_pass http://127.0.0.1:12301/  （末尾有 /）
    ↓
后端收到：/api/health  （/mas/ 已被 Nginx 移除）
```

#### 问题 2：WebSocket 双路由**完全不必要**
**错误原因**：
- 由于 Nginx 已经移除了 `/mas/` 前缀，后端只需要标准路由 `/ws/agent/stream`
- 创建 `/mas/ws/agent/stream` 路由是**多余的**，永远不会被匹配到
- 增加了代码复杂度，没有任何实际作用

#### 问题 3：控制面板 API 代理路径**错误**
**错误配置**：
```nginx
location /Control/api/ {
    proxy_pass http://127.0.0.1:12301/api/;
}
```
**问题**：控制面板的 API 请求应该直接代理到后端，不需要特殊的 `/Control/api/` 路径

#### 问题 4：本地开发端口**不一致**
- 配置文件中后端端口是 `12301`
- vite.config.ts 中代理目标是 `http://localhost:8001`
- 会导致本地开发时控制面板无法连接后端

---

## 一、项目定位与服务架构

### 1.1 项目核心定位

**MuseumAgent Server** - 博物馆智能体服务端，基于 WebSocket+HTTP 混合协议提供专有增强对话服务。

### 1.2 两大核心服务

#### 1️⃣ 管理员控制面板（`control-panel`）
- **用途**：供管理员配置系统参数、监控运行状态、管理用户会话
- **技术栈**：React + TypeScript + Vite
- **访问方式**：HTTPS Web 页面

#### 2️⃣ 智能体对话服务（`WebSocket + HTTP`）
- **用途**：为客户端（Unity/Web）提供实时智能对话、语音交互、函数调用能力
- **协议规范**：`docs/CommunicationProtocol.md`
- **访问方式**：WebSocket + HTTP API

---

## 二、部署架构设计

### 2.1 部署目标

| 服务 | 访问路径 | 服务器路径 | 端口 | 部署方式 |
|------|----------|------------|------|----------|
| **智能体客户端** | `https://www.soulflaw.com/` | `/www/wwwroot/MuseumAgent_Client` | - | 静态文件（Nginx） |
| **Unity Addressables 资源** | `https://www.soulflaw.com/unity/ServerData/` | `/www/wwwroot/MuseumAgent_Client/unity/ServerData/` | - | 静态文件（Nginx） |
| **管理员控制面板** | `https://www.soulflaw.com/Control/` | `/www/wwwroot/MuseumAgent_Client/control-panel/dist/` | - | 静态文件（Nginx） |
| **智能体服务端** | `https://www.soulflaw.com/mas/` | `/opt/MuseumAgent_Server` | 12301 | 反向代理 |
| **SRS 语义检索系统** | `https://www.soulflaw.com/srs/` | `/opt/SemanticRetrievalSystem` | 12315 | 反向代理 |

### 2.2 架构特点

```
┌──────────────────────────────────────────────────────────────┐
│                      Nginx (443/80)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ /            │  │ /unity/      │  │ /Control/    │      │
│  │ (Demo 静态)   │  │ (Unity资源)   │  │ (控制面板)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ /mas/        │  │ /srs/        │                        │
│  │ (智能体服务)  │  │ (SRS服务)     │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
└─────────┼──────────────────┼───────────────────────────────┘
          │                  │
┌─────────▼─────────┐  ┌─────▼──────────┐
│ FastAPI (12301)   │  │ SRS (12315)    │
│  ┌─────────────┐  │  │                │
│  │ API Gateway │  │  │                │
│  ├─────────────┤  │  │                │
│  │ /api/*      │  │  │                │
│  │ /ws/*       │  │  │                │
│  └─────────────┘  │  │                │
└───────────────────┘  └────────────────┘
```

### 2.3 核心设计原则

✅ **一套代码，多环境运行**：本地开发/生产部署零代码修改  
✅ **Nginx 自动处理路径前缀**：proxy_pass 末尾带 `/` 自动移除前缀  
✅ **协议统一**：WebSocket+HTTP 混合协议，支持流式传输  
✅ **安全隔离**：控制面板与智能体服务独立路径，互不干扰  

---

## 三、服务端代码调整清单

### 3.1 ✅ 无需修改后端代码！

**重要结论**：由于 Nginx 的 `proxy_pass` 配置末尾带 `/`，会自动移除路径前缀，**后端代码完全不需要修改**！

#### 原理说明

```nginx
# Nginx 配置
location /mas/ { 
    proxy_pass http://127.0.0.1:12301/;  # ← 注意末尾的 /
}
```

**路径转换规则**：
```
客户端请求：https://www.soulflaw.com/mas/api/health
    ↓
Nginx 接收：/mas/api/health
    ↓
proxy_pass 处理（末尾有 /）：移除 /mas/，保留 /api/health
    ↓
后端收到：http://127.0.0.1:12301/api/health
```

**结论**：
- ✅ 后端路由保持原样：`/api/*`、`/ws/*`
- ✅ 无需添加任何中间件
- ✅ 无需创建双路由
- ✅ 本地开发和生产环境使用完全相同的代码

---

### 3.2 ✅ 客户端自动推导服务端地址（已完成）

**文件**：`client/web/Demo/src/app.js`

```javascript
/**
 * 自动推导智能体服务端地址
 * 从当前页面 URL 推导出 WebSocket 地址
 * @returns {string} WebSocket 服务端地址
 */
function getAgentServerUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;  // 包含域名和端口
    return `${protocol}//${host}/mas/`;
}
```

**效果**：
- 本地开发：`ws://localhost:端口/mas/` → Nginx 转发到后端
- 生产环境：`wss://www.soulflaw.com/mas/` → Nginx 转发到后端
- 无需硬编码域名，自动适配

---

### 3.3 ⚠️ 需要修改：控制面板 API 基础路径

**问题**：控制面板的 API 请求需要通过 `/Control/api/` 路径访问

**修改文件 1**：`control-panel/src/utils/request.ts`

```typescript
// 修改前
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
});

// 修改后
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/Control',  // ← 添加 /Control 前缀
  timeout: 30000,
});
```

**修改文件 2**：`control-panel/.env.production`（新建）

```env
# 生产环境配置
VITE_API_BASE_URL=/Control
```

**修改文件 3**：`control-panel/.env.development`（新建）

```env
# 本地开发配置（使用 Vite 代理）
VITE_API_BASE_URL=
```

---

### 3.4 ⚠️ 需要修改：本地开发端口统一

**问题**：配置文件中后端端口是 `12301`，但 vite.config.ts 中代理目标是 `8001`

**修改文件**：`control-panel/vite.config.ts`

```typescript
// 修改前
proxy: {
  '/api': { 
    target: 'http://localhost:8001',  // ← 错误端口
    changeOrigin: true,
  }
}

// 修改后
proxy: {
  '/api': { 
    target: 'http://localhost:12301',  // ← 修正为正确端口
    changeOrigin: true,
  },
  '/internal': {
    target: 'http://localhost:12301',
    changeOrigin: true,
  }
}
```

---

### 3.5 📋 代码修改总结

| 文件 | 修改内容 | 必要性 |
|------|----------|--------|
| `src/gateway/api_gateway.py` | ❌ 无需修改 | Nginx 已处理前缀 |
| `src/ws/agent_handler.py` | ❌ 无需修改 | Nginx 已处理前缀 |
| `client/web/Demo/src/app.js` | ✅ 已完成 | 自动推导地址 |
| `control-panel/src/utils/request.ts` | ⚠️ 需修改 | 添加 /Control 前缀 |
| `control-panel/.env.production` | ⚠️ 需新建 | 生产环境配置 |
| `control-panel/.env.development` | ⚠️ 需新建 | 开发环境配置 |
| `control-panel/vite.config.ts` | ⚠️ 需修改 | 修正代理端口 |  

---

## 四、Nginx 配置方案

### 4.1 完整配置文件（已修正）

**文件位置**：`server/nginx/html_www.soulflaw.com.conf`

```nginx
server 
{ 
    listen 80; 
    listen 443 ssl; 
    listen 443 quic; 
    http2 on; 
    server_name www.soulflaw.com; 
    index index.html index.htm default.htm default.html; 
    root /www/wwwroot/MuseumAgent_Client; 
    
    #CERT-APPLY-CHECK--START 
    include /www/server/panel/vhost/nginx/well-known/www.soulflaw.com.conf; 
    #CERT-APPLY-CHECK--END 
    
    #SSL-START SSL相关配置
    #HTTP_TO_HTTPS_START 
    set $isRedcert 1; 
    if ($server_port != 443) { 
        set $isRedcert 2; 
    } 
    if ( $uri ~ /\.well-known/ ) { 
        set $isRedcert 1; 
    } 
    if ($isRedcert != 1) { 
        rewrite ^(/.*)$ https://$host$1 permanent; 
    } 
    #HTTP_TO_HTTPS_END 
    
    ssl_certificate    /www/server/panel/vhost/cert/www.soulflaw.com/fullchain.pem; 
    ssl_certificate_key    /www/server/panel/vhost/cert/www.soulflaw.com/privkey.pem; 
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3; 
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5; 
    ssl_prefer_server_ciphers on; 
    ssl_session_tickets on; 
    ssl_session_cache shared:SSL:10m; 
    ssl_session_timeout 10m; 
    add_header Strict-Transport-Security "max-age=31536000"; 
    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"'; 
    error_page 497 https://$host$request_uri; 
    #SSL-END 
    
    # ========== Unity Addressables 资源服务（优先级最高）==========
    location /unity/ServerData/ {
        alias /www/wwwroot/MuseumAgent_Client/Demo/unity/ServerData/;
        
        # 允许跨域访问（Unity WebGL 必需）
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type";
        
        # 处理 OPTIONS 预检请求
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
        
        # Unity AssetBundle 文件类型
        types {
            application/octet-stream bundle;
            application/json json;
            text/plain hash;
        }
        
        # 长期缓存（AssetBundle 文件名包含哈希值，可以安全缓存）
        expires 365d;
        add_header Cache-Control "public, immutable";
        
        # 禁用访问日志（减少 I/O）
        access_log off;
    }
    
    # ========== 博物馆智能体服务代理（优先级第二）==========
    location /mas/ { 
        # 关键：末尾的 / 会自动移除 /mas/ 前缀
        proxy_pass http://127.0.0.1:12301/; 
        proxy_set_header Host $host; 
        proxy_set_header X-Real-IP $remote_addr; 
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; 
        proxy_set_header X-Forwarded-Proto $scheme; 
        
        # WebSocket 支持（关键配置）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时配置（适当延长以支持长连接）
        proxy_connect_timeout 60s; 
        proxy_read_timeout 300s;  # 延长到 5 分钟
        proxy_send_timeout 300s;  # 延长到 5 分钟
        
        # 禁用缓冲（流式传输必需）
        proxy_buffering off;
    } 

    # ========== 控制面板 API 代理（优先级第三） ==========
    location /Control/api/ {
        # 关键：末尾的 / 会自动移除 /Control 前缀
        proxy_pass http://127.0.0.1:12301/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
    
    # ========== 控制面板内部 API 代理（优先级第四）==========
    location /Control/internal/ {
        proxy_pass http://127.0.0.1:12301/internal/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    # ========== 控制面板静态文件服务（优先级第五）==========
    location /Control/ {
        alias /www/wwwroot/MuseumAgent_Client/control-panel/dist/;
        try_files $uri $uri/ /Control/index.html;
        
        # 静态文件缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 控制面板登录页重定向
    location = /Control/login {
        return 301 /Control/;
    }

    # ========== SRS 语义检索系统代理（优先级第六）==========
    location /srs/ { 
        proxy_pass http://127.0.0.1:12315/; 
        proxy_set_header Host $host; 
        proxy_set_header X-Real-IP $remote_addr; 
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; 
        proxy_set_header X-Forwarded-Proto $scheme; 
        proxy_connect_timeout 60s; 
        proxy_read_timeout 60s; 
        proxy_send_timeout 60s; 
    } 
    
    # ========== 智能体客户端 Demo（静态文件，优先级最低） ==========
    location / {
        root /www/wwwroot/MuseumAgent_Client/Demo;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # 静态文件缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|wasm|data)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    #ERROR-PAGE-START  错误页配置
    #error_page 404 /404.html; 
    #error_page 502 /502.html; 
    #ERROR-PAGE-END 

    #REWRITE-START URL重写规则引用
    include /www/server/panel/vhost/rewrite/html_www.soulflaw.com.conf; 
    #REWRITE-END 

    # 禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md) 
    { 
        return 404; 
    } 

    # SSL 证书验证目录
    location ~ \.well-known{ 
        allow all; 
    } 

    # 禁止在证书验证目录放入敏感文件
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) { 
        return 403; 
    } 

    # 静态资源缓存（全局规则）
    location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$ 
    { 
        expires      30d; 
        error_log /dev/null; 
        access_log /dev/null; 
    } 

    location ~ .*\.(js|css)?$ 
    { 
        expires      12h; 
        error_log /dev/null; 
        access_log /dev/null; 
    } 
    
    access_log  /www/wwwlogs/www.soulflaw.com.log; 
    error_log  /www/wwwlogs/www.soulflaw.com.error.log; 
}
```

### 4.2 配置要点说明

#### 🔑 关键点 1：location 优先级顺序

Nginx 的 location 匹配优先级（从高到低）：
1. `=` 精确匹配
2. `^~` 前缀匹配（不检查正则）
3. `~` 和 `~*` 正则匹配
4. 普通前缀匹配（最长匹配优先）

**本配置的匹配顺序**：
```
/unity/ServerData/    ← 优先级最高（Unity Addressables 资源）
/mas/                 ← 优先级第二（智能体服务）
/Control/api/         ← 优先级第三（控制面板 API）
/Control/internal/    ← 优先级第四（控制面板内部 API）
/Control/             ← 优先级第五（控制面板静态文件）
/srs/                 ← 优先级第六（SRS 服务）
/                     ← 优先级最低（Demo 静态文件）
```

#### 🔑 关键点 2：proxy_pass 末尾的 `/` 作用

```nginx
# 有末尾 /：移除匹配的前缀
location /mas/ {
    proxy_pass http://127.0.0.1:12301/;  # ← 有 /
}
# 请求：/mas/api/health → 转发：/api/health

# 无末尾 /：保留完整路径
location /mas/ {
    proxy_pass http://127.0.0.1:12301;  # ← 无 /
}
# 请求：/mas/api/health → 转发：/mas/api/health
```

**本配置统一使用末尾 `/`，自动移除路径前缀！**

#### 🔑 关键点 3：WebSocket 支持配置

```nginx
proxy_http_version 1.1;                    # 必需：WebSocket 需要 HTTP/1.1
proxy_set_header Upgrade $http_upgrade;    # 必需：升级协议
proxy_set_header Connection "upgrade";     # 必需：保持连接
proxy_buffering off;                       # 推荐：禁用缓冲，支持流式传输
proxy_read_timeout 300s;                   # 推荐：延长超时，支持长连接
```

#### 🔑 关键点 4：Unity Addressables 资源配置

Unity WebGL 使用 Addressables 系统动态加载资源包，需要特殊配置：

```nginx
location /unity/ServerData/ {
    alias /www/wwwroot/MuseumAgent_Client/unity/ServerData/;
    
    # 必需：允许跨域访问
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    
    # 必需：处理 OPTIONS 预检请求
    if ($request_method = 'OPTIONS') {
        return 204;
    }
    
    # 推荐：长期缓存（文件名包含哈希值）
    expires 365d;
    add_header Cache-Control "public, immutable";
}
```

**为什么需要 CORS？**
- Unity WebGL 从不同路径加载资源时，浏览器会进行跨域检查
- 即使是同域名，不同路径也可能触发 CORS 预检
- 必须正确配置 CORS 头，否则资源加载失败

---

## 五、部署步骤详解

### 5.1 服务器环境准备

```bash
# 1. 安装 Python 3.10+
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# 2. 安装 Node.js（用于构建控制面板，可选）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# 3. 安装 Nginx（宝塔面板已自带）
# 通过宝塔面板安装 Nginx

# 4. 创建项目目录
sudo mkdir -p /www/wwwroot/MuseumAgent_Server
sudo mkdir -p /www/wwwroot/MuseumAgent_Client/Demo
sudo mkdir -p /www/wwwroot/MuseumAgent_Client/control-panel

# 5. 设置目录权限
sudo chown -R www:www /www/wwwroot/MuseumAgent_Server
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client
```

---

### 5.2 后端服务部署

```bash
# 1. 上传代码到服务器
# 使用 FTP/SFTP 将整个项目上传到 /opt/MuseumAgent_Server
# 或使用 git clone（推荐）

# 2. 创建虚拟环境
cd /opt/MuseumAgent_Server
python3.10 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 配置数据库（首次部署）
python main.py  # 运行一次初始化数据库
# Ctrl+C 停止

# 5. 创建 systemd 服务文件
sudo nano /etc/systemd/system/museum-agent.service
```

**systemd 服务配置**：

```ini
[Unit]
Description=MuseumAgent Server
After=network.target

[Service]
Type=simple
User=www
Group=www
WorkingDirectory=/opt/MuseumAgent_Server
Environment="PATH=/opt/MuseumAgent_Server/venv/bin"
ExecStart=/opt/MuseumAgent_Server/venv/bin/python main.py --host 0.0.0.0 --port 12301
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 6. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable museum-agent
sudo systemctl start museum-agent

# 7. 检查服务状态
sudo systemctl status museum-agent

# 8. 查看日志
sudo journalctl -u museum-agent -f
```

---

### 5.3 控制面板构建与部署

#### 方式 1：本地构建（推荐）

```bash
# 在本地开发机器上
cd control-panel

# 安装依赖
npm install

# 构建生产版本
npm run build

# 上传 dist 目录到服务器
# 目标路径：/www/wwwroot/MuseumAgent_Client/control-panel/dist/
```

#### 方式 2：服务器构建

```bash
# 在服务器上
cd /www/wwwroot/MuseumAgent_Server/control-panel

# 安装依赖
npm install

# 构建
npm run build

# 复制到部署目录
sudo cp -r dist /www/wwwroot/MuseumAgent_Client/control-panel/
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/control-panel/dist
```

---

### 5.4 客户端 Demo 部署

```bash
# 上传客户端目录到服务器
# 源路径：client/web/MuseumAgent_Client/*
# 目标路径：/www/wwwroot/MuseumAgent_Client/

# 特别注意：确保 Unity Addressables 资源目录完整
# 必须包含：unity/ServerData/ 目录及其所有 .bundle 文件

# 设置权限
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client

# 验证 Unity 资源目录结构
ls -la /www/wwwroot/MuseumAgent_Client/Demo/unity/ServerData/WebGL/
# 应该看到多个 .bundle 文件和 catalog.json
```

**Unity Addressables 目录结构**：
```
MuseumAgent_Client/
├── unity/
│   ├── Build/                    # Unity WebGL 构建文件
│   │   ├── build.data
│   │   ├── build.framework.js
│   │   ├── build.loader.js
│   │   └── build.wasm
│   └── ServerData/               # Addressables 资源（重要！）
│       └── WebGL/
│           ├── *.bundle          # AssetBundle 文件
│           └── catalog.json      # 资源目录
├── control-panel/
│   └── dist/                     # 控制面板构建产物
├── src/
├── lib/
└── index.html
```

---

### 5.5 Nginx 配置

```bash
# 1. 在宝塔面板中创建站点 www.soulflaw.com
#    - 根目录：/www/wwwroot/MuseumAgent_Client
#    - 启用 SSL（Let's Encrypt）

# 2. 编辑站点配置
#    - 在宝塔面板中找到站点配置文件
#    - 将上面的完整 Nginx 配置复制进去

# 3. 测试配置
sudo nginx -t

# 4. 重载 Nginx
sudo systemctl reload nginx
# 或
sudo nginx -s reload
```

---

## 六、本地开发测试

### 6.1 本地运行后端服务

```bash
# 1. 激活虚拟环境
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. 启动服务（使用配置文件中的端口 12301）
python main.py

# 或使用自定义端口
python main.py --host 0.0.0.0 --port 12301
```

**访问测试**：
- 健康检查：`http://localhost:12301/health`
- API 文档：`http://localhost:12301/docs`

---

### 6.2 本地运行控制面板（开发模式）

```bash
cd control-panel

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000/Control/
```

**注意**：
- Vite 开发服务器会自动代理 `/api` 请求到 `http://localhost:12301`
- 确保后端服务已启动

---

### 6.3 本地运行客户端 Demo

#### 方式 1：使用 Python 简易服务器

```bash
cd client/web/Demo

# Python 3
python -m http.server 8080

# 访问 http://localhost:8080/
```

#### 方式 2：使用 ssl_server.py（支持 HTTPS）

```bash
cd client/web/Demo
python ssl_server.py

# 访问 https://localhost:8443/
```

#### 方式 3：使用 Nginx 本地代理（推荐，完全模拟生产环境）

**本地 Nginx 配置**：

```nginx
server {
    listen 80;
    server_name localhost;
    
    # Demo 静态文件
    location / {
        root /path/to/client/web/Demo;
        index index.html;
    }
    
    # 智能体服务代理
    location /mas/ {
        proxy_pass http://127.0.0.1:12301/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 控制面板代理
    location /Control/ {
        proxy_pass http://127.0.0.1:3000/Control/;
    }
}
```

---

### 6.4 本地开发完整流程

```bash
# 终端 1：启动后端服务
cd /path/to/MuseumAgent_Server
source venv/bin/activate
python main.py

# 终端 2：启动控制面板开发服务器
cd /path/to/MuseumAgent_Server/control-panel
npm run dev

# 终端 3：启动 Demo 静态服务器
cd /path/to/MuseumAgent_Server/client/web/Demo
python -m http.server 8080
```

**访问地址**：
- Demo：`http://localhost:8080/`
- 控制面板：`http://localhost:3000/Control/`
- 后端 API：`http://localhost:12301/docs`

---

## 七、配置管理

### 7.1 配置文件说明

**文件**：`config/config.json`

```json
{
  "server": {
    "host": "0.0.0.0",           // 监听地址（生产环境用 0.0.0.0 或 127.0.0.1）
    "port": 12301,               // 服务端口（保持不变）
    "ssl_enabled": false,        // 是否启用 SSL（Nginx 已处理，保持 false）
    "cors_allow_origins": ["*"]  // CORS 配置（生产环境建议限制域名）
  },
  "llm": {
    "api_type": "openai_compatible",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "sk-xxx",         // ⚠️ 生产环境请使用环境变量
    "model": "qwen-max"
  },
  "tts": {
    "base_url": "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
    "api_key": "sk-xxx",         // ⚠️ 生产环境请使用环境变量
    "model": "cosyvoice-v1"
  },
  "stt": {
    "base_url": "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
    "api_key": "sk-xxx",         // ⚠️ 生产环境请使用环境变量
    "model": "paraformer-realtime-v2"
  },
  "semantic_retrieval": {
    "base_url": "http://localhost:12315/api/v1",  // ⚠️ 生产环境改为实际地址
    "timeout": 300
  }
}
```

### 7.2 生产环境配置优化

#### 优化 1：使用环境变量保护敏感信息

**创建环境变量文件**：`/www/wwwroot/MuseumAgent_Server/.env`

```bash
# API 密钥
DASHSCOPE_API_KEY=sk-your-actual-api-key-here

# 数据库配置（如果使用 MySQL）
DB_HOST=localhost
DB_PORT=3306
DB_USER=museum_agent
DB_PASSWORD=your-secure-password

# 管理员密钥
ADMIN_JWT_SECRET=your-random-secret-key-change-in-production
ADMIN_SESSION_SECRET=another-random-secret-key
```

**修改 systemd 服务配置**：

```ini
[Service]
EnvironmentFile=/www/wwwroot/MuseumAgent_Server/.env
```

#### 优化 2：CORS 安全配置

**生产环境配置**：

```json
{
  "server": {
    "cors_allow_origins": [
      "https://www.soulflaw.com",
      "https://soulflaw.com"
    ]
  }
}
```

#### 优化 3：SRS 服务地址配置

**生产环境配置**：

```json
{
  "semantic_retrieval": {
    "base_url": "http://127.0.0.1:12315/api/v1"  // 使用本地回环地址
  }
}
```

### 7.3 配置文件管理策略

```bash
# 1. 创建配置模板
cp config/config.json config/config.example.json

# 2. 将实际配置加入 .gitignore
echo "config/config.json" >> .gitignore
echo ".env" >> .gitignore

# 3. 服务器上使用实际配置
# 首次部署时从模板复制并修改
cp config/config.example.json config/config.json
nano config/config.json  # 修改为实际配置
```

---

## 八、安全加固建议

### 8.1 防火墙配置

```bash
# 1. 启用 UFW 防火墙
sudo ufw enable

# 2. 仅开放必要端口
sudo ufw allow 22/tcp     # SSH（建议修改默认端口）
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS

# 3. 拒绝直接访问后端端口（仅允许本地访问）
sudo ufw deny 12301/tcp   # 智能体服务端口
sudo ufw deny 12315/tcp   # SRS 服务端口

# 4. 查看防火墙状态
sudo ufw status verbose
```

### 8.2 后端服务安全

#### 配置 1：监听地址限制

```json
{
  "server": {
    "host": "127.0.0.1",  // ⚠️ 仅监听本地，不对外暴露
    "port": 12301
  }
}
```

#### 配置 2：限制请求大小

```json
{
  "server": {
    "client_max_body_size": "10M"  // 限制上传文件大小
  }
}
```

### 8.3 Nginx 安全加固

```nginx
# 隐藏 Nginx 版本信息
server_tokens off;

# 防止点击劫持
add_header X-Frame-Options "SAMEORIGIN" always;

# 防止 MIME 类型嗅探
add_header X-Content-Type-Options "nosniff" always;

# XSS 保护
add_header X-XSS-Protection "1; mode=block" always;

# 限制请求方法
if ($request_method !~ ^(GET|POST|PUT|DELETE|OPTIONS)$ ) {
    return 405;
}

# 限制请求速率（防止 DDoS）
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req zone=api_limit burst=20 nodelay;
```

### 8.4 数据库安全

```bash
# 1. 设置强密码
# 2. 限制远程访问（仅本地）
# 3. 定期备份

# SQLite 备份脚本
#!/bin/bash
BACKUP_DIR="/www/backup/museum_agent"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /www/wwwroot/MuseumAgent_Server/data/museum_agent_app.db \
   $BACKUP_DIR/museum_agent_app_$DATE.db
# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

### 8.5 API 密钥管理

```bash
# 1. 使用环境变量存储密钥
# 2. 定期轮换密钥
# 3. 限制 API 调用频率
# 4. 监控异常调用

# 密钥轮换脚本示例
#!/bin/bash
# 1. 生成新密钥
# 2. 更新配置文件
# 3. 重启服务
# 4. 验证服务正常
```

### 8.6 SSL/TLS 配置优化

```nginx
# 使用强加密套件
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers on;

# 启用 HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# 启用 OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
```

---

## 九、监控与日志

### 9.1 日志文件位置

```bash
# Nginx 访问日志
/www/wwwlogs/www.soulflaw.com.log

# Nginx 错误日志
/www/wwwlogs/www.soulflaw.com.error.log

# 应用日志（systemd）
sudo journalctl -u museum-agent -f

# 应用日志（文件）
/www/wwwroot/MuseumAgent_Server/logs/enhanced_museum_agent.log
```

### 9.2 日志查看命令

```bash
# 实时查看 Nginx 访问日志
tail -f /www/wwwlogs/www.soulflaw.com.log

# 实时查看应用日志
sudo journalctl -u museum-agent -f

# 查看最近 100 行日志
sudo journalctl -u museum-agent -n 100

# 查看今天的日志
sudo journalctl -u museum-agent --since today

# 查看错误日志
sudo journalctl -u museum-agent -p err

# 搜索特定关键词
sudo journalctl -u museum-agent | grep "ERROR"
```

### 9.3 健康检查端点

```bash
# 检查后端服务状态
curl http://127.0.0.1:12301/health

# 检查通过 Nginx 代理的服务
curl https://www.soulflaw.com/mas/health

# 检查 WebSocket 连接（使用 wscat）
npm install -g wscat
wscat -c wss://www.soulflaw.com/mas/ws/agent/stream
```

### 9.4 性能监控

#### 监控脚本：`monitor.sh`

```bash
#!/bin/bash
# 博物馆智能体服务监控脚本

LOG_FILE="/var/log/museum-agent-monitor.log"

# 检查服务状态
check_service() {
    if systemctl is-active --quiet museum-agent; then
        echo "[$(date)] ✓ 服务运行正常" >> $LOG_FILE
    else
        echo "[$(date)] ✗ 服务已停止，尝试重启..." >> $LOG_FILE
        systemctl restart museum-agent
    fi
}

# 检查端口监听
check_port() {
    if netstat -tuln | grep -q ":12301"; then
        echo "[$(date)] ✓ 端口 12301 正常监听" >> $LOG_FILE
    else
        echo "[$(date)] ✗ 端口 12301 未监听" >> $LOG_FILE
    fi
}

# 检查内存使用
check_memory() {
    MEM_USAGE=$(ps aux | grep "python main.py" | grep -v grep | awk '{print $4}')
    echo "[$(date)] 内存使用率: $MEM_USAGE%" >> $LOG_FILE
}

# 检查磁盘空间
check_disk() {
    DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}')
    echo "[$(date)] 磁盘使用率: $DISK_USAGE" >> $LOG_FILE
}

# 执行检查
check_service
check_port
check_memory
check_disk

echo "[$(date)] ==================" >> $LOG_FILE
```

#### 设置定时任务

```bash
# 编辑 crontab
crontab -e

# 每 5 分钟执行一次监控
*/5 * * * * /path/to/monitor.sh
```

### 9.5 日志轮转配置

**创建配置文件**：`/etc/logrotate.d/museum-agent`

```
/www/wwwroot/MuseumAgent_Server/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www www
    sharedscripts
    postrotate
        systemctl reload museum-agent > /dev/null 2>&1 || true
    endscript
}
```

---

## 十、故障排查

### 10.1 常见问题诊断

#### 问题 1：WebSocket 连接失败

**现象**：
- 前端报错 `WebSocket connection failed`
- 浏览器控制台显示 `WebSocket is closed before the connection is established`

**排查步骤**：

```bash
# 1. 检查后端服务是否运行
sudo systemctl status museum-agent

# 2. 检查端口是否监听
sudo netstat -tuln | grep 12301

# 3. 检查 Nginx 配置
sudo nginx -t

# 4. 查看 Nginx 错误日志
tail -f /www/wwwlogs/www.soulflaw.com.error.log

# 5. 查看应用日志
sudo journalctl -u museum-agent -n 50

# 6. 测试 WebSocket 连接
wscat -c ws://127.0.0.1:12301/ws/agent/stream
```

**常见原因**：
- ✗ Nginx 未配置 WebSocket 支持（缺少 `Upgrade` 和 `Connection` 头）
- ✗ 后端服务未启动或崩溃
- ✗ 防火墙阻止连接
- ✗ SSL 证书问题（wss 连接）

**解决方案**：
```nginx
# 确保 Nginx 配置包含 WebSocket 支持
location /mas/ {
    proxy_pass http://127.0.0.1:12301/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_buffering off;
}
```

---

#### 问题 2：控制面板 404 或白屏

**现象**：
- 访问 `https://www.soulflaw.com/Control/` 返回 404
- 页面显示白屏，控制台报错 `Failed to load resource`

**排查步骤**：

```bash
# 1. 检查 dist 目录是否存在
ls -la /www/wwwroot/MuseumAgent_Client/control-panel/dist/

# 2. 检查 index.html 是否存在
ls -la /www/wwwroot/MuseumAgent_Client/control-panel/dist/index.html

# 3. 检查文件权限
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/control-panel/dist/

# 4. 检查 Nginx 配置
sudo nginx -t

# 5. 查看 Nginx 错误日志
tail -f /www/wwwlogs/www.soulflaw.com.error.log
```

**常见原因**：
- ✗ dist 目录未上传或路径错误
- ✗ 文件权限不正确
- ✗ Nginx 配置中的 `alias` 路径错误
- ✗ 构建时 `base` 配置错误

**解决方案**：
```bash
# 重新构建控制面板
cd control-panel
npm run build

# 确保 vite.config.ts 中 base 配置正确
# base: '/Control/'

# 上传并设置权限
sudo cp -r dist /www/wwwroot/MuseumAgent_Client/control-panel/
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/control-panel/dist/
```

---

#### 问题 3：API 请求 404

**现象**：
- 控制面板或 Demo 发起的 API 请求返回 404
- 浏览器控制台显示 `GET https://www.soulflaw.com/mas/api/xxx 404`

**排查步骤**：

```bash
# 1. 检查后端服务是否运行
sudo systemctl status museum-agent

# 2. 直接测试后端 API
curl http://127.0.0.1:12301/health

# 3. 通过 Nginx 测试
curl https://www.soulflaw.com/mas/health

# 4. 查看后端日志
sudo journalctl -u museum-agent -n 50

# 5. 检查路由注册
# 访问 http://127.0.0.1:12301/docs 查看 API 文档
```

**常见原因**：
- ✗ 后端路由未正确注册
- ✗ Nginx `proxy_pass` 配置错误
- ✗ 客户端请求路径错误
- ✗ CORS 配置问题

**解决方案**：
```bash
# 检查 Nginx 配置中的 proxy_pass
# 确保末尾有 /
location /mas/ {
    proxy_pass http://127.0.0.1:12301/;  # ← 注意末尾的 /
}

# 重启服务
sudo systemctl restart museum-agent
sudo systemctl reload nginx
```

---

#### 问题 4：控制面板 API 请求失败

**现象**：
- 控制面板登录失败
- API 请求返回 401 或 403

**排查步骤**：

```bash
# 1. 检查控制面板 API 代理配置
# Nginx 配置中应该有：
location /Control/api/ {
    proxy_pass http://127.0.0.1:12301/api/;
}

# 2. 测试 API 连接
curl http://127.0.0.1:12301/api/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# 3. 检查浏览器控制台
# 查看请求的完整 URL 和响应
```

**常见原因**：
- ✗ 控制面板的 `baseURL` 配置错误
- ✗ Nginx 代理路径配置错误
- ✗ 认证 token 过期或无效

**解决方案**：
```typescript
// control-panel/src/utils/request.ts
const request = axios.create({
  baseURL: '/Control',  // ← 确保配置正确
  timeout: 30000,
});
```

---

#### 问题 5：Demo 无法连接智能体服务

**现象**：
- Demo 页面加载正常，但无法连接智能体
- 控制台显示 WebSocket 连接失败

**排查步骤**：

```bash
# 1. 检查 Demo 中的服务端地址推导逻辑
# 打开浏览器控制台，查看实际连接的 URL

# 2. 测试 WebSocket 连接
wscat -c wss://www.soulflaw.com/mas/ws/agent/stream

# 3. 检查 Nginx WebSocket 配置
# 确保包含 Upgrade 和 Connection 头
```

**常见原因**：
- ✗ `getAgentServerUrl()` 函数返回错误的 URL
- ✗ Nginx 未正确配置 WebSocket 支持
- ✗ SSL 证书问题（wss 连接）

**解决方案**：
```javascript
// 确保 app.js 中的地址推导正确
function getAgentServerUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/mas/`;
}
```

---

#### 问题 6：Unity Addressables 资源加载失败

**现象**：
- Unity WebGL 运行正常，但无法加载场景或资源
- 浏览器控制台显示 `Failed to load AssetBundle`
- 控制台显示 CORS 错误：`Access to fetch at 'https://www.soulflaw.com/unity/ServerData/...' has been blocked by CORS policy`

**排查步骤**：

```bash
# 1. 检查资源目录是否存在
ls -la /www/wwwroot/MuseumAgent_Client/unity/ServerData/WebGL/

# 2. 检查文件权限
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/unity/

# 3. 测试资源访问
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json

# 4. 检查 CORS 头
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json | grep -i "access-control"

# 5. 查看 Nginx 错误日志
tail -f /www/wwwlogs/www.soulflaw.com.error.log
```

**常见原因**：
- ✗ 资源目录未上传或路径错误
- ✗ Nginx 未配置 CORS 头
- ✗ 文件权限不正确
- ✗ Nginx 配置中的 `alias` 路径错误

**解决方案**：

```nginx
# 确保 Nginx 配置包含 Unity 资源服务
location /unity/ServerData/ {
    alias /www/wwwroot/MuseumAgent_Client/Demo/unity/ServerData/;
    
    # 必需：CORS 配置
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type";
    
    # 必需：处理 OPTIONS 预检
    if ($request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type";
        add_header Content-Length 0;
        add_header Content-Type text/plain;
        return 204;
    }
}
```

**验证修复**：

```bash
# 1. 重载 Nginx
sudo nginx -s reload

# 2. 测试 CORS 头
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json

# 应该看到：
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, OPTIONS

# 3. 在浏览器中打开 Demo
# 打开开发者工具 -> Network 标签
# 筛选 "bundle" 文件
# 确认所有资源都成功加载（状态码 200）
```

---

#### 问题 7：服务启动失败

**现象**：
- `systemctl start museum-agent` 失败
- 服务状态显示 `failed`

**排查步骤**：

```bash
# 1. 查看详细错误信息
sudo journalctl -u museum-agent -n 50 --no-pager

# 2. 手动启动服务（查看完整错误）
cd /www/wwwroot/MuseumAgent_Server
source venv/bin/activate
python main.py

# 3. 检查依赖是否完整
pip list

# 4. 检查配置文件
cat config/config.json

# 5. 检查文件权限
ls -la /www/wwwroot/MuseumAgent_Server/
```

**常见原因**：
- ✗ Python 依赖缺失
- ✗ 配置文件格式错误
- ✗ 数据库文件权限问题
- ✗ 端口被占用

**解决方案**：
```bash
# 重新安装依赖
pip install -r requirements.txt

# 检查端口占用
sudo netstat -tuln | grep 12301
# 如果被占用，杀死进程
sudo kill -9 $(sudo lsof -t -i:12301)

# 修复文件权限
sudo chown -R www:www /www/wwwroot/MuseumAgent_Server/
```

---

### 10.2 调试技巧

#### 技巧 1：启用详细日志

```python
# main.py 中添加调试模式
python main.py --debug
```

#### 技巧 2：使用浏览器开发者工具

```
1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 筛选 WS（WebSocket）或 XHR（API 请求）
4. 查看请求和响应的详细信息
```

#### 技巧 3：使用 curl 测试 API

```bash
# 测试健康检查
curl -v http://127.0.0.1:12301/health

# 测试登录 API
curl -v -X POST http://127.0.0.1:12301/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# 测试带 token 的 API
curl -v http://127.0.0.1:12301/api/auth/me \
  -H "Authorization: Bearer your-token-here"
```

#### 技巧 4：使用 wscat 测试 WebSocket

```bash
# 安装 wscat
npm install -g wscat

# 测试本地 WebSocket
wscat -c ws://127.0.0.1:12301/ws/agent/stream

# 测试生产环境 WebSocket
wscat -c wss://www.soulflaw.com/mas/ws/agent/stream
```

---

## 十一、性能优化建议

### 11.1 Nginx 性能优化

```nginx
# 工作进程数（根据 CPU 核心数调整）
worker_processes auto;

# 工作进程最大连接数
events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

# 启用 Gzip 压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# 启用 Brotli 压缩（如果已安装）
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# 连接池优化
keepalive_timeout 65;
keepalive_requests 100;

# 缓冲区优化
client_body_buffer_size 128k;
client_max_body_size 10m;
client_header_buffer_size 1k;
large_client_header_buffers 4 4k;

# 代理缓冲优化
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
proxy_busy_buffers_size 8k;

# 静态文件缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
}
```

### 11.2 后端性能优化

#### 优化 1：启用 Uvicorn 多进程

```bash
# 修改 systemd 服务配置
ExecStart=/www/wwwroot/MuseumAgent_Server/venv/bin/uvicorn main:app \
    --host 127.0.0.1 \
    --port 12301 \
    --workers 4 \
    --loop uvloop \
    --log-level warning
```

#### 优化 2：数据库连接池

```python
# 如果使用 MySQL，配置连接池
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
SQLALCHEMY_POOL_RECYCLE = 3600
```

#### 优化 3：启用响应缓存

```python
# 对频繁访问的 API 启用缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def get_config():
    # 缓存配置读取
    pass
```

### 11.3 前端性能优化

#### 优化 1：代码分割

```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
        }
      }
    }
  }
})
```

#### 优化 2：资源压缩

```bash
# 构建时启用压缩
npm run build

# 生成 gzip 文件
find dist -type f \( -name '*.js' -o -name '*.css' -o -name '*.html' \) -exec gzip -k {} \;
```

#### 优化 3：CDN 加速

```html
<!-- 使用 CDN 加载大型库 -->
<script src="https://cdn.jsdelivr.net/npm/react@18/umd/react.production.min.js"></script>
```

### 11.4 WebSocket 性能优化

```nginx
# 增加 WebSocket 超时时间
proxy_read_timeout 300s;
proxy_send_timeout 300s;

# 禁用缓冲（流式传输）
proxy_buffering off;

# 启用 TCP_NODELAY
tcp_nodelay on;
```

### 11.5 数据库性能优化

```bash
# SQLite 优化
# 1. 启用 WAL 模式
sqlite3 museum_agent_app.db "PRAGMA journal_mode=WAL;"

# 2. 增加缓存大小
sqlite3 museum_agent_app.db "PRAGMA cache_size=10000;"

# 3. 定期清理
sqlite3 museum_agent_app.db "VACUUM;"
```

---

## 十二、版本更新流程

### 12.1 更新前准备

```bash
# 1. 备份当前版本
sudo cp -r /www/wwwroot/MuseumAgent_Server /www/wwwroot/MuseumAgent_Server.bak.$(date +%Y%m%d)

# 2. 备份数据库
sudo cp /www/wwwroot/MuseumAgent_Server/data/museum_agent_app.db \
       /www/backup/museum_agent_app.db.$(date +%Y%m%d)

# 3. 备份配置文件
sudo cp /www/wwwroot/MuseumAgent_Server/config/config.json \
       /www/backup/config.json.$(date +%Y%m%d)

# 4. 记录当前版本
cd /www/wwwroot/MuseumAgent_Server
git log -1 > /www/backup/version.$(date +%Y%m%d).txt
```

### 12.2 更新步骤

```bash
# 1. 停止服务
sudo systemctl stop museum-agent

# 2. 拉取最新代码（如果使用 git）
cd /www/wwwroot/MuseumAgent_Server
git pull origin main

# 或上传新版本文件（如果使用 FTP）
# 覆盖旧文件，但保留 config/config.json 和 data/ 目录

# 3. 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 4. 运行数据库迁移（如果有）
python update_db.py

# 5. 重新构建控制面板（如果前端有更新）
cd control-panel
npm install
npm run build
sudo cp -r dist /www/wwwroot/MuseumAgent_Client/control-panel/

# 6. 重启服务
sudo systemctl start museum-agent

# 7. 验证服务状态
sudo systemctl status museum-agent

# 8. 测试关键功能
curl https://www.soulflaw.com/mas/health
```

### 12.3 回滚方案

```bash
# 如果更新后出现问题，立即回滚

# 1. 停止服务
sudo systemctl stop museum-agent

# 2. 恢复备份
sudo rm -rf /www/wwwroot/MuseumAgent_Server
sudo cp -r /www/wwwroot/MuseumAgent_Server.bak.$(date +%Y%m%d) \
       /www/wwwroot/MuseumAgent_Server

# 3. 恢复数据库
sudo cp /www/backup/museum_agent_app.db.$(date +%Y%m%d) \
       /www/wwwroot/MuseumAgent_Server/data/museum_agent_app.db

# 4. 恢复配置
sudo cp /www/backup/config.json.$(date +%Y%m%d) \
       /www/wwwroot/MuseumAgent_Server/config/config.json

# 5. 重启服务
sudo systemctl start museum-agent

# 6. 验证回滚成功
sudo systemctl status museum-agent
curl https://www.soulflaw.com/mas/health
```

### 12.4 灰度发布（可选）

```bash
# 1. 在新端口启动新版本
cd /www/wwwroot/MuseumAgent_Server_v2
python main.py --port 12302

# 2. 配置 Nginx 按比例分流
upstream museum_agent {
    server 127.0.0.1:12301 weight=9;  # 旧版本 90%
    server 127.0.0.1:12302 weight=1;  # 新版本 10%
}

location /mas/ {
    proxy_pass http://museum_agent/;
}

# 3. 观察新版本运行情况
# 如果稳定，逐步增加新版本权重

# 4. 完全切换到新版本
upstream museum_agent {
    server 127.0.0.1:12302;  # 仅使用新版本
}

# 5. 停止旧版本
sudo systemctl stop museum-agent
```

### 12.5 自动化更新脚本

**创建脚本**：`/www/scripts/update_museum_agent.sh`

```bash
#!/bin/bash
# 博物馆智能体自动更新脚本

set -e  # 遇到错误立即退出

PROJECT_DIR="/www/wwwroot/MuseumAgent_Server"
BACKUP_DIR="/www/backup"
DATE=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "博物馆智能体服务更新脚本"
echo "开始时间: $(date)"
echo "=========================================="

# 1. 备份
echo "[1/7] 备份当前版本..."
sudo cp -r $PROJECT_DIR $BACKUP_DIR/MuseumAgent_Server.$DATE
sudo cp $PROJECT_DIR/data/museum_agent_app.db $BACKUP_DIR/museum_agent_app.db.$DATE
echo "✓ 备份完成"

# 2. 停止服务
echo "[2/7] 停止服务..."
sudo systemctl stop museum-agent
echo "✓ 服务已停止"

# 3. 更新代码
echo "[3/7] 更新代码..."
cd $PROJECT_DIR
git pull origin main
echo "✓ 代码已更新"

# 4. 更新依赖
echo "[4/7] 更新依赖..."
source venv/bin/activate
pip install -r requirements.txt --upgrade
echo "✓ 依赖已更新"

# 5. 数据库迁移
echo "[5/7] 数据库迁移..."
if [ -f "update_db.py" ]; then
    python update_db.py
    echo "✓ 数据库迁移完成"
else
    echo "⊘ 无需数据库迁移"
fi

# 6. 启动服务
echo "[6/7] 启动服务..."
sudo systemctl start museum-agent
sleep 5
echo "✓ 服务已启动"

# 7. 验证
echo "[7/7] 验证服务..."
if systemctl is-active --quiet museum-agent; then
    echo "✓ 服务运行正常"
    
    # 测试健康检查
    if curl -s http://127.0.0.1:12301/health > /dev/null; then
        echo "✓ 健康检查通过"
    else
        echo "✗ 健康检查失败"
        exit 1
    fi
else
    echo "✗ 服务启动失败"
    echo "正在回滚..."
    
    # 回滚
    sudo systemctl stop museum-agent
    sudo rm -rf $PROJECT_DIR
    sudo cp -r $BACKUP_DIR/MuseumAgent_Server.$DATE $PROJECT_DIR
    sudo systemctl start museum-agent
    
    echo "✗ 更新失败，已回滚到之前版本"
    exit 1
fi

echo "=========================================="
echo "更新完成！"
echo "结束时间: $(date)"
echo "=========================================="

# 清理旧备份（保留最近 7 天）
find $BACKUP_DIR -name "MuseumAgent_Server.*" -mtime +7 -exec rm -rf {} \;
find $BACKUP_DIR -name "museum_agent_app.db.*" -mtime +7 -delete
```

**使用方法**：

```bash
# 赋予执行权限
sudo chmod +x /www/scripts/update_museum_agent.sh

# 执行更新
sudo /www/scripts/update_museum_agent.sh
```

---

## 十三、总结与检查清单

### 13.1 核心优势

✅ **零代码切换环境**：一套代码同时满足本地开发和生产部署  
✅ **Nginx 自动处理路径前缀**：`proxy_pass` 末尾带 `/` 自动移除前缀，后端无感知  
✅ **协议统一规范**：WebSocket+HTTP 混合协议，支持流式传输  
✅ **安全隔离**：控制面板与智能体服务独立路径，互不干扰  
✅ **自动地址推导**：客户端自动根据当前域名推导服务端地址  

### 13.2 关键技术要点

#### 要点 1：Nginx 路径前缀处理机制

```nginx
# proxy_pass 末尾有 /：自动移除匹配的前缀
location /mas/ {
    proxy_pass http://127.0.0.1:12301/;  # ← 末尾有 /
}
# 请求：/mas/api/health → 转发：/api/health

# proxy_pass 末尾无 /：保留完整路径
location /mas/ {
    proxy_pass http://127.0.0.1:12301;  # ← 末尾无 /
}
# 请求：/mas/api/health → 转发：/mas/api/health
```

**结论**：使用末尾带 `/` 的配置，后端代码完全不需要修改！

#### 要点 2：WebSocket 支持配置

```nginx
# 必需的三个配置
proxy_http_version 1.1;                    # HTTP/1.1 协议
proxy_set_header Upgrade $http_upgrade;    # 升级协议
proxy_set_header Connection "upgrade";     # 保持连接

# 推荐的优化配置
proxy_buffering off;                       # 禁用缓冲
proxy_read_timeout 300s;                   # 延长超时
```

#### 要点 3：客户端自动地址推导

```javascript
// 自动根据当前页面 URL 推导服务端地址
function getAgentServerUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/mas/`;
}
```

**效果**：
- 本地开发：`ws://localhost:8080/mas/`
- 生产环境：`wss://www.soulflaw.com/mas/`

### 13.3 需要修改的文件清单

| 文件 | 修改内容 | 状态 |
|------|----------|------|
| `src/gateway/api_gateway.py` | ❌ 无需修改 | Nginx 已处理 |
| `src/ws/agent_handler.py` | ❌ 无需修改 | Nginx 已处理 |
| `client/web/Demo/src/app.js` | ✅ 已完成 | 自动推导地址 |
| `control-panel/src/utils/request.ts` | ⚠️ 需修改 | 添加 /Control 前缀 |
| `control-panel/.env.production` | ⚠️ 需新建 | 生产环境配置 |
| `control-panel/.env.development` | ⚠️ 需新建 | 开发环境配置 |
| `control-panel/vite.config.ts` | ⚠️ 需修改 | 修正代理端口 |
| `server/nginx/html_www.soulflaw.com.conf` | ⚠️ 需修改 | 完整 Nginx 配置 |

### 13.4 部署前检查清单

#### 服务器环境

- [ ] Python 3.10+ 已安装
- [ ] Nginx 已安装并运行
- [ ] SSL 证书已配置
- [ ] 防火墙已配置（仅开放 22/80/443）
- [ ] 项目目录已创建并设置权限

#### 后端服务

- [ ] 代码已上传到 `/www/wwwroot/MuseumAgent_Server`
- [ ] 虚拟环境已创建
- [ ] 依赖已安装（`pip install -r requirements.txt`）
- [ ] 配置文件已修改（`config/config.json`）
- [ ] 数据库已初始化
- [ ] systemd 服务已配置
- [ ] 服务已启动并运行正常

#### 控制面板

- [ ] 代码已构建（`npm run build`）
- [ ] dist 目录已上传到 `/www/wwwroot/MuseumAgent_Client/control-panel/`
- [ ] 文件权限已设置（`chown -R www:www`）
- [ ] `request.ts` 已修改（baseURL: '/Control'）
- [ ] `.env.production` 已创建
- [ ] vite.config.ts 代理端口已修正

#### 客户端 Demo

- [ ] Demo 文件已上传到 `/www/wwwroot/MuseumAgent_Client/Demo/`
- [ ] Unity Addressables 资源目录完整（`unity/ServerData/`）
- [ ] 所有 .bundle 文件已上传
- [ ] catalog.json 文件存在
- [ ] 文件权限已设置
- [ ] `app.js` 中的地址推导函数已确认

#### Nginx 配置

- [ ] 站点已创建（www.soulflaw.com）
- [ ] 配置文件已更新（包含 Unity 资源配置）
- [ ] 配置测试通过（`nginx -t`）
- [ ] Nginx 已重载（`nginx -s reload`）
- [ ] location 优先级顺序正确

#### 功能测试

- [ ] 后端健康检查：`curl https://www.soulflaw.com/mas/health`
- [ ] 控制面板访问：`https://www.soulflaw.com/Control/`
- [ ] 控制面板登录功能正常
- [ ] Demo 访问：`https://www.soulflaw.com/`
- [ ] Demo WebSocket 连接正常
- [ ] Unity WebGL 加载正常
- [ ] Unity Addressables 资源加载正常（检查 Network 标签）
- [ ] 智能体对话功能正常
- [ ] 语音功能正常（如果启用）

#### 安全检查

- [ ] 后端服务仅监听 127.0.0.1
- [ ] 防火墙已配置，后端端口不对外开放
- [ ] SSL 证书有效
- [ ] CORS 配置正确（Unity 资源允许跨域）
- [ ] API 密钥已使用环境变量
- [ ] 敏感文件已加入 .gitignore

#### 监控与日志

- [ ] 日志轮转已配置
- [ ] 监控脚本已部署（可选）
- [ ] 备份策略已制定
- [ ] 告警机制已配置（可选）

### 13.5 部署后验证

```bash
# 1. 检查服务状态
sudo systemctl status museum-agent

# 2. 检查端口监听
sudo netstat -tuln | grep 12301

# 3. 测试后端健康检查
curl http://127.0.0.1:12301/health
curl https://www.soulflaw.com/mas/health

# 4. 测试 WebSocket 连接
wscat -c wss://www.soulflaw.com/mas/ws/agent/stream

# 5. 测试 Unity Addressables 资源
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json
# 应该看到：
# HTTP/2 200
# Access-Control-Allow-Origin: *

# 6. 访问控制面板
# 浏览器打开：https://www.soulflaw.com/Control/

# 7. 访问 Demo
# 浏览器打开：https://www.soulflaw.com/

# 8. 验证 Unity 资源加载
# 打开浏览器开发者工具 -> Network 标签
# 筛选 "bundle" 文件
# 确认所有 .bundle 文件都成功加载（状态码 200）
# 确认响应头包含 Access-Control-Allow-Origin: *

# 9. 查看日志
sudo journalctl -u museum-agent -n 50
tail -f /www/wwwlogs/www.soulflaw.com.log
```

### 13.6 常见错误总结

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| WebSocket 连接失败 | Nginx 缺少 WebSocket 配置 | 添加 Upgrade 和 Connection 头 |
| 控制面板 404 | dist 目录路径错误 | 检查 alias 路径和文件权限 |
| API 请求 404 | proxy_pass 配置错误 | 确保末尾有 / |
| Unity 资源加载失败 | CORS 配置缺失 | 添加 Access-Control-Allow-Origin 头 |
| AssetBundle 403/404 | 资源目录路径错误 | 检查 alias 路径和文件权限 |
| 服务启动失败 | 依赖缺失或配置错误 | 查看日志，重新安装依赖 |
| CORS 错误 | CORS 配置不正确 | 检查 Nginx 中的 CORS 头配置 |

### 13.7 性能基准

**预期性能指标**：

- 并发连接数：1000+
- WebSocket 延迟：< 100ms
- API 响应时间：< 200ms
- 静态文件加载：< 500ms
- 内存占用：< 500MB
- CPU 占用：< 30%

### 13.8 后续优化方向

1. **高可用部署**：使用 Nginx 负载均衡 + 多实例部署
2. **数据库优化**：迁移到 PostgreSQL 或 MySQL
3. **缓存优化**：引入 Redis 缓存热点数据
4. **CDN 加速**：静态资源使用 CDN 分发
5. **监控告警**：接入 Prometheus + Grafana
6. **日志分析**：使用 ELK 栈分析日志
7. **容器化部署**：使用 Docker + Docker Compose
8. **CI/CD**：自动化构建和部署流程

---

## 十四、快速参考

### 14.1 常用命令

```bash
# 服务管理
sudo systemctl start museum-agent      # 启动服务
sudo systemctl stop museum-agent       # 停止服务
sudo systemctl restart museum-agent    # 重启服务
sudo systemctl status museum-agent     # 查看状态
sudo systemctl enable museum-agent     # 开机自启

# 日志查看
sudo journalctl -u museum-agent -f     # 实时查看日志
sudo journalctl -u museum-agent -n 100 # 查看最近 100 行
tail -f /www/wwwlogs/www.soulflaw.com.log  # Nginx 访问日志

# Nginx 管理
sudo nginx -t                          # 测试配置
sudo nginx -s reload                   # 重载配置
sudo systemctl restart nginx           # 重启 Nginx

# 端口检查
sudo netstat -tuln | grep 12301        # 检查端口监听
sudo lsof -i :12301                    # 查看端口占用

# 进程管理
ps aux | grep python                   # 查看 Python 进程
sudo kill -9 PID                       # 强制杀死进程
```

### 14.2 重要路径

```
# 服务器路径
/opt/MuseumAgent_Server/                      # 智能体服务端
/opt/SemanticRetrievalSystem/                 # SRS 语义检索系统
/www/wwwroot/MuseumAgent_Client/              # 客户端静态文件
/www/wwwroot/MuseumAgent_Client/control-panel/dist/  # 控制面板

# 配置文件
/opt/MuseumAgent_Server/config/config.json    # 应用配置
/etc/systemd/system/museum-agent.service      # 服务配置
/www/server/panel/vhost/nginx/html_www.soulflaw.com.conf  # Nginx 配置

# 日志文件
/www/wwwlogs/www.soulflaw.com.log             # Nginx 访问日志
/www/wwwlogs/www.soulflaw.com.error.log       # Nginx 错误日志
/opt/MuseumAgent_Server/logs/                 # 应用日志

# 备份目录
/www/backup/                                   # 备份文件
```

### 14.3 访问地址

```
# 生产环境
https://www.soulflaw.com/                     # Demo 客户端
https://www.soulflaw.com/unity/ServerData/    # Unity Addressables 资源
https://www.soulflaw.com/Control/             # 控制面板
https://www.soulflaw.com/mas/health           # 健康检查
wss://www.soulflaw.com/mas/ws/agent/stream    # WebSocket

# 本地开发
http://localhost:12301/health                 # 后端健康检查
http://localhost:12301/docs                   # API 文档
http://localhost:3000/Control/                # 控制面板开发服务器
http://localhost:8080/                        # Demo 本地服务器
```

---

**文档版本**：v2.0（已修正原方案的严重错误）  
**最后更新**：2026-03-09  
**维护者**：MuseumAgent Team

---

## 附录：原方案错误分析

### ❌ 错误 1：不必要的 Nginx 前缀处理中间件

**原方案**：在 `api_gateway.py` 中添加中间件处理 `/mas/` 前缀

**错误原因**：
- Nginx 的 `proxy_pass http://127.0.0.1:12301/` 末尾有 `/`，会自动移除 `/mas/` 前缀
- 后端收到的请求路径已经是 `/api/xxx`，不包含 `/mas/`
- 添加中间件是多余的，反而会导致路由匹配失败

**正确做法**：完全不需要修改后端代码，Nginx 已经处理好了！

### ❌ 错误 2：不必要的 WebSocket 双路由

**原方案**：创建 `/ws/agent/stream` 和 `/mas/ws/agent/stream` 两个路由

**错误原因**：
- Nginx 已经移除了 `/mas/` 前缀
- 后端只会收到 `/ws/agent/stream` 请求
- `/mas/ws/agent/stream` 路由永远不会被匹配到

**正确做法**：只需要标准路由 `/ws/agent/stream`！

### ❌ 错误 3：控制面板 API 代理路径错误

**原方案**：`location /Control/api/` 代理到 `http://127.0.0.1:12301/api/`

**问题**：这个配置是正确的，但需要配合前端的 baseURL 配置

**正确做法**：前端 `baseURL: '/Control'`，让请求路径变为 `/Control/api/xxx`

### ❌ 错误 4：本地开发端口不一致

**原方案**：vite.config.ts 代理到 `http://localhost:8001`

**错误原因**：配置文件中后端端口是 `12301`，不是 `8001`

**正确做法**：统一使用 `12301` 端口！
