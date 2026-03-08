# Unity Addressables 资源部署配置

## 📋 概述

本文档说明如何配置 Nginx 以支持 Unity WebGL 项目的 Addressables 资源动态加载。

---

## 🎯 问题背景

Unity WebGL 使用 Addressables 系统动态加载资源包（AssetBundle），这些资源需要通过 HTTP/HTTPS 从服务器下载。由于浏览器的同源策略（CORS），必须正确配置服务器才能成功加载资源。

---

## 📁 资源目录结构

```
MuseumAgent_Client/
├── unity/
│   ├── Build/                    # Unity WebGL 构建文件
│   │   ├── build.data
│   │   ├── build.framework.js
│   │   ├── build.loader.js
│   │   └── build.wasm
│   └── ServerData/               # Addressables 资源（重要！）
│       ├── WebGL/
│       │   ├── *.bundle          # AssetBundle 文件
│       │   ├── catalog.json      # 资源目录
│       │   └── settings.json     # 设置文件
│       └── aa/
│           └── AddressablesLink/
```

---

## 🔧 Nginx 配置

### 完整配置

```nginx
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
```

### 配置说明

#### 1. CORS 配置（必需）

```nginx
add_header Access-Control-Allow-Origin *;
add_header Access-Control-Allow-Methods "GET, OPTIONS";
add_header Access-Control-Allow-Headers "Content-Type";
```

**为什么需要？**
- Unity WebGL 从不同路径加载资源时，浏览器会进行跨域检查
- 即使是同域名，不同路径也可能触发 CORS 预检
- 没有 CORS 头，浏览器会阻止资源加载

#### 2. OPTIONS 预检处理（必需）

```nginx
if ($request_method = 'OPTIONS') {
    return 204;
}
```

**为什么需要？**
- 浏览器在发送实际请求前，会先发送 OPTIONS 请求检查权限
- 必须正确响应 OPTIONS 请求，否则后续请求会被阻止

#### 3. 文件类型配置（推荐）

```nginx
types {
    application/octet-stream bundle;
    application/json json;
    text/plain hash;
}
```

**为什么需要？**
- 确保 AssetBundle 文件以正确的 MIME 类型返回
- Unity 可能根据 Content-Type 判断文件类型

#### 4. 缓存配置（推荐）

```nginx
expires 365d;
add_header Cache-Control "public, immutable";
```

**为什么需要？**
- AssetBundle 文件名包含内容哈希值，内容不变则文件名不变
- 可以安全地长期缓存，减少服务器负载和加载时间

---

## 🚀 部署步骤

### 1. 上传资源文件

```bash
# 确保完整上传 unity/ServerData/ 目录
scp -r client/web/MuseumAgent_Client/unity/ServerData/ \
    user@server:/www/wwwroot/MuseumAgent_Client/unity/
```

### 2. 设置文件权限

```bash
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/unity/
sudo chmod -R 755 /www/wwwroot/MuseumAgent_Client/unity/
```

### 3. 应用 Nginx 配置

```bash
# 编辑站点配置文件
sudo nano /www/server/panel/vhost/nginx/www.soulflaw.com.conf

# 添加上述 location 配置

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo nginx -s reload
```

---

## ✅ 验证部署

### 1. 测试资源访问

```bash
# 测试 catalog.json
curl -I https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json

# 应该看到：
# HTTP/2 200
# Access-Control-Allow-Origin: *
# Content-Type: application/json
```

### 2. 测试 CORS 头

```bash
# 模拟浏览器 OPTIONS 预检请求
curl -X OPTIONS https://www.soulflaw.com/unity/ServerData/WebGL/catalog.json \
  -H "Origin: https://www.soulflaw.com" \
  -H "Access-Control-Request-Method: GET" \
  -v

# 应该看到：
# HTTP/2 204
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, OPTIONS
```

### 3. 浏览器验证

1. 打开 Demo：`https://www.soulflaw.com/`
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 筛选 "bundle" 文件
5. 确认所有 .bundle 文件都成功加载（状态码 200）
6. 点击任意 bundle 文件，查看响应头
7. 确认包含：`Access-Control-Allow-Origin: *`

---

## 🐛 常见问题

### 问题 1：CORS 错误

**现象**：
```
Access to fetch at 'https://www.soulflaw.com/unity/ServerData/...' 
from origin 'https://www.soulflaw.com' has been blocked by CORS policy
```

**解决方案**：
```nginx
# 确保配置了 CORS 头
add_header Access-Control-Allow-Origin *;
add_header Access-Control-Allow-Methods "GET, OPTIONS";
```

### 问题 2：OPTIONS 请求失败

**现象**：
- Network 标签显示 OPTIONS 请求返回 405 或其他错误
- 后续 GET 请求被阻止

**解决方案**：
```nginx
# 添加 OPTIONS 处理
if ($request_method = 'OPTIONS') {
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type";
    return 204;
}
```

### 问题 3：资源 404

**现象**：
- 浏览器控制台显示 404 错误
- 资源路径看起来正确

**解决方案**：
```bash
# 检查文件是否存在
ls -la /www/wwwroot/MuseumAgent_Client/unity/ServerData/WebGL/

# 检查 Nginx 配置中的 alias 路径
# 确保路径末尾有 /
alias /www/wwwroot/MuseumAgent_Client/unity/ServerData/;

# 检查文件权限
sudo chown -R www:www /www/wwwroot/MuseumAgent_Client/unity/
```

### 问题 4：缓存问题

**现象**：
- 更新了资源文件，但浏览器仍加载旧版本

**解决方案**：
```bash
# 方案 1：清除浏览器缓存（Ctrl+Shift+Delete）

# 方案 2：Unity 重新构建 Addressables
# 这会生成新的哈希文件名，自动绕过缓存

# 方案 3：临时禁用缓存（调试用）
# expires off;
# add_header Cache-Control "no-cache, no-store, must-revalidate";
```

---

## 📊 性能优化

### 1. 启用 Gzip 压缩

```nginx
location /unity/ServerData/ {
    # ... 其他配置 ...
    
    # 启用 Gzip（对 JSON 文件有效）
    gzip on;
    gzip_types application/json text/plain;
    gzip_min_length 1024;
}
```

### 2. 启用 HTTP/2

```nginx
# 在 server 块中
listen 443 ssl http2;
```

### 3. 使用 CDN（可选）

如果资源文件较大或访问量大，可以考虑使用 CDN：

1. 将 `unity/ServerData/` 目录上传到 CDN
2. 修改 Unity Addressables 配置中的 Remote Load Path
3. 确保 CDN 配置了正确的 CORS 头

---

## 📝 Unity 项目配置

### Addressables 设置

在 Unity 编辑器中：

1. 打开 Addressables Groups 窗口
2. 选择 Default Local Group
3. 修改 Build & Load Paths：
   - Build Path: `ServerData/[BuildTarget]`
   - Load Path: `https://www.soulflaw.com/unity/ServerData/[BuildTarget]`

### 构建设置

```csharp
// 构建 Addressables
AddressableAssetSettings.BuildPlayerContent();

// 构建 WebGL
BuildPipeline.BuildPlayer(scenes, "Build/WebGL", BuildTarget.WebGL, BuildOptions.None);
```

---

## 🔒 安全建议

### 1. 限制访问方法

```nginx
# 仅允许 GET 和 OPTIONS
if ($request_method !~ ^(GET|OPTIONS)$) {
    return 405;
}
```

### 2. 防止目录遍历

```nginx
# 禁止访问隐藏文件
location ~ /\. {
    deny all;
}
```

### 3. 限制文件类型

```nginx
# 仅允许特定文件类型
location ~ \.(bundle|json|hash)$ {
    # ... 配置 ...
}

location /unity/ServerData/ {
    # 其他文件返回 404
    return 404;
}
```

---

**文档版本**：v1.0  
**最后更新**：2026-03-09  
**适用于**：Unity WebGL + Addressables 1.x/2.x

