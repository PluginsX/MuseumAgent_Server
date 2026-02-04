# MuseumAgent Server 通信协议规范

## 1. 概述

本文档定义了MuseumAgent服务器与客户端之间的标准化通信协议。服务器完全遵循OpenAI Function Calling标准，支持双模式操作：普通对话模式和函数调用模式。

## 2. 通信架构

### 2.1 整体架构
```
客户端 ↔ HTTP/HTTPS ↔ MuseumAgent服务器 ↔ LLM API
         ↑                                  ↑
    标准RESTful API                   OpenAI兼容API
```

### 2.2 支持的通信模式
- **普通对话模式**：无函数定义时的基础对话交互
- **函数调用模式**：提供函数定义时的高级交互

## 3. API端点规范

### 3.1 核心API端点

#### `/api/agent/parse` - 智能体解析接口
- **方法**: POST
- **用途**: 主要的用户输入处理接口
- **认证**: 通过session-id请求头
- **请求格式**: JSON

**请求体结构**:
```json
{
  "user_input": "用户自然语言输入",
  "client_type": "客户端类型标识（可选）",
  "spirit_id": "器灵ID（可选）",
  "scene_type": "场景类型：study/leisure/public"
}
```

**响应格式**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "artifact_id": "文物ID（可选）",
    "artifact_name": "文物名称（可选）",
    "operation": "操作类型（可选）",
    "operation_params": {},
    "keywords": [],
    "tips": "提示信息（可选）",
    "response": "自然语言对话内容"
  }
}
```

### 3.2 会话管理端点

#### `/api/session/register` - 会话注册
- **方法**: POST
- **用途**: 客户端首次连接时注册会话

**请求体**:
```json
{
  "client_metadata": {
    "client_type": "客户端类型",
    "client_version": "版本号",
    "capabilities": ["feature1", "feature2"]
  },
  "functions": [
    {
      "name": "函数名",
      "description": "函数描述",
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

**响应**:
```json
{
  "session_id": "会话唯一标识符",
  "expires_at": "过期时间ISO格式",
  "server_timestamp": "服务器时间",
  "supported_features": ["dynamic_operations", "session_management", "heartbeat", "function_calling"]
}
```

#### `/api/session/heartbeat` - 心跳维护
- **方法**: POST
- **认证**: session-id请求头
- **用途**: 维持会话活跃状态

#### `/api/session/unregister` - 会话注销
- **方法**: DELETE
- **认证**: session-id请求头
- **用途**: 客户端主动断开连接

### 3.3 管理端点

#### `/api/admin/*` - 管理员接口
- 包括配置管理、监控、嵌入等后台管理功能
- 需要JWT Token认证

## 4. 数据结构规范

### 4.1 OpenAI Function Calling标准

服务器严格遵循OpenAI Function Calling标准，支持的标准字段包括：

**函数定义结构**:
```json
{
  "name": "函数名称（字母数字下划线，不超过64字符）",
  "description": "函数功能详细描述",
  "parameters": {
    "type": "object",
    "properties": {
      "参数名": {
        "type": "参数类型（string/number/boolean/object/array）",
        "description": "参数描述",
        "enum": ["枚举值1", "枚举值2"]
      }
    },
    "required": ["必需参数列表"]
  }
}
```

### 4.2 会话元数据结构
```json
{
  "client_type": "客户端类型标识",
  "client_version": "客户端版本",
  "platform": "运行平台",
  "capabilities": ["支持的功能列表"],
  "custom_fields": {}
}
```

## 5. 通信流程

### 5.1 完整交互流程

```
1. 客户端启动
   ↓
2. 调用 /api/session/register 注册会话
   ↓
3. 服务器返回 session_id 和有效期
   ↓
4. 客户端在后续请求中使用 session-id 头
   ↓
5. 调用 /api/agent/parse 处理用户输入
   ↓
6. 服务器根据会话模式选择处理策略
   ↓
7. 返回标准化响应给客户端
   ↓
8. 定期发送心跳维持会话
   ↓
9. 断开连接时调用注销接口
```

### 5.2 双模式处理逻辑

#### 普通对话模式
- 条件：会话注册时未提供函数定义
- 特点：纯自然语言交互
- 应用场景：基础问答、简单咨询

#### 函数调用模式
- 条件：会话注册时提供OpenAI标准函数定义
- 特点：支持复杂操作、精确控制
- 应用场景：桌面宠物行为控制、复杂业务操作

### 5.3 错误处理流程
```
客户端请求
    ↓
服务器验证会话
    ↓
是 → 处理业务逻辑
    ↓
否 → 返回401错误
    ↓
业务处理
    ↓
成功 → 返回200响应
    ↓
失败 → 根据错误类型返回相应状态码
```

## 6. 认证与安全

### 6.1 会话认证
- 使用UUID4生成唯一会话ID
- 通过HTTP头部 `session-id` 传递
- 支持会话过期和自动清理

### 6.2 管理员认证
- 使用JWT Token
- 通过HTTP头部 `Authorization: Bearer <token>` 传递
- 支持Token刷新机制

### 6.3 安全措施
- HTTPS支持（生产环境推荐）
- CORS跨域资源共享控制
- 请求频率限制（可配置）
- 输入验证和清理

## 7. 配置管理

### 7.1 动态配置
服务器支持运行时配置更新：
- LLM模型参数
- 会话超时设置
- 系统提示词模板
- 日志级别调整

### 7.2 配置优先级
```
环境变量 > 配置文件 > 默认值
```

## 8. 监控与日志

### 8.1 日志级别
- DEBUG: 详细调试信息
- INFO: 一般操作信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

### 8.2 监控指标
- 会话活跃数
- API调用统计
- 响应时间分布
- 错误率统计
- LLM调用成本

## 9. 性能优化

### 9.1 连接复用
- HTTP长连接支持
- 连接池管理
- 自动重试机制

### 9.2 缓存策略
- 会话信息缓存
- 常用响应缓存
- 知识库查询缓存

## 10. 兼容性说明

### 10.1 向前兼容
- 保持现有API端点不变
- 逐步迁移旧功能
- 提供过渡期支持

### 10.2 版本管理
- API版本通过URL路径区分
- 响应格式版本控制
- 废弃功能标记

## 11. 最佳实践

### 11.1 客户端开发建议
1. 实现会话管理机制
2. 正确处理错误响应
3. 合理使用心跳机制
4. 遵循函数定义标准
5. 实现优雅降级

### 11.2 服务器部署建议
1. 启用HTTPS加密传输
2. 配置适当的超时时间
3. 设置合理的资源限制
4. 定期备份配置和数据
5. 监控系统性能指标

---

*文档版本：v1.0*
*最后更新：2026年2月*
*适用服务器版本：1.0.0+*