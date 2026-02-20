# 会话管理与提示词构建升级计划 - 可行性分析与修正建议

## 📋 执行摘要

**总体评估**: ✅ **可行，但需要重要修正**

你的升级计划核心思想非常好，但在实现细节上需要一些调整以适配现有架构。本文档提供详细的可行性分析和具体的修正建议。

---

## 🎯 核心需求回顾

### 你的需求
1. **系统提示词**（客户端提供）：LLM 角色描述 + 响应要求
2. **场景描述**（客户端提供）：当前所处的场景描述
3. **用户提问**（客户端提供）：本次用户的实际提问
4. **SRS 材料**（服务器生成）：服务器调用 SRS API 检索的相关资料
5. **API 参数**（客户端提供）：函数定义

### 你的期望
- 客户端提供的数据存储在会话中
- 客户端注册时提供初始配置
- 每次请求可更新配置（类似 FunctionCalling）
- 服务器从会话实时获取配置
- **服务器负责调用 SRS API 并整合到提示词**

---

## ✅ 可行性分析

### 1. 会话存储能力 ✅ **完全可行**

**现有实现**：
```python
@dataclass
class EnhancedClientSession:
    session_id: str
    client_metadata: Dict[str, Any]  # ✅ 可以存储任意数据
    created_at: datetime
    last_heartbeat: datetime
    last_activity: datetime
    expires_at: datetime
    is_registered: bool = True
```

**评估**：
- ✅ `client_metadata` 是一个字典，可以存储任意结构的数据
- ✅ 现有代码已经在使用它存储 `require_tts`, `enable_srs`, `functions` 等
- ✅ 完全支持你的需求

### 2. 客户端配置能力 ✅ **完全可行**

**现有实现**：
```python
# 注册时已经支持传递 client_metadata
def register_session(self, session_id: str, client_metadata: Dict[str, Any]):
    # ...
    session = EnhancedClientSession(
        session_id=session_id,
        client_metadata=client_metadata,  # ✅ 直接存储
        # ...
    )
```

**评估**：
- ✅ 注册时可以传递任意 `client_metadata`
- ✅ 客户端可以在注册时提供所有配置

### 3. 动态更新能力 ✅ **完全可行**

**现有实现**：
```python
def update_session_attributes(
    self,
    session_id: str,
    require_tts: Optional[bool] = None,
    enable_srs: Optional[bool] = None,
    function_calling_op: Optional[str] = None,
    function_calling: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    # ✅ 已经支持动态更新
    with self._lock:
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        if require_tts is not None:
            session.client_metadata["require_tts"] = require_tts
        # ...
```

**评估**：
- ✅ 已经有动态更新机制
- ✅ 支持 REPLACE/ADD/UPDATE/DELETE 操作
- ✅ 完全符合你的需求

### 4. 服务器实时获取 ✅ **完全可行**

**现有实现**：
```python
# CommandGenerator 中
session = strict_session_manager.get_session(session_id)
enable_srs = session.client_metadata.get("enable_srs", True)
functions = strict_session_manager.get_functions_for_session(session_id)
```

**评估**：
- ✅ 服务器已经在从会话中实时获取配置
- ✅ 完全符合你的需求

---

## ⚠️ 关键问题与修正建议

### 问题 1: 数据存储位置混乱 ⚠️

**你的计划**：
```python
# 你希望的结构
{
    "system_prompt": {
        "role_description": "...",
        "response_requirements": "..."
    },
    "scene_context": {
        "description": "...",
        "keywords": [...]
    },
    "current_question": "",
    "related_materials": ""
}
```

**问题**：
- ❌ `current_question` 和 `related_materials` 不应该存储在会话中
- ❌ 这些是**请求级别**的数据，不是**会话级别**的数据
- ❌ 每次请求都不同，不应该持久化

**修正建议**：

#### 会话级别数据（存储在 `client_metadata`）
```python
{
    "system_prompt": {
        "role_description": "你是博物馆智能助手...",
        "response_requirements": "请友好、专业地回答用户问题..."
    },
    "scene_context": {
        "current_scene": "纹样展示场景",
        "scene_description": "展示中国传统纹样的艺术价值",
        "keywords": ["纹样", "艺术", "历史"]
    },
    "require_tts": true,
    "enable_srs": true,
    "functions": [...]
}
```

#### 请求级别数据（每次请求传递，不存储）
```python
{
    "user_input": "介绍一下青铜鼎",  # ✅ 请求参数
    "rag_results": {...}              # ✅ 实时检索结果
}
```

### 问题 2: SRS 材料的职责划分 ✅ **已明确**

**正确理解**：
- ✅ SRS 材料**完全由服务器负责**
- ✅ 客户端**不需要**提供 SRS 材料
- ✅ 客户端只需要提供 `enable_srs` 开关

**正确流程**：
```python
# ✅ 服务器端完整流程
1. 客户端发送请求：user_input = "介绍一下青铜鼎"
2. 服务器从会话获取：enable_srs = session.client_metadata.get("enable_srs")
3. 如果 enable_srs = true：
   a. 服务器调用 SRS API 检索相关资料
   b. 服务器整合检索结果到提示词
4. 服务器构建最终提示词并调用 LLM API
5. 检索结果不存储（临时使用）
```

**客户端职责**：
- ✅ 提供 `enable_srs` 开关（是否启用 SRS）
- ❌ **不需要**调用 SRS API
- ❌ **不需要**提供 SRS 材料

**服务器职责**：
- ✅ 检查 `enable_srs` 开关
- ✅ 调用 SRS API 检索相关资料
- ✅ 整合 SRS 材料到提示词
- ✅ 构建最终 LLM API 请求

### 问题 3: 场景描述的定位不清 ⚠️

**你的计划**：
```
2.1 当前所处的场景描述(例如:纹样展示场景、铸造工艺展示场景、历史文化展示场景)
```

**问题**：
- ⚠️ 场景描述可能是**会话级别**的（整个会话都在同一个场景）
- ⚠️ 也可能是**请求级别**的（每次请求切换场景）
- ⚠️ 需要明确定位

**修正建议**：

#### 方案 A：场景是会话级别的（推荐）
```python
# 存储在 client_metadata
{
    "scene_context": {
        "current_scene": "纹样展示场景",
        "scene_description": "展示中国传统纹样的艺术价值",
        "keywords": ["纹样", "艺术", "历史"]
    }
}

# 允许动态更新
update_session_attributes(
    session_id=session_id,
    scene_context={
        "current_scene": "铸造工艺展示场景",
        "scene_description": "展示青铜器的铸造工艺",
        "keywords": ["铸造", "工艺", "技术"]
    }
)
```

#### 方案 B：场景是请求级别的
```python
# 每次请求传递
{
    "request_id": "req_xxx",
    "content": {"text": "介绍一下青铜鼎"},
    "scene_type": "纹样展示场景"  # ✅ 请求参数
}
```

**推荐**：使用方案 A（会话级别），因为：
- 大多数情况下，用户在一个会话中不会频繁切换场景
- 减少每次请求的数据传输量
- 更符合会话的语义

---

## 📐 修正后的数据结构设计

### 1. 会话级别数据（`client_metadata`）- 客户端提供并存储

```python
{
    # ===== 系统提示词配置（客户端提供）=====
    "system_prompt": {
        "role_description": "你是博物馆智能助手，专注于文物知识讲解和互动体验。",
        "response_requirements": "请用友好、专业的语言回答问题，注重知识性和趣味性的结合。"
    },
    
    # ===== 场景上下文配置（客户端提供）=====
    "scene_context": {
        "current_scene": "纹样展示场景",
        "scene_description": "展示中国传统纹样的艺术价值和文化内涵",
        "keywords": ["纹样", "艺术", "历史", "文化"],
        "scene_specific_prompt": "重点介绍纹样的艺术特点和历史演变"
    },
    
    # ===== 现有配置（保持不变）=====
    "require_tts": true,
    "enable_srs": true,      # ✅ 客户端只提供开关，服务器负责调用 SRS API
    "platform": "WEB",
    
    # ===== 函数定义（客户端提供）=====
    "functions": [
        {
            "name": "play_animation",
            "description": "播放宠物动画",
            "parameters": {...}
        }
    ],
    "function_names": ["play_animation"]
}
```

### 2. 请求级别数据（每次请求传递）- 客户端提供

```python
{
    "version": "1.0",
    "msg_type": "REQUEST",
    "session_id": "session_xxx",
    "payload": {
        "request_id": "req_xxx",
        "data_type": "TEXT",
        "content": {
            "text": "介绍一下青铜鼎"  # ✅ 用户提问（客户端提供）
        },
        
        # ===== 可选：更新会话配置（客户端提供）=====
        "update_session": {
            "system_prompt": {
                "role_description": "更新后的角色描述"
            },
            "scene_context": {
                "current_scene": "铸造工艺展示场景"
            },
            "enable_srs": true  # ✅ 可以动态开关 SRS
        }
    }
}
```

### 3. 服务器端生成数据（不存储，临时使用）

```python
# ===== SRS 检索结果（服务器调用 SRS API 生成）=====
rag_results = {
    "query": "青铜鼎",
    "documents": [
        {
            "content": "青铜鼎是中国古代重要的礼器...",
            "score": 0.95
        }
    ]
}

# ===== 整合后的提示词（服务器构建）=====
rag_instruction = """
参考资料：
青铜鼎是中国古代重要的礼器...
"""

# ✅ 服务器负责：
# 1. 从会话获取 enable_srs
# 2. 如果 enable_srs = true，调用 SRS API
# 3. 整合 SRS 结果到提示词
# 4. 构建最终 LLM API 请求
# 5. 不存储 SRS 结果
```

---

## 🔧 具体实现方案

### 服务器端修改

#### 1. 扩展 `update_session_attributes` 方法

**文件**: `src/session/strict_session_manager.py`

```python
def update_session_attributes(
    self,
    session_id: str,
    require_tts: Optional[bool] = None,
    enable_srs: Optional[bool] = None,
    function_calling_op: Optional[str] = None,
    function_calling: Optional[List[Dict[str, Any]]] = None,
    system_prompt: Optional[Dict[str, str]] = None,  # ✅ 新增
    scene_context: Optional[Dict[str, Any]] = None,  # ✅ 新增
) -> bool:
    """更新会话属性"""
    with self._lock:
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # 现有逻辑保持不变
        if require_tts is not None:
            session.client_metadata["require_tts"] = require_tts
        if enable_srs is not None:
            session.client_metadata["enable_srs"] = enable_srs
        
        # ✅ 新增：更新系统提示词
        if system_prompt is not None:
            current_prompt = session.client_metadata.get("system_prompt", {})
            current_prompt.update(system_prompt)
            session.client_metadata["system_prompt"] = current_prompt
        
        # ✅ 新增：更新场景上下文
        if scene_context is not None:
            current_scene = session.client_metadata.get("scene_context", {})
            current_scene.update(scene_context)
            session.client_metadata["scene_context"] = current_scene
        
        # 函数调用逻辑保持不变
        if function_calling_op and function_calling is not None:
            # ... 现有逻辑
        
        return True
```

#### 2. 修改 `DynamicLLMClient.generate_function_calling_payload`

**文件**: `src/core/dynamic_llm_client.py`

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
    
    # ✅ 从会话中获取系统提示词配置
    from ..session.strict_session_manager import strict_session_manager
    session = strict_session_manager.get_session(session_id)
    
    system_prompt_config = session.client_metadata.get("system_prompt", {})
    scene_context_config = session.client_metadata.get("scene_context", {})
    
    # ✅ 构建系统消息（使用会话配置）
    role_description = system_prompt_config.get(
        "role_description",
        "你是智能助手。"  # 默认值
    )
    response_requirements = system_prompt_config.get(
        "response_requirements",
        "请用友好、专业的语言回答问题。"  # 默认值
    )
    
    system_message = f"{role_description}\n\n{response_requirements}"
    
    # 如果有函数定义，添加函数调用规则
    if functions and len(functions) > 0:
        system_message += "\n\n必须遵守以下规则：\n"
        system_message += "1. 每次响应都必须包含自然语言对话内容；\n"
        system_message += "2. 在调用函数时，要先解释将要做什么；\n"
        system_message += "3. 用友好自然的语言与用户交流。"
    
    # ✅ 构建用户消息（使用会话配置的场景信息）
    scene_description = scene_context_config.get(
        "scene_description",
        f"场景：{scene_type}"  # 默认值
    )
    scene_specific_prompt = scene_context_config.get("scene_specific_prompt", "")
    
    user_message = f"{scene_description}\n"
    
    if scene_specific_prompt:
        user_message += f"{scene_specific_prompt}\n"
    
    if rag_instruction:
        user_message += f"\n{rag_instruction}\n"
    
    user_message += f"\n用户输入：{user_input}"
    
    # 构建消息列表
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    # 构建 payload
    payload = {
        "model": self.model,
        "messages": messages,
        "temperature": self.parameters.get("temperature", 0.1),
        "max_tokens": self.parameters.get("max_tokens", 1024),
        "top_p": self.parameters.get("top_p", 0.1),
    }
    
    # 添加函数定义
    if functions and len(functions) > 0:
        payload["functions"] = functions
        payload["function_call"] = "auto"
    
    return payload
```

#### 3. 修改 WebSocket 协议处理

**文件**: `src/ws/agent_stream_router.py` (假设)

```python
# 处理 REQUEST 消息时
payload = message.get("payload", {})

# ✅ 检查是否有会话更新
update_session = payload.get("update_session", {})
if update_session:
    strict_session_manager.update_session_attributes(
        session_id=session_id,
        system_prompt=update_session.get("system_prompt"),
        scene_context=update_session.get("scene_context"),
        require_tts=update_session.get("require_tts"),
        enable_srs=update_session.get("enable_srs"),
        function_calling_op=update_session.get("function_calling_op"),
        function_calling=update_session.get("function_calling")
    )
```

### 客户端修改

#### 1. 扩展 WebSocketClient.register

**文件**: `client/web/lib/core/WebSocketClient.js`

```javascript
async register(
    authData, 
    platform = 'WEB', 
    requireTTS = false, 
    enableSRS = true, 
    functionCalling = [],
    systemPrompt = null,      // ✅ 新增
    sceneContext = null       // ✅ 新增
) {
    const message = {
        version: '1.0',
        msg_type: 'REGISTER',
        session_id: null,
        payload: {
            auth: authData,
            platform: platform,
            require_tts: requireTTS,
            enable_srs: enableSRS,
            function_calling: functionCalling
        },
        timestamp: Date.now()
    };
    
    // ✅ 添加系统提示词配置
    if (systemPrompt) {
        message.payload.system_prompt = systemPrompt;
    }
    
    // ✅ 添加场景上下文配置
    if (sceneContext) {
        message.payload.scene_context = sceneContext;
    }
    
    // ... 发送消息
}
```

#### 2. 扩展 SendManager.sendText

**文件**: `client/web/lib/core/SendManager.js`

```javascript
sendText(text, options = {}) {
    const requestId = this.wsClient.generateId();
    
    const message = {
        version: '1.0',
        msg_type: 'REQUEST',
        session_id: this.sessionId,
        payload: {
            request_id: requestId,
            data_type: 'TEXT',
            stream_flag: false,
            stream_seq: 0,
            require_tts: options.requireTTS || false,
            content: { text }
        },
        timestamp: Date.now()
    };
    
    // ✅ 添加会话更新（如果有）
    const updateSession = {};
    
    if (options.systemPrompt) {
        updateSession.system_prompt = options.systemPrompt;
    }
    
    if (options.sceneContext) {
        updateSession.scene_context = options.sceneContext;
    }
    
    if (options.enableSRS !== undefined) {
        updateSession.enable_srs = options.enableSRS;
    }
    
    if (options.functionCallingOp) {
        updateSession.function_calling_op = options.functionCallingOp;
        updateSession.function_calling = options.functionCalling || [];
    }
    
    // 只有在有更新时才添加 update_session 字段
    if (Object.keys(updateSession).length > 0) {
        message.payload.update_session = updateSession;
    }
    
    this.wsClient.send(message);
    
    return requestId;
}
```

#### 3. 扩展 SettingsPanel

**文件**: `client/web/Demo/src/components/SettingsPanel.js`

```javascript
renderBasicSettings() {
    const section = createElement('div', {
        className: 'settings-section'
    });
    
    // ... 现有配置项
    
    // ✅ 新增：系统提示词配置
    const systemPromptSection = createElement('div', {
        className: 'settings-subsection'
    });
    
    const systemPromptTitle = createElement('h5', {
        textContent: '系统提示词配置'
    });
    systemPromptSection.appendChild(systemPromptTitle);
    
    // 角色描述
    const roleDescGroup = this.createTextareaGroup(
        'LLM 角色描述',
        'system_prompt.role_description',
        this.config.system_prompt?.role_description || '你是博物馆智能助手',
        'LLM 的角色定位和身份描述'
    );
    systemPromptSection.appendChild(roleDescGroup);
    
    // 响应要求
    const responseReqGroup = this.createTextareaGroup(
        'LLM 响应要求',
        'system_prompt.response_requirements',
        this.config.system_prompt?.response_requirements || '请友好、专业地回答问题',
        'LLM 的回答风格和要求'
    );
    systemPromptSection.appendChild(responseReqGroup);
    
    section.appendChild(systemPromptSection);
    
    // ✅ 新增：场景上下文配置
    const sceneContextSection = createElement('div', {
        className: 'settings-subsection'
    });
    
    const sceneContextTitle = createElement('h5', {
        textContent: '场景上下文配置'
    });
    sceneContextSection.appendChild(sceneContextTitle);
    
    // 当前场景
    const currentSceneGroup = this.createInputGroup(
        '当前场景',
        'scene_context.current_scene',
        this.config.scene_context?.current_scene || '公共场景',
        '当前所处的场景名称'
    );
    sceneContextSection.appendChild(currentSceneGroup);
    
    // 场景描述
    const sceneDescGroup = this.createTextareaGroup(
        '场景描述',
        'scene_context.scene_description',
        this.config.scene_context?.scene_description || '',
        '场景的详细描述'
    );
    sceneContextSection.appendChild(sceneDescGroup);
    
    section.appendChild(sceneContextSection);
    
    return section;
}
```

---

## 📊 最终的数据流转图（职责明确版）

```
【阶段 1：客户端注册】
SettingsPanel 配置（客户端）
    ↓
{
    system_prompt: {
        role_description: "你是博物馆智能助手",
        response_requirements: "请友好、专业地回答"
    },
    scene_context: {
        current_scene: "纹样展示场景",
        scene_description: "展示传统纹样艺术",
        keywords: ["纹样", "艺术"]
    },
    require_tts: true,
    enable_srs: true,      // ✅ 客户端只提供开关
    functions: [...]
}
    ↓
WebSocketClient.register()（客户端）
    ↓
服务器 REGISTER 处理（服务器）
    ↓
strict_session_manager.register_session()（服务器）
    ↓
存储到 session.client_metadata（服务器）

【阶段 2：客户端请求】
用户输入："介绍一下青铜鼎"（客户端）
    ↓
ChatWindow.sendMessage()（客户端）
    ↓
SendManager.sendText(text, {
    // 可选：更新会话配置
    systemPrompt: {...},
    sceneContext: {...},
    enableSRS: true
})（客户端）
    ↓
WebSocket REQUEST 消息（客户端 → 服务器）
    ↓
服务器 REQUEST 处理（服务器）

【阶段 3：服务器处理】
1. 更新会话配置（如果有 update_session）
    ↓
2. 从会话获取配置
   - system_prompt（客户端提供）
   - scene_context（客户端提供）
   - enable_srs（客户端提供）
   - functions（客户端提供）
    ↓
3. ✅ 服务器调用 SRS API（如果 enable_srs = true）
   - 服务器负责调用 SRS API
   - 服务器获取检索结果
   - 服务器整合到提示词
    ↓
4. 服务器构建最终提示词
   - 系统消息：system_prompt
   - 用户消息：scene_context + SRS结果 + user_input
    ↓
5. 服务器调用 LLM API

【阶段 4：LLM API 请求】
{
    "model": "qwen-turbo",
    "messages": [
        {
            "role": "system",
            "content": "你是博物馆智能助手...\n\n请友好、专业地回答问题..."
            // ↑ 来自 session.client_metadata.system_prompt
        },
        {
            "role": "user",
            "content": "展示中国传统纹样的艺术价值\n\n[SRS检索结果]\n\n用户输入：介绍一下青铜鼎"
            // ↑ 场景来自 session.client_metadata.scene_context
            // ↑ SRS结果由服务器调用 SRS API 获取
            // ↑ 用户输入来自客户端请求
        }
    ],
    "functions": [...],  // ↑ 来自 session.client_metadata.functions
    "function_call": "auto"
}

【职责划分总结】
┌─────────────────────────────────────────────────────────┐
│ 客户端职责                                               │
├─────────────────────────────────────────────────────────┤
│ ✅ 提供 system_prompt（角色描述 + 响应要求）            │
│ ✅ 提供 scene_context（场景描述）                       │
│ ✅ 提供 user_input（用户提问）                          │
│ ✅ 提供 enable_srs（SRS 开关）                          │
│ ✅ 提供 functions（函数定义）                           │
│ ❌ 不调用 SRS API                                       │
│ ❌ 不提供 SRS 材料                                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 服务器职责                                               │
├─────────────────────────────────────────────────────────┤
│ ✅ 存储客户端提供的配置到会话                            │
│ ✅ 从会话获取配置                                        │
│ ✅ 检查 enable_srs 开关                                 │
│ ✅ 调用 SRS API 检索相关资料                            │
│ ✅ 整合 SRS 材料到提示词                                │
│ ✅ 构建最终 LLM API 请求                                │
│ ✅ 调用 LLM API                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ⚡ 实施优先级

### 阶段 1: 核心功能（必须）
1. ✅ 扩展 `update_session_attributes` 支持 `system_prompt` 和 `scene_context`
2. ✅ 修改 `generate_function_calling_payload` 从会话获取配置
3. ✅ 修改 WebSocket 协议处理支持 `update_session`

### 阶段 2: 客户端支持（必须）
1. ✅ 扩展 `WebSocketClient.register` 支持新字段
2. ✅ 扩展 `SendManager.sendText` 支持 `update_session`
3. ✅ 扩展 `SettingsPanel` 添加新配置项

### 阶段 3: 优化和完善（可选）
1. ⭐ 添加配置预设模板（如"讲解模式"、"互动模式"）
2. ⭐ 添加配置导入/导出功能
3. ⭐ 添加配置历史记录

---

## 🎯 总结

### ✅ 你的计划的优点
1. **思路清晰**：明确了需要存储的数据类型
2. **灵活性高**：支持动态更新配置
3. **架构合理**：集中管理提示词相关数据
4. **职责明确**：客户端和服务器职责划分清晰

### ⚠️ 需要修正的地方
1. **数据分层**：区分会话级别和请求级别数据
2. **SRS 职责**：✅ **已明确 - SRS 完全由服务器负责**
3. **场景定位**：明确场景是会话级别的配置

### 🚀 修正后的方案

#### 客户端职责
1. **提供配置**：`system_prompt`, `scene_context`, `enable_srs`, `functions`
2. **提供输入**：`user_input`
3. **动态更新**：通过 `update_session` 更新配置
4. **❌ 不负责**：调用 SRS API、提供 SRS 材料

#### 服务器职责
1. **存储配置**：将客户端配置存储到会话
2. **获取配置**：从会话实时获取配置
3. **✅ 调用 SRS**：根据 `enable_srs` 开关调用 SRS API
4. **✅ 整合材料**：将 SRS 检索结果整合到提示词
5. **构建请求**：构建最终 LLM API 请求

#### 数据流转
```
客户端提供 → 会话存储 → 服务器获取 → 服务器调用SRS → 服务器构建提示词 → LLM API
```

### 📈 预期效果
- ✅ 提示词构建更灵活
- ✅ 配置管理更清晰
- ✅ 用户体验更个性化
- ✅ 系统架构更合理
- ✅ **职责划分更明确（SRS 完全由服务器负责）**

---

**修正后的方案完全可行，职责划分清晰，建议立即开始实施！** 🎉

