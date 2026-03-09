# 🚀 Unity WebGL 优化快速参考

## 📝 问题总结

### 问题1：Unity 加载缓慢（3-5分钟）
**原因**：Nginx 未正确配置 Content-Encoding 头，浏览器无法识别文件已压缩

### 问题2：会话过期
**原因**：Unity 加载阻塞主线程，心跳无法发送，服务器超时释放会话

---

## ✅ 已完成的修改

### 1. Nginx 配置优化
**文件**：`server/nginx/html_www.soulflaw.com.conf`

**关键修改**：
```nginx
# Unity .unityweb 文件
location ~ ^/unity/Build/.*\.unityweb$ {
    add_header Content-Encoding gzip;  # ✅ 关键：告诉浏览器文件已压缩
    add_header Cache-Control "public, max-age=31536000, immutable";
    expires 365d;
    send_timeout 600s;  # ✅ 增加超时
}

# WebSocket 超时
location /agent/ws/ {
    proxy_read_timeout 600s;  # ✅ 从 300s 增加到 600s
    proxy_send_timeout 600s;
}
```

---

### 2. 客户端代码优化
**文件**：`client/web/MuseumAgent_Client/src/components/UnityContainer.js`

**关键修改**：
```javascript
async loadUnity() {
    // ✅ 添加保活心跳（每30秒）
    const keepAliveInterval = setInterval(() => {
        if (this.client && this.client.wsClient && this.client.wsClient.isConnected()) {
            this.client.wsClient.send({
                msg_type: 'HEARTBEAT_REPLY',
                payload: { client_status: 'LOADING_UNITY' }
            });
        }
    }, 30000);
    
    try {
        // Unity 加载...
        const config = {
            dataUrl: buildUrl + '/build.data.unityweb',  // ✅ 添加 .unityweb
            frameworkUrl: buildUrl + '/build.framework.js.unityweb',
            codeUrl: buildUrl + '/build.wasm.unityweb',
            compressionFormat: 'gzip'  // ✅ 指定压缩格式
        };
    } finally {
        clearInterval(keepAliveInterval);  // ✅ 清理定时器
    }
}
```

---

### 3. SDK 心跳超时优化
**文件**：`client/sdk/src/core/WebSocketClient.js`

**关键修改**：
```javascript
constructor(config = {}) {
    this.config = {
        heartbeatTimeout: config.heartbeatTimeout || 600000  // ✅ 从 120000 增加到 600000（10分钟）
    };
}
```

---

### 4. 服务器会话管理优化
**文件**：`src/session/strict_session_manager.py`

**关键修改**：
```python
def is_disconnected(self, heartbeat_timeout: timedelta = None) -> bool:
    """检查会话是否断开连接"""
    # ✅ 修复：不再使用硬编码的 2 分钟
    if heartbeat_timeout is None:
        return False  # 由外部传入正确的超时时间
    return datetime.now() - self.last_activity > heartbeat_timeout

def is_active(self) -> bool:
    """检查会话是否活跃"""
    # ✅ 修复：不再调用 is_disconnected()
    return not self.is_expired() and not self.is_inactive()
```

---

## 📋 部署步骤（快速版）

### 1. 备份
```bash
cp /www/server/panel/vhost/nginx/html_www.soulflaw.com.conf{,.backup}
```

### 2. 更新 Nginx 配置
```bash
# 上传新配置
scp server/nginx/html_www.soulflaw.com.conf root@server:/www/server/panel/vhost/nginx/

# 测试并重载
nginx -t && nginx -s reload
```

### 3. 重新构建 SDK
```bash
cd client/sdk
npm run build
```

### 4. 上传客户端文件
```bash
scp client/sdk/dist/museum-agent-sdk.min.js root@server:/www/wwwroot/MuseumAgent_Client/lib/
scp client/web/MuseumAgent_Client/src/components/UnityContainer.js root@server:/www/wwwroot/MuseumAgent_Client/src/components/
```

### 5. 检查权限
```bash
chown -R www:www /www/wwwroot/MuseumAgent_Client
```

### 6. 验证
```bash
# 检查 Content-Encoding 头
curl -I https://www.soulflaw.com/unity/Build/build.wasm.unityweb | grep Content-Encoding
# 应该看到：Content-Encoding: gzip

# 清除浏览器缓存并测试
```

---

## 🎯 预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| Unity 加载时间 | 3-5 分钟 | 30-60 秒 |
| 会话状态 | 加载后过期 | 始终有效 |
| 用户体验 | 极差 | 良好 |

---

## 🔍 验证检查点

### 1. Nginx 响应头
```bash
curl -I https://www.soulflaw.com/unity/Build/build.wasm.unityweb
```
**必须包含**：
- ✅ `Content-Encoding: gzip`
- ✅ `Cache-Control: public, max-age=31536000, immutable`
- ✅ `Access-Control-Allow-Origin: *`

### 2. 浏览器 Console
**Unity 加载期间应该看到**：
```
[UnityContainer] 开始加载 Unity...
[UnityContainer] 发送保活心跳（Unity 加载中）  ← 每30秒出现一次
[UnityContainer] Unity 加载进度: 50%
[UnityContainer] 发送保活心跳（Unity 加载中）
[UnityContainer] Unity 加载完成
[UnityContainer] 已停止保活心跳
```

### 3. Network 标签
**build.wasm.unityweb**：
- ✅ 状态码：200
- ✅ 大小：压缩后（通常 10-20MB）
- ✅ 时间：< 60 秒

---

## ⚠️ 常见问题

### Q1: Unity 文件返回 404
**A**: 检查文件路径和权限
```bash
ls -lh /www/wwwroot/MuseumAgent_Client/unity/Build/
chown -R www:www /www/wwwroot/MuseumAgent_Client/unity
```

### Q2: 会话仍然过期
**A**: 检查心跳日志
```bash
# 浏览器 Console 应该看到心跳日志
# 服务器日志应该收到心跳
tail -f /opt/MuseumAgent_Server/logs/enhanced_museum_agent.log | grep HEARTBEAT
```

### Q3: Unity 加载仍然很慢
**A**: 检查文件大小和网速
```bash
# 检查文件是否正确压缩
du -h /www/wwwroot/MuseumAgent_Client/unity/Build/*.unityweb

# 检查压缩格式
xxd -l 2 -p /www/wwwroot/MuseumAgent_Client/unity/Build/build.wasm.unityweb
# 应该输出: 1f8b (Gzip)
```

---

## 📞 需要帮助？

运行部署检查脚本：
```bash
bash check_deployment.sh
```

查看完整文档：
- `UNITY_OPTIMIZATION_GUIDE.md` - 优化方案详解
- `DEPLOYMENT_GUIDE.md` - 部署指南

---

**最后更新**：2024-03-09

