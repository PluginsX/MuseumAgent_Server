# MuseumAgent Web客户端API文档

## 概述

本文档描述了MuseumAgent Web客户端与服务端通信的API接口，包括HTTPS REST API和WebSocket两种协议。

## 协议说明

### HTTPS REST API
用于认证、会话管理、间断式对话等操作，采用请求-响应模式。

### WebSocket API
用于流式通信，支持实时双向通信，适用于语音对话、长文本流式生成等场景。

---

## 认证相关API

### 1. 用户登录

**接口地址**: `POST /api/auth/login`

**请求参数**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应数据**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**说明**: 登录成功后获取JWT Token，后续请求需要在Header中携带该Token。

**使用示例**:
```javascript
const client = new MuseumAgentClient({ baseUrl: 'http://localhost:8000' });
const response = await client.login('admin', 'admin123');
console.log(response.access_token);
```

---

### 2. 获取当前用户信息

**接口地址**: `GET /api/auth/me`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应数据**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "last_login": "2026-02-12T10:00:00Z"
}
```

**使用示例**:
```javascript
const user = await client.getCurrentUser();
console.log(user);
```

---

## 会话管理API

### 1. 注册会话

**接口地址**: `POST /api/session/register`

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "client_type": "web",
  "scene_type": "public",
  "spirit_id": "string"
}
```

**响应数据**:
```json
{
  "session_id": "uuid-string",
  "created_at": "2026-02-12T10:00:00Z",
  "expires_at": "2026-02-12T12:00:00Z"
}
```

**使用示例**:
```javascript
const session = await client.registerSession({
  client_type: 'web',
  scene_type: 'public'
});
console.log(session.session_id);
```

---

### 2. 验证会话

**接口地址**: `GET /api/session/validate/{session_id}`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应数据**:
```json
{
  "valid": true,
  "session_id": "uuid-string",
  "expires_at": "2026-02-12T12:00:00Z"
}
```

**使用示例**:
```javascript
const isValid = await client.validateSession(sessionId);
console.log(isValid);
```

---

### 3. 断开会话

**接口地址**: `DELETE /api/session/{session_id}`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应数据**:
```json
{
  "message": "会话已断开",
  "session_id": "uuid-string",
  "timestamp": "2026-02-12T10:00:00Z"
}
```

**使用示例**:
```javascript
await client.disconnectSession(sessionId);
```

---

## 智能体交互API（HTTPS REST API）

### 1. 智能体解析接口

**接口地址**: `POST /api/agent/parse`

**请求头**:
```
Authorization: Bearer {access_token}
X-Session-ID: {session_id}
```

**请求参数**:
```json
{
  "user_input": "string",
  "client_type": "web",
  "scene_type": "public",
  "spirit_id": "string"
}
```

**响应数据**:
```json
{
  "code": 200,
  "msg": "请求处理成功",
  "data": {
    "operation": "query",
    "artifact_name": "青铜鼎",
    "artifact_id": "artifact-001",
    "response": "这是一件商周时期的青铜鼎..."
  }
}
```

**使用示例**:
```javascript
const result = await client.parseAgent('请介绍一下青铜鼎', {
  clientType: 'web',
  sceneType: 'public'
});
console.log(result);
```

---

## WebSocket API

### 1. 智能体流式WebSocket

**连接地址**: `ws://host/ws/agent/stream?token={access_token}`

**连接参数**:
- `token`: JWT认证令牌（URL参数）

**客户端发送消息格式**:
```json
{
  "type": "text_stream",
  "session_id": "uuid-string",
  "content": "用户输入文本",
  "stream_id": "uuid-string"
}
```

**服务端推送消息格式**:
```json
{
  "type": "text_stream",
  "stream_id": "uuid-string",
  "chunk": "生成的文本片段",
  "done": false
}
```

**完成消息**:
```json
{
  "type": "text_stream",
  "stream_id": "uuid-string",
  "done": true
}
```

**错误消息**:
```json
{
  "type": "error",
  "stream_id": "uuid-string",
  "message": "错误描述"
}
```

**使用示例**:
```javascript
const ws = await client.connectAgentStream();
await client.sendTextStream(
  ws,
  '请介绍一下青铜鼎',
  (chunk) => {
    console.log('收到数据块:', chunk);
  },
  (data) => {
    console.log('流式生成完成');
  }
);
```

---

### 2. 音频TTS WebSocket

**连接地址**: `ws://host/ws/audio/tts?token={access_token}`

**连接参数**:
- `token`: JWT认证令牌（URL参数）

**客户端发送消息格式**:
```json
{
  "type": "tts_request",
  "text": "要合成的文本"
}
```

**服务端推送消息格式**:
- 音频数据以二进制格式发送（ArrayBuffer或Blob）

**错误消息**:
```json
{
  "type": "error",
  "message": "错误描述"
}
```

**使用示例**:
```javascript
const ws = await client.connectAudioTTS();
await client.sendTTSRequest(
  ws,
  '欢迎使用博物馆智能体',
  (audioChunk) => {
    console.log('收到音频数据块:', audioChunk.byteLength);
    // 处理音频数据
  }
);
```

---

### 3. 心跳消息

**客户端发送**:
```json
{
  "type": "session_heartbeat",
  "timestamp": 1676208000000
}
```

**服务端响应**:
```json
{
  "type": "session_heartbeat",
  "timestamp": 1676208000000
}
```

**说明**: 客户端应定期发送心跳消息以保持连接活跃，默认间隔为30秒。

---

## 错误处理

### HTTP错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权，Token无效或过期 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### WebSocket错误

**连接错误**:
- `1000`: 正常关闭
- `1001`: 端点离开
- `1002`: 协议错误
- `1003`: 不支持的数据类型
- `1006`: 连接异常关闭
- `1008`: 策略违规（如Token无效）

**错误消息格式**:
```json
{
  "type": "error",
  "message": "错误描述",
  "code": "error_code"
}
```

---

## 事件系统

客户端库提供了事件系统，可以监听各种事件：

### 事件列表

| 事件名称 | 触发时机 | 数据格式 |
|---------|---------|---------|
| `login` | 登录成功 | `{ access_token, token_type, expires_in }` |
| `error` | 发生错误 | `{ type, error }` |
| `session_registered` | 会话注册成功 | `{ session_id, created_at, expires_at }` |
| `session_disconnected` | 会话断开 | `{ session_id }` |
| `agent_response` | 收到智能体响应 | `{ operation, artifact_name, response }` |
| `ws_connected` | WebSocket连接成功 | `{ type }` |
| `ws_disconnected` | WebSocket连接断开 | `{ type }` |
| `stream_chunk` | 收到流式数据块 | `{ stream_id, chunk }` |
| `stream_complete` | 流式生成完成 | `{ stream_id, data }` |
| `audio_chunk` | 收到音频数据块 | `{ size }` |

### 事件监听示例

```javascript
const client = new MuseumAgentClient({ baseUrl: 'http://localhost:8000' });

client.on('login', (data) => {
  console.log('登录成功:', data);
});

client.on('error', (data) => {
  console.error('发生错误:', data);
});

client.on('stream_chunk', (data) => {
  console.log('收到流式数据:', data.chunk);
});

client.on('stream_complete', (data) => {
  console.log('流式生成完成');
});
```

---

## 配置选项

### 客户端初始化配置

```javascript
const client = new MuseumAgentClient({
  baseUrl: 'http://localhost:8000',  // 服务端基础URL
  timeout: 30000,                      // HTTP请求超时时间（毫秒）
  autoReconnect: true,                 // 是否自动重连WebSocket
  reconnectInterval: 5000,              // 重连间隔（毫秒）
  heartbeatInterval: 30000              // 心跳间隔（毫秒）
});
```

---

## 最佳实践

1. **认证管理**
   - 登录后妥善保存Token
   - Token过期后重新登录获取新Token
   - 不要在客户端代码中硬编码用户名和密码

2. **会话管理**
   - 应用启动时注册会话
   - 定期验证会话有效性
   - 应用退出时主动断开会话

3. **错误处理**
   - 监听`error`事件处理所有错误
   - 根据错误类型进行相应的处理
   - 记录错误日志便于排查问题

4. **WebSocket连接**
   - 连接成功后发送心跳保持连接
   - 处理连接断开和重连逻辑
   - 及时清理不再使用的WebSocket连接

5. **性能优化**
   - 合理设置超时时间
   - 避免频繁的HTTP请求
   - 使用流式API处理大量数据

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-02-12 | 初始版本，支持HTTPS REST API和WebSocket混合协议 |

---

## 技术支持

如有问题，请联系技术支持团队或查看项目文档。
