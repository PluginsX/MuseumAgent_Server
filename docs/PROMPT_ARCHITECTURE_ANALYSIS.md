# 提示词构建架构分析报告

## 一、设计图架构概览

根据你提供的设计图，提示词构建应包含以下信息来源：

### 1. 客户端配置（绿色路径）
- **客户端基本配置**：Platform, RequireTTS, EnableSRS, AutoPlay
- **智能体角色配置**：角色描述、响应要求
- **上下文配置**：场景描述、绝望描述

### 2. 会话配置（红色路径）
- **智能体角色配置**：角色描述、响应要求
- **上下文配置**：场景描述、绝望描述

### 3. FunctionCalling（蓝色路径）
- **FunctionCalling**：Function(), Function(), Function()
- VAD配置、EnableVAD、Silence Threshold等

### 4. 用户消息（白色路径）
- **用户消息**：用户内容

### 5. SRS服务（白色路径）
- **SRS服务**：相关资料

## 二、实际实现分析

### ✅ 符合设计的部分

#### 1. 会话配置支持（红色路径）✅
**位置**：`agent_handler.py` + `strict_session_manager.py`

```python
# 支持从客户端更新会话配置
if "system_prompt" in update_session:
    strict_session_manager.update_session_attributes(
        session_id, system_prompt=update_session["system_prompt"]
    )

if "scene_context" in update_session:
    strict_session_manager.update_session_attributes(
        session_id, scene_context=update_session["scene_context"]
    )
```

#### 2. 提示词构建使用会话配置（红色路径）✅
**位置**：`dynamic_llm_client.py` - `generate_function_calling_payload()`

```python
# 从会话获取系统提示词配置
system_prompt_config = session.client_metadata.get("system_prompt", {})
role_description = system_prompt_config.get("role_description", "你是智能助手。")
response_requirements = system_prompt_config.get("response_requirements", "...")

# 从会话获取场景上下文配置
scene_context_config = session.client_metadata.get("scene_context", {})
scene_description = scene_context_config.get("scene_description", f"场景：{scene_type}")
scene_specific_prompt = scene_context_config.get("scene_specific_prompt", "")
```

#### 3. FunctionCalling支持（蓝色路径）✅
**位置**：`agent_handler.py` + `dynamic_llm_client.py`

```python
# 从会话获取函数定义
functions = strict_session_manager.get_functions_for_session(session_id)

# 添加到LLM请求
if functions and len(functions) > 0:
    payload["functions"] = functions
    payload["function_call"] = "auto"
```

#### 4. SRS检索支持（白色路径）✅
**位置**：`command_generator.py` + `semantic_retrieval_processor.py`

```python
# 根据EnableSRS决定是否执行RAG检索
enable_srs = session.client_metadata.get("enable_srs", True)
if enable_srs:
    rag_context = self._perform_rag_retrieval(user_input, session_id=session_id)
    rag_instruction = self._build_rag_instruction(rag_context)
```

#### 5. 用户消息支持（白色路径）✅
**位置**：`dynamic_llm_client.py`

```python
user_message_parts.append(f"用户输入：{user_input}")
```

### ⚠️ 与设计图的差异

#### 1. 缺少客户端基本配置的直接使用（绿色路径部分缺失）
**问题**：Platform, RequireTTS, EnableSRS, AutoPlay 等配置存储在会话中，但**未直接用于提示词构建**

**当前实现**：
- Platform：仅用于日志记录
- RequireTTS：仅控制TTS流程，不影响提示词
- EnableSRS：控制是否执行RAG检索 ✅
- AutoPlay：未在代码中找到使用

**建议**：如果这些配置需要影响LLM行为，应在提示词中体现

#### 2. VAD配置未找到（蓝色路径部分缺失）
**问题**：设计图中的 VAD配置、EnableVAD、Silence Threshold 等未在代码中找到

**搜索结果**：未找到相关实现

**建议**：如果需要VAD功能，需要补充实现

#### 3. 配置文件中的提示词模板未被使用
**问题**：`config.json` 中定义了 `system_prompts` 和 `prompt_template`，但实际代码中**直接从会话配置构建**，未使用配置文件模板

**配置文件**：
```json
"system_prompts": {
  "base": "你是辽宁省博物馆智能助手...",
  "function_calling": "你是辽宁省博物馆智能助手...",
  "fallback": "你是辽宁省博物馆智能助手..."
}
```

**实际代码**（`dynamic_llm_client.py`）：
```python
# 直接从会话获取，未使用配置文件模板
role_description = system_prompt_config.get("role_description", "你是智能助手。")
response_requirements = system_prompt_config.get("response_requirements", "...")
```

**影响**：配置文件中的精心设计的提示词模板被忽略了

## 三、最终提示词构建流程

### 实际执行路径

```
用户请求 
  ↓
agent_handler.py (接收WebSocket消息)
  ↓
request_processor.py (调用CommandGenerator)
  ↓
command_generator.py (协调器)
  ├─→ semantic_retrieval_processor.py (执行RAG检索，如果enable_srs=True)
  │     └─→ 返回 rag_context
  ├─→ prompt_builder.py (构建RAG指令)
  │     └─→ 返回 rag_instruction
  └─→ dynamic_llm_client.py (构建最终payload)
        ├─→ 从会话获取 system_prompt 配置
        ├─→ 从会话获取 scene_context 配置
        ├─→ 从会话获取 functions 定义
        ├─→ 构建 messages 数组
        └─→ 调用 LLM API
```

### 最终LLM API调用参数

```json
{
  "model": "qwen-turbo",
  "messages": [
    {
      "role": "system",
      "content": "{role_description}\n\n{response_requirements}\n\n必须遵守以下规则：..."
    },
    {
      "role": "user",
      "content": "{scene_description}\n\n{scene_specific_prompt}\n\n{rag_instruction}\n\n用户输入：{user_input}"
    }
  ],
  "functions": [...],  // 从会话获取
  "function_call": "auto",
  "temperature": 0.1,
  "max_tokens": 1024,
  "top_p": 0.1
}
```

## 四、关键发现

### ✅ 正确实现的部分
1. **会话配置驱动**：提示词完全由会话配置驱动（符合设计）
2. **支持动态更新**：通过 `update_session` 可以动态更新配置
3. **RAG集成**：根据 `enable_srs` 动态决定是否检索
4. **函数调用支持**：完整支持OpenAI Function Calling标准

### ⚠️ 需要注意的问题
1. **配置文件模板未使用**：`config.json` 中的 `system_prompts` 被忽略
2. **客户端基本配置未用于提示词**：Platform等配置未影响LLM行为
3. **VAD配置缺失**：设计图中的VAD相关配置未实现
4. **后备机制不一致**：代码中有多处后备提示词，但与配置文件不一致

### 🔍 计划外的内容
1. **PromptBuilder模块**：设计图中未体现，但代码中存在（用于构建RAG指令）
2. **ResponseParser模块**：设计图中未体现，但代码中存在（用于解析LLM响应）
3. **中断管理器**：设计图中未体现，但代码中实现了完整的中断机制

## 五、建议

### 1. 统一配置管理
建议明确配置优先级：
- 会话配置（最高优先级）
- 配置文件（后备）
- 硬编码默认值（最后后备）

### 2. 补充VAD功能
如果设计图中的VAD配置是必需的，需要补充实现

### 3. 文档更新
建议更新设计图，包含：
- PromptBuilder模块
- ResponseParser模块
- 中断管理器

### 4. 配置文件清理
清理未使用的配置项，或确保它们被正确使用

## 六、总结

**符合度评估**：85%

**核心架构符合设计**：
- ✅ 会话配置驱动提示词构建
- ✅ 支持智能体角色配置
- ✅ 支持场景上下文配置
- ✅ 支持函数调用
- ✅ 支持RAG检索
- ✅ 支持用户消息

**需要改进的地方**：
- ⚠️ 配置文件模板未被使用
- ⚠️ 客户端基本配置未用于提示词
- ⚠️ VAD配置缺失
- ⚠️ 后备机制不一致

**额外实现的功能**（计划外但有价值）：
- ✅ 完整的中断管理机制
- ✅ 模块化的提示词构建器
- ✅ 响应解析器

总体而言，实际实现**基本符合设计图的核心架构**，但在细节上有一些差异和遗漏。

