# 模块分工与接口规则详细分析

## 1. 模块职责划分

### 1.1 API层模块职责

#### agent_api.py (核心API入口)
**主要职责**：
- FastAPI应用实例创建和配置
- 中间件注册（CORS、Session）
- API路由挂载
- 服务生命周期管理

**对外接口**：
```python
# 核心解析接口
POST /api/agent/parse → AgentParseResponse

# 健康检查接口
GET / → {"status": "ok", "service": "MuseumAgent"}

# 管理面板接口
GET/POST /Control/* → 管理界面路由
```

#### session_api.py (会话管理API)
**主要职责**：
- 客户端会话生命周期管理
- 会话注册、验证、注销
- 心跳检测机制

**对外接口**：
```python
# 会话注册
POST /api/session/register → ClientRegistrationResponse

# 心跳检测
POST /api/session/heartbeat → HeartbeatResponse

# 会话注销
DELETE /api/session/unregister → 注销响应

# 函数获取
GET /api/session/functions → SessionOperationsResponse

# 会话信息
GET /api/session/info → SessionInfoResponse
```

#### function_api.py (函数管理API) ⭐新增
**主要职责**：
- OpenAI标准函数注册
- 函数定义验证
- 函数规范化处理

**对外接口**：
```python
# 函数注册
POST /api/v1/functions/register → 函数注册响应

# 函数验证
POST /api/v1/functions/validate → 验证结果

# 函数规范化
POST /api/v1/functions/normalize → 规范化结果
```

### 1.2 核心业务层模块职责

#### command_generator.py (流程协调器) ⭐核心
**主要职责**：
- 协调各专业模块工作
- 执行标准化指令生成流程
- 管理RAG-LLM-解析整个链路

**对外接口**：
```python
def generate_standard_command(
    user_input: str,
    scene_type: str = "public",
    session_id: str = None
) -> Dict[str, Any]
```

**依赖模块接口**：
```python
# 调用RAG处理器
rag_context = rag_processor.perform_retrieval(user_input, top_k=3)

# 调用提示词构建器
rag_instruction = prompt_builder.build_rag_instruction(rag_context)

# 调用会话管理器
functions = strict_session_manager.get_functions_for_session(session_id)

# 调用LLM客户端
payload = llm_client.generate_function_calling_payload(...)
response = llm_client._chat_completions_with_functions(payload)
command = llm_client.parse_function_call_response(response)
```

#### dynamic_llm_client.py (LLM客户端)
**主要职责**：
- 与外部LLM服务通信
- 构建函数调用请求
- 解析LLM响应

**对外接口**：
```python
def generate_function_calling_payload(
    session_id: str,
    user_input: str,
    scene_type: str = "public",
    rag_instruction: str = "",
    functions: List[Dict[str, Any]] = None
) -> Dict[str, Any]

def _chat_completions_with_functions(
    payload: Dict[str, Any]
) -> Dict[str, Any]

def parse_function_call_response(
    response: Dict[str, Any]
) -> Dict[str, Any]
```

### 1.3 专业处理模块职责

#### rag_processor.py (RAG处理器)
**主要职责**：
- 向量数据库检索
- 相关文物信息召回
- 上下文信息构建

**对外接口**：
```python
def perform_retrieval(
    query: str,
    top_k: int = 3
) -> Dict[str, Any]
```

#### prompt_builder.py (提示词构建器)
**主要职责**：
- 构建RAG增强提示词
- 系统提示词管理
- 用户意图理解优化

**对外接口**：
```python
def build_rag_instruction(
    rag_context: Dict[str, Any]
) -> str
```

#### response_parser.py (响应解析器)
**主要职责**：
- 解析LLM原始响应
- 提取结构化信息
- 构建标准化指令

**对外接口**：
```python
def parse_llm_response(
    llm_response: str
) -> Dict[str, Any]

def build_standard_command(
    parsed_data: Dict[str, Any],
    rag_context: Dict[str, Any]
) -> Dict[str, Any]
```

### 1.4 会话管理层模块职责

#### strict_session_manager.py (严格会话管理器)
**主要职责**：
- 会话生命周期管理
- 会话状态验证
- 自动清理机制
- 函数定义存储管理

**对外接口**：
```python
def register_session_with_functions(
    session_id: str,
    client_metadata: Dict[str, Any],
    functions: List[Dict[str, Any]]
) -> EnhancedClientSession

def validate_session(
    session_id: str
) -> Optional[EnhancedClientSession]

def get_functions_for_session(
    session_id: str
) -> List[Dict[str, Any]]

def heartbeat(
    session_id: str
) -> bool

def unregister_session(
    session_id: str
) -> bool
```

## 2. 接口规则与约束

### 2.1 数据传递规则

#### 会话数据流
```
客户端 → session_api.register → strict_session_manager.register_session_with_functions
    ↓
会话ID ← 返回 ← EnhancedClientSession对象
    ↓
客户端 → agent_api.parse → command_generator.generate_standard_command(session_id)
    ↓
函数定义 ← strict_session_manager.get_functions_for_session(session_id)
    ↓
LLM请求 ← dynamic_llm_client.generate_function_calling_payload(functions)
    ↓
标准化指令 → 返回给客户端
```

#### 函数定义传递规则
```
1. 客户端提交OpenAI标准函数定义
2. function_api.validate验证标准合规性
3. session_api.register存储到会话元数据
4. command_generator获取函数列表
5. dynamic_llm_client构建函数调用请求
```

### 2.2 错误处理规则

#### 层级错误传播
```
底层异常 → 业务层捕获 → API层封装 → HTTP响应
    ↓           ↓           ↓          ↓
RuntimeError   ValueError   HTTPException  4xx/5xx状态码
```

#### 会话相关错误
```
会话不存在 → 404 Not Found
会话过期 → 401 Unauthorized
会话无效 → 403 Forbidden
函数定义无效 → 400 Bad Request
```

### 2.3 性能与并发规则

#### 线程安全保障
```
strict_session_manager: 使用threading.RLock
database操作: 使用连接池和事务
LLM调用: 异步非阻塞设计
```

#### 资源清理机制
```
会话过期自动清理 (15分钟)
心跳超时清理 (2分钟)
不活跃会话清理 (5分钟)
应用关闭时优雅清理
```

## 3. 模块间协作协议

### 3.1 命名规范
```
函数名: snake_case
类名: PascalCase
常量: UPPER_CASE
私有成员: _前缀
```

### 3.2 日志规范
```
格式: [MODULE] ACTION: message {context}
级别: DEBUG < INFO < WARNING < ERROR < CRITICAL
追踪: 每个重要步骤都要有日志记录
```

### 3.3 配置管理
```
全局配置: config_utils.get_global_config()
模块配置: 各模块独立配置项
环境变量: 优先级高于配置文件
```

## 4. 接口稳定性保证

### 4.1 向后兼容性
```
API接口: 保持URL和基本参数不变
数据结构: 新增字段可选，不删除现有字段
错误码: 保持错误码语义一致
```

### 4.2 版本管理
```
主版本: 重大架构变更
次版本: 新功能添加
修订版本: bug修复和优化
```