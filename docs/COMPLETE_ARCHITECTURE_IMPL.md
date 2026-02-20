# 完整架构实现细节

## 📋 文档概述

本文档提供服务器端和客户端的详细实现代码和修改清单。

---

## 🖥️ 服务器端实现

### 1. 会话管理器扩展

**文件**: `src/session/strict_session_manager.py`

**修改内容**: 扩展 `update_session_attributes` 方法

```python
def update_session_attributes(
    self,
    session_id: str,
    require_tts: Optional[bool] = None,
    enable_srs: Optional[bool] = None,
    function_calling_op: Optional[str] = None,
    function_calling: Optional[List[Dict[str, Any]]] = None,
    system_prompt: Optional[Dict[str, str]] = None,      # ✅ 新增
    scene_context: Optional[Dict[str, Any]] = None,      # ✅ 新增
) -> bool:
    """更新会话属性（完整版）
    
    Args:
        session_id: 会话ID
        require_tts: TTS 开关
        enable_srs: SRS 开关
        function_calling_op: 函数操作类型
        function_calling: 函数定义列表
        system_prompt: 系统提示词配置（可选）
        scene_context: 场景上下文配置（可选）
    
    Returns:
        是否更新成功
    """
    with self._lock:
        session = self.sessions.get(session_id)
        if not session:
            self.logger.sess.warn('Update failed - session not found', 
                          {'session_id': session_id[:8]})
            return False
        
        # 现有逻辑保持不变
        if require_tts is not None:
            session.client_metadata["require_tts"] = require_tts
            self.logger.sess.debug('Updated require_tts', 
                          {'session_id': session_id[:8], 'value': require_tts})
        
        if enable_srs is not None:
            session.client_metadata["enable_srs"] = enable_srs
            self.logger.sess.debug('Updated enable_srs', 
                          {'session_id': session_id[:8], 'value': enable_srs})
        
        # ✅ 新增：更新系统提示词
        if system_prompt is not None:
            current_prompt = session.client_metadata.get("system_prompt", {})
            # 只更新提供的字段
            if "role_description" in system_prompt:
                current_prompt["role_description"] = system_prompt["role_description"]
            if "response_requirements" in system_prompt:
                current_prompt["response_requirements"] = system_prompt["response_requirements"]
            
            session.client_metadata["system_prompt"] = current_prompt
            self.logger.sess.info('Updated system_prompt', 
                          {'session_id': session_id[:8], 
                           'has_role': "role_description" in system_prompt,
                           'has_requirements': "response_requirements" in system_prompt})
        
        # ✅ 新增：更新场景上下文
        if scene_context is not None:
            current_scene = session.client_metadata.get("scene_context", {})
            # 只更新提供的字段
            if "current_scene" in scene_context:
                current_scene["current_scene"] = scene_context["current_scene"]
            if "scene_description" in scene_context:
                current_scene["scene_description"] = scene_context["scene_description"]
            if "keywords" in scene_context:
                current_scene["keywords"] = scene_context["keywords"]
            if "scene_specific_prompt" in scene_context:
                current_scene["scene_specific_prompt"] = scene_context["scene_specific_prompt"]
            
            session.client_metadata["scene_context"] = current_scene
            self.logger.sess.info('Updated scene_context', 
                          {'session_id': session_id[:8],
                           'scene': current_scene.get("current_scene", "unknown")})
        
        # 函数调用逻辑保持不变
        if function_calling_op and function_calling is not None:
            fc = session.client_metadata.get("functions", [])
            names = {f.get("name") for f in fc if isinstance(f, dict) and f.get("name")}
            
            if function_calling_op == "REPLACE":
                session.client_metadata["functions"] = list(function_calling)
                session.client_metadata["function_names"] = [
                    f.get("name", "") for f in function_calling if isinstance(f, dict)
                ]
                self.logger.sess.info('Replaced functions', 
                              {'session_id': session_id[:8], 
                               'count': len(function_calling)})
            
            elif function_calling_op == "ADD":
                session.client_metadata["functions"] = fc + list(function_calling)
                session.client_metadata["function_names"] = (
                    session.client_metadata.get("function_names", []) + 
                    [f.get("name", "") for f in function_calling if isinstance(f, dict)]
                )
                self.logger.sess.info('Added functions', 
                              {'session_id': session_id[:8], 
                               'added': len(function_calling)})
            
            elif function_calling_op == "UPDATE":
                new_names = {f.get("name") for f in function_calling 
                           if isinstance(f, dict) and f.get("name")}
                fc = [x for x in fc if x.get("name") not in new_names]
                fc.extend(function_calling)
                session.client_metadata["functions"] = fc
                session.client_metadata["function_names"] = [
                    f.get("name", "") for f in fc if isinstance(f, dict) and f.get("name")
                ]
                self.logger.sess.info('Updated functions', 
                              {'session_id': session_id[:8], 
                               'updated': len(new_names)})
            
            elif function_calling_op == "DELETE":
                del_names = {f.get("name") for f in function_calling if isinstance(f, dict)}
                fc = [x for x in fc if x.get("name") not in del_names]
                session.client_metadata["functions"] = fc
                session.client_metadata["function_names"] = [
                    f.get("name", "") for f in fc if isinstance(f, dict) and f.get("name")
                ]
                self.logger.sess.info('Deleted functions', 
                              {'session_id': session_id[:8], 
                               'deleted': len(del_names)})
        
        return True
```

### 2. 会话注册 API 扩展

**文件**: `src/api/session_api.py`

**修改内容**: 扩展注册请求模型和处理逻辑

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# ✅ 新增：系统提示词配置模型
class SystemPromptConfig(BaseModel):
    """系统提示词配置"""
    role_description: str = Field(..., description="LLM 角色描述")
    response_requirements: str = Field(..., description="LLM 响应要求")

# ✅ 新增：场景上下文配置模型
class SceneContextConfig(BaseModel):
    """场景上下文配置"""
    current_scene: str = Field(..., description="当前场景名称")
    scene_description: str = Field(..., description="场景描述")
    keywords: List[str] = Field(default_factory=list, description="场景关键词")
    scene_specific_prompt: Optional[str] = Field(None, description="场景特定提示")

# ✅ 修改：扩展注册请求模型
class ClientRegistrationRequest(BaseModel):
    """客户端注册请求（完整版）"""
    auth: Dict[str, Any] = Field(..., description="认证信息")
    platform: str = Field(default="WEB", description="平台类型")
    require_tts: bool = Field(default=False, description="是否需要 TTS")
    enable_srs: bool = Field(default=True, description="是否启用 SRS")
    function_calling: List[Dict[str, Any]] = Field(default_factory=list, description="函数定义列表")
    system_prompt: Optional[SystemPromptConfig] = Field(None, description="系统提示词配置")  # ✅ 新增
    scene_context: Optional[SceneContextConfig] = Field(None, description="场景上下文配置")  # ✅ 新增

@router.post("/register")
async def register_session(request: ClientRegistrationRequest):
    """注册会话（完整版）"""
    try:
        # 生成会话 ID
        session_id = generate_session_id()
        
        # 构建客户端元数据
        client_metadata = {
            "platform": request.platform,
            "client_type": request.platform,
            "require_tts": request.require_tts,
            "enable_srs": request.enable_srs
        }
        
        # ✅ 添加系统提示词配置
        if request.system_prompt:
            client_metadata["system_prompt"] = {
                "role_description": request.system_prompt.role_description,
                "response_requirements": request.system_prompt.response_requirements
            }
        else:
            # 使用默认值
            client_metadata["system_prompt"] = {
                "role_description": "你是智能助手。",
                "response_requirements": "请用友好、专业的语言回答问题。"
            }
        
        # ✅ 添加场景上下文配置
        if request.scene_context:
            client_metadata["scene_context"] = {
                "current_scene": request.scene_context.current_scene,
                "scene_description": request.scene_context.scene_description,
                "keywords": request.scene_context.keywords,
                "scene_specific_prompt": request.scene_context.scene_specific_prompt or ""
            }
        else:
            # 使用默认值
            client_metadata["scene_context"] = {
                "current_scene": "公共场景",
                "scene_description": "通用对话场景",
                "keywords": [],
                "scene_specific_prompt": ""
            }
        
        # 注册会话
        session = strict_session_manager.register_session_with_functions(
            session_id=session_id,
            client_metadata=client_metadata,
            functions=request.function_calling
        )
        
        logger.info(
            "Session registered with complete config",
            {
                "session_id": session_id[:8],
                "platform": request.platform,
                "has_system_prompt": bool(request.system_prompt),
                "has_scene_context": bool(request.scene_context),
                "function_count": len(request.function_calling)
            }
        )
        
        # 返回注册成功响应
        return {
            "status": "success",
            "session_id": session_id,
            "session_data": strict_session_manager.get_protocol_session_data(session_id)
        }
        
    except Exception as e:
        logger.error(f"Session registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. LLM 客户端修改

**文件**: `src/core/dynamic_llm_client.py`

**修改内容**: 修改 `generate_function_calling_payload` 方法从会话获取配置

```python
def generate_function_calling_payload(
    self,
    session_id: str,
    user_input: str,
    scene_type: str = "public",
    rag_instruction: str = "",
    functions: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """生成 OpenAI 标准函数调用格式的请求（完整版）"""
    
    # ✅ 从会话中获取完整配置
    from ..session.strict_session_manager import strict_session_manager
    session = strict_session_manager.get_session(session_id)
    
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    # ✅ 获取系统提示词配置
    system_prompt_config = session.client_metadata.get("system_prompt", {})
    role_description = system_prompt_config.get(
        "role_description",
        "你是智能助手。"
    )
    response_requirements = system_prompt_config.get(
        "response_requirements",
        "请用友好、专业的语言回答问题。"
    )
    
    # ✅ 获取场景上下文配置
    scene_context_config = session.client_metadata.get("scene_context", {})
    scene_description = scene_context_config.get(
        "scene_description",
        f"场景：{scene_type}"
    )
    scene_specific_prompt = scene_context_config.get(
        "scene_specific_prompt",
        ""
    )
    
    # ✅ 构建系统消息
    system_message = f"{role_description}\n\n{response_requirements}"
    
    # 如果有函数定义，添加函数调用规则
    if functions and len(functions) > 0:
        system_message += "\n\n必须遵守以下规则：\n"
        system_message += "1. 每次响应都必须包含自然语言对话内容；\n"
        system_message += "2. 在调用函数时，要先解释将要做什么；\n"
        system_message += "3. 用友好自然的语言与用户交流。"
    
    # ✅ 构建用户消息
    user_message_parts = []
    
    # 1. 场景描述
    user_message_parts.append(scene_description)
    
    # 2. 场景特定提示
    if scene_specific_prompt:
        user_message_parts.append(scene_specific_prompt)
    
    # 3. RAG 检索结果（如果有）
    if rag_instruction:
        user_message_parts.append(rag_instruction)
    
    # 4. 用户输入
    user_message_parts.append(f"用户输入：{user_input}")
    
    user_message = "\n\n".join(user_message_parts)
    
    # ✅ 构建消息列表
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    # 记录提示词构建信息
    self.logger.info(
        "Prompt constructed from session config",
        {
            "session_id": session_id[:8],
            "system_message_length": len(system_message),
            "user_message_length": len(user_message),
            "has_rag": bool(rag_instruction),
            "has_functions": bool(functions),
            "scene": scene_context_config.get("current_scene", "unknown")
        }
    )
    
    # ✅ 构建完整 payload
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

---

## 📱 客户端实现

### 1. WebSocket 客户端扩展

**文件**: `client/web/lib/core/WebSocketClient.js`

**修改内容**: 扩展 `register` 方法

```javascript
/**
 * 注册会话（完整版）
 */
async register(
    authData,
    platform = 'WEB',
    requireTTS = false,
    enableSRS = true,
    functionCalling = [],
    systemPrompt = null,      // ✅ 新增
    sceneContext = null       // ✅ 新增
) {
    return new Promise((resolve, reject) => {
        // 构建注册消息
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
        
        // 设置响应监听器
        const timeout = setTimeout(() => {
            this.off('register_success', onSuccess);
            this.off('register_failed', onFailed);
            reject(new Error('Registration timeout'));
        }, 10000);
        
        const onSuccess = (data) => {
            clearTimeout(timeout);
            this.off('register_failed', onFailed);
            resolve(data);
        };
        
        const onFailed = (error) => {
            clearTimeout(timeout);
            this.off('register_success', onSuccess);
            reject(error);
        };
        
        this.once('register_success', onSuccess);
        this.once('register_failed', onFailed);
        
        // 发送注册消息
        this.send(message);
    });
}
```

### 2. SDK 主接口扩展

**文件**: `client/web/lib/MuseumAgentSDK.js`

**修改内容**: 扩展 `connect` 方法

```javascript
/**
 * 连接并注册（完整版）
 */
async connect(config) {
    try {
        // 连接 WebSocket
        await this.wsClient.connect();
        
        // 注册会话
        const registerData = await this.wsClient.register(
            config.auth,
            config.platform,
            config.require_tts,
            config.enable_srs,
            config.function_calling,
            config.system_prompt,      // ✅ 传递系统提示词
            config.scene_context       // ✅ 传递场景上下文
        );
        
        this.sessionId = registerData.session_id;
        this.isConnected = true;
        
        // 初始化管理器
        this.sendManager = new SendManager(this.wsClient, this.sessionId);
        this.receiveManager = new ReceiveManager(this.eventBus);
        
        this.emit('connected', {
            session_id: this.sessionId,
            session_data: registerData.session_data
        });
        
        return registerData;
    } catch (error) {
        this.emit('error', error);
        throw error;
    }
}
```

### 3. 发送管理器扩展

**文件**: `client/web/lib/core/SendManager.js`

**修改内容**: 扩展 `sendText` 方法支持会话更新

```javascript
/**
 * 发送文本消息（完整版）
 */
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
    
    // ✅ 构建会话更新（如果有）
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

---

## 📋 修改清单

### 服务器端修改

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `src/session/strict_session_manager.py` | 扩展方法 | 扩展 `update_session_attributes` 支持 `system_prompt` 和 `scene_context` |
| `src/api/session_api.py` | 新增模型 + 修改接口 | 新增 `SystemPromptConfig` 和 `SceneContextConfig`，修改注册接口 |
| `src/core/dynamic_llm_client.py` | 修改方法 | 修改 `generate_function_calling_payload` 从会话获取配置 |
| `src/core/command_generator.py` | 修改逻辑 | 从会话获取 `enable_srs` 并决定是否调用 SRS |
| `src/ws/agent_stream_router.py` | 新增逻辑 | 处理 `update_session` 字段 |

### 客户端修改

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `client/web/lib/core/WebSocketClient.js` | 扩展方法 | 扩展 `register` 方法支持新参数 |
| `client/web/lib/MuseumAgentSDK.js` | 扩展方法 | 扩展 `connect` 方法传递新配置 |
| `client/web/lib/core/SendManager.js` | 扩展方法 | 扩展 `sendText` 支持 `update_session` |
| `client/web/Demo/src/components/SettingsPanel.js` | 新增UI | 添加系统提示词和场景上下文配置区域 |

---

## 🧪 测试建议

### 单元测试

1. **会话管理器测试**
```python
def test_update_session_with_system_prompt():
    # 注册会话
    session_id = "test_session"
    client_metadata = {...}
    session = manager.register_session(session_id, client_metadata)
    
    # 更新系统提示词
    success = manager.update_session_attributes(
        session_id=session_id,
        system_prompt={
            "role_description": "新的角色描述"
        }
    )
    
    assert success
    assert session.client_metadata["system_prompt"]["role_description"] == "新的角色描述"
```

2. **提示词构建测试**
```python
def test_prompt_construction():
    # 创建测试会话
    session_id = create_test_session()
    
    # 生成 payload
    payload = llm_client.generate_function_calling_payload(
        session_id=session_id,
        user_input="测试输入",
        rag_instruction="测试RAG",
        functions=[]
    )
    
    # 验证提示词包含会话配置
    assert "你是博物馆智能助手" in payload["messages"][0]["content"]
    assert "测试RAG" in payload["messages"][1]["content"]
```

### 集成测试

1. **完整流程测试**
```javascript
// 客户端测试
const sdk = new MuseumAgentSDK(wsUrl);

// 连接并注册
await sdk.connect({
    auth: { type: 'API_KEY', api_key: 'test_key' },
    system_prompt: {
        role_description: '测试角色',
        response_requirements: '测试要求'
    },
    scene_context: {
        current_scene: '测试场景',
        scene_description: '测试描述'
    }
});

// 发送请求
const requestId = sdk.sendText('测试问题');

// 验证响应
sdk.on('response', (data) => {
    console.log('收到响应:', data);
});
```

---

**上一步**: [COMPLETE_ARCHITECTURE_FLOW_2.md](./COMPLETE_ARCHITECTURE_FLOW_2.md)  
**下一步**: [COMPLETE_ARCHITECTURE_API.md](./COMPLETE_ARCHITECTURE_API.md)

