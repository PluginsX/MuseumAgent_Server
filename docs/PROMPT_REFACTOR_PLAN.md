# 提示词构建模块重构计划

## 一、设计理念

### 核心原则：模板与数据分离

**配置文件职责**：定义提示词的**结构模板**（如何组装）
**运行时数据**：提供提示词的**具体内容**（组装什么）

### 变量定义

提示词构建需要的6个核心变量：

| 变量ID | 变量名 | 来源 | 示例 |
|--------|--------|------|------|
| 1 | `role_description` | 会话配置 | "你叫韩立，是辽宁省博物馆的智能讲解员..." |
| 2 | `response_requirements` | 会话配置 | "基于当前所处的场景以及场景的内容..." |
| 3 | `scene_description` | 会话配置 | "当前所处的是'西周青铜器造型纹样展示区'..." |
| 4 | `functions_description` | 运行时生成 | "移动摄像机到(瓶口、瓶身...)、播放音乐..." |
| 5 | `user_input` | 用户请求 | "饕餮纹是什么寓意？" |
| 6 | `retrieved_materials` | RAG检索 | "饕餮纹相关材料1、饕餮纹相关材料2" |

---

## 二、新配置文件结构

### config.json 新增配置节

```json
{
  "llm": {
    "prompt_templates": {
      "system_message": {
        "template": "{role_description}\n\n{response_requirements}\n\n{scene_description}\n\n当前场景下支持以下函数调用：\n{functions_description}",
        "variables": ["role_description", "response_requirements", "scene_description", "functions_description"],
        "description": "系统消息模板，定义智能体的角色、职责和能力"
      },
      "user_message": {
        "template": "用户的问题是：{user_input}\n\n相关的资料包括：\n{retrieved_materials}",
        "variables": ["user_input", "retrieved_materials"],
        "description": "用户消息模板，包含用户输入和检索到的相关材料"
      },
      "user_message_without_rag": {
        "template": "用户的问题是：{user_input}",
        "variables": ["user_input"],
        "description": "无RAG检索时的用户消息模板"
      },
      "functions_description_format": {
        "template": "- {name}: {description}",
        "description": "单个函数的描述格式"
      }
    }
  }
}
```

---

## 三、重构架构设计

### 3.1 新增模块：PromptTemplateEngine

**职责**：解析模板、填充变量、生成最终提示词

**位置**：`src/core/modules/prompt_template_engine.py`

```python
class PromptTemplateEngine:
    """提示词模板引擎 - 负责模板解析和变量填充"""
    
    def __init__(self):
        """从配置文件加载模板"""
        self.templates = self._load_templates()
    
    def render_system_message(self, variables: Dict[str, str]) -> str:
        """渲染系统消息"""
        pass
    
    def render_user_message(self, variables: Dict[str, str], has_rag: bool = True) -> str:
        """渲染用户消息"""
        pass
    
    def render_functions_description(self, functions: List[Dict]) -> str:
        """渲染函数描述列表"""
        pass
    
    def validate_variables(self, template_name: str, variables: Dict[str, str]) -> bool:
        """验证变量完整性"""
        pass
```

### 3.2 重构模块：PromptBuilder

**职责**：收集变量、调用模板引擎、构建最终payload

**位置**：`src/core/modules/prompt_builder.py`

```python
class PromptBuilder:
    """提示词构建器 - 负责收集变量并调用模板引擎"""
    
    def __init__(self):
        self.template_engine = PromptTemplateEngine()
    
    def build_llm_payload(
        self,
        session_id: str,
        user_input: str,
        rag_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        构建完整的LLM API请求payload
        
        流程：
        1. 从会话获取变量1、2、3
        2. 从函数定义生成变量4
        3. 从用户输入获取变量5
        4. 从RAG上下文获取变量6
        5. 调用模板引擎渲染
        6. 构建最终payload
        """
        pass
    
    def _collect_variables(self, session_id: str, user_input: str, 
                          rag_context: Optional[Dict]) -> Dict[str, str]:
        """收集所有变量"""
        pass
    
    def _get_role_description(self, session: Session) -> str:
        """从会话获取角色描述（变量1）"""
        pass
    
    def _get_response_requirements(self, session: Session) -> str:
        """从会话获取响应要求（变量2）"""
        pass
    
    def _get_scene_description(self, session: Session) -> str:
        """从会话获取场景描述（变量3）"""
        pass
    
    def _generate_functions_description(self, functions: List[Dict]) -> str:
        """生成函数描述（变量4）"""
        pass
    
    def _format_retrieved_materials(self, rag_context: Dict) -> str:
        """格式化检索材料（变量6）"""
        pass
```

### 3.3 简化模块：DynamicLLMClient

**职责**：仅负责HTTP调用，不再参与提示词构建

**位置**：`src/core/dynamic_llm_client.py`

```python
class DynamicLLMClient:
    """LLM客户端 - 仅负责API调用"""
    
    def chat_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """同步调用LLM API"""
        pass
    
    async def chat_completion_stream(self, payload: Dict[str, Any], 
                                    cancel_event: Optional[asyncio.Event] = None) -> AsyncGenerator:
        """异步流式调用LLM API"""
        pass
```

### 3.4 简化模块：CommandGenerator

**职责**：协调各模块，不再直接构建提示词

**位置**：`src/core/command_generator.py`

```python
class CommandGenerator:
    """指令生成器 - 协调器模式"""
    
    def __init__(self):
        self.rag_processor = SemanticRetrievalProcessor()
        self.prompt_builder = PromptBuilder()  # 使用新的PromptBuilder
        self.llm_client = DynamicLLMClient()
        self.response_parser = ResponseParser()
    
    async def stream_generate(self, user_input: str, session_id: str, 
                            cancel_event: Optional[asyncio.Event] = None):
        """
        流式生成响应
        
        流程：
        1. 检查enable_srs，决定是否执行RAG
        2. 调用PromptBuilder构建payload
        3. 调用LLMClient执行请求
        4. 流式返回结果
        """
        # 1. RAG检索（如果启用）
        rag_context = None
        if self._should_perform_rag(session_id):
            rag_context = self.rag_processor.perform_retrieval(user_input, session_id)
        
        # 2. 构建payload（所有提示词构建逻辑都在PromptBuilder中）
        payload = self.prompt_builder.build_llm_payload(
            session_id=session_id,
            user_input=user_input,
            rag_context=rag_context
        )
        
        # 3. 调用LLM
        async for chunk in self.llm_client.chat_completion_stream(payload, cancel_event):
            yield chunk
```

---

## 四、数据流转图

```
用户请求 (user_input)
    ↓
CommandGenerator.stream_generate()
    ↓
    ├─→ [可选] RAG检索 → rag_context (变量6来源)
    ↓
PromptBuilder.build_llm_payload()
    ↓
    ├─→ 从会话获取变量
    │   ├─→ system_prompt.role_description (变量1)
    │   ├─→ system_prompt.response_requirements (变量2)
    │   └─→ scene_context.scene_description (变量3)
    │
    ├─→ 从会话获取函数定义
    │   └─→ 生成 functions_description (变量4)
    │
    ├─→ 用户输入 (变量5)
    │
    ├─→ 格式化RAG结果 (变量6)
    │
    └─→ 调用 PromptTemplateEngine
        ├─→ render_system_message(变量1,2,3,4)
        ├─→ render_user_message(变量5,6)
        └─→ 返回 messages 数组
    ↓
构建完整 payload
    {
        "model": "...",
        "messages": [
            {"role": "system", "content": "渲染后的系统消息"},
            {"role": "user", "content": "渲染后的用户消息"}
        ],
        "functions": [...],
        "function_call": "auto",
        ...
    }
    ↓
DynamicLLMClient.chat_completion_stream(payload)
    ↓
LLM API
```

---

## 五、重构步骤

### Phase 1: 创建新模块（不影响现有功能）

**Step 1.1**: 创建 `PromptTemplateEngine`
- 文件：`src/core/modules/prompt_template_engine.py`
- 实现模板加载、解析、渲染功能
- 编写单元测试

**Step 1.2**: 更新配置文件
- 在 `config.json` 中添加 `prompt_templates` 配置节
- 定义系统消息和用户消息模板

**Step 1.3**: 编写集成测试
- 测试模板引擎能否正确渲染
- 验证变量替换逻辑

### Phase 2: 重构 PromptBuilder（向后兼容）

**Step 2.1**: 重写 `PromptBuilder.build_llm_payload()`
- 实现变量收集逻辑
- 调用 `PromptTemplateEngine` 渲染
- 保留旧方法作为后备

**Step 2.2**: 更新 `CommandGenerator`
- 修改调用方式，使用新的 `build_llm_payload()`
- 保持接口不变

**Step 2.3**: 测试验证
- 对比新旧实现的输出
- 确保提示词质量不下降

### Phase 3: 简化 DynamicLLMClient

**Step 3.1**: 移除提示词构建逻辑
- 删除 `generate_function_calling_payload()`
- 保留纯粹的API调用方法

**Step 3.2**: 更新所有调用点
- 确保所有地方都使用 `PromptBuilder`

### Phase 4: 清理和优化

**Step 4.1**: 删除废弃代码
- 移除旧的提示词构建逻辑
- 清理未使用的配置项

**Step 4.2**: 更新文档
- 更新架构文档
- 添加配置说明

**Step 4.3**: 性能优化
- 缓存模板解析结果
- 优化变量收集逻辑

---

## 六、配置文件示例

### 完整的 prompt_templates 配置

```json
{
  "llm": {
    "prompt_templates": {
      "system_message": {
        "template": "{role_description}\n\n职责要求：\n{response_requirements}\n\n当前场景：\n{scene_description}\n\n可用功能：\n{functions_description}",
        "variables": ["role_description", "response_requirements", "scene_description", "functions_description"],
        "description": "系统消息模板"
      },
      "user_message_with_rag": {
        "template": "用户问题：{user_input}\n\n参考资料：\n{retrieved_materials}",
        "variables": ["user_input", "retrieved_materials"],
        "description": "带RAG的用户消息模板"
      },
      "user_message_without_rag": {
        "template": "用户问题：{user_input}",
        "variables": ["user_input"],
        "description": "不带RAG的用户消息模板"
      },
      "function_item_format": {
        "template": "• {name}: {description}\n  参数：{parameters}",
        "description": "单个函数的格式化模板"
      },
      "rag_material_format": {
        "template": "【{title}】\n{content}\n相似度：{similarity}",
        "description": "单条RAG材料的格式化模板"
      }
    }
  }
}
```

---

## 七、优势分析

### 7.1 灵活性提升
- **模板可配置**：无需修改代码即可调整提示词结构
- **A/B测试友好**：可以快速切换不同的提示词模板
- **多语言支持**：可以为不同语言定义不同模板

### 7.2 可维护性提升
- **职责清晰**：模板引擎、变量收集、API调用各司其职
- **易于测试**：每个模块可以独立测试
- **易于扩展**：新增变量只需修改配置和收集逻辑

### 7.3 可观测性提升
- **变量可追踪**：可以记录每次请求使用的变量值
- **模板可审计**：可以查看历史使用的模板版本
- **问题可定位**：提示词问题可以快速定位到具体变量或模板

---

## 八、风险评估

### 8.1 兼容性风险
**风险**：新实现可能与现有行为不一致
**缓解**：
- Phase 2 保留旧实现作为后备
- 充分的对比测试
- 灰度发布

### 8.2 性能风险
**风险**：模板解析可能增加延迟
**缓解**：
- 缓存解析后的模板
- 预编译模板
- 性能基准测试

### 8.3 配置复杂度风险
**风险**：配置文件变得复杂难以理解
**缓解**：
- 提供详细的配置文档
- 提供配置验证工具
- 提供配置示例

---

## 九、时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| Phase 1 | 创建 PromptTemplateEngine | 2天 |
| Phase 1 | 更新配置文件 | 0.5天 |
| Phase 1 | 编写单元测试 | 1天 |
| Phase 2 | 重构 PromptBuilder | 2天 |
| Phase 2 | 更新 CommandGenerator | 1天 |
| Phase 2 | 集成测试 | 1天 |
| Phase 3 | 简化 DynamicLLMClient | 1天 |
| Phase 3 | 更新调用点 | 0.5天 |
| Phase 4 | 清理和优化 | 1天 |
| Phase 4 | 文档更新 | 1天 |
| **总计** | | **11天** |

---

## 十、成功标准

### 功能标准
- ✅ 所有提示词通过模板生成
- ✅ 支持动态变量替换
- ✅ 支持RAG材料格式化
- ✅ 支持函数描述生成

### 质量标准
- ✅ 单元测试覆盖率 > 90%
- ✅ 集成测试通过率 100%
- ✅ 提示词质量不下降

### 性能标准
- ✅ 提示词构建延迟 < 10ms
- ✅ 内存占用增加 < 5%

### 可维护性标准
- ✅ 代码行数减少 > 20%
- ✅ 模块耦合度降低
- ✅ 配置文档完整

---

## 十一、后续优化方向

### 11.1 模板版本管理
- 支持多版本模板共存
- 支持模板回滚
- 支持模板A/B测试

### 11.2 智能模板选择
- 根据场景自动选择最优模板
- 根据用户反馈优化模板

### 11.3 模板可视化编辑
- 提供Web界面编辑模板
- 实时预览渲染效果
- 模板语法高亮

---

## 十二、总结

本重构计划的核心是**实现模板与数据的彻底分离**，让配置文件专注于定义"如何组装"，让运行时数据专注于提供"组装什么"。

通过引入 `PromptTemplateEngine` 和重构 `PromptBuilder`，我们可以实现：
1. **更灵活的提示词管理**
2. **更清晰的代码结构**
3. **更容易的维护和扩展**

这个重构是**不考虑兼容的全面升级**，但通过分阶段实施，可以将风险控制在可接受范围内。

