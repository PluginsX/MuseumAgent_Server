# MuseumAgent 完整架构设计文档

## 📋 文档概述

本文档描述了 MuseumAgent 系统从客户端配置到 LLM 调用的完整流程架构。

**版本**: 2.0  
**更新日期**: 2026-02-20  
**状态**: 设计完成，待实施

---

## 🎯 核心设计理念

### 设计原则
1. **职责分离**：客户端负责配置，服务器负责处理
2. **会话中心**：所有配置数据存储在会话中
3. **动态更新**：支持运行时更新配置
4. **实时获取**：服务器从会话实时获取配置
5. **按需检索**：根据配置按需调用 SRS API

### 五大核心流程
```
1. 客户端定义基本信息和配置
   ↓
2. 会话注册和缓存数据
   ↓
3. 服务器根据要求选择性查询 SRS 获取相关资料
   ↓
4. 最终提示词构建
   ↓
5. 调用 LLM API
```

---

## 📐 完整数据结构设计

### 1. 客户端配置数据结构

客户端在注册时提供的完整配置：

```javascript
// 客户端配置对象
const clientConfig = {
    // ===== 认证信息 =====
    auth: {
        type: "API_KEY",           // 认证类型：API_KEY | TOKEN
        api_key: "your_api_key"    // API 密钥
    },
    
    // ===== 平台信息 =====
    platform: "WEB",               // 平台类型：WEB | MOBILE | DESKTOP
    
    // ===== 系统提示词配置 =====
    system_prompt: {
        role_description: "你是博物馆智能助手，专注于文物知识讲解和互动体验。你具备丰富的历史文化知识，能够用生动有趣的方式介绍文物背后的故事。",
        response_requirements: "请用友好、专业的语言回答问题，注重知识性和趣味性的结合。回答要准确、简洁，适合普通观众理解。"
    },
    
    // ===== 场景上下文配置 =====
    scene_context: {
        current_scene: "纹样展示场景",
        scene_description: "展示中国传统纹样的艺术价值和文化内涵，包括龙纹、凤纹、云纹等经典纹样的演变历史",
        keywords: ["纹样", "艺术", "历史", "文化"],
        scene_specific_prompt: "重点介绍纹样的艺术特点、历史演变和文化象征意义"
    },
    
    // ===== 功能开关配置 =====
    require_tts: true,             // 是否需要 TTS 语音合成
    enable_srs: true,              // 是否启用 SRS 检索增强
    
    // ===== 函数调用配置 =====
    function_calling: [
        {
            name: "play_animation",
            description: "播放宠物动画效果",
            parameters: {
                type: "object",
                properties: {
                    animation_type: {
                        type: "string",
                        enum: ["happy", "sad", "excited", "thinking"],
                        description: "动画类型"
                    }
                },
                required: ["animation_type"]
            }
        },
        {
            name: "show_artifact_detail",
            description: "显示文物详细信息",
            parameters: {
                type: "object",
                properties: {
                    artifact_id: {
                        type: "string",
                        description: "文物ID"
                    }
                },
                required: ["artifact_id"]
            }
        }
    ]
};
```

### 2. 会话存储数据结构

服务器端会话中存储的完整数据：

```python
# EnhancedClientSession 数据结构
@dataclass
class EnhancedClientSession:
    # ===== 会话基本信息 =====
    session_id: str                    # 会话唯一标识
    created_at: datetime               # 创建时间
    last_heartbeat: datetime           # 最后心跳时间
    last_activity: datetime            # 最后活动时间
    expires_at: datetime               # 过期时间
    is_registered: bool = True         # 是否已注册
    
    # ===== 客户端元数据（完整配置）=====
    client_metadata: Dict[str, Any] = {
        # --- 平台信息 ---
        "platform": "WEB",
        "client_type": "WEB",          # 兼容旧版
        
        # --- 系统提示词配置 ---
        "system_prompt": {
            "role_description": "你是博物馆智能助手...",
            "response_requirements": "请用友好、专业的语言..."
        },
        
        # --- 场景上下文配置 ---
        "scene_context": {
            "current_scene": "纹样展示场景",
            "scene_description": "展示中国传统纹样...",
            "keywords": ["纹样", "艺术", "历史"],
            "scene_specific_prompt": "重点介绍纹样的艺术特点..."
        },
        
        # --- 功能开关配置 ---
        "require_tts": True,           # TTS 开关
        "enable_srs": True,            # SRS 开关
        
        # --- 函数调用配置 ---
        "functions": [                 # OpenAI 标准函数定义列表
            {
                "name": "play_animation",
                "description": "播放宠物动画效果",
                "parameters": {...}
            }
        ],
        "function_names": ["play_animation", "show_artifact_detail"]
    }
```

### 3. 请求消息数据结构

客户端发送请求时的消息格式：

```javascript
// REQUEST 消息格式
const requestMessage = {
    version: "1.0",
    msg_type: "REQUEST",
    session_id: "session_abc123",
    payload: {
        // --- 请求基本信息 ---
        request_id: "req_xyz789",
        data_type: "TEXT",         // TEXT | VOICE
        stream_flag: false,
        stream_seq: 0,
        
        // --- 请求内容 ---
        content: {
            text: "介绍一下青铜鼎的历史"
        },
        
        // --- 可选：动态更新会话配置 ---
        update_session: {
            // 更新系统提示词（可选）
            system_prompt: {
                role_description: "更新后的角色描述"
            },
            
            // 更新场景上下文（可选）
            scene_context: {
                current_scene: "铸造工艺展示场景",
                scene_description: "展示青铜器的铸造工艺和技术演变"
            },
            
            // 更新功能开关（可选）
            enable_srs: true,
            require_tts: false,
            
            // 更新函数定义（可选）
            function_calling_op: "UPDATE",  // REPLACE | ADD | UPDATE | DELETE
            function_calling: [
                {
                    name: "show_casting_process",
                    description: "展示铸造工艺流程",
                    parameters: {...}
                }
            ]
        }
    },
    timestamp: 1708444800000
};
```

### 4. SRS 检索结果数据结构

服务器调用 SRS API 后的检索结果：

```python
# SRS 检索结果（服务器内部使用，不存储）
srs_result = {
    "query": "青铜鼎的历史",
    "documents": [
        {
            "content": "青铜鼎是中国古代重要的礼器，始于商代，盛于周代。鼎最初用于烹煮食物，后来演变为祭祀和权力的象征。",
            "score": 0.95,
            "metadata": {
                "source": "文物数据库",
                "artifact_id": "bronze_001"
            }
        },
        {
            "content": "著名的司母戊鼎是商代晚期的青铜器，重达832.84公斤，是目前已知最大的青铜鼎。",
            "score": 0.88,
            "metadata": {
                "source": "文物数据库",
                "artifact_id": "bronze_002"
            }
        }
    ],
    "total_results": 2
}

# 整合后的 RAG 指令
rag_instruction = """
参考资料：
1. 青铜鼎是中国古代重要的礼器，始于商代，盛于周代。鼎最初用于烹煮食物，后来演变为祭祀和权力的象征。
2. 著名的司母戊鼎是商代晚期的青铜器，重达832.84公斤，是目前已知最大的青铜鼎。

请基于以上参考资料回答用户问题。
"""
```

### 5. LLM API 请求数据结构

服务器构建的最终 LLM API 请求：

```python
# OpenAI 标准格式的 LLM API 请求
llm_request = {
    "model": "qwen-turbo",
    "messages": [
        {
            "role": "system",
            "content": """你是博物馆智能助手，专注于文物知识讲解和互动体验。你具备丰富的历史文化知识，能够用生动有趣的方式介绍文物背后的故事。

请用友好、专业的语言回答问题，注重知识性和趣味性的结合。回答要准确、简洁，适合普通观众理解。

必须遵守以下规则：
1. 每次响应都必须包含自然语言对话内容；
2. 在调用函数时，要先解释将要做什么；
3. 用友好自然的语言与用户交流。"""
        },
        {
            "role": "user",
            "content": """展示中国传统纹样的艺术价值和文化内涵，包括龙纹、凤纹、云纹等经典纹样的演变历史
重点介绍纹样的艺术特点、历史演变和文化象征意义

参考资料：
1. 青铜鼎是中国古代重要的礼器，始于商代，盛于周代。鼎最初用于烹煮食物，后来演变为祭祀和权力的象征。
2. 著名的司母戊鼎是商代晚期的青铜器，重达832.84公斤，是目前已知最大的青铜鼎。

请基于以上参考资料回答用户问题。

用户输入：介绍一下青铜鼎的历史"""
        }
    ],
    "functions": [
        {
            "name": "play_animation",
            "description": "播放宠物动画效果",
            "parameters": {...}
        },
        {
            "name": "show_artifact_detail",
            "description": "显示文物详细信息",
            "parameters": {...}
        }
    ],
    "function_call": "auto",
    "temperature": 0.1,
    "max_tokens": 1024,
    "top_p": 0.1,
    "stream": True
}
```

---

## 🔄 完整流程详解

详细的流程设计请参考：
- [流程阶段 1-2](./COMPLETE_ARCHITECTURE_FLOW_1.md) - 客户端配置与会话注册
- [流程阶段 3-5](./COMPLETE_ARCHITECTURE_FLOW_2.md) - SRS 检索、提示词构建与 LLM 调用
- [实现细节](./COMPLETE_ARCHITECTURE_IMPL.md) - 服务器端和客户端实现
- [API 接口](./COMPLETE_ARCHITECTURE_API.md) - 完整的 API 接口定义

---

## 📊 架构总览图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │SettingsPanel │    │  ChatWindow  │    │ AudioManager │     │
│  │  配置面板    │    │   聊天窗口   │    │  音频管理器  │     │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘     │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┘              │
│                             │                                   │
│                    ┌────────▼────────┐                         │
│                    │ MuseumAgentSDK  │                         │
│                    │   主SDK接口     │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐              │
│         │                   │                   │              │
│  ┌──────▼───────┐  ┌────────▼────────┐  ┌──────▼───────┐     │
│  │SendManager   │  │WebSocketClient  │  │ReceiveManager│     │
│  │  发送管理器  │  │  WebSocket客户端│  │  接收管理器  │     │
│  └──────────────┘  └────────┬────────┘  └──────────────┘     │
│                             │                                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │ WebSocket
                              │ 连接
┌─────────────────────────────┼───────────────────────────────────┐
│                         服务器层                                 │
├─────────────────────────────┼───────────────────────────────────┤
│                             │                                   │
│                    ┌────────▼────────┐                         │
│                    │ WebSocket Router│                         │
│                    │  消息路由器     │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐              │
│         │                   │                   │              │
│  ┌──────▼───────┐  ┌────────▼────────┐  ┌──────▼───────┐     │
│  │Session API   │  │  Request API    │  │ Response API │     │
│  │  会话接口    │  │   请求接口      │  │  响应接口    │     │
│  └──────┬───────┘  └────────┬────────┘  └──────────────┘     │
│         │                   │                                   │
│  ┌──────▼──────────────────┐│                                   │
│  │StrictSessionManager     ││                                   │
│  │  会话管理器             ││                                   │
│  │  ┌──────────────────┐  ││                                   │
│  │  │client_metadata   │  ││                                   │
│  │  │ - system_prompt  │  ││                                   │
│  │  │ - scene_context  │  ││                                   │
│  │  │ - enable_srs     │  ││                                   │
│  │  │ - functions      │  ││                                   │
│  │  └──────────────────┘  ││                                   │
│  └─────────────────────────┘│                                   │
│                             │                                   │
│                    ┌────────▼────────┐                         │
│                    │ CommandGenerator│                         │
│                    │  命令生成器     │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐              │
│         │                   │                   │              │
│  ┌──────▼───────┐  ┌────────▼────────┐  ┌──────▼───────┐     │
│  │  SRS Client  │  │DynamicLLMClient │  │  TTS Client  │     │
│  │  检索客户端  │  │  LLM客户端      │  │  语音客户端  │     │
│  └──────┬───────┘  └────────┬────────┘  └──────────────┘     │
│         │                   │                                   │
└─────────┼───────────────────┼───────────────────────────────────┘
          │                   │
┌─────────┼───────────────────┼───────────────────────────────────┐
│     外部服务层              │                                   │
├─────────┼───────────────────┼───────────────────────────────────┤
│         │                   │                                   │
│  ┌──────▼───────┐  ┌────────▼────────┐                         │
│  │   SRS API    │  │   LLM API       │                         │
│  │  检索增强服务│  │  (Qwen/GPT)     │                         │
│  └──────────────┘  └─────────────────┘                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 核心特性

### 1. 配置灵活性
- ✅ 客户端完全控制系统提示词
- ✅ 客户端完全控制场景上下文
- ✅ 支持运行时动态更新配置
- ✅ 支持多场景切换

### 2. 职责清晰
- ✅ 客户端：配置提供者
- ✅ 服务器：数据处理者和 API 调用者
- ✅ SRS：由服务器按需调用
- ✅ 会话：配置存储中心

### 3. 性能优化
- ✅ 配置存储在会话中，避免重复传输
- ✅ SRS 结果不存储，按需检索
- ✅ 支持流式响应
- ✅ 异步处理

### 4. 扩展性
- ✅ 易于添加新的配置项
- ✅ 易于添加新的函数定义
- ✅ 易于切换不同的 LLM 模型
- ✅ 易于集成新的检索服务

---

## 📝 下一步

1. 查看详细流程：[COMPLETE_ARCHITECTURE_FLOW_1.md](./COMPLETE_ARCHITECTURE_FLOW_1.md)
2. 查看实现细节：[COMPLETE_ARCHITECTURE_IMPL.md](./COMPLETE_ARCHITECTURE_IMPL.md)
3. 查看 API 接口：[COMPLETE_ARCHITECTURE_API.md](./COMPLETE_ARCHITECTURE_API.md)
4. 开始实施升级

---

**文档版本**: 2.0  
**最后更新**: 2026-02-20  
**维护者**: MuseumAgent Team

