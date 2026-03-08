# 🔧 Nginx 500 错误修复

## 问题分析

访问 `https://www.soulflaw.com/mas/` 返回 500 错误。

**原因**：Nginx 配置中 `try_files` 路径错误。

当使用 `alias` 指令时，`try_files` 中的路径是相对于 `alias` 指定的目录，不应该包含 location 前缀。

---

## 错误配置

```nginx
location /mas/ {
    alias /www/wwwroot/MuseumAgent_Client/control-panel/dist/;
    try_files $uri $uri/ /mas/index.html;  # ❌ 错误：包含了 /mas/ 前缀
}
```

**问题**：
- `alias` 已经将 `/mas/` 映射到 `/www/wwwroot/MuseumAgent_Client/control-panel/dist/`
- `try_files` 中的 `/mas/index.html` 会被解析为 `/www/wwwroot/MuseumAgent_Client/control-panel/dist/mas/index.html`
- 这个文件不存在，导致 500 错误

---

## 正确配置

```nginx
# API 路径必须在静态文件之前（优先级更高）
location /mas/api/ {
    proxy_pass http://127.0.0.1:12301/api/;
    # ... 其他配置
}

location /mas/internal/ {
    proxy_pass http://127.0.0.1:12301/internal/;
    # ... 其他配置
}

location /mas/ws/ {
    proxy_pass http://127.0.0.1:12301/ws/;
    # ... 其他配置
}

# 静态文件路径必须在最后
location /mas/ {
    alias /www/wwwroot/MuseumAgent_Client/control-panel/dist/;
    index index.html;
    try_files $uri $uri/ /index.html;  # ✅ 正确：不包含 /mas/ 前缀
}
```

**关键点**：
1. `try_files` 改为 `/index.html`（不是 `/mas/index.html`）
2. API 路径必须在静态文件路径之前配置
3. 添加 `index index.html;` 指令

---

## 修复步骤

### 1. 更新服务器上的 Nginx 配置

```bash
# 编辑配置文件
sudo nano /www/server/panel/vhost/nginx/html_www.soulflaw.com.conf
```

**找到 `/mas/` location 块，修改为**：

```nginx
# 控制面板 API 代理（必须在静态文件之前）
location /mas/api/ {
    proxy_pass http://127.0.0.1:12301/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
}

location /mas/internal/ {
    proxy_pass http://127.0.0.1:12301/internal/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
}

location /mas/ws/ {
    proxy_pass http://127.0.0.1:12301/ws/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_connect_timeout 60s;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    proxy_buffering off;
}

# 控制面板静态文件（必须在 API 之后）
location /mas/ {
    alias /www/wwwroot/MuseumAgent_Client/control-panel/dist/;
    index index.html;
    try_files $uri $uri/ /index.html;
}
```

### 2. 测试配置

```bash
sudo nginx -t
```

**应该看到**：
```
nginx: the configuration file /www/server/nginx/conf/nginx.conf syntax is ok
nginx: configuration file /www/server/nginx/conf/nginx.conf test is successful
```

### 3. 重载 Nginx

```bash
sudo nginx -s reload
```

### 4. 验证修复

```bash
# 测试控制面板
curl -I https://www.soulflaw.com/mas/

# 应该返回 200
```

**浏览器测试**：
1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 访问 `https://www.soulflaw.com/mas/`
3. 应该看到控制面板登录页面

---

## 其他可能的问题

### 问题 1：dist 目录不存在或为空

```bash
# 检查目录
ls -la /www/wwwroot/MuseumAgent_Client/control-panel/dist/

# 应该看到 index.html 和 assets/ 目录
```

**解决**：
```bash
# 重新上传 dist 目录
sudo cp -r /path/to/control-panel/dist /www/wwwroot/MuseumAgent_Client/control-panel/
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/control-panel/dist/
```

### 问题 2：文件权限错误

```bash
# 检查权限
ls -la /www/wwwroot/MuseumAgent_Client/control-panel/dist/index.html

# 应该是 www:www
```

**解决**：
```bash
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/control-panel/dist/
sudo chmod -R 755 /www/wwwroot/MuseumAgent_Client/control-panel/dist/
```

### 问题 3：查看 Nginx 错误日志

```bash
# 查看错误日志
tail -f /www/wwwlogs/www.soulflaw.com.error.log

# 或
tail -f /www/server/nginx/logs/error.log
```

---

## 验证清单

- [ ] Nginx 配置已更新
- [ ] `try_files` 改为 `/index.html`
- [ ] API 路径在静态文件路径之前
- [ ] 配置测试通过（`nginx -t`）
- [ ] Nginx 已重载
- [ ] dist 目录存在且包含 index.html
- [ ] 文件权限正确（www:www）
- [ ] 访问 `https://www.soulflaw.com/mas/` 返回 200
- [ ] 可以看到控制面板登录页面

---

## 快速修复命令

```bash
# 1. 备份当前配置
sudo cp /www/server/panel/vhost/nginx/html_www.soulflaw.com.conf /www/backup/html_www.soulflaw.com.conf.bak

# 2. 编辑配置（手动修改 try_files）
sudo nano /www/server/panel/vhost/nginx/html_www.soulflaw.com.conf

# 3. 测试配置
sudo nginx -t

# 4. 重载 Nginx
sudo nginx -s reload

# 5. 验证
curl -I https://www.soulflaw.com/mas/
```

---

**修复时间**：2026-03-09  
**状态**：✅ 配置已修正，等待应用到服务器

