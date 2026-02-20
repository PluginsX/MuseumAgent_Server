# 完整架构 API 接口定义

## 📋 文档概述

本文档定义了完整架构中所有的 API 接口和消息格式。

---

## 🔌 WebSocket 通信协议

### 1. REGISTER - 会话注册（完整版）

#### 客户端 → 服务器

```json
{
    "version": "1.0",
    "msg_type": "REGISTER",
    "session_id": null,
    "payload": {
        "auth": {
            "type": "API_KEY",
            "api_key": "your_api_key_here"
        },
        "platform": "WEB",
        "require_tts": false,
        "enable_srs": true,
        "function_calling": [
            {
                "name": "play_animation",
                "description": "播放宠物动画效果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "animation_type": {
                            "type": "string",
                            "enum": ["happy", "sad", "excited", "thinking"],
                            "description": "动画类型"
                        }
                    },
                    "required": ["animation_type"]
                }
            }
        ],
        "system_prompt": {
            "role_description": "你是博物馆智能助手，专注于文物知识讲解和互动体验。你具备丰富的历史文化知识，能够用生动有趣的方式介绍文物背后的故事。",
            "response_requirements": "请用友好、专业的语言回答问题，注重知识性和趣味性的结合。回答要准确、简洁，适合普通观众理解。"
        },
        "scene_context": {
            "current_scene": "纹样展示场景",
            "scene_description": "展示中国传统纹样的艺术价值和文化内涵，包括龙纹、凤纹、云纹等经典纹样的演变历史",
            "keywords": ["纹样", "艺术", "历史", "文化"],
            "scene_specific_prompt": "重点介绍纹样的艺术特点、历史演变和文化象征意义"
        }
    },
    "timestamp": 1708444800000
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `auth` | Object | ✅ | 认证信息 |
| `auth.type` | String | ✅ | 认证类型：`API_KEY` 或 `TOKEN` |
| `auth.api_key` | String | ✅ | API 密钥 |
| `platform` | String | ❌ | 平台类型，默认 `WEB` |
| `require_tts` | Boolean | ❌ | 是否需要 TTS，默认 `false` |
| `enable_srs` | Boolean | ❌ | 是否启用 SRS，默认 `true` |
| `function_calling` | Array | ❌ | 函数定义列表，默认 `[]` |
| `system_prompt` | Object | ❌ | 系统提示词配置 |
| `system_prompt.role_description` | String | ✅ | LLM 角色描述 |
| `system_prompt.response_requirements` | String | ✅ | LLM 响应要求 |
| `scene_context` | Object | ❌ | 场景上下文配置 |
| `scene_context.current_scene` | String | ✅ | 当前场景名称 |
| `scene_context.scene_description` | String | ✅ | 场景描述 |
| `scene_context.keywords` | Array | ❌ | 场景关键词，默认 `[]` |
| `scene_context.scene_specific_prompt` | String | ❌ | 场景特定提示 |

#### 服务器 → 客户端（成功）

```json
{
    "version": "1.0",
    "msg_type": "REGISTER_SUCCESS",
    "session_id": "session_abc123def456",
    "payload": {
        "session_data": {
            "platform": "WEB",
            "require_tts": false,
            "enable_srs": true,
            "function_calling": [...],
            "create_time": 1708444800000,
            "remaining_seconds": 7200
        }
    },
    "timestamp": 1708444800100
}
```

#### 服务器 → 客户端（失败）

```json
{
    "version": "1.0",
    "msg_type": "REGISTER_FAILED",
    "session_id": null,
    "payload": {
        "error": "Authentication failed",
        "error_code": "AUTH_ERROR"
    },
    "timestamp": 1708444800100
}
```

---

### 2. REQUEST - 发送请求（完整版）

#### 客户端 → 服务器

```json
{
    "version": "1.0",
    "msg_type": "REQUEST",
    "session_id": "session_abc123def456",
    "payload": {
        "request_id": "req_xyz789",
        "data_type": "TEXT",
        "stream_flag": false,
        "stream_seq": 0,
        "require_tts": true,
        "content": {
            "text": "介绍一下青铜鼎的历史"
        },
        "update_session": {
            "system_prompt": {
                "role_description": "更新后的角色描述"
            },
            "scene_context": {
                "current_scene": "铸造工艺展示场景",
                "scene_description": "展示青铜器的铸造工艺和技术演变",
                "scene_specific_prompt": "重点介绍铸造技术的发展历程和工艺特点"
            },
            "enable_srs": true,
            "require_tts": false,
            "function_calling_op": "UPDATE",
            "function_calling": [
                {
                    "name": "show_casting_process",
                    "description": "展示铸造工艺流程",
                    "parameters": {...}
                }
            ]
        }
    },
    "timestamp": 1708444810000
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `request_id` | String | ✅ | 请求唯一标识 |
| `data_type` | String | ✅ | 数据类型：`TEXT` 或 `VOICE` |
| `stream_flag` | Boolean | ✅ | 是否为流式数据 |
| `stream_seq` | Number | ✅ | 流式序列号 |
| `require_tts` | Boolean | ❌ | 本次请求是否需要 TTS |
| `content` | Object | ✅ | 请求内容 |
| `content.text` | String | ✅ | 文本内容（TEXT 类型） |
| `content.audio` | String | ✅ | 音频数据（VOICE 类型） |
| `update_session` | Object | ❌ | 会话更新配置 |
| `update_session.system_prompt` | Object | ❌ | 更新系统提示词 |
| `update_session.scene_context` | Object | ❌ | 更新场景上下文 |
| `update_session.enable_srs` | Boolean | ❌ | 更新 SRS 开关 |
| `update_session.require_tts` | Boolean | ❌ | 更新 TTS 开关 |
| `update_session.function_calling_op` | String | ❌ | 函数操作：`REPLACE`/`ADD`/`UPDATE`/`DELETE` |
| `update_session.function_calling` | Array | ❌ | 函数定义列表 |

---

### 3. RESPONSE - 响应消息

#### 服务器 → 客户端（文本响应）

```json
{
    "version": "1.0",
    "msg_type": "RESPONSE",
    "session_id": "session_abc123def456",
    "payload": {
        "request_id": "req_xyz789",
        "data_type": "TEXT",
        "content": {
            "text": "青铜鼎是中国古代重要的礼器，始于商代，盛于周代..."
        },
        "is_final": false
    },
    "timestamp": 1708444811000
}
```

#### 服务器 → 客户端（函数调用）

```json
{
    "version": "1.0",
    "msg_type": "RESPONSE",
    "session_id": "session_abc123def456",
    "payload": {
        "request_id": "req_xyz789",
        "data_type": "TEXT",
        "content": {
            "text": "让我为你展示一下青铜鼎的详细信息。"
        },
        "function_call": {
            "name": "show_artifact_detail",
            "arguments": {
                "artifact_id": "bronze_001"
            }
        },
        "is_final": true
    },
    "timestamp": 1708444812000
}
```

#### 服务器 → 客户端（TTS 音频）

```json
{
    "version": "1.0",
    "msg_type": "RESPONSE",
    "session_id": "session_abc123def456",
    "payload": {
        "request_id": "req_xyz789",
        "data_type": "AUDIO",
        "content": {
            "audio": "base64_encoded_audio_data...",
            "format": "mp3",
            "duration": 5.2
        },
        "is_final": true
    },
    "timestamp": 1708444813000
}
```

---

### 4. HEARTBEAT - 心跳消息

#### 客户端 → 服务器

```json
{
    "version": "1.0",
    "msg_type": "HEARTBEAT",
    "session_id": "session_abc123def456",
    "payload": {},
    "timestamp": 1708444820000
}
```

#### 服务器 → 客户端

```json
{
    "version": "1.0",
    "msg_type": "HEARTBEAT_ACK",
    "session_id": "session_abc123def456",
    "payload": {
        "remaining_seconds": 7190
    },
    "timestamp": 1708444820100
}
```

---

### 5. SESSION_INFO - 会话信息查询

#### 客户端 → 服务器

```json
{
    "version": "1.0",
    "msg_type": "SESSION_INFO",
    "session_id": "session_abc123def456",
    "payload": {},
    "timestamp": 1708444830000
}
```

#### 服务器 → 客户端

```json
{
    "version": "1.0",
    "msg_type": "SESSION_INFO",
    "session_id": "session_abc123def456",
    "payload": {
        "session_data": {
            "platform": "WEB",
            "require_tts": false,
            "enable_srs": true,
            "function_calling": [...],
            "system_prompt": {
                "role_description": "你是博物馆智能助手...",
                "response_requirements": "请用友好、专业的语言..."
            },
            "scene_context": {
                "current_scene": "铸造工艺展示场景",
                "scene_description": "展示青铜器的铸造工艺...",
                "keywords": ["铸造", "工艺", "技术"],
                "scene_specific_prompt": "重点介绍铸造技术..."
            },
            "create_time": 1708444800000,
            "remaining_seconds": 7170
        }
    },
    "timestamp": 1708444830100
}
```

---

### 6. ERROR - 错误消息

#### 服务器 → 客户端

```json
{
    "version": "1.0",
    "msg_type": "ERROR",
    "session_id": "session_abc123def456",
    "payload": {
        "request_id": "req_xyz789",
        "error": "Session expired",
        "error_code": "SESSION_EXPIRED",
        "details": "The session has expired. Please register again."
    },
    "timestamp": 1708444840000
}
```

#### 错误码列表

| 错误码 | 说明 |
|--------|------|
| `AUTH_ERROR` | 认证失败 |
| `SESSION_NOT_FOUND` | 会话不存在 |
| `SESSION_EXPIRED` | 会话已过期 |
| `INVALID_REQUEST` | 无效的请求 |
| `INVALID_MESSAGE_FORMAT` | 消息格式错误 |
| `SRS_ERROR` | SRS 服务错误 |
| `LLM_ERROR` | LLM 服务错误 |
| `TTS_ERROR` | TTS 服务错误 |
| `INTERNAL_ERROR` | 内部错误 |

---

## 📊 数据流示例

### 完整对话流程

```
1. 客户端注册会话
   ↓
   REGISTER (包含 system_prompt 和 scene_context)
   ↓
   REGISTER_SUCCESS (返回 session_id)

2. 客户端发送第一个问题
   ↓
   REQUEST (user_input: "介绍一下青铜鼎")
   ↓
   服务器从会话获取配置
   ↓
   服务器调用 SRS API（因为 enable_srs = true）
   ↓
   服务器构建提示词
   ↓
   服务器调用 LLM API
   ↓
   RESPONSE (流式返回文本)
   ↓
   RESPONSE (is_final: true)
   ↓
   RESPONSE (TTS 音频，如果 require_tts = true)

3. 客户端切换场景并发送第二个问题
   ↓
   REQUEST (
       user_input: "介绍铸造工艺",
       update_session: {
           scene_context: {
               current_scene: "铸造工艺场景"
           }
       }
   )
   ↓
   服务器更新会话配置
   ↓
   服务器从会话获取新配置
   ↓
   服务器调用 SRS API
   ↓
   服务器构建提示词（使用新的场景配置）
   ↓
   服务器调用 LLM API
   ↓
   RESPONSE (流式返回文本)
   ↓
   RESPONSE (函数调用: show_casting_process)
   ↓
   RESPONSE (is_final: true)

4. 客户端定期发送心跳
   ↓
   HEARTBEAT
   ↓
   HEARTBEAT_ACK (remaining_seconds: 7000)

5. 客户端查询会话信息
   ↓
   SESSION_INFO
   ↓
   SESSION_INFO (返回完整会话配置)
```

---

## 🔧 客户端 SDK API

### MuseumAgentSDK 类

```javascript
class MuseumAgentSDK {
    /**
     * 连接并注册
     * @param {Object} config - 完整配置
     * @returns {Promise<Object>} 注册结果
     */
    async connect(config) {
        // config 结构：
        // {
        //     auth: { type: 'API_KEY', api_key: 'xxx' },
        //     platform: 'WEB',
        //     require_tts: false,
        //     enable_srs: true,
        //     function_calling: [...],
        //     system_prompt: {
        //         role_description: '...',
        //         response_requirements: '...'
        //     },
        //     scene_context: {
        //         current_scene: '...',
        //         scene_description: '...',
        //         keywords: [...],
        //         scene_specific_prompt: '...'
        //     }
        // }
    }
    
    /**
     * 发送文本消息
     * @param {string} text - 用户输入
     * @param {Object} options - 可选配置
     * @returns {string} 请求ID
     */
    sendText(text, options = {}) {
        // options 结构：
        // {
        //     requireTTS: false,
        //     enableSRS: true,
        //     systemPrompt: { ... },      // 可选：更新系统提示词
        //     sceneContext: { ... },      // 可选：更新场景上下文
        //     functionCallingOp: 'UPDATE',
        //     functionCalling: [...]
        // }
    }
    
    /**
     * 开始录音
     * @param {Object} options - 可选配置
     * @returns {string} 请求ID
     */
    startRecording(options = {}) {
        // 同 sendText 的 options
    }
    
    /**
     * 停止录音
     */
    stopRecording() {}
    
    /**
     * 断开连接
     */
    disconnect() {}
    
    /**
     * 查询会话信息
     * @returns {Promise<Object>} 会话信息
     */
    async getSessionInfo() {}
}
```

### 事件监听

```javascript
// 连接成功
sdk.on('connected', (data) => {
    console.log('Session ID:', data.session_id);
    console.log('Session Data:', data.session_data);
});

// 接收响应
sdk.on('response', (data) => {
    console.log('Text:', data.text);
    console.log('Is Final:', data.isFinal);
    console.log('Function Call:', data.functionCall);
});

// 接收音频
sdk.on('audio', (data) => {
    console.log('Audio Data:', data.audio);
    console.log('Format:', data.format);
});

// 错误
sdk.on('error', (error) => {
    console.error('Error:', error);
});

// 断开连接
sdk.on('disconnected', () => {
    console.log('Disconnected');
});
```

---

## 📝 使用示例

### 基本使用

```javascript
import { MuseumAgentSDK } from './lib/MuseumAgentSDK.js';

// 创建 SDK 实例
const sdk = new MuseumAgentSDK('ws://localhost:8000/ws');

// 配置
const config = {
    auth: {
        type: 'API_KEY',
        api_key: 'your_api_key'
    },
    platform: 'WEB',
    require_tts: true,
    enable_srs: true,
    system_prompt: {
        role_description: '你是博物馆智能助手',
        response_requirements: '请用友好、专业的语言回答'
    },
    scene_context: {
        current_scene: '纹样展示场景',
        scene_description: '展示中国传统纹样',
        keywords: ['纹样', '艺术'],
        scene_specific_prompt: '重点介绍纹样的艺术特点'
    },
    function_calling: [
        {
            name: 'play_animation',
            description: '播放动画',
            parameters: {...}
        }
    ]
};

// 连接
await sdk.connect(config);

// 发送消息
sdk.sendText('介绍一下青铜鼎');

// 监听响应
sdk.on('response', (data) => {
    console.log(data.text);
});
```

### 动态切换场景

```javascript
// 切换到铸造工艺场景
sdk.sendText('介绍铸造工艺', {
    sceneContext: {
        current_scene: '铸造工艺展示场景',
        scene_description: '展示青铜器的铸造工艺',
        scene_specific_prompt: '重点介绍铸造技术'
    }
});
```

### 动态更新系统提示词

```javascript
// 切换到儿童模式
sdk.sendText('介绍一下青铜鼎', {
    systemPrompt: {
        role_description: '你是博物馆儿童讲解员',
        response_requirements: '请用简单易懂的语言，适合儿童理解'
    }
});
```

---

**上一步**: [COMPLETE_ARCHITECTURE_IMPL.md](./COMPLETE_ARCHITECTURE_IMPL.md)  
**返回**: [COMPLETE_ARCHITECTURE.md](./COMPLETE_ARCHITECTURE.md)

