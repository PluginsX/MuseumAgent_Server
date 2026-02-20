# 会话管理与提示词构建升级计划

## 一、需求分析

### 1. 核心需求
- **扩展会话数据**：在会话中存储完整的提示词构建所需资料
- **客户端配置**：允许客户端在注册和请求时提供/更新这些资料
- **实时获取**：服务器构建LLM调用时从会话中实时获取资料
- **向后兼容**：保持现有功能正常运行

### 2. 数据结构需求

#### 2.1 系统提示词
- 1.1 LLM角色描述
- 1.2 LLM响应要求

#### 2.2 用户提示词相关
- 2.1 当前所处场景描述
- 2.2 本次用户提问消息
- 2.3 本次用户提问相关材料(SRS返回)

#### 2.3 API参数
- 3.1 当前场景可执行的函数定义

## 二、现有实现分析

### 1. 服务器端
- **会话管理**：`src/session/strict_session_manager.py`
- **提示词构建**：`src/core/dynamic_llm_client.py`
- **会话结构**：`EnhancedClientSession` 数据类
- **元数据存储**：`client_metadata` 字典

### 2. 客户端
- **WebSocket客户端**：`client/web/Demo/lib/core/WebSocketClient.js`
- **注册流程**：`register` 方法
- **消息格式**：符合通信协议的JSON格式

## 三、升级方案

### 1. 服务器端升级

#### 1.1 扩展会话数据结构

**修改文件**：`src/session/strict_session_manager.py`

**升级内容**：
- 在 `client_metadata` 中添加新字段支持
- 确保新字段的默认值设置
- 扩展会话验证逻辑

**新增字段**：
```python
# client_metadata 新增字段
{
    "system_prompt": {
        "role_description": "你是博物馆智能助手...",
        "response_requirements": "请友好、专业地回答用户问题..."
    },
    "scene_context": {
        "description": "纹样展示场景",
        "keywords": ["纹样", "艺术", "历史"]
    },
    "current_question": "",
    "related_materials": ""
}
```

#### 1.2 修改提示词构建逻辑

**修改文件**：`src/core/dynamic_llm_client.py`

**升级内容**：
- 修改 `generate_function_calling_payload` 方法
- 从会话中获取完整提示词资料
- 构建更丰富的系统消息

**核心逻辑**：
```python
def generate_function_calling_payload(self, session_id: str, user_input: str, 
                                    scene_type: str = "public", rag_instruction: str = "", 
                                    functions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    # 从会话中获取系统提示词
    session = strict_session_manager.get_session(session_id)
    system_prompt_data = session.client_metadata.get("system_prompt", {})
    scene_context = session.client_metadata.get("scene_context", {})
    
    # 构建系统消息
    system_message = f"{system_prompt_data.get('role_description', '你是智能助手')}"
    if system_prompt_data.get('response_requirements'):
        system_message += f"\n\n{system_prompt_data.get('response_requirements')}"
    
    # 构建用户消息
    scene_description = scene_context.get('description', scene_type)
    user_message = f"场景：{scene_description}\n{rag_instruction}\n用户输入：{user_input}"
    
    # 构建消息列表
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    
    # 构建payload
    # ...
```

#### 1.3 扩展会话注册接口

**修改文件**：`src/api/session_api.py`

**升级内容**：
- 扩展 `ClientRegistrationRequest` 模型
- 支持新字段的验证和存储

### 2. 客户端升级

#### 2.1 扩展注册流程

**修改文件**：`client/web/Demo/lib/core/WebSocketClient.js`

**升级内容**：
- 扩展 `register` 方法参数
- 支持新字段的传递

**核心修改**：
```javascript
async register(authData, platform = 'WEB', requireTTS = false, enableSRS = true, 
              functionCalling = [], systemPrompt = {}, sceneContext = {}) {
    const message = {
        version: '1.0',
        msg_type: 'REGISTER',
        session_id: null,
        payload: {
            auth: authData,
            platform: platform,
            require_tts: requireTTS,
            enable_srs: enableSRS,
            function_calling: functionCalling,
            system_prompt: systemPrompt,
            scene_context: sceneContext
        },
        timestamp: Date.now()
    };
    // ...
}
```

#### 2.2 扩展请求流程

**修改文件**：`client/web/Demo/lib/MuseumAgentSDK.js`

**升级内容**：
- 扩展 `sendText` 和 `startRecording` 方法
- 支持在请求中更新会话数据

**核心修改**：
```javascript
async sendText(text, options = {}) {
    // ...
    const requestId = this.sendManager.sendText(text, {
        requireTTS: options.requireTTS,
        enableSRS: options.enableSRS,
        functionCallingOp: options.functionCalling ? 'REPLACE' : undefined,
        functionCalling: options.functionCalling,
        systemPrompt: options.systemPrompt,
        sceneContext: options.sceneContext,
        currentQuestion: text
    });
    // ...
}
```

#### 2.3 扩展配置面板

**修改文件**：`client/web/Demo/src/components/SettingsPanel.js`

**升级内容**：
- 添加系统提示词配置区域
- 添加场景描述配置区域
- 支持实时预览和保存

### 3. 通信协议扩展

#### 3.1 注册消息扩展

**修改文件**：`docs/CommunicationProtocol_CS.md`

**扩展内容**：
```json
// REGISTER payload 扩展
{
  "auth": {
    "type": "API_KEY",
    "api_key": "xxx"
  },
  "platform": "WEB",
  "require_tts": false,
  "enable_srs": true,
  "function_calling": [],
  "system_prompt": {
    "role_description": "你是博物馆智能助手...",
    "response_requirements": "请友好、专业地回答用户问题..."
  },
  "scene_context": {
    "description": "纹样展示场景",
    "keywords": ["纹样", "艺术", "历史"]
  }
}
```

#### 3.2 请求消息扩展

**扩展内容**：
```json
// REQUEST payload 扩展
{
  "request_id": "req_xxx",
  "data_type": "TEXT",
  "stream_flag": false,
  "stream_seq": 0,
  "require_tts": true,
  "content": {
    "text": "用户提问"
  },
  "system_prompt": {
    "role_description": "更新后的角色描述"
  },
  "scene_context": {
    "description": "更新后的场景描述"
  }
}
```

## 四、升级步骤

### 1. 服务器端升级
1. **修改会话管理**：扩展 `EnhancedClientSession` 支持新字段
2. **修改API接口**：扩展会话注册和请求接口
3. **修改提示词构建**：从会话中获取完整提示词资料
4. **测试服务器功能**：确保现有功能正常，新功能可用

### 2. 客户端升级
1. **修改WebSocket客户端**：扩展注册和请求方法
2. **修改SDK**：扩展 `MuseumAgentSDK` 支持新字段
3. **修改配置面板**：添加新配置区域
4. **测试客户端功能**：确保配置和更新功能正常

### 3. 协议更新
1. **更新通信协议文档**：添加新字段说明
2. **确保向后兼容**：旧客户端仍能正常工作

### 4. 集成测试
1. **端到端测试**：测试完整的注册、配置、请求流程
2. **边界情况测试**：测试部分字段更新的情况
3. **性能测试**：确保新数据结构不影响系统性能

## 五、技术优势

### 1. 灵活性提升
- **动态配置**：客户端可随时更新系统提示词和场景信息
- **个性化体验**：不同场景可配置不同的LLM行为
- **实时调整**：根据对话进展调整提示词策略

### 2. 可维护性提升
- **集中管理**：所有提示词相关数据集中存储在会话中
- **统一构建**：服务器端统一构建最终提示词
- **清晰流程**：数据流向和构建逻辑清晰明了

### 3. 功能增强
- **场景感知**：LLM可根据具体场景调整回答风格
- **上下文丰富**：提供更丰富的上下文信息给LLM
- **智能适配**：根据不同场景自动调整函数调用策略

## 六、风险评估

### 1. 潜在风险
- **数据量增加**：会话数据量增加可能影响性能
- **兼容性问题**：旧客户端可能不支持新字段
- **配置复杂度**：客户端配置复杂度增加

### 2. 风险缓解
- **数据优化**：仅存储必要字段，使用合理默认值
- **向后兼容**：保持旧字段和流程不变
- **简化配置**：提供合理默认配置，减少用户配置负担

## 七、预期效果

### 1. 系统层面
- **会话管理更完善**：支持更丰富的会话数据
- **提示词构建更智能**：基于会话数据动态构建
- **API调用更高效**：减少重复数据传输

### 2. 用户层面
- **配置更灵活**：可根据需要调整LLM行为
- **体验更个性化**：不同场景有不同的交互体验
- **响应更准确**：LLM获得更丰富的上下文信息

## 八、总结

本次升级通过扩展会话数据结构和提示词构建逻辑，实现了客户端配置与服务器实时获取的完整流程。这将显著提升系统的灵活性、可维护性和用户体验，为后续功能扩展奠定坚实基础。

升级计划遵循最小改动原则，保持向后兼容，确保系统平稳过渡。通过分阶段实施和充分测试，可以确保升级过程的顺利进行和最终效果的达成。