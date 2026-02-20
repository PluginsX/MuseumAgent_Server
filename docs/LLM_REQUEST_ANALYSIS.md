# MuseumAgent 服务器 LLM API 请求构建流程分析

## 📋 概述

本文档详细分析 MuseumAgent 服务器如何构建最终发送给 LLM API 的请求，包括提示词构建、参数配置和完整的调用链路。

---

## 🔄 完整调用链路

```
客户端请求
    ↓
WebSocket 协议层 (agent_stream_router)
    ↓
CommandGenerator (协调器)
    ↓
├─ SemanticRetrievalProcessor (RAG检索)
├─ PromptBuilder (提示词构建)
└─ DynamicLLMClient (LLM调用)
    ↓
外部 LLM API (OpenAI 兼容)
```

---

## 📝 详细流程分析

### 1. 客户端请求接收

**位置**: WebSocket 协议层

**接收的参数**：
```python
{
    "version": "1.0",
    "msg_type": "REQUEST",
    "session_id": "session_xxx",
    "payload": {
        "request_id": "req_xxx",
        "data_type": "TEXT" | "VOICE",
        "require_tts": true | false,      # ✅ 客户端配置
        "enable_srs": true | false,       # ✅ 客户端配置
        "content": {
            "text": "用户输入的文本"
        },
        "function_calling": [...]          # ✅ 客户端配置
    }
}
```

**关键配置参数**：
- `require_tts`: 是否需要 TTS 语音合成
- `enable_srs`: 是否启用语义检索系统 (SRS)
- `function_calling`: 函数调用定义列表

---

### 2. CommandGenerator 协调处理

**位置**: `src/core/command_generator.py`

**核心方法**: `generate_standard_command()`

#### 步骤 1: 检查 EnableSRS 配置

```python
# 从会话中获取 EnableSRS 配置
session = strict_session_manager.get_session(session_id)
enable_srs = session.client_metadata.get("enable_srs", True)

print(f"[Coordinator] EnableSRS 配置: {enable_srs}")
```

**说明**：
- 客户端发送的 `enable_srs` 参数会保存到会话的 `client_metadata` 中
- 每次请求都会从会话中读取最新的配置

#### 步骤 2: 条件执行 RAG 检索

```python
rag_context = None
if enable_srs:
    print(f"[Coordinator] 执行 RAG 检索（EnableSRS=True）")
    rag_context = self._perform_rag_retrieval(user_input, session_id=session_id)
else:
    print(f"[Coordinator] 跳过 RAG 检索（EnableSRS=False）")
```

**RAG 检索结果示例**：
```python
{
    "artifacts": [
        {
            "id": "artifact_001",
            "name": "青铜鼎",
            "content": "商代青铜器，用于祭祀...",
            "score": 0.85
        },
        {
            "id": "artifact_002",
            "name": "玉璧",
            "content": "西周玉器，象征权力...",
            "score": 0.78
        }
    ],
    "timestamp": "2026-02-19T23:45:00"
}
```

#### 步骤 3: 获取函数定义

```python
# 从会话中获取 OpenAI 标准函数定义
functions = strict_session_manager.get_functions_for_session(session_id)

print(f"[Coordinator] 获取到的函数数量: {len(functions)}")
```

**函数定义示例**：
```python
[
    {
        "name": "play_animation",
        "description": "播放宠物动画",
        "parameters": {
            "type": "object",
            "properties": {
                "animation": {
                    "type": "string",
                    "enum": ["idle", "walk", "run", "jump"],
                    "description": "动画类型"
                }
            },
            "required": ["animation"]
        }
    }
]
```

#### 步骤 4: 构建 RAG 指令

**位置**: `src/core/modules/prompt_builder.py`

```python
def build_rag_instruction(self, rag_context: Dict[str, Any]) -> str:
    """构建 RAG 增强指令"""
    artifacts = rag_context.get("artifacts", [])
    
    if not artifacts:
        return ""
    
    instruction = "以下是检索到的相关文物信息：\n\n"
    
    for i, artifact in enumerate(artifacts, 1):
        instruction += f"{i}. {artifact.get('name', '未知文物')}\n"
        instruction += f"   {artifact.get('content', '无描述')}\n"
        instruction += f"   相关度: {artifact.get('score', 0):.2f}\n\n"
    
    instruction += "请基于以上信息回答用户问题。"
    
    return instruction
```

**生成的 RAG 指令示例**：
```
以下是检索到的相关文物信息：

1. 青铜鼎
   商代青铜器，用于祭祀...
   相关度: 0.85

2. 玉璧
   西周玉器，象征权力...
   相关度: 0.78

请基于以上信息回答用户问题。
```

---

### 3. DynamicLLMClient 构建请求

**位置**: `src/core/dynamic_llm_client.py`

**核心方法**: `generate_function_calling_payload()`

#### 完整的请求构建逻辑

```python
def generate_function_calling_payload(
    self, 
    session_id: str, 
    user_input: str, 
    scene_type: str = "public", 
    rag_instruction: str = "", 
    functions: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """生成 OpenAI 标准函数调用格式的请求"""
    
    # 1. 构建系统消息
    system_message = (
        "你是智能助手。必须遵守以下规则：\n"
        "1. 每次响应都必须包含自然语言对话内容；\n"
        "2. 在调用函数时，要先解释将要做什么；\n"
        "3. 用友好自然的语言与用户交流。"
    )
    
    # 2. 构建用户消息（包含场景和 RAG 信息）
    user_message = f"场景：{scene_type}\n"
    
    if rag_instruction:
        user_message += f"{rag_instruction}\n"
    
    user_message += f"用户输入：{user_input}"
    
    # 3. 构建消息列表
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    # 4. 构建基础 payload
    payload = {
        "model": self.model,  # 从配置读取，如 "qwen-turbo"
        "messages": messages,
        "temperature": self.parameters.get("temperature", 0.1),
        "max_tokens": self.parameters.get("max_tokens", 1024),
        "top_p": self.parameters.get("top_p", 0.1),
    }
    
    # 5. 添加函数定义（如果有）
    if functions and len(functions) > 0:
        payload["functions"] = functions
        payload["function_call"] = "auto"
        print(f"[LLM] 已添加 {len(functions)} 个函数定义")
    else:
        print("[LLM] 未提供函数定义，使用普通对话模式")
        messages[0]["content"] = (
            f"{system_message}\n\n"
            "当前处于普通对话模式，请以友好、专业的态度回答用户问题。"
        )
    
    return payload
```

---

### 4. 最终发送的 LLM API 请求

#### 场景 A: 启用 SRS + 有函数定义

**完整请求示例**：
```json
{
  "model": "qwen-turbo",
  "messages": [
    {
      "role": "system",
      "content": "你是智能助手。必须遵守以下规则：\n1. 每次响应都必须包含自然语言对话内容；\n2. 在调用函数时，要先解释将要做什么；\n3. 用友好自然的语言与用户交流。"
    },
    {
      "role": "user",
      "content": "场景：public\n以下是检索到的相关文物信息：\n\n1. 青铜鼎\n   商代青铜器，用于祭祀...\n   相关度: 0.85\n\n2. 玉璧\n   西周玉器，象征权力...\n   相关度: 0.78\n\n请基于以上信息回答用户问题。\n用户输入：介绍一下青铜鼎"
    }
  ],
  "temperature": 0.1,
  "max_tokens": 1024,
  "top_p": 0.1,
  "functions": [
    {
      "name": "play_animation",
      "description": "播放宠物动画",
      "parameters": {
        "type": "object",
        "properties": {
          "animation": {
            "type": "string",
            "enum": ["idle", "walk", "run", "jump"],
            "description": "动画类型"
          }
        },
        "required": ["animation"]
      }
    }
  ],
  "function_call": "auto"
}
```

#### 场景 B: 禁用 SRS + 无函数定义

**完整请求示例**：
```json
{
  "model": "qwen-turbo",
  "messages": [
    {
      "role": "system",
      "content": "你是智能助手。必须遵守以下规则：\n1. 每次响应都必须包含自然语言对话内容；\n2. 在调用函数时，要先解释将要做什么；\n3. 用友好自然的语言与用户交流。\n\n当前处于普通对话模式，请以友好、专业的态度回答用户问题。"
    },
    {
      "role": "user",
      "content": "场景：public\n用户输入：你好"
    }
  ],
  "temperature": 0.1,
  "max_tokens": 1024,
  "top_p": 0.1
}
```

#### 场景 C: 启用 SRS + 无函数定义

**完整请求示例**：
```json
{
  "model": "qwen-turbo",
  "messages": [
    {
      "role": "system",
      "content": "你是智能助手。必须遵守以下规则：\n1. 每次响应都必须包含自然语言对话内容；\n2. 在调用函数时，要先解释将要做什么；\n3. 用友好自然的语言与用户交流。\n\n当前处于普通对话模式，请以友好、专业的态度回答用户问题。"
    },
    {
      "role": "user",
      "content": "场景：public\n以下是检索到的相关文物信息：\n\n1. 青铜鼎\n   商代青铜器，用于祭祀...\n   相关度: 0.85\n\n请基于以上信息回答用户问题。\n用户输入：介绍一下青铜鼎"
    }
  ],
  "temperature": 0.1,
  "max_tokens": 1024,
  "top_p": 0.1
}
```

---

## 🔧 配置参数来源

### 1. LLM 基础配置

**来源**: `config.json` 或环境变量

```json
{
  "llm": {
    "base_url": "https://api.example.com/v1",
    "api_key": "sk-xxx",
    "model": "qwen-turbo",
    "parameters": {
      "temperature": 0.1,
      "max_tokens": 1024,
      "top_p": 0.1
    }
  }
}
```

### 2. 客户端动态配置

**来源**: 客户端每次请求携带

```python
# 从客户端请求中提取
payload = message.get("payload", {})
require_tts = payload.get("require_tts", False)
enable_srs = payload.get("enable_srs", True)
function_calling = payload.get("function_calling", [])

# 保存到会话
session.client_metadata["require_tts"] = require_tts
session.client_metadata["enable_srs"] = enable_srs
session.client_metadata["function_calling"] = function_calling
```

### 3. 会话配置

**来源**: 会话管理器

```python
# 从会话中读取配置
session = strict_session_manager.get_session(session_id)
enable_srs = session.client_metadata.get("enable_srs", True)
functions = session.client_metadata.get("function_calling", [])
```

---

## 📊 参数优先级

```
客户端请求参数 > 会话配置 > 服务器默认配置
```

**示例**：
1. 客户端发送 `enable_srs: false`
2. 保存到会话: `session.client_metadata["enable_srs"] = false`
3. 下次请求从会话读取: `enable_srs = session.client_metadata.get("enable_srs", True)`
4. 如果会话中没有，使用默认值 `True`

---

## 🎯 关键决策点

### 决策 1: 是否执行 RAG 检索

```python
if enable_srs:
    # 执行 RAG 检索
    rag_context = self._perform_rag_retrieval(user_input)
    rag_instruction = self._build_rag_instruction(rag_context)
else:
    # 跳过 RAG 检索
    rag_instruction = ""
```

**影响**：
- `enable_srs = true`: 提示词包含检索到的文物信息
- `enable_srs = false`: 提示词只包含用户输入

### 决策 2: 是否启用函数调用

```python
if functions and len(functions) > 0:
    # 启用函数调用模式
    payload["functions"] = functions
    payload["function_call"] = "auto"
else:
    # 普通对话模式
    # 不添加 functions 字段
```

**影响**：
- 有函数定义: LLM 可以调用函数
- 无函数定义: LLM 只返回文本响应

### 决策 3: 是否调用 TTS

```python
# 在响应处理阶段
if require_tts:
    # 调用 TTS 服务
    tts_audio = await tts_service.synthesize_text(llm_response)
else:
    # 不调用 TTS
    tts_audio = None
```

**影响**：
- `require_tts = true`: 返回文本 + 语音
- `require_tts = false`: 只返回文本

---

## 🔍 调试日志示例

```
[Coordinator] 开始OpenAI标准函数调用流程
[Coordinator] EnableSRS 配置: True
[Coordinator] 步骤1: 执行 RAG 检索（EnableSRS=True）
[RAG] 检索到 2 个相关文物
[Coordinator] 步骤2: 获取函数定义（可能为空）
[Coordinator] Session ID: session_xxx
[Coordinator] 获取到的函数数量: 1
[Coordinator] 函数列表: ['play_animation']
[Coordinator] 步骤3: 构建基于Function Calling的提示词
[Coordinator] 步骤4: 生成OpenAI标准函数调用请求
[DEBUG] 发送到LLM的请求负载:
{
  "model": "qwen-turbo",
  "messages": [...],
  "temperature": 0.1,
  "max_tokens": 1024,
  "top_p": 0.1,
  "functions": [...],
  "function_call": "auto"
}
[Coordinator] 步骤5: 调用LLM处理函数调用
[LLM] Sending function call request to LLM
[LLM] Successfully received LLM response
[DEBUG] LLM原始响应:
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "好的，让我为你介绍青铜鼎...",
        "function_call": {
          "name": "play_animation",
          "arguments": "{\"animation\": \"idle\"}"
        }
      }
    }
  ]
}
[Coordinator] 步骤6: 直接转发LLM原始响应
[Coordinator] 处理完成，直接转发LLM原始响应
```

---

## 📝 总结

### 提示词构建流程

```
1. 系统消息（固定）
   ↓
2. 场景信息（scene_type）
   ↓
3. RAG 检索结果（如果 enable_srs = true）
   ↓
4. 用户输入
   ↓
5. 函数定义（如果有）
```

### API 参数构建流程

```
1. 基础参数（model, temperature, max_tokens, top_p）
   ← 从 config.json 读取
   ↓
2. 消息列表（messages）
   ← 从提示词构建
   ↓
3. 函数定义（functions, function_call）
   ← 从会话配置读取
   ↓
4. 发送到 LLM API
```

### 配置参数流转

```
客户端设置面板
    ↓
WebSocket 请求 payload
    ↓
会话 client_metadata
    ↓
CommandGenerator 读取
    ↓
DynamicLLMClient 使用
    ↓
LLM API 请求
```

---

**所有配置参数都能正确传递并影响最终的 LLM 请求！** ✅

