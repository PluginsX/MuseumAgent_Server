# 完整架构流程 - 阶段 1-2：客户端配置与会话注册

## 📋 流程概述

本文档详细描述流程的前两个阶段：
1. **客户端定义基本信息和配置**
2. **会话注册和缓存数据**

---

## 🎯 阶段 1：客户端定义基本信息和配置

### 1.1 配置面板初始化

**文件**: `client/web/Demo/src/components/SettingsPanel.js`

```javascript
class SettingsPanel {
    constructor() {
        // 默认配置
        this.config = {
            // ===== 认证信息 =====
            auth: {
                type: 'API_KEY',
                api_key: ''
            },
            
            // ===== 平台信息 =====
            platform: 'WEB',
            
            // ===== 系统提示词配置 =====
            system_prompt: {
                role_description: '你是博物馆智能助手，专注于文物知识讲解和互动体验。你具备丰富的历史文化知识，能够用生动有趣的方式介绍文物背后的故事。',
                response_requirements: '请用友好、专业的语言回答问题，注重知识性和趣味性的结合。回答要准确、简洁，适合普通观众理解。'
            },
            
            // ===== 场景上下文配置 =====
            scene_context: {
                current_scene: '公共场景',
                scene_description: '博物馆公共展示区域',
                keywords: ['文物', '历史', '文化'],
                scene_specific_prompt: ''
            },
            
            // ===== 功能开关配置 =====
            require_tts: false,
            enable_srs: true,
            
            // ===== 函数调用配置 =====
            function_calling: []
        };
        
        // 从本地存储加载配置
        this.loadConfig();
    }
    
    // 加载配置
    loadConfig() {
        const saved = localStorage.getItem('museum_agent_config');
        if (saved) {
            try {
                this.config = JSON.parse(saved);
            } catch (e) {
                console.error('Failed to load config:', e);
            }
        }
    }
    
    // 保存配置
    saveConfig() {
        localStorage.setItem('museum_agent_config', JSON.stringify(this.config));
    }
    
    // 渲染配置面板
    render() {
        const panel = document.createElement('div');
        panel.className = 'settings-panel';
        
        // 渲染各个配置区域
        panel.appendChild(this.renderAuthSection());
        panel.appendChild(this.renderSystemPromptSection());
        panel.appendChild(this.renderSceneContextSection());
        panel.appendChild(this.renderFunctionSection());
        panel.appendChild(this.renderSwitchSection());
        
        return panel;
    }
    
    // 渲染系统提示词配置区域
    renderSystemPromptSection() {
        const section = document.createElement('div');
        section.className = 'config-section';
        
        const title = document.createElement('h3');
        title.textContent = '系统提示词配置';
        section.appendChild(title);
        
        // 角色描述
        const roleGroup = document.createElement('div');
        roleGroup.className = 'form-group';
        
        const roleLabel = document.createElement('label');
        roleLabel.textContent = 'LLM 角色描述';
        roleGroup.appendChild(roleLabel);
        
        const roleTextarea = document.createElement('textarea');
        roleTextarea.value = this.config.system_prompt.role_description;
        roleTextarea.rows = 4;
        roleTextarea.addEventListener('input', (e) => {
            this.config.system_prompt.role_description = e.target.value;
            this.saveConfig();
        });
        roleGroup.appendChild(roleTextarea);
        
        section.appendChild(roleGroup);
        
        // 响应要求
        const reqGroup = document.createElement('div');
        reqGroup.className = 'form-group';
        
        const reqLabel = document.createElement('label');
        reqLabel.textContent = 'LLM 响应要求';
        reqGroup.appendChild(reqLabel);
        
        const reqTextarea = document.createElement('textarea');
        reqTextarea.value = this.config.system_prompt.response_requirements;
        reqTextarea.rows = 3;
        reqTextarea.addEventListener('input', (e) => {
            this.config.system_prompt.response_requirements = e.target.value;
            this.saveConfig();
        });
        reqGroup.appendChild(reqTextarea);
        
        section.appendChild(reqGroup);
        
        return section;
    }
    
    // 渲染场景上下文配置区域
    renderSceneContextSection() {
        const section = document.createElement('div');
        section.className = 'config-section';
        
        const title = document.createElement('h3');
        title.textContent = '场景上下文配置';
        section.appendChild(title);
        
        // 当前场景
        const sceneGroup = document.createElement('div');
        sceneGroup.className = 'form-group';
        
        const sceneLabel = document.createElement('label');
        sceneLabel.textContent = '当前场景';
        sceneGroup.appendChild(sceneLabel);
        
        const sceneInput = document.createElement('input');
        sceneInput.type = 'text';
        sceneInput.value = this.config.scene_context.current_scene;
        sceneInput.addEventListener('input', (e) => {
            this.config.scene_context.current_scene = e.target.value;
            this.saveConfig();
        });
        sceneGroup.appendChild(sceneInput);
        
        section.appendChild(sceneGroup);
        
        // 场景描述
        const descGroup = document.createElement('div');
        descGroup.className = 'form-group';
        
        const descLabel = document.createElement('label');
        descLabel.textContent = '场景描述';
        descGroup.appendChild(descLabel);
        
        const descTextarea = document.createElement('textarea');
        descTextarea.value = this.config.scene_context.scene_description;
        descTextarea.rows = 3;
        descTextarea.addEventListener('input', (e) => {
            this.config.scene_context.scene_description = e.target.value;
            this.saveConfig();
        });
        descGroup.appendChild(descTextarea);
        
        section.appendChild(descGroup);
        
        // 场景特定提示
        const promptGroup = document.createElement('div');
        promptGroup.className = 'form-group';
        
        const promptLabel = document.createElement('label');
        promptLabel.textContent = '场景特定提示';
        promptGroup.appendChild(promptLabel);
        
        const promptTextarea = document.createElement('textarea');
        promptTextarea.value = this.config.scene_context.scene_specific_prompt || '';
        promptTextarea.rows = 2;
        promptTextarea.placeholder = '例如：重点介绍纹样的艺术特点和历史演变';
        promptTextarea.addEventListener('input', (e) => {
            this.config.scene_context.scene_specific_prompt = e.target.value;
            this.saveConfig();
        });
        promptGroup.appendChild(promptTextarea);
        
        section.appendChild(promptGroup);
        
        return section;
    }
    
    // 获取完整配置
    getConfig() {
        return this.config;
    }
}
```

### 1.2 场景预设模板

为了方便用户快速切换场景，提供预设模板：

```javascript
// 场景预设模板
const SCENE_PRESETS = {
    '纹样展示场景': {
        scene_context: {
            current_scene: '纹样展示场景',
            scene_description: '展示中国传统纹样的艺术价值和文化内涵，包括龙纹、凤纹、云纹等经典纹样的演变历史',
            keywords: ['纹样', '艺术', '历史', '文化'],
            scene_specific_prompt: '重点介绍纹样的艺术特点、历史演变和文化象征意义'
        }
    },
    '铸造工艺场景': {
        scene_context: {
            current_scene: '铸造工艺展示场景',
            scene_description: '展示青铜器的铸造工艺和技术演变，包括范铸法、失蜡法等传统工艺',
            keywords: ['铸造', '工艺', '技术', '青铜器'],
            scene_specific_prompt: '重点介绍铸造技术的发展历程和工艺特点'
        }
    },
    '历史文化场景': {
        scene_context: {
            current_scene: '历史文化展示场景',
            scene_description: '展示文物背后的历史故事和文化背景，帮助观众理解文物的历史价值',
            keywords: ['历史', '文化', '故事', '背景'],
            scene_specific_prompt: '重点讲述文物背后的历史故事和文化意义'
        }
    },
    '互动体验场景': {
        scene_context: {
            current_scene: '互动体验场景',
            scene_description: '提供互动式的文物体验，包括虚拟展示、动画演示等',
            keywords: ['互动', '体验', '动画', '展示'],
            scene_specific_prompt: '注重互动性和趣味性，引导用户参与体验'
        }
    }
};

// 应用场景预设
function applyScenePreset(presetName) {
    const preset = SCENE_PRESETS[presetName];
    if (preset) {
        settingsPanel.config.scene_context = preset.scene_context;
        settingsPanel.saveConfig();
        settingsPanel.render(); // 重新渲染
    }
}
```

---

## 🔄 阶段 2：会话注册和缓存数据

### 2.1 客户端发起注册

**文件**: `client/web/lib/core/WebSocketClient.js`

```javascript
class WebSocketClient extends EventEmitter {
    /**
     * 注册会话（完整版）
     * @param {Object} authData - 认证信息
     * @param {string} platform - 平台类型
     * @param {boolean} requireTTS - 是否需要 TTS
     * @param {boolean} enableSRS - 是否启用 SRS
     * @param {Array} functionCalling - 函数定义列表
     * @param {Object} systemPrompt - 系统提示词配置
     * @param {Object} sceneContext - 场景上下文配置
     */
    async register(
        authData,
        platform = 'WEB',
        requireTTS = false,
        enableSRS = true,
        functionCalling = [],
        systemPrompt = null,
        sceneContext = null
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
            
            // 添加系统提示词配置
            if (systemPrompt) {
                message.payload.system_prompt = systemPrompt;
            }
            
            // 添加场景上下文配置
            if (sceneContext) {
                message.payload.scene_context = sceneContext;
            }
            
            // 设置注册响应监听器
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
}
```

### 2.2 SDK 层封装

**文件**: `client/web/lib/MuseumAgentSDK.js`

```javascript
class MuseumAgentSDK extends EventEmitter {
    /**
     * 连接并注册
     * @param {Object} config - 完整配置对象
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
}
```

### 2.3 服务器端接收注册请求

**文件**: `src/api/session_api.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class SystemPromptConfig(BaseModel):
    """系统提示词配置"""
    role_description: str = Field(..., description="LLM 角色描述")
    response_requirements: str = Field(..., description="LLM 响应要求")

class SceneContextConfig(BaseModel):
    """场景上下文配置"""
    current_scene: str = Field(..., description="当前场景名称")
    scene_description: str = Field(..., description="场景描述")
    keywords: List[str] = Field(default_factory=list, description="场景关键词")
    scene_specific_prompt: Optional[str] = Field(None, description="场景特定提示")

class ClientRegistrationRequest(BaseModel):
    """客户端注册请求（完整版）"""
    auth: Dict[str, Any] = Field(..., description="认证信息")
    platform: str = Field(default="WEB", description="平台类型")
    require_tts: bool = Field(default=False, description="是否需要 TTS")
    enable_srs: bool = Field(default=True, description="是否启用 SRS")
    function_calling: List[Dict[str, Any]] = Field(default_factory=list, description="函数定义列表")
    system_prompt: Optional[SystemPromptConfig] = Field(None, description="系统提示词配置")
    scene_context: Optional[SceneContextConfig] = Field(None, description="场景上下文配置")

@router.post("/register")
async def register_session(request: ClientRegistrationRequest):
    """注册会话（完整版）"""
    try:
        # 生成会话 ID
        session_id = generate_session_id()
        
        # 构建客户端元数据
        client_metadata = {
            "platform": request.platform,
            "client_type": request.platform,  # 兼容旧版
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
        
        # 注册会话（包含函数定义）
        session = strict_session_manager.register_session_with_functions(
            session_id=session_id,
            client_metadata=client_metadata,
            functions=request.function_calling
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

### 2.4 会话管理器存储数据

**文件**: `src/session/strict_session_manager.py`

```python
def register_session_with_functions(
    self, 
    session_id: str, 
    client_metadata: Dict[str, Any], 
    functions: List[Dict[str, Any]]
) -> EnhancedClientSession:
    """注册支持完整配置的会话"""
    
    # 验证函数定义
    from ..models.function_calling_models import is_valid_openai_function
    valid_functions = []
    function_names = []
    
    if functions:
        for func_def in functions:
            if is_valid_openai_function(func_def):
                valid_functions.append(func_def)
                function_names.append(func_def.get("name", "unknown"))
            else:
                self.logger.sess.warn(
                    f'Skipping non-OpenAI compliant function: {func_def.get("name", "unknown")}'
                )
    
    # 存储验证后的函数定义
    client_metadata["functions"] = valid_functions
    client_metadata["function_names"] = function_names
    
    # 记录注册信息
    self.logger.sess.info(
        'Session registered with complete config',
        {
            'session_id': session_id[:8],
            'platform': client_metadata.get('platform'),
            'require_tts': client_metadata.get('require_tts'),
            'enable_srs': client_metadata.get('enable_srs'),
            'has_system_prompt': 'system_prompt' in client_metadata,
            'has_scene_context': 'scene_context' in client_metadata,
            'function_count': len(valid_functions),
            'functions': function_names if function_names else '普通对话模式'
        }
    )
    
    # 调用基础注册方法
    return self.register_session(session_id, client_metadata)
```

### 2.5 会话数据结构

注册完成后，会话中存储的完整数据：

```python
# session.client_metadata 的完整结构
{
    # 平台信息
    "platform": "WEB",
    "client_type": "WEB",
    
    # 系统提示词配置
    "system_prompt": {
        "role_description": "你是博物馆智能助手，专注于文物知识讲解和互动体验...",
        "response_requirements": "请用友好、专业的语言回答问题..."
    },
    
    # 场景上下文配置
    "scene_context": {
        "current_scene": "纹样展示场景",
        "scene_description": "展示中国传统纹样的艺术价值和文化内涵...",
        "keywords": ["纹样", "艺术", "历史", "文化"],
        "scene_specific_prompt": "重点介绍纹样的艺术特点、历史演变和文化象征意义"
    },
    
    # 功能开关
    "require_tts": True,
    "enable_srs": True,
    
    # 函数定义
    "functions": [
        {
            "name": "play_animation",
            "description": "播放宠物动画效果",
            "parameters": {...}
        }
    ],
    "function_names": ["play_animation"]
}
```

---

## 📊 流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    阶段 1：客户端配置                        │
└─────────────────────────────────────────────────────────────┘

用户打开配置面板
    ↓
配置系统提示词
    - 角色描述
    - 响应要求
    ↓
配置场景上下文
    - 当前场景
    - 场景描述
    - 场景特定提示
    ↓
配置功能开关
    - require_tts
    - enable_srs
    ↓
配置函数定义
    - 添加/编辑函数
    ↓
保存配置到本地存储

┌─────────────────────────────────────────────────────────────┐
│                    阶段 2：会话注册                          │
└─────────────────────────────────────────────────────────────┘

用户点击"连接"按钮
    ↓
SDK.connect(config)
    ↓
WebSocketClient.connect()
    ↓
WebSocket 连接建立
    ↓
WebSocketClient.register(
    auth,
    platform,
    requireTTS,
    enableSRS,
    functionCalling,
    systemPrompt,      ← 系统提示词配置
    sceneContext       ← 场景上下文配置
)
    ↓
发送 REGISTER 消息
    ↓
服务器接收消息
    ↓
session_api.register_session()
    ↓
构建 client_metadata
    - 添加 system_prompt
    - 添加 scene_context
    - 添加 require_tts
    - 添加 enable_srs
    - 验证 functions
    ↓
strict_session_manager.register_session_with_functions()
    ↓
创建 EnhancedClientSession
    ↓
存储到 sessions 字典
    ↓
返回 REGISTER_SUCCESS 消息
    ↓
客户端接收响应
    ↓
SDK 初始化完成
    ↓
触发 'connected' 事件
```

---

## ✅ 关键要点

### 客户端职责
1. ✅ 提供完整的配置信息
2. ✅ 支持配置的持久化（本地存储）
3. ✅ 提供场景预设模板
4. ✅ 支持配置的实时编辑

### 服务器职责
1. ✅ 接收并验证配置信息
2. ✅ 存储配置到会话中
3. ✅ 验证函数定义的合法性
4. ✅ 提供默认配置值

### 数据完整性
1. ✅ 所有配置都存储在 `client_metadata` 中
2. ✅ 支持可选配置（提供默认值）
3. ✅ 配置数据结构清晰、易于扩展

---

**下一步**: 查看 [COMPLETE_ARCHITECTURE_FLOW_2.md](./COMPLETE_ARCHITECTURE_FLOW_2.md) 了解后续流程

