# MuseumAgent 博物馆智能体服务 API 文档

## 1. 服务概述

MuseumAgent 是一个博物馆文物智能解析服务，支持多客户端标准化对接。本服务提供了丰富的 API 接口，用于客户端与服务端的通信、配置管理、系统监控等功能。

### 1.1 服务信息

- **服务名称**：MuseumAgent 博物馆智能体服务
- **服务版本**：1.0.0
- **API 基础路径**：根据不同模块有所不同，详见各模块说明
- **认证方式**：JWT（JSON Web Token）
- **数据格式**：JSON
- **错误处理**：使用 HTTP 状态码表示错误类型，返回标准化错误信息

### 1.2 标准化通信流程

1. **认证流程**：
   - 客户端通过 POST /api/auth/login 获取 JWT 令牌
   - 后续请求在 Authorization 头中携带该令牌：`Authorization: Bearer <token>`

2. **智能体交互流程**：
   - 客户端注册会话：POST /api/session/register
   - 发送用户输入：POST /api/agent/parse
   - 服务器处理并返回标准化指令
   - 客户端定期发送心跳：POST /api/session/heartbeat
   - 会话结束时注销：DELETE /api/session/unregister

3. **配置管理流程**：
   - 管理员登录：POST /Control/api/login
   - 修改配置：PUT /api/admin/config/{module}
   - 服务器验证并保存配置

4. **会话管理流程**：
   - 客户端注册 -> 定期发送心跳 -> 服务器维护会话状态 -> 客户端注销

## 2. 认证 API

### 2.1 登录

**请求**：
- 方法：POST
- URL：/api/auth/login
- 请求体：
  ```json
  {
    "username": "admin",
    "password": "password123"
  }
  ```

**响应**：
- 成功：
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```
- 失败：
  ```json
  {
    "detail": "用户名或密码错误"
  }
  ```

### 2.2 获取当前用户信息

**请求**：
- 方法：GET
- URL：/api/auth/me
- 头信息：
  ```
  Authorization: Bearer <token>
  ```

**响应**：
- 成功：
  ```json
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "last_login": "2023-12-01T12:00:00"
  }
  ```
- 失败：
  ```json
  {
    "detail": "用户不存在"
  }
  ```

## 3. 智能体核心 API

### 3.1 服务健康检查

**请求**：
- 方法：GET
- URL：/

**响应**：
  ```json
  {
    "status": "ok",
    "service": "MuseumAgent",
    "version": "1.0.0"
  }
  ```

### 3.2 智能体解析接口

**请求**：
- 方法：POST
- URL：/api/agent/parse
- 头信息（可选）：
  ```
  session_id: <session_id>
  ```
- 请求体：
  ```json
  {
    "user_input": "介绍一下这个文物",
    "client_type": "web3d",
    "spirit_id": "",
    "scene_type": "public"
  }
  ```

**响应**：
- 成功：
  ```json
  {
    "code": 200,
    "msg": "请求处理成功",
    "data": {
      "operation": "introduce_artifact",
      "artifact_name": "青花瓷瓶",
      "parameters": {
        "detail_level": "medium"
      }
    }
  }
  ```
- 失败：
  ```json
  {
    "code": 500,
    "msg": "请求处理失败: 未知错误"
  }
  ```

## 4. 配置管理 API

### 4.1 LLM 配置

#### 4.1.1 获取 LLM 配置（API Key 脱敏）

**请求**：
- 方法：GET
- URL：/api/admin/config/llm
- 头信息：
  ```
  Authorization: Bearer <token>
  ```

**响应**：
  ```json
  {
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-****a1b2",
    "model": "gpt-3.5-turbo",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "version": 1
  }
  ```

#### 4.1.2 更新 LLM 配置

**请求**：
- 方法：PUT
- URL：/api/admin/config/llm
- 头信息：
  ```
  Authorization: Bearer <token>
  ```
- 请求体：
  ```json
  {
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-1234567890abcdef",
    "model": "gpt-4",
    "parameters": {
      "temperature": 0.5,
      "max_tokens": 2000
    }
  }
  ```

**响应**：
  ```json
  {
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-****cdef",
    "model": "gpt-4",
    "parameters": {
      "temperature": 0.5,
      "max_tokens": 2000
    }
  }
  ```

### 4.2 SRS（语义检索系统）配置

#### 4.2.1 获取 SRS 配置（API Key 脱敏）

**请求**：
- 方法：GET
- URL：/api/admin/config/srs
- 头信息：
  ```
  Authorization: Bearer <token>
  ```

**响应**：
  ```json
  {
    "base_url": "http://localhost:12315/api/v1",
    "api_key": "srs-****7890",
    "timeout": 30,
    "search_params": {
      "top_k": 3,
      "threshold": 0.5
    },
    "version": 1
  }
  ```

#### 4.2.2 更新 SRS 配置

**请求**：
- 方法：PUT
- URL：/api/admin/config/srs
- 头信息：
  ```
  Authorization: Bearer <token>
  ```
- 请求体：
  ```json
  {
    "base_url": "http://localhost:12315/api/v1",
    "api_key": "srs-1234567890abcdef",
    "timeout": 30,
    "search_params": {
      "top_k": 5,
      "threshold": 0.6
    }
  }
  ```

**响应**：
  ```json
  {
    "base_url": "http://localhost:12315/api/v1",
    "api_key": "srs-****cdef",
    "timeout": 30,
    "search_params": {
      "top_k": 5,
      "threshold": 0.6
    }
  }
  ```

### 4.3 配置验证

#### 4.3.1 验证 LLM 配置

**请求**：
- 方法：POST
- URL：/api/admin/config/llm/validate
- 头信息：
  ```
  Authorization: Bearer <token>
  ```
- 请求体：
  ```json
  {
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-1234567890abcdef",
    "model": "gpt-3.5-turbo"
  }
  ```

**响应**：
  ```json
  {
    "valid": true,
    "message": "连接成功"
  }
  ```

#### 4.3.2 验证 SRS 配置

**请求**：
- 方法：POST
- URL：/api/admin/config/srs/validate
- 头信息：
  ```
  Authorization: Bearer <token>
  ```
- 请求体：
  ```json
  {
    "base_url": "http://localhost:12315/api/v1",
    "api_key": "srs-1234567890abcdef"
  }
  ```

**响应**：
  ```json
  {
    "valid": true,
    "message": "连接成功"
  }
  ```

## 5. 系统监控 API

### 5.1 获取系统状态

**请求**：
- 方法：GET
- URL：/api/admin/monitor/status

**响应**：
  ```json
  {
    "code": 200,
    "msg": "success",
    "data": {
      "service_status": "running",
      "version": "1.0.0",
      "uptime": "N/A",
      "timestamp": "2023-12-01T12:00:00"
    }
  }
  ```

### 5.2 获取系统日志

**请求**：
- 方法：GET
- URL：/api/admin/monitor/logs?page=1&size=50

**响应**：
  ```json
  {
    "code": 200,
    "msg": "success",
    "data": {
      "lines": [
        "2023-12-01 12:00:00 INFO: Server started",
        "2023-12-01 12:01:00 INFO: Client connected"
      ],
      "total": 100
    }
  }
  ```

### 5.3 清空系统日志

**请求**：
- 方法：DELETE
- URL：/api/admin/monitor/logs

**响应**：
  ```json
  {
    "code": 200,
    "msg": "日志已清空"
  }
  ```

### 5.4 下载日志文件

**请求**：
- 方法：GET
- URL：/api/admin/monitor/logs/download

**响应**：
- 返回日志文件的二进制数据，Content-Type: text/plain

## 6. 用户管理 API

### 6.1 获取用户列表

**请求**：
- 方法：GET
- URL：/api/admin/users?page=1&size=10&search=admin
- 头信息：
  ```
  Authorization: Bearer <token>
  ```

**响应**：
  ```json
  [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true
    }
  ]
  ```

### 6.2 创建用户

**请求**：
- 方法：POST
- URL：/api/admin/users
- 头信息：
  ```
  Authorization: Bearer <token>
  ```
- 请求体：
  ```json
  {
    "username": "user1",
    "email": "user1@example.com",
    "password": "password123",
    "role": "user"
  }
  ```

**响应**：
  ```json
  {
    "id": 2,
    "username": "user1",
    "email": "user1@example.com",
    "role": "user",
    "is_active": true
  }
  ```

### 6.3 更新用户

**请求**：
- 方法：PUT
- URL：/api/admin/users/2
- 头信息：
  ```
  Authorization: Bearer <token>
  ```
- 请求体：
  ```json
  {
    "email": "user1_updated@example.com",
    "role": "admin",
    "is_active": true
  }
  ```

**响应**：
  ```json
  {
    "id": 2,
    "username": "user1",
    "email": "user1_updated@example.com",
    "role": "admin",
    "is_active": true
  }
  ```

### 6.4 删除用户

**请求**：
- 方法：DELETE
- URL：/api/admin/users/2
- 头信息：
  ```
  Authorization: Bearer <token>
  ```

**响应**：
  ```json
  {
    "deleted": 2
  }
  ```

## 7. 会话管理 API

### 7.1 客户端注册

**请求**：
- 方法：POST
- URL：/api/session/register
- 请求体：
  ```json
  {
    "client_metadata": {
      "client_type": "web3d",
      "client_id": "client_123",
      "platform": "web",
      "client_version": "1.0.0"
    },
    "functions": [
      {
        "name": "introduce_artifact",
        "description": "介绍文物",
        "parameters": {
          "type": "object",
          "properties": {
            "artifact_id": {
              "type": "string",
              "description": "文物ID"
            },
            "detail_level": {
              "type": "string",
              "enum": ["basic", "medium", "detailed"],
              "description": "详细程度"
            }
          },
          "required": ["artifact_id"]
        }
      }
    ]
  }
  ```

**响应**：
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2023-12-01T13:00:00",
    "server_timestamp": "2023-12-01T12:00:00",
    "supported_features": ["dynamic_operations", "session_management", "heartbeat", "function_calling"]
  }
  ```

### 7.2 会话心跳

**请求**：
- 方法：POST
- URL：/api/session/heartbeat
- 头信息：
  ```
  session_id: 550e8400-e29b-41d4-a716-446655440000
  ```

**响应**：
  ```json
  {
    "status": "alive",
    "timestamp": "2023-12-01T12:01:00",
    "session_valid": true
  }
  ```

### 7.3 注销会话

**请求**：
- 方法：DELETE
- URL：/api/session/unregister
- 头信息：
  ```
  session_id: 550e8400-e29b-41d4-a716-446655440000
  ```

**响应**：
  ```json
  {
    "status": "unregistered",
    "timestamp": "2023-12-01T12:30:00",
    "message": "会话已成功注销"
  }
  ```

### 7.4 获取会话支持的函数

**请求**：
- 方法：GET
- URL：/api/session/functions
- 头信息：
  ```
  session_id: 550e8400-e29b-41d4-a716-446655440000
  ```

**响应**：
  ```json
  {
    "operations": ["introduce_artifact"],
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_type": "web3d"
  }
  ```

### 7.5 获取会话信息

**请求**：
- 方法：GET
- URL：/api/session/info
- 头信息：
  ```
  session_id: 550e8400-e29b-41d4-a716-446655440000
  ```

**响应**：
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_metadata": {
      "client_type": "web3d",
      "client_id": "client_123"
    },
    "operations": ["introduce_artifact"],
    "created_at": "2023-12-01T12:00:00",
    "expires_at": "2023-12-01T13:00:00",
    "is_active": true
  }
  ```

### 7.6 获取会话统计信息

**请求**：
- 方法：GET
- URL：/api/session/stats

**响应**：
  ```json
  {
    "active_sessions": 5,
    "total_sessions": 10,
    "server_time": "2023-12-01T12:00:00",
    "sessions_detail": [
      {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "client_type": "web3d",
        "function_count": 1,
        "created_at": "2023-12-01T12:00:00",
        "expires_at": "2023-12-01T13:00:00",
        "is_expired": false
      }
    ]
  }
  ```

## 8. 客户端管理 API

### 8.1 获取连接的客户端

**请求**：
- 方法：GET
- URL：/api/admin/clients/connected

**响应**：
  ```json
  [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_type": "web3d",
      "client_id": "client_123",
      "platform": "web",
      "client_version": "1.0.0",
      "ip_address": "127.0.0.1",
      "created_at": "2023-12-01T12:00:00",
      "expires_at": "2023-12-01T13:00:00",
      "is_active": true,
      "function_names": ["introduce_artifact"],
      "function_count": 1,
      "supports_openai_standard": true,
      "last_heartbeat": "2023-12-01T12:01:00",
      "time_since_heartbeat": 60
    }
  ]
  ```

### 8.2 获取客户端详情

**请求**：
- 方法：GET
- URL：/api/admin/clients/session/550e8400-e29b-41d4-a716-446655440000

**响应**：
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_metadata": {
      "client_type": "web3d",
      "client_id": "client_123"
    },
    "functions": [
      {
        "name": "introduce_artifact",
        "description": "介绍文物",
        "parameters": {
          "type": "object",
          "properties": {
            "artifact_id": {
              "type": "string",
              "description": "文物ID"
            }
          },
          "required": ["artifact_id"]
        }
      }
    ],
    "function_count": 1,
    "supports_openai_standard": true,
    "created_at": "2023-12-01T12:00:00",
    "expires_at": "2023-12-01T13:00:00",
    "is_active": true,
    "is_alive": true,
    "time_remaining": 3540
  }
  ```

### 8.3 检查客户端状态

**请求**：
- 方法：GET
- URL：/api/admin/clients/session/550e8400-e29b-41d4-a716-446655440000/status

**响应**：
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "is_alive": true,
    "is_active": true,
    "last_heartbeat": "2023-12-01T12:01:00",
    "time_since_heartbeat": 60,
    "expires_at": "2023-12-01T13:00:00",
    "time_until_expiry": 3540,
    "should_cleanup": false
  }
  ```

### 8.4 清理僵尸会话

**请求**：
- 方法：POST
- URL：/api/admin/clients/cleanup/zombie-sessions

**响应**：
  ```json
  {
    "message": "僵尸会话清理完成",
    "total_sessions": 10,
    "active_sessions": 5,
    "cleaned_up": 2,
    "timestamp": "2023-12-01T12:00:00"
  }
  ```

### 8.5 获取客户端统计信息

**请求**：
- 方法：GET
- URL：/api/admin/clients/stats

**响应**：
  ```json
  {
    "total_clients": 5,
    "active_sessions": 4,
    "inactive_sessions": 1,
    "client_types": {
      "web3d": 3,
      "mobile": 2
    },
    "timestamp": "2023-12-01T12:00:00"
  }
  ```

## 9. 会话配置 API

### 9.1 获取当前会话配置

**请求**：
- 方法：GET
- URL：/api/admin/session-config/current

**响应**：
  ```json
  {
    "current_config": {
      "session_timeout_minutes": 15,
      "inactivity_timeout_minutes": 5,
      "heartbeat_timeout_minutes": 2,
      "cleanup_interval_seconds": 30,
      "deep_validation_interval_seconds": 300,
      "enable_auto_cleanup": true,
      "enable_heartbeat_monitoring": true,
      "log_level": "INFO"
    },
    "runtime_info": {
      "session_timeout": "15分钟",
      "inactivity_timeout": "5分钟",
      "heartbeat_timeout": "2分钟",
      "cleanup_interval": "30秒",
      "deep_validation_interval": "300秒",
      "auto_cleanup_enabled": true,
      "heartbeat_monitoring_enabled": true
    },
    "session_stats": {
      "active_sessions": 5,
      "total_sessions": 10
    },
    "timestamp": "2023-12-01T12:00:00"
  }
  ```

### 9.2 更新会话配置

**请求**：
- 方法：PUT
- URL：/api/admin/session-config/update
- 请求体：
  ```json
  {
    "session_timeout_minutes": 30,
    "inactivity_timeout_minutes": 10,
    "cleanup_interval_seconds": 60
  }
  ```

**响应**：
  ```json
  {
    "message": "配置更新成功",
    "changes_made": [
      {
        "key": "session_timeout_minutes",
        "old_value": 15,
        "new_value": 30
      },
      {
        "key": "inactivity_timeout_minutes",
        "old_value": 5,
        "new_value": 10
      },
      {
        "key": "cleanup_interval_seconds",
        "old_value": 30,
        "new_value": 60
      }
    ],
    "restart_required": true,
    "updated_config": {
      "session_timeout_minutes": 30,
      "inactivity_timeout_minutes": 10,
      "heartbeat_timeout_minutes": 2,
      "cleanup_interval_seconds": 60,
      "deep_validation_interval_seconds": 300,
      "enable_auto_cleanup": true,
      "enable_heartbeat_monitoring": true,
      "log_level": "INFO"
    },
    "timestamp": "2023-12-01T12:00:00"
  }
  ```

### 9.3 重置为默认配置

**请求**：
- 方法：POST
- URL：/api/admin/session-config/reset-defaults

**响应**：
  ```json
  {
    "message": "配置已重置为默认值",
    "old_config": {
      "session_timeout_minutes": 30,
      "inactivity_timeout_minutes": 10
    },
    "new_config": {
      "session_timeout_minutes": 15,
      "inactivity_timeout_minutes": 5,
      "heartbeat_timeout_minutes": 2,
      "cleanup_interval_seconds": 30,
      "deep_validation_interval_seconds": 300,
      "enable_auto_cleanup": true,
      "enable_heartbeat_monitoring": true,
      "log_level": "INFO"
    },
    "timestamp": "2023-12-01T12:00:00"
  }
  ```

### 9.4 验证配置格式

**请求**：
- 方法：GET
- URL：/api/admin/session-config/validate
- 请求体：
  ```json
  {
    "session_timeout_minutes": 30,
    "inactivity_timeout_minutes": 10,
    "log_level": "DEBUG"
  }
  ```

**响应**：
  ```json
  {
    "is_valid": true,
    "validation_results": {
      "session_timeout_minutes": {
        "valid": true
      },
      "inactivity_timeout_minutes": {
        "valid": true
      },
      "log_level": {
        "valid": true
      }
    },
    "errors": [],
    "timestamp": "2023-12-01T12:00:00"
  }
  ```

## 10. 函数管理 API

### 10.1 注册客户端自定义函数

**请求**：
- 方法：POST
- URL：/api/v1/functions/register
- 请求体：
  ```json
  {
    "client_id": "client_123",
    "functions": [
      {
        "name": "introduce_artifact",
        "description": "介绍文物",
        "parameters": {
          "type": "object",
          "properties": {
            "artifact_id": {
              "type": "string",
              "description": "文物ID"
            },
            "detail_level": {
              "type": "string",
              "enum": ["basic", "medium", "detailed"],
              "description": "详细程度"
            }
          },
          "required": ["artifact_id"]
        }
      }
    ]
  }
  ```

**响应**：
  ```json
  {
    "status": "success",
    "client_id": "client_123",
    "registered_functions": [
      {
        "name": "introduce_artifact",
        "description": "介绍文物",
        "parameters": {
          "type": "object",
          "properties": {
            "artifact_id": {
              "type": "string",
              "description": "文物ID"
            },
            "detail_level": {
              "type": "string",
              "enum": ["basic", "medium", "detailed"],
              "description": "详细程度"
            }
          },
          "required": ["artifact_id"]
        }
      }
    ],
    "validation_results": [
      {
        "name": "introduce_artifact",
        "status": "approved",
        "reason": "符合OpenAI标准"
      }
    ],
    "timestamp": "2023-12-01T12:00:00"
  }
  ```

### 10.2 验证函数定义

**请求**：
- 方法：POST
- URL：/api/v1/functions/validate
- 请求体：
  ```json
  {
    "name": "introduce_artifact",
    "description": "介绍文物",
    "parameters": {
      "type": "object",
      "properties": {
        "artifact_id": {
          "type": "string",
          "description": "文物ID"
        }
      },
      "required": ["artifact_id"]
    }
  }
  ```

**响应**：
  ```json
  {
    "is_valid": true,
    "function_name": "introduce_artifact",
    "validation_details": {}
  }
  ```

### 10.3 规范化函数定义

**请求**：
- 方法：POST
- URL：/api/v1/functions/normalize
- 请求体：
  ```json
  {
    "name": "introduce_artifact",
    "description": "介绍文物",
    "parameters": {
      "type": "object",
      "properties": {
        "artifact_id": {
          "type": "string",
          "description": "文物ID"
        }
      },
      "required": ["artifact_id"]
    }
  }
  ```

**响应**：
  ```json
  {
    "status": "success",
    "original_function": {
      "name": "introduce_artifact",
      "description": "介绍文物",
      "parameters": {
        "type": "object",
        "properties": {
          "artifact_id": {
            "type": "string",
            "description": "文物ID"
          }
        },
        "required": ["artifact_id"]
      }
    },
    "normalized_function": {
      "name": "introduce_artifact",
      "description": "介绍文物",
      "parameters": {
        "type": "object",
        "properties": {
          "artifact_id": {
            "type": "string",
            "description": "文物ID"
          }
        },
        "required": ["artifact_id"]
      }
    },
    "is_already_standard": true
  }
  ```

## 11. 管理员控制面板 API

### 11.1 登录页面

**请求**：
- 方法：GET
- URL：/Control/login

**响应**：
- 返回登录页面的 HTML 内容

### 11.2 获取验证码

**请求**：
- 方法：GET
- URL：/Control/api/captcha?t=1234567890

**响应**：
- 返回验证码图片的二进制数据，Content-Type: image/png

### 11.3 处理登录

**请求**：
- 方法：POST
- URL：/Control/api/login
- 请求体（form-data）：
  ```
  username: admin
  password: password123
  captcha: ABC123
  ```

**响应**：
- 登录成功：重定向到 /Control/dashboard
- 登录失败：返回包含错误信息的登录页面

### 11.4 退出登录

**请求**：
- 方法：GET
- URL：/Control/logout

**响应**：
- 重定向到 /Control/login

### 11.5 仪表盘

**请求**：
- 方法：GET
- URL：/Control/dashboard

**响应**：
- 返回仪表盘页面的 HTML 内容，显示系统配置信息

## 12. 数据结构定义

### 12.1 认证相关

#### LoginRequest
```json
{
  "username": "admin",
  "password": "password123"
}
```

#### TokenResponse
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### UserInfoResponse
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "last_login": "2023-12-01T12:00:00"
}
```

### 12.2 智能体相关

#### AgentParseRequest
```json
{
  "user_input": "介绍一下这个文物",
  "client_type": "web3d",
  "spirit_id": "",
  "scene_type": "public"
}
```

### 12.3 配置相关

#### LLMConfigUpdate
```json
{
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-1234567890abcdef",
  "model": "gpt-3.5-turbo",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

#### SRSConfigUpdate
```json
{
  "base_url": "http://localhost:12315/api/v1",
  "api_key": "srs-1234567890abcdef",
  "timeout": 30,
  "search_params": {
    "top_k": 3,
    "threshold": 0.5
  }
}
```

### 12.4 会话相关

#### ClientRegistrationRequest
```json
{
  "client_metadata": {
    "client_type": "web3d",
    "client_id": "client_123",
    "platform": "web",
    "client_version": "1.0.0"
  },
  "functions": [
    {
      "name": "introduce_artifact",
      "description": "介绍文物",
      "parameters": {
        "type": "object",
        "properties": {
          "artifact_id": {
            "type": "string",
            "description": "文物ID"
          }
        },
        "required": ["artifact_id"]
      }
    }
  ]
}
```

#### ClientRegistrationResponse
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_at": "2023-12-01T13:00:00",
  "server_timestamp": "2023-12-01T12:00:00",
  "supported_features": ["dynamic_operations", "session_management", "heartbeat", "function_calling"]
}
```

### 12.5 函数相关

#### FunctionRegistrationRequest
```json
{
  "client_id": "client_123",
  "functions": [
    {
      "name": "introduce_artifact",
      "description": "介绍文物",
      "parameters": {
        "type": "object",
        "properties": {
          "artifact_id": {
            "type": "string",
            "description": "文物ID"
          }
        },
        "required": ["artifact_id"]
      }
    }
  ]
}
```

## 13. 错误处理

### 13.1 常见错误状态码

| 状态码 | 描述 | 示例 |
|--------|------|------|
| 400 | 请求参数错误 | `{"detail": "无效的客户端注册数据格式"}` |
| 401 | 未授权 | `{"detail": "用户名或密码错误"}` |
| 404 | 资源不存在 | `{"detail": "会话不存在或已过期"}` |
| 500 | 服务器内部错误 | `{"detail": "请求处理失败: 未知错误"}` |

### 13.2 错误响应格式

大多数 API 错误响应遵循以下格式：

```json
{
  "detail": "错误信息"
}
```

部分 API 使用自定义错误响应格式，例如：

```json
{
  "code": 500,
  "msg": "请求处理失败: 未知错误"
}
```

## 14. 最佳实践

### 14.1 客户端开发建议

1. **会话管理**：
   - 客户端启动时注册会话
   - 定期发送心跳（建议每 30 秒一次）
   - 应用退出时注销会话

2. **错误处理**：
   - 正确处理 HTTP 错误状态码
   - 实现重试机制，特别是网络错误
   - 对用户友好的错误提示

3. **性能优化**：
   - 减少不必要的 API 调用
   - 缓存常用数据
   - 批量处理请求

4. **安全性**：
   - 不要在客户端存储敏感信息
   - 使用 HTTPS 协议
   - 定期更新 JWT 令牌

### 14.2 服务端部署建议

1. **配置管理**：
   - 使用环境变量或配置文件管理敏感信息
   - 定期备份配置文件
   - 不同环境使用不同配置

2. **监控与日志**：
   - 启用详细的日志记录
   - 定期检查系统状态
   - 设置告警机制

3. **扩展性**：
   - 考虑使用负载均衡
   - 数据库连接池配置
   - 合理的缓存策略

4. **安全性**：
   - 定期更新依赖包
   - 实施访问控制
   - 防止 SQL 注入和 XSS 攻击

## 15. 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2023-12-01 | 初始版本，包含完整的 API 文档 |

## 16. 联系方式

如有任何问题或建议，请联系：

- **项目地址**：https://github.com/example/museum-agent
- **邮件**：support@example.com
- **文档**：https://example.com/docs
