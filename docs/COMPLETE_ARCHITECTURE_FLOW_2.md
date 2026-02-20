# 完整架构流程 - 阶段 3-5：SRS 检索、提示词构建与 LLM 调用

## 📋 流程概述

本文档详细描述流程的后三个阶段：
3. **服务器根据要求选择性查询 SRS 获取相关资料**
4. **最终提示词构建**
5. **调用 LLM API**

---

## 🎯 阶段 3：服务器根据要求选择性查询 SRS

### 3.1 客户端发送请求

**文件**: `client/web/lib/core/SendManager.js`

```javascript
class SendManager {
    /**
     * 发送文本消息（完整版）
     * @param {string} text - 用户输入文本
     * @param {Object} options - 可选配置
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
}
```

### 3.2 服务器接收请求并更新会话

**文件**: `src/ws/agent_stream_router.py`

```python
async def handle_request_message(websocket, message: Dict[str, Any], session_id: str):
    """处理 REQUEST 消息"""
    try:
        payload = message.get("payload", {})
        request_id = payload.get("request_id")
        
        # ✅ 检查是否有会话更新
        update_session = payload.get("update_session", {})
        if update_session:
            logger.info(f"Updating session config for {session_id[:8]}")
            
            # 更新会话配置
            success = strict_session_manager.update_session_attributes(
                session_id=session_id,
                system_prompt=update_session.get("system_prompt"),
                scene_context=update_session.get("scene_context"),
                require_tts=update_session.get("require_tts"),
                enable_srs=update_session.get("enable_srs"),
                function_calling_op=update_session.get("function_calling_op"),
                function_calling=update_session.get("function_calling")
            )
            
            if not success:
                logger.error(f"Failed to update session config for {session_id[:8]}")
        
        # 验证会话
        session = strict_session_manager.validate_session(session_id)
        if not session:
            await send_error_response(websocket, "Invalid session", request_id)
            return
        
        # 获取用户输入
        content = payload.get("content", {})
        user_input = content.get("text", "")
        
        # ✅ 从会话获取 enable_srs 配置
        enable_srs = session.client_metadata.get("enable_srs", True)
        
        # 调用命令生成器处理请求
        await command_generator.process_request(
            websocket=websocket,
            session_id=session_id,
            request_id=request_id,
            user_input=user_input,
            enable_srs=enable_srs  # ✅ 传递 SRS 开关
        )
        
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        await send_error_response(websocket, str(e), request_id)
```

### 3.3 命令生成器决定是否调用 SRS

**文件**: `src/core/command_generator.py`

```python
class CommandGenerator:
    """命令生成器（完整版）"""
    
    async def process_request(
        self,
        websocket,
        session_id: str,
        request_id: str,
        user_input: str,
        enable_srs: bool = True
    ):
        """处理用户请求"""
        try:
            # 获取会话
            session = strict_session_manager.get_session(session_id)
            if not session:
                raise ValueError("Session not found")
            
            # ✅ 根据 enable_srs 决定是否调用 SRS
            rag_instruction = ""
            if enable_srs:
                logger.info(f"SRS enabled, querying relevant materials for: {user_input[:50]}")
                rag_instruction = await self._query_srs(user_input, session)
            else:
                logger.info(f"SRS disabled, skipping RAG retrieval")
            
            # 获取函数定义
            functions = strict_session_manager.get_functions_for_session(session_id)
            
            # 获取场景类型（从会话中获取）
            scene_context = session.client_metadata.get("scene_context", {})
            scene_type = scene_context.get("current_scene", "public")
            
            # 调用 LLM
            await self._call_llm(
                websocket=websocket,
                session_id=session_id,
                request_id=request_id,
                user_input=user_input,
                scene_type=scene_type,
                rag_instruction=rag_instruction,
                functions=functions
            )
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise
    
    async def _query_srs(self, user_input: str, session: EnhancedClientSession) -> str:
        """查询 SRS 获取相关资料"""
        try:
            # 获取场景关键词（用于优化检索）
            scene_context = session.client_metadata.get("scene_context", {})
            keywords = scene_context.get("keywords", [])
            
            # 构建检索查询（结合用户输入和场景关键词）
            query = user_input
            if keywords:
                query = f"{user_input} {' '.join(keywords)}"
            
            # 调用 SRS API
            logger.info(f"Querying SRS with: {query[:100]}")
            srs_result = await self.srs_client.query(
                query=query,
                top_k=3,  # 返回前 3 个最相关的结果
                threshold=0.7  # 相关度阈值
            )
            
            # 整合检索结果
            if srs_result and srs_result.get("documents"):
                documents = srs_result["documents"]
                logger.info(f"SRS returned {len(documents)} relevant documents")
                
                # 构建 RAG 指令
                rag_instruction = "参考资料：\n"
                for idx, doc in enumerate(documents, 1):
                    content = doc.get("content", "")
                    score = doc.get("score", 0)
                    rag_instruction += f"{idx}. {content}\n"
                
                rag_instruction += "\n请基于以上参考资料回答用户问题。\n"
                
                logger.info(f"RAG instruction generated: {len(rag_instruction)} chars")
                return rag_instruction
            else:
                logger.info("No relevant documents found in SRS")
                return ""
                
        except Exception as e:
            logger.error(f"Error querying SRS: {str(e)}")
            # SRS 失败不影响主流程，返回空字符串
            return ""
```

### 3.4 SRS 客户端实现

**文件**: `src/services/srs_client.py`

```python
class SRSClient:
    """SRS 检索增强服务客户端"""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.logger = get_enhanced_logger()
    
    async def query(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """查询相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 相关度阈值
            
        Returns:
            检索结果
        """
        try:
            # 构建请求
            request_data = {
                "query": query,
                "top_k": top_k,
                "threshold": threshold
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/query",
                    json=request_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(
                            "SRS query successful",
                            {
                                "query": query[:50],
                                "results": len(result.get("documents", []))
                            }
                        )
                        return result
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            "SRS query failed",
                            {
                                "status": response.status,
                                "error": error_text
                            }
                        )
                        return {"documents": []}
                        
        except Exception as e:
            self.logger.error(f"SRS query exception: {str(e)}")
            return {"documents": []}
```

---

## 🔨 阶段 4：最终提示词构建

### 4.1 从会话获取配置

**文件**: `src/core/dynamic_llm_client.py`

```python
class DynamicLLMClient:
    """动态 LLM 客户端（完整版）"""
    
    def generate_function_calling_payload(
        self,
        session_id: str,
        user_input: str,
        scene_type: str = "public",
        rag_instruction: str = "",
        functions: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成 OpenAI 标准函数调用格式的请求"""
        
        # ✅ 从会话中获取完整配置
        from ..session.strict_session_manager import strict_session_manager
        session = strict_session_manager.get_session(session_id)
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 获取系统提示词配置
        system_prompt_config = session.client_metadata.get("system_prompt", {})
        role_description = system_prompt_config.get(
            "role_description",
            "你是智能助手。"
        )
        response_requirements = system_prompt_config.get(
            "response_requirements",
            "请用友好、专业的语言回答问题。"
        )
        
        # 获取场景上下文配置
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
            "Prompt constructed",
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

### 4.2 提示词构建示例

**完整的提示词构建示例**：

```python
# 输入数据
session_id = "session_abc123"
user_input = "介绍一下青铜鼎的历史"
rag_instruction = """参考资料：
1. 青铜鼎是中国古代重要的礼器，始于商代，盛于周代。
2. 著名的司母戊鼎是商代晚期的青铜器，重达832.84公斤。
"""

# 从会话获取的配置
system_prompt = {
    "role_description": "你是博物馆智能助手，专注于文物知识讲解和互动体验。",
    "response_requirements": "请用友好、专业的语言回答问题，注重知识性和趣味性的结合。"
}

scene_context = {
    "current_scene": "铸造工艺展示场景",
    "scene_description": "展示青铜器的铸造工艺和技术演变",
    "scene_specific_prompt": "重点介绍铸造技术的发展历程和工艺特点"
}

# 构建后的最终提示词
final_prompt = {
    "messages": [
        {
            "role": "system",
            "content": """你是博物馆智能助手，专注于文物知识讲解和互动体验。

请用友好、专业的语言回答问题，注重知识性和趣味性的结合。

必须遵守以下规则：
1. 每次响应都必须包含自然语言对话内容；
2. 在调用函数时，要先解释将要做什么；
3. 用友好自然的语言与用户交流。"""
        },
        {
            "role": "user",
            "content": """展示青铜器的铸造工艺和技术演变

重点介绍铸造技术的发展历程和工艺特点

参考资料：
1. 青铜鼎是中国古代重要的礼器，始于商代，盛于周代。
2. 著名的司母戊鼎是商代晚期的青铜器，重达832.84公斤。

用户输入：介绍一下青铜鼎的历史"""
        }
    ]
}
```

---

## 🚀 阶段 5：调用 LLM API

### 5.1 发起 LLM API 调用

**文件**: `src/core/command_generator.py`

```python
async def _call_llm(
    self,
    websocket,
    session_id: str,
    request_id: str,
    user_input: str,
    scene_type: str,
    rag_instruction: str,
    functions: List[Dict[str, Any]]
):
    """调用 LLM API"""
    try:
        # 生成 LLM 请求 payload
        payload = self.llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input=user_input,
            scene_type=scene_type,
            rag_instruction=rag_instruction,
            functions=functions
        )
        
        # 获取会话配置
        session = strict_session_manager.get_session(session_id)
        require_tts = session.client_metadata.get("require_tts", False)
        
        # 调用 LLM（流式响应）
        logger.info(f"Calling LLM API for request {request_id[:8]}")
        
        async for chunk in self.llm_client.stream_chat(payload):
            # 处理流式响应
            await self._handle_llm_chunk(
                websocket=websocket,
                session_id=session_id,
                request_id=request_id,
                chunk=chunk,
                require_tts=require_tts
            )
        
        logger.info(f"LLM API call completed for request {request_id[:8]}")
        
    except Exception as e:
        logger.error(f"Error calling LLM: {str(e)}")
        raise
```

### 5.2 处理 LLM 响应

```python
async def _handle_llm_chunk(
    self,
    websocket,
    session_id: str,
    request_id: str,
    chunk: Dict[str, Any],
    require_tts: bool
):
    """处理 LLM 流式响应块"""
    try:
        # 提取内容
        content = chunk.get("content", "")
        function_call = chunk.get("function_call")
        
        # 构建响应消息
        response_message = {
            "version": "1.0",
            "msg_type": "RESPONSE",
            "session_id": session_id,
            "payload": {
                "request_id": request_id,
                "data_type": "TEXT",
                "content": {
                    "text": content
                },
                "is_final": chunk.get("is_final", False)
            },
            "timestamp": int(time.time() * 1000)
        }
        
        # 如果有函数调用
        if function_call:
            response_message["payload"]["function_call"] = function_call
        
        # 发送响应
        await websocket.send_json(response_message)
        
        # 如果需要 TTS 且是最终响应
        if require_tts and chunk.get("is_final") and content:
            await self._generate_tts(
                websocket=websocket,
                session_id=session_id,
                request_id=request_id,
                text=content
            )
        
    except Exception as e:
        logger.error(f"Error handling LLM chunk: {str(e)}")
```

---

## 📊 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    阶段 3：SRS 检索                          │
└─────────────────────────────────────────────────────────────┘

用户输入："介绍一下青铜鼎的历史"
    ↓
SendManager.sendText(text, options)
    ↓
发送 REQUEST 消息
    ↓
服务器接收消息
    ↓
handle_request_message()
    ↓
检查 update_session（如果有）
    ↓
更新会话配置
    ↓
验证会话
    ↓
从会话获取 enable_srs
    ↓
CommandGenerator.process_request()
    ↓
判断：enable_srs == true?
    ├─ Yes → 调用 SRS API
    │         ↓
    │    SRSClient.query(user_input)
    │         ↓
    │    返回检索结果
    │         ↓
    │    整合为 rag_instruction
    │
    └─ No → rag_instruction = ""

┌─────────────────────────────────────────────────────────────┐
│                    阶段 4：提示词构建                        │
└─────────────────────────────────────────────────────────────┘

从会话获取配置
    ├─ system_prompt
    ├─ scene_context
    ├─ functions
    └─ require_tts
    ↓
DynamicLLMClient.generate_function_calling_payload()
    ↓
构建系统消息
    = role_description + response_requirements + 函数调用规则
    ↓
构建用户消息
    = scene_description + scene_specific_prompt + rag_instruction + user_input
    ↓
构建消息列表
    = [system_message, user_message]
    ↓
构建完整 payload
    = {model, messages, functions, temperature, ...}

┌─────────────────────────────────────────────────────────────┐
│                    阶段 5：调用 LLM                          │
└─────────────────────────────────────────────────────────────┘

DynamicLLMClient.stream_chat(payload)
    ↓
发送请求到 LLM API
    ↓
接收流式响应
    ↓
for each chunk:
    ↓
    提取 content 和 function_call
    ↓
    构建 RESPONSE 消息
    ↓
    发送给客户端
    ↓
    如果 require_tts && is_final:
        ↓
        生成 TTS 音频
        ↓
        发送音频数据
    ↓
LLM 响应完成
```

---

## ✅ 关键要点

### SRS 检索（阶段 3）
1. ✅ 完全由服务器负责
2. ✅ 根据 `enable_srs` 开关决定是否调用
3. ✅ 检索失败不影响主流程
4. ✅ 结合场景关键词优化检索

### 提示词构建（阶段 4）
1. ✅ 从会话实时获取所有配置
2. ✅ 系统消息 = 角色描述 + 响应要求 + 函数规则
3. ✅ 用户消息 = 场景描述 + 场景提示 + RAG 结果 + 用户输入
4. ✅ 结构清晰、易于调试

### LLM 调用（阶段 5）
1. ✅ 使用 OpenAI 标准格式
2. ✅ 支持流式响应
3. ✅ 支持函数调用
4. ✅ 根据配置决定是否生成 TTS

---

## 🔍 数据流转示例

### 输入数据
```javascript
// 客户端发送
{
    user_input: "介绍一下青铜鼎的历史",
    update_session: {
        scene_context: {
            current_scene: "铸造工艺展示场景"
        }
    }
}
```

### 会话配置
```python
# 从会话获取
{
    "system_prompt": {
        "role_description": "你是博物馆智能助手...",
        "response_requirements": "请用友好、专业的语言..."
    },
    "scene_context": {
        "current_scene": "铸造工艺展示场景",
        "scene_description": "展示青铜器的铸造工艺...",
        "scene_specific_prompt": "重点介绍铸造技术..."
    },
    "enable_srs": true,
    "require_tts": true,
    "functions": [...]
}
```

### SRS 检索结果
```python
# 服务器调用 SRS API
{
    "documents": [
        {
            "content": "青铜鼎是中国古代重要的礼器...",
            "score": 0.95
        }
    ]
}

# 整合为
rag_instruction = "参考资料：\n1. 青铜鼎是中国古代重要的礼器...\n"
```

### 最终 LLM 请求
```python
{
    "model": "qwen-turbo",
    "messages": [
        {
            "role": "system",
            "content": "你是博物馆智能助手...\n\n请用友好、专业的语言..."
        },
        {
            "role": "user",
            "content": "展示青铜器的铸造工艺...\n\n重点介绍铸造技术...\n\n参考资料：...\n\n用户输入：介绍一下青铜鼎的历史"
        }
    ],
    "functions": [...],
    "function_call": "auto"
}
```

---

**上一步**: [COMPLETE_ARCHITECTURE_FLOW_1.md](./COMPLETE_ARCHITECTURE_FLOW_1.md)  
**下一步**: [COMPLETE_ARCHITECTURE_IMPL.md](./COMPLETE_ARCHITECTURE_IMPL.md)

