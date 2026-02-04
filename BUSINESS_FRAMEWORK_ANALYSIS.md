# 博物馆代理服务器业务流程框架分析

## 1. 整体架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   客户端应用     │    │   管理面板       │    │   移动客户端     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │     FastAPI服务器        │
                    │  (博物馆代理服务核心)     │
                    └─────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   ChromaDB    │      │  SQL数据库     │      │   LLM服务      │
│  (向量存储)    │      │  (用户数据)    │      │  (AI推理)      │
└───────────────┘      └───────────────┘      └───────────────┘
```

## 2. 核心业务流程

### 2.1 服务启动流程
```
main.py → 加载配置 → 初始化日志 → 启动FastAPI应用
    ↓
agent_api.py → 注册中间件 → 挂载API路由 → 初始化数据库
    ↓
启动后台清理线程 → 服务就绪监听请求
```

### 2.2 客户端会话注册流程
```
客户端 → POST /api/session/register
    ↓
验证函数定义(OpenAI标准) → 注册会话 → 返回session_id
    ↓
客户端 → POST /api/v1/functions/register (可选)
    ↓
注册自定义函数 → 验证OpenAI标准 → 存储函数定义
```

### 2.3 智能体解析核心流程
```
客户端 → POST /api/agent/parse (带session_id)
    ↓
会话验证 → RAG检索 → 获取函数定义
    ↓
构建函数调用请求 → 调用LLM → 解析函数调用响应
    ↓
返回标准化指令 → 客户端执行
```

## 3. 模块分工与职责

### 3.1 API层模块
```
src/api/
├── agent_api.py          # 核心API入口，路由注册
├── session_api.py        # 会话管理API
├── function_api.py       # 函数注册API (新增)
├── client_api.py         # 客户端管理API
├── auth_api.py           # 认证授权API
└── 其他管理API...
```

### 3.2 核心业务层模块
```
src/core/
├── command_generator.py     # 流程协调器(核心)
├── dynamic_llm_client.py    # LLM客户端
├── modules/
│   ├── rag_processor.py     # RAG检索处理器
│   ├── prompt_builder.py    # 提示词构建器
│   └── response_parser.py   # 响应解析器
```

### 3.3 会话管理层模块
```
src/session/
├── strict_session_manager.py  # 严格会话管理器
└── session_manager.py         # 已废弃(待删除)
```

### 3.4 数据访问层模块
```
src/db/
├── database.py              # 数据库连接
├── models.py                # 数据模型定义
└── seed.py                  # 初始化数据
```

### 3.5 公共工具层模块
```
src/common/
├── config_utils.py          # 配置工具
├── log_utils.py             # 日志工具
├── auth_utils.py            # 认证工具
└── 其他工具...
```

## 4. 模块间接口规则

### 4.1 数据流向接口
```
API层 → 业务层 → 会话层 → 数据层
   ↓        ↓        ↓        ↓
响应数据  处理结果  会话状态  持久化数据
```

### 4.2 核心协调接口
```
CommandGenerator (协调器)
├── 调用: RAGProcessor.perform_retrieval()
├── 调用: PromptBuilder.build_rag_instruction()
├── 调用: DynamicLLMClient.generate_function_calling_payload()
├── 调用: strict_session_manager.get_functions_for_session()
└── 返回: 标准化指令字典
```

### 4.3 会话管理接口
```
strict_session_manager
├── register_session_with_functions() → 注册函数会话
├── validate_session() → 验证会话有效性
├── get_functions_for_session() → 获取函数定义
├── heartbeat() → 心跳检测
└── unregister_session() → 注销会话
```

## 5. 关键数据结构

### 5.1 会话数据结构
```python
EnhancedClientSession:
- session_id: str                    # 会话ID
- client_metadata: Dict              # 客户端元数据
- created_at: datetime               # 创建时间
- last_heartbeat: datetime           # 最后心跳时间
- expires_at: datetime               # 过期时间
- is_registered: bool                # 是否已注册
```

### 5.2 函数定义结构
```python
OpenAI标准函数定义:
{
    "name": "function_name",
    "description": "函数描述",
    "parameters": {
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string|number|boolean",
                "description": "参数描述"
            }
        },
        "required": ["必需参数"]
    }
}
```

## 6. 异常处理机制

### 6.1 层级异常处理
```
API层: HTTP异常封装
↓
业务层: 业务逻辑异常
↓
数据层: 数据库异常
↓
底层: 系统级异常
```

### 6.2 会话异常处理
```
会话不存在 → 返回404错误
会话过期 → 返回401错误
会话无效 → 自动清理并返回错误
函数定义无效 → 拒绝注册并返回400错误
```