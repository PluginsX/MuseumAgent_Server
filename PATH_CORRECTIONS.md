# 路径更正说明

## 📋 更正内容

根据实际部署需求，已更正所有文档中的路径信息。

---

## 🗂️ 正确的服务器路径

### 1. 后端服务

| 服务 | 服务器路径 | 监听地址 | 外部访问 |
|------|-----------|---------|---------|
| **智能体服务端** | `/opt/MuseumAgent_Server` | `0.0.0.0:12301` | `https://www.soulflaw.com/mas/` |
| **SRS 语义检索系统** | `/opt/SemanticRetrievalSystem` | `0.0.0.0:12315` | `https://www.soulflaw.com/srs/` |

### 2. 前端服务（静态文件）

| 服务 | 服务器路径 | 外部访问 |
|------|-----------|---------|
| **智能体客户端** | `/www/wwwroot/MuseumAgent_Client` | `https://www.soulflaw.com/` |
| **Unity Addressables 资源** | `/www/wwwroot/MuseumAgent_Client/unity/ServerData/` | `https://www.soulflaw.com/unity/ServerData/` |
| **控制面板** | `/www/wwwroot/MuseumAgent_Client/control-panel/dist/` | `https://www.soulflaw.com/Control/` |

---

## 🔄 主要更正

### 更正 1：后端服务路径

```diff
- /www/wwwroot/MuseumAgent_Server
+ /opt/MuseumAgent_Server
```

**原因**：后端服务不对外直接提供静态文件访问，应部署在 `/opt/` 目录

### 更正 2：客户端路径

```diff
- /www/wwwroot/MuseumAgent_Client/Demo
+ /www/wwwroot/MuseumAgent_Client
```

**原因**：
- "Demo" 是临时名称，正式名称是 "MuseumAgent_Client"
- 客户端直接部署在 `/www/wwwroot/MuseumAgent_Client/` 根目录
- 已在本地将 `client/web/Demo` 重命名为 `client/web/MuseumAgent_Client`

### 更正 3：SRS 服务配置

```diff
# config/config.json
"semantic_retrieval": {
-   "base_url": "http://localhost:12315/api/v1",
+   "base_url": "http://127.0.0.1:12315/api/v1",
}
```

**原因**：使用 `127.0.0.1` 更明确表示本地回环地址

### 更正 4：systemd 服务监听地址

```diff
[Service]
- ExecStart=/opt/MuseumAgent_Server/venv/bin/python main.py --host 127.0.0.1 --port 12301
+ ExecStart=/opt/MuseumAgent_Server/venv/bin/python main.py --host 0.0.0.0 --port 12301
```

**原因**：
- 服务需要监听 `0.0.0.0` 以接受来自 Nginx 的代理请求
- Nginx 通过 `127.0.0.1:12301` 访问后端
- 防火墙已配置，外部无法直接访问 12301 端口

---

## 📂 完整目录结构

### 服务器部署结构

```
/opt/
├── MuseumAgent_Server/              # 智能体服务端
│   ├── venv/                        # Python 虚拟环境
│   ├── config/
│   │   └── config.json              # 配置文件
│   ├── src/                         # 源代码
│   ├── data/                        # 数据库
│   ├── logs/                        # 日志
│   └── main.py                      # 入口文件
│
└── SemanticRetrievalSystem/         # SRS 语义检索系统
    └── ...

/www/wwwroot/
└── MuseumAgent_Client/              # 客户端静态文件（根目录）
    ├── index.html                   # 客户端入口
    ├── src/                         # 客户端源码
    ├── lib/                         # SDK 库
    ├── unity/                       # Unity WebGL
    │   ├── Build/                   # Unity 构建文件
    │   └── ServerData/              # Addressables 资源
    │       └── WebGL/
    │           ├── *.bundle         # AssetBundle 文件
    │           └── catalog.json     # 资源目录
    └── control-panel/               # 控制面板
        └── dist/                    # 构建产物
            └── index.html

/etc/systemd/system/
└── museum-agent.service             # systemd 服务配置

/www/server/panel/vhost/nginx/
└── html_www.soulflaw.com.conf       # Nginx 站点配置

/www/wwwlogs/
├── www.soulflaw.com.log             # Nginx 访问日志
└── www.soulflaw.com.error.log       # Nginx 错误日志

/www/backup/                         # 备份目录
```

---

## ✅ 已更新的文件

| 文件 | 更新内容 |
|------|---------|
| `config/config.json` | SRS 服务地址改为 `127.0.0.1:12315` |
| `server/nginx/html_www.soulflaw.com.conf` | 所有路径已更正 |
| `UpGrade.md` | 所有路径和部署步骤已更正 |
| `DEPLOYMENT_SUMMARY.md` | 路径信息已更正 |
| `DEPLOYMENT_COMPLETE.md` | 路径信息已更正 |
| `UNITY_ADDRESSABLES_CONFIG.md` | 路径信息已更正 |
| `client/web/Demo` → `client/web/MuseumAgent_Client` | 文件夹已重命名 |

---

## 🚀 部署命令（已更正）

### 1. 创建目录

```bash
# 后端服务目录
sudo mkdir -p /opt/MuseumAgent_Server
sudo mkdir -p /opt/SemanticRetrievalSystem

# 前端静态文件目录
sudo mkdir -p /www/wwwroot/MuseumAgent_Client
sudo mkdir -p /www/wwwroot/MuseumAgent_Client/control-panel

# 设置权限
sudo chown -R www:www /opt/MuseumAgent_Server
sudo chown -R www:www /opt/SemanticRetrievalSystem
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client
```

### 2. 部署后端服务

```bash
# 上传代码到 /opt/MuseumAgent_Server
cd /opt/MuseumAgent_Server
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置 systemd 服务
sudo systemctl enable museum-agent
sudo systemctl start museum-agent
```

### 3. 部署前端服务

```bash
# 上传客户端文件到 /www/wwwroot/MuseumAgent_Client
# 包括：index.html, src/, lib/, unity/ 等

# 构建并上传控制面板
cd control-panel
npm run build
sudo cp -r dist /www/wwwroot/MuseumAgent_Client/control-panel/

# 设置权限
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client
```

### 4. 验证部署

```bash
# 检查后端服务
curl http://127.0.0.1:12301/health
curl https://www.soulflaw.com/mas/health

# 检查 SRS 服务
curl http://127.0.0.1:12315/api/v1/health
curl https://www.soulflaw.com/srs/health

# 检查 Unity 资源
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json

# 检查客户端
curl -I https://www.soulflaw.com/

# 检查控制面板
curl -I https://www.soulflaw.com/Control/
```

---

## 📝 systemd 服务配置（已更正）

**文件**：`/etc/systemd/system/museum-agent.service`

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

**关键点**：
- `WorkingDirectory=/opt/MuseumAgent_Server`
- `--host 0.0.0.0` （监听所有接口，但防火墙限制外部访问）
- `--port 12301`

---

## 🔒 安全配置

### 防火墙规则

```bash
# 仅开放必要端口
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS

# 拒绝直接访问后端端口
sudo ufw deny 12301/tcp   # 智能体服务端口
sudo ufw deny 12315/tcp   # SRS 服务端口

# 启用防火墙
sudo ufw enable
```

### Nginx 代理配置

```nginx
# 智能体服务代理
location /mas/ {
    proxy_pass http://127.0.0.1:12301/;  # 通过本地回环访问
    # ... 其他配置
}

# SRS 服务代理
location /srs/ {
    proxy_pass http://127.0.0.1:12315/;  # 通过本地回环访问
    # ... 其他配置
}
```

**安全原理**：
- 后端服务监听 `0.0.0.0:12301`，但防火墙阻止外部访问
- Nginx 通过 `127.0.0.1:12301` 访问后端（本地回环，不受防火墙限制）
- 外部只能通过 Nginx 代理访问（`https://www.soulflaw.com/mas/`）

---

## ✨ 总结

所有路径已更正为实际部署路径：

✅ 后端服务：`/opt/MuseumAgent_Server`  
✅ SRS 服务：`/opt/SemanticRetrievalSystem`  
✅ 客户端：`/www/wwwroot/MuseumAgent_Client`  
✅ Unity 资源：`/www/wwwroot/MuseumAgent_Client/unity/ServerData/`  
✅ 控制面板：`/www/wwwroot/MuseumAgent_Client/control-panel/dist/`  
✅ SRS 配置：`http://127.0.0.1:12315/api/v1`  
✅ 监听地址：`0.0.0.0:12301`（配合防火墙使用）  

现在所有文档和配置都已同步更新，可以直接按照文档部署！

---

**更新时间**：2026-03-09  
**更新者**：Kiro AI Assistant

