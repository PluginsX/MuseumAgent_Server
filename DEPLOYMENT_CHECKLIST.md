# 🚀 博物馆智能体服务端部署检查清单

> 本清单用于确保部署过程中的每个步骤都正确完成

---

## 📋 部署前准备

### 服务器环境检查

- [ ] Ubuntu Linux 系统已安装
- [ ] Python 3.10+ 已安装
  ```bash
  python3 --version  # 应显示 3.10 或更高版本
  ```
- [ ] Nginx 已安装并运行
  ```bash
  nginx -v
  systemctl status nginx
  ```
- [ ] 宝塔面板已安装（可选，但推荐）
- [ ] SSL 证书已申请（Let's Encrypt）
- [ ] 域名 www.soulflaw.com 已解析到服务器 IP

### 本地准备

- [ ] 所有代码已提交到 Git（推荐）
- [ ] 控制面板已构建
  ```bash
  cd control-panel
  npm install
  npm run build
  ```
- [ ] 客户端文件已准备完整（包括 Unity 资源）

---

## 📂 第一步：创建目录结构

```bash
# 1. 创建后端服务目录
sudo mkdir -p /opt/MuseumAgent_Server
sudo mkdir -p /opt/SemanticRetrievalSystem

# 2. 创建前端静态文件目录
sudo mkdir -p /www/wwwroot/MuseumAgent_Client
sudo mkdir -p /www/wwwroot/MuseumAgent_Client/control-panel

# 3. 创建备份目录
sudo mkdir -p /www/backup

# 4. 设置目录权限
sudo chown -R www:www /opt/MuseumAgent_Server
sudo chown -R www:www /opt/SemanticRetrievalSystem
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client
```

**检查点**：
- [ ] 所有目录已创建
- [ ] 目录权限正确（所有者为 www:www）

---

## 📤 第二步：上传文件

### 2.1 上传智能体服务端

```bash
# 方式 1：使用 Git（推荐）
cd /opt/MuseumAgent_Server
git clone <your-repo-url> .

# 方式 2：使用 SCP/SFTP
# 将本地项目上传到 /opt/MuseumAgent_Server
```

**检查点**：
- [ ] 所有 Python 代码已上传
- [ ] config/config.json 已上传
- [ ] requirements.txt 已上传
- [ ] main.py 存在

### 2.2 上传客户端文件

```bash
# 上传客户端到 /www/wwwroot/MuseumAgent_Client
# 包括：
# - index.html
# - src/
# - lib/
# - unity/（包含 ServerData/）
```

**检查点**：
- [ ] index.html 已上传
- [ ] src/ 目录已上传
- [ ] lib/ 目录已上传
- [ ] unity/Build/ 已上传
- [ ] unity/ServerData/ 已上传（重要！）
- [ ] unity/ServerData/WebGL/*.bundle 文件存在
- [ ] unity/ServerData/WebGL/catalog.json 存在

### 2.3 上传控制面板

```bash
# 上传控制面板构建产物
sudo cp -r control-panel/dist /www/wwwroot/MuseumAgent_Client/control-panel/
```

**检查点**：
- [ ] control-panel/dist/index.html 存在
- [ ] control-panel/dist/assets/ 目录存在

---

## 🐍 第三步：配置后端服务

### 3.1 创建虚拟环境

```bash
cd /opt/MuseumAgent_Server
python3.10 -m venv venv
source venv/bin/activate
```

**检查点**：
- [ ] venv/ 目录已创建
- [ ] 虚拟环境可以激活

### 3.2 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**检查点**：
- [ ] 所有依赖安装成功
- [ ] 没有错误信息

### 3.3 验证配置文件

```bash
cat config/config.json
```

**检查点**：
- [ ] `server.host` 为 `0.0.0.0`
- [ ] `server.port` 为 `12301`
- [ ] `semantic_retrieval.base_url` 为 `http://127.0.0.1:12315/api/v1`
- [ ] LLM API 密钥已配置
- [ ] TTS API 密钥已配置
- [ ] STT API 密钥已配置

### 3.4 初始化数据库

```bash
python main.py
# 等待看到 "应用初始化完成" 后按 Ctrl+C 停止
```

**检查点**：
- [ ] data/museum_agent_app.db 已创建
- [ ] 默认管理员账户已创建
- [ ] 没有错误信息

---

## ⚙️ 第四步：配置 systemd 服务

### 4.1 创建服务文件

```bash
sudo nano /etc/systemd/system/museum-agent.service
```

**内容**：
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

### 4.2 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable museum-agent
sudo systemctl start museum-agent
```

**检查点**：
- [ ] 服务文件已创建
- [ ] 服务已启用（enable）
- [ ] 服务已启动（start）
- [ ] 服务状态为 active (running)
  ```bash
  sudo systemctl status museum-agent
  ```

---

## 🌐 第五步：配置 Nginx

### 5.1 创建站点配置

在宝塔面板中：
1. 添加站点：www.soulflaw.com
2. 设置根目录：/www/wwwroot/MuseumAgent_Client
3. 申请 SSL 证书（Let's Encrypt）

### 5.2 应用完整配置

```bash
# 编辑站点配置文件
sudo nano /www/server/panel/vhost/nginx/html_www.soulflaw.com.conf
```

**复制 `server/nginx/html_www.soulflaw.com.conf` 的完整内容**

**检查点**：
- [ ] 配置文件已更新
- [ ] 包含 Unity Addressables 配置（/unity/ServerData/）
- [ ] 包含智能体服务代理（/mas/）
- [ ] 包含控制面板配置（/Control/）
- [ ] 包含 SRS 服务代理（/srs/）
- [ ] SSL 证书路径正确

### 5.3 测试并重载配置

```bash
sudo nginx -t
sudo nginx -s reload
```

**检查点**：
- [ ] 配置测试通过（nginx -t 显示 successful）
- [ ] Nginx 已重载
- [ ] 没有错误信息

---

## 🔒 第六步：配置防火墙

```bash
# 1. 启用 UFW
sudo ufw enable

# 2. 开放必要端口
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS

# 3. 拒绝直接访问后端端口
sudo ufw deny 12301/tcp
sudo ufw deny 12315/tcp

# 4. 查看状态
sudo ufw status verbose
```

**检查点**：
- [ ] UFW 已启用
- [ ] 22/80/443 端口已开放
- [ ] 12301/12315 端口已拒绝外部访问
- [ ] 防火墙规则正确

---

## ✅ 第七步：功能验证

### 7.1 后端服务验证

```bash
# 1. 检查服务状态
sudo systemctl status museum-agent

# 2. 检查端口监听
sudo netstat -tuln | grep 12301

# 3. 测试本地健康检查
curl http://127.0.0.1:12301/health

# 4. 测试通过 Nginx 代理
curl https://www.soulflaw.com/mas/health
```

**检查点**：
- [ ] 服务状态为 active (running)
- [ ] 端口 12301 正在监听
- [ ] 本地健康检查返回 200
- [ ] Nginx 代理健康检查返回 200

### 7.2 Unity Addressables 资源验证

```bash
# 1. 测试资源访问
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json

# 2. 检查 CORS 头
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json | grep -i "access-control"
```

**检查点**：
- [ ] catalog.json 返回 200
- [ ] 响应头包含 `Access-Control-Allow-Origin: *`
- [ ] 响应头包含 `Access-Control-Allow-Methods: GET, OPTIONS`

### 7.3 控制面板验证

**浏览器访问**：`https://www.soulflaw.com/Control/`

**检查点**：
- [ ] 页面正常加载
- [ ] 没有 404 错误
- [ ] 静态资源（JS/CSS）正常加载
- [ ] 可以看到登录界面

### 7.4 客户端验证

**浏览器访问**：`https://www.soulflaw.com/`

**检查点**：
- [ ] 页面正常加载
- [ ] Unity WebGL 正常加载
- [ ] 打开开发者工具 -> Network 标签
- [ ] 筛选 "bundle" 文件
- [ ] 所有 .bundle 文件状态码为 200
- [ ] 响应头包含 CORS 头

### 7.5 WebSocket 验证

```bash
# 安装 wscat（如果没有）
npm install -g wscat

# 测试 WebSocket 连接
wscat -c wss://www.soulflaw.com/mas/ws/agent/stream
```

**检查点**：
- [ ] WebSocket 连接成功
- [ ] 没有连接错误

### 7.6 完整功能测试

**在浏览器中**：
1. 访问 `https://www.soulflaw.com/`
2. 登录（使用默认管理员账户）
3. 发送测试消息
4. 验证智能体回复

**检查点**：
- [ ] 登录成功
- [ ] WebSocket 连接正常
- [ ] 可以发送消息
- [ ] 收到智能体回复
- [ ] Unity 场景加载正常
- [ ] 函数调用正常（如果有）

---

## 📊 第八步：监控与日志

### 8.1 查看应用日志

```bash
# 实时查看日志
sudo journalctl -u museum-agent -f

# 查看最近 100 行
sudo journalctl -u museum-agent -n 100

# 查看错误日志
sudo journalctl -u museum-agent -p err
```

### 8.2 查看 Nginx 日志

```bash
# 访问日志
tail -f /www/wwwlogs/www.soulflaw.com.log

# 错误日志
tail -f /www/wwwlogs/www.soulflaw.com.error.log
```

### 8.3 配置日志轮转

```bash
sudo nano /etc/logrotate.d/museum-agent
```

**内容**：
```
/opt/MuseumAgent_Server/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www www
}
```

**检查点**：
- [ ] 可以查看应用日志
- [ ] 可以查看 Nginx 日志
- [ ] 日志轮转已配置

---

## 🔐 第九步：安全加固

### 9.1 修改默认管理员密码

```bash
cd /opt/MuseumAgent_Server
source venv/bin/activate
python scripts/gen_admin_password.py
```

### 9.2 配置环境变量

```bash
sudo nano /opt/MuseumAgent_Server/.env
```

**内容**：
```bash
DASHSCOPE_API_KEY=your-actual-api-key
ADMIN_JWT_SECRET=your-random-secret-key
ADMIN_SESSION_SECRET=another-random-secret-key
```

### 9.3 更新 systemd 服务

```bash
sudo nano /etc/systemd/system/museum-agent.service
```

**添加**：
```ini
EnvironmentFile=/opt/MuseumAgent_Server/.env
```

**重启服务**：
```bash
sudo systemctl daemon-reload
sudo systemctl restart museum-agent
```

**检查点**：
- [ ] 默认密码已修改
- [ ] 环境变量已配置
- [ ] API 密钥已保护
- [ ] 服务重启成功

---

## 💾 第十步：配置备份

### 10.1 创建备份脚本

```bash
sudo nano /www/scripts/backup_museum_agent.sh
```

**内容**：
```bash
#!/bin/bash
BACKUP_DIR="/www/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份代码
sudo cp -r /opt/MuseumAgent_Server $BACKUP_DIR/MuseumAgent_Server.$DATE

# 备份数据库
sudo cp /opt/MuseumAgent_Server/data/museum_agent_app.db $BACKUP_DIR/museum_agent_app.db.$DATE

# 备份配置
sudo cp /opt/MuseumAgent_Server/config/config.json $BACKUP_DIR/config.json.$DATE

# 清理旧备份（保留最近 7 天）
find $BACKUP_DIR -name "MuseumAgent_Server.*" -mtime +7 -exec rm -rf {} \;
find $BACKUP_DIR -name "museum_agent_app.db.*" -mtime +7 -delete
find $BACKUP_DIR -name "config.json.*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 10.2 设置定时备份

```bash
sudo chmod +x /www/scripts/backup_museum_agent.sh
crontab -e
```

**添加**：
```
0 2 * * * /www/scripts/backup_museum_agent.sh
```

**检查点**：
- [ ] 备份脚本已创建
- [ ] 脚本有执行权限
- [ ] 定时任务已配置
- [ ] 手动执行备份成功

---

## 📝 部署完成检查

### 最终验证清单

- [ ] 后端服务运行正常
- [ ] 端口监听正确（12301）
- [ ] Nginx 配置正确
- [ ] SSL 证书有效
- [ ] 防火墙配置正确
- [ ] 客户端访问正常
- [ ] Unity 资源加载正常
- [ ] 控制面板访问正常
- [ ] WebSocket 连接正常
- [ ] 智能体对话功能正常
- [ ] 日志记录正常
- [ ] 备份策略已配置
- [ ] 安全加固已完成

### 性能检查

```bash
# 检查内存使用
free -h

# 检查磁盘空间
df -h

# 检查 CPU 使用
top -bn1 | grep "Cpu(s)"

# 检查进程
ps aux | grep python
```

**检查点**：
- [ ] 内存使用正常（< 80%）
- [ ] 磁盘空间充足（> 20% 可用）
- [ ] CPU 使用正常（< 50%）
- [ ] Python 进程运行正常

---

## 🎉 部署完成！

恭喜！如果所有检查点都已完成，说明部署成功！

### 访问地址

- **客户端**：https://www.soulflaw.com/
- **控制面板**：https://www.soulflaw.com/Control/
- **API 文档**：https://www.soulflaw.com/mas/docs

### 后续维护

1. 定期查看日志
2. 监控服务状态
3. 定期备份数据
4. 及时更新依赖
5. 关注安全公告

### 故障排查

如遇问题，请参考：
- [UpGrade.md](./UpGrade.md) 第十章：故障排查
- [UNITY_ADDRESSABLES_CONFIG.md](./UNITY_ADDRESSABLES_CONFIG.md) 常见问题

---

**检查清单版本**：v1.0  
**最后更新**：2026-03-09  
**适用于**：MuseumAgent Server 生产环境部署

