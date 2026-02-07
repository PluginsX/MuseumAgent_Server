# MuseumAgent 博物馆智能体通信协议规范

## 1. 概述

MuseumAgent 是一个基于 FastAPI 构建的博物馆智能体服务，支持多客户端标准化对接。本规范定义了客户端与服务器之间的完整通信协议，包括数据格式、API 接口、会话管理和错误处理。

### 1.1 技术架构

- **服务端**: Python 3.8+, FastAPI, SQLAlchemy, ChromaDB
- **客户端**: 支持任意 HTTP 客户端
- **通信协议**: RESTful API over HTTPS
- **数据格式**: JSON
- **认证方式**: Session-based (会话ID)
- **函数调用**: OpenAI Function Calling 标准

### 1.2 核心特性

- ✅ OpenAI Function Calling 标准兼容
- ✅ 双模式支持：普通对话 + 函数调用
- ✅ 动态会话管理
- ✅ RAG 检索增强
- ✅ 实时心跳机制
- ✅ 完整的日志追踪

## 2. 数据模型规范

### 2.1 请求数据模型

#### AgentParseRequest
客户端向 `/api/agent/parse` 发送的主要请求模型：

```json
{
  "user_input": "string",           // 用户自然语言输入 (必填)
  "client_type": "string",          // 客户端类型 (可选)
  "spirit_id": "string",            // 器灵ID (可选)
  "scene_type": "string"            // 场景类型: study/leisure/public (可选，默认public)
}
```

**字段说明**:
- `user_input`: 用户输入文本，长度1-2000字符
- `client_type`: 用于日志统计，不影响业务逻辑
- `spirit_id`: 第三方客户端可传空
- `scene_type`: 影响提示词构建，支持三种场景模式

#### ClientRegistrationRequest
客户端注册会话时的请求模型：

```json
{
  "client_metadata": {
    "client_id": "string",
    "client_type": "string",
    "client_version": "string",
    "platform": "string",
    "capabilities": {
      "max_concurrent_requests": 3,
      "supported_scenes": ["study", "leisure", "public"],
      "preferred_response_format": "json",
      "function_calling_supported": true
    }
  },
  "functions": [
    {
      "name": "function_name",
      "description": "函数功能描述",
      "parameters": {
        "type": "object",
        "properties": {
          "param1": {
            "type": "string",
            "description": "参数描述"
          }
        },
        "required": ["param1"]
      }
    }
  ]
}
```

### 2.2 响应数据模型

#### 标准响应格式
所有 API 响应遵循统一格式：

```json
{
  "code": 200,
  "msg": "请求处理成功",
  "data": {}
}
```

**状态码说明**:
- `200`: 成功
- `400`: 请求参数错误
- `401`: 会话无效或过期
- `404`: 资源不存在
- `500`: 服务器内部错误

#### LLM 原始响应格式
智能体核心接口 `/api/agent/parse` 直接返回 LLM 的原始响应数据：

```json
{
  "code": 200,
  "msg": "请求处理成功",
  "data": {
    "choices": [
      {
        "finish_reason": "stop",
        "index": 0,
        "message": {
          "content": "自然语言回复内容",
          "role": "assistant"
        }
      }
    ],
    "created": 1770216830,
    "id": "chatcmpl-xxx",
    "model": "qwen-turbo",
    "object": "chat.completion",
    "usage": {
      "completion_tokens": 47,
      "prompt_tokens": 650,
      "total_tokens": 697
    }
  }
}
```

函数调用模式下的响应：

```json
{
  "code": 200,
  "msg": "请求处理成功",
  "data": {
    "choices": [
      {
        "finish_reason": "function_call",
        "index": 0,
        "message": {
          "content": "解释性对话内容",
          "function_call": {
            "arguments": "{\"emotion\": \"angry\"}",
            "name": "show_emotion"
          },
          "role": "assistant"
        }
      }
    ],
    // ... 其他字段同上
  }
}
```

## 3. API 接口规范

### 3.1 会话管理接口

#### 注册会话
```
POST /api/session/register
Content-Type: application/json
```

**请求示例**:
```json
{
  "client_metadata": {
    "client_id": "desktop_pet_001",
    "client_type": "windows_desktop",
    "client_version": "1.0.0",
    "platform": "windows"
  },
  "functions": [
    {
      "name": "move_to_position",
      "description": "移动到指定坐标位置",
      "parameters": {
        "type": "object",
        "properties": {
          "x": {"type": "number", "description": "X坐标"},
          "y": {"type": "number", "description": "Y坐标"}
        },
        "required": ["x", "y"]
      }
    }
  ]
}
```

**响应示例**:
```json
{
  "session_id": "uuid-string",
  "expires_at": "2026-02-05T01:00:00",
  "server_timestamp": "2026-02-05T00:45:00",
  "supported_features": [
    "dynamic_operations",
    "session_management",
    "heartbeat",
    "function_calling"
  ]
}
```

#### 心跳保持
```
POST /api/session/heartbeat
Content-Type: application/json
session-id: {session_id}
```

**响应示例**:
```json
{
  "status": "alive",
  "timestamp": "2026-02-05T00:45:30",
  "session_valid": true
}
```

#### 注销会话
```
DELETE /api/session/unregister
session-id: {session_id}
```

### 3.2 智能体核心接口

#### 解析用户输入
```
POST /api/agent/parse
Content-Type: application/json
session-id: {session_id} (可选)
```

**请求示例**:
```json
{
  "user_input": "移动到屏幕中央",
  "client_type": "desktop_pet",
  "scene_type": "public"
}
```

**响应**: 直接返回 LLM 原始响应数据（如 2.2 节所示）

### 3.3 管理接口

#### 配置管理
```
GET/PUT /api/admin/config/llm
```

#### 监控接口
```
GET /api/admin/monitor/stats
GET /api/admin/monitor/logs
```

## 4. 会话管理机制

### 4.1 会话生命周期

```
[未注册] → 注册会话 → [活跃] → 心跳超时/过期 → [清理]
              ↓
          注销会话
              ↓
           [结束]
```

### 4.2 会话参数配置

```json
{
  "session_management": {
    "session_timeout_minutes": 15,
    "inactivity_timeout_minutes": 5,
    "heartbeat_timeout_minutes": 2,
    "cleanup_interval_seconds": 30,
    "enable_auto_cleanup": true,
    "enable_heartbeat_monitoring": true
  }
}
```

### 4.3 会话状态检查

服务器定期检查会话状态：
1. **过期检查**: 会话是否超过 15 分钟
2. **心跳检查**: 最近心跳是否超过 2 分钟
3. **活跃度检查**: 最近活动是否超过 5 分钟

## 5. 函数调用机制

### 5.1 OpenAI 标准函数定义

函数定义严格遵循 OpenAI Function Calling 标准：

```json
{
  "name": "function_name",
  "description": "函数功能的详细描述",
  "parameters": {
    "type": "object",
    "properties": {
      "param_name": {
        "type": "string|number|boolean|object|array",
        "description": "参数描述",
        "enum": ["可选枚举值"]
      }
    },
    "required": ["必需参数列表"]
  }
}
```

### 5.2 双模式支持

#### 函数调用模式
- 客户端注册时提供函数定义列表
- 服务器根据函数定义构建 LLM 提示词
- LLM 可能返回函数调用指令

#### 普通对话模式
- 客户端注册时不提供函数定义
- 服务器使用通用对话提示词
- LLM 只返回自然语言回复

### 5.3 函数调用响应解析

LLM 返回的函数调用会被解析为标准格式：

```json
{
  "command": "function_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "type": "function_call",
  "format": "openai_standard",
  "response": "解释性的自然语言内容"
}
```

## 6. 通信安全

### 6.1 HTTPS 传输
所有通信必须通过 HTTPS 加密传输。

### 6.2 CORS 配置
```json
{
  "server": {
    "cors_allow_origins": ["https://your-domain.com"]
  }
}
```

### 6.3 会话安全性
- 会话 ID 使用 UUID 生成
- 会话有过期时间限制
- 定期清理无效会话
- 心跳机制防止连接中断

## 7. 错误处理

### 7.1 标准错误响应
```json
{
  "code": 400,
  "msg": "具体的错误信息",
  "data": null
}
```

### 7.2 常见错误类型

| 错误码 | 场景 | 处理建议 |
|--------|------|----------|
| 400 | 请求参数格式错误 | 检查请求数据格式 |
| 401 | 会话无效或过期 | 重新注册会话 |
| 404 | 资源不存在 | 检查 API 路径 |
| 500 | 服务器内部错误 | 查看服务器日志 |

### 7.3 客户端错误处理建议
```javascript
try {
  const response = await fetch('/api/agent/parse', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'session-id': sessionId
    },
    body: JSON.stringify(requestData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    if (response.status === 401) {
      // 会话失效，需要重新注册
      await registerSession();
    }
    throw new Error(error.msg);
  }
  
  const result = await response.json();
  // 处理成功响应
} catch (error) {
  // 处理网络错误或其他异常
  console.error('请求失败:', error);
}
```

## 8. 部署配置

### 8.1 环境变量配置
```bash
# LLM 配置
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=your-api-key
LLM_MODEL=qwen-turbo



# 服务器配置
SERVER_HOST=localhost
SERVER_PORT=8000
```

### 8.2 config.json 配置示例
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "cors_allow_origins": ["*"],
    "request_timeout": 30
  },
  "llm": {
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "your-api-key",
    "model": "qwen-turbo",
    "parameters": {
      "temperature": 0.1,
      "max_tokens": 1024,
      "top_p": 0.1
    }
   }
}
```

## 9. 监控与日志

### 9.1 日志级别
- `INFO`: 正常操作日志
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `DEBUG`: 调试信息

### 9.2 关键监控指标
- 会话总数和活跃会话数
- API 请求响应时间
- LLM 调用成功率
- 错误率统计
- 系统资源使用情况

### 9.3 日志格式示例
```
[00:45:30.123] [SESSION] REGISTER  新会话注册成功 | [SESSION] 📊 Data: | { |   "session_id": "abcd1234", |   "client_type": "desktop_pet", |   "function_count": 5, |   "expires_in": 15.0 | }
```

## 10. 最佳实践

### 10.1 客户端开发建议

1. **会话管理**: 实现自动会话注册和心跳机制
2. **错误处理**: 完善的错误处理和重试机制
3. **超时设置**: 合理设置请求超时时间
4. **连接池**: 复用 HTTP 连接提高性能
5. **本地缓存**: 缓存常用配置减少请求

### 10.2 服务器运维建议

1. **监控告警**: 设置关键指标监控和告警
2. **日志轮转**: 定期清理和归档日志文件
3. **备份策略**: 定期备份配置和数据
4. **容量规划**: 根据业务量合理规划资源
5. **安全更新**: 及时更新依赖包修复安全漏洞

### 10.3 性能优化建议

1. **连接复用**: 使用连接池减少 TCP 握手开销
2. **批量处理**: 支持批量向量化操作
3. **缓存策略**: 合理使用缓存减少重复计算
4. **异步处理**: 耗时操作使用异步处理
5. **压缩传输**: 大数据传输时考虑压缩

---

*本文档版本: 1.0*
*更新时间: 2026-02-05*
*适用版本: MuseumAgent Server v1.0.0*