# 博物馆智能体服务器架构重大更新说明

## 🏗️ 架构演进：从预设指令集到完全动态注册

### 版本变更
- **旧架构**：服务器预设固定指令集（zoom_pattern, introduce等）
- **新架构**：完全依赖客户端动态注册指令集

### 核心变化

#### 1. 配置文件变更 (`config/config.json`)
```json
// 旧配置
"valid_operations": [
  "zoom_pattern",
  "restore_scene", 
  "introduce",
  "spirit_interact",
  "query_param"
]

// 新配置  
"valid_operations": []
```

#### 2. 知识库模块变更 (`src/core/knowledge_base.py`)
- 移除了硬编码的操作验证逻辑
- `validate_operation()` 方法现在总是返回 `False`
- 完全交由会话管理层进行操作验证

#### 3. 指令生成器变更 (`src/core/command_generator.py`)
- 传统模式已被废弃并抛出运行时错误
- 强制使用动态LLM + 会话注册机制
- **只做基本的指令集匹配验证**，不判断指令可行性
- 明确区分服务端验证（范围检查）和客户端执行（可行性判断）

#### 4. 数据库清理
- 删除了所有指令集相关的表：`instruction_sets`, `client_capabilities`, `command_sets`
- 清理了客户端表中可能存在的指令集相关字段

### 🎯 新架构优势

#### 完全解耦
- 服务端不再预设任何客户端能力
- 客户端可以注册任意自定义指令集
- 真正实现了客户端能力的动态发现

#### 明确的职责分离
- **服务端职责**：只验证指令是否在客户端注册的指令集中
- **客户端职责**：判断具体指令是否可以执行和如何执行
- **安全边界**：服务端严格限制指令范围，客户端负责执行逻辑

#### 更高的灵活性
- 支持无限多种客户端类型
- 每个客户端可以有不同的指令集
- 会话结束后自动清理客户端能力信息

### 📋 使用示例

#### 客户端注册自定义指令集
```javascript
// 宠物客户端注册动画指令
const petInstructions = ["idle", "Walk", "Run", "Sprint", "Speaking", "Happy", "Crying", "Sleeping"];

// Web3D客户端注册可视化指令  
const web3dInstructions = ["zoom_pattern", "restore_scene", "highlight_detail", "rotate_view"];

// 游戏客户端注册交互指令
const gameInstructions = ["move_to", "interact_object", "trigger_event", "play_animation"];
```

#### 服务端处理流程
1. 客户端连接并注册会话
2. 服务端接收并存储客户端指令集
3. LLM根据客户端指令集生成响应
4. 指令验证完全基于会话注册的指令集
5. 会话结束时自动清理指令集信息

### ⚠️ 注意事项

1. **向后兼容性**：传统模式已完全废弃
2. **必须使用会话机制**：所有客户端必须先注册会话
3. **指令集隔离**：每个会话的指令集完全独立
4. **会话管理重要性**：及时注销会话以释放资源

### 🧪 验证测试

运行 `test_custom_instructions_fix.py` 验证新架构功能：
- ✅ 自定义指令集注册
- ✅ 指令集隔离验证  
- ✅ 非法指令拦截
- ✅ 会话生命周期管理

---
**更新时间**：2026-02-02  
**影响范围**：核心架构、配置管理、数据库结构