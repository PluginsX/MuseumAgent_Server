# Unity 智能体集成组件开发计划

## 一、项目结构

```
Assets/
├── Scripts/
│   ├── AgentIntegration/
│   │   ├── Runtime/
│   │   │   ├── AgentBridge.cs               # 通信桥接组件（单例）
│   │   │   ├── AgentContext.cs              # 智能体上下文组件（多实例）
│   │   │   ├── ClientConfigDeclaration.cs   # 客户端配置声明组件（集成函数执行器）
│   │   │   ├── AgentFunctionDefinitionComponent.cs  # 函数定义组件
│   │   │   └── SimpleJSON.cs                # JSON解析库
│   │   └── Editor/
│   │       └── AgentFunctionDefinitionEditor.cs  # 函数定义编辑器扩展
└── Plugins/
    └── WebGLTemplates/
        └── Museum/  # 自定义WebGL模板（可选）
```

## 二、核心组件设计

### 1. AgentBridge (通信桥接组件)

#### 职责
- 作为Unity与JS智能体前端之间的通信桥梁
- 处理双向通信，包括接收函数调用和发送上下文更新
- 单例模式，全局唯一实例

#### 核心功能
- 注册Unity实例到JS环境
- 接收JS传来的函数调用消息
- 向JS发送上下文更新消息
- 向JS回传函数执行结果

#### 实现要点
- 使用`Application.ExternalCall`与JS通信
- 提供JS可调用的公共方法
- 错误处理和异常捕获
- 自动查找相关组件

#### 关键方法
- `RegisterToJS()`: 向JS注册Unity实例
- `OnFunctionCall(string)`: 接收函数调用
- `UpdateContext(string)`: 更新上下文
- `NotifyFunctionExecuteResult(string)`: 回传执行结果

### 2. AgentContext (智能体上下文组件)

#### 职责
- 管理当前场景的上下文信息
- 支持多场景切换时的上下文切换
- 与AgentBridge联动，自动更新上下文

#### 核心功能
- 存储场景描述信息
- 管理角色信息
- 控制功能开关（如函数调用）
- 构建并发送上下文数据

#### 实现要点
- 可挂载到任意GameObject上
- 支持多实例（每个场景一个）
- 场景激活时自动发送上下文
- 提供上下文切换事件

#### 关键方法
- `BuildContextJson()`: 构建上下文JSON（公共方法）

### 3. ClientConfigDeclaration (客户端配置声明组件)

#### 职责
- 声明和管理客户端配置
- 集成函数执行器功能
- 处理函数调用的执行

#### 核心功能
- 配置通信参数
- 配置音频功能
- 配置VAD参数
- 执行函数调用
- 回传执行结果

#### 实现要点
- 与AgentFunctionDefinitionComponent联动
- 使用SimpleJSON解析JSON数据
- 反射执行C#函数
- 错误处理和日志记录

#### 关键方法
- `GetConfigJson()`: 获取配置JSON
- `NotifyConfigChange()`: 通知配置变更
- `ExecuteFunctionCall(string)`: 执行函数调用

### 4. AgentFunctionDefinitionComponent (函数定义组件)

#### 职责
- 可视化定义可被智能体调用的函数
- 生成OpenAI兼容的Function Calling格式
- 管理函数定义列表

#### 核心功能
- Inspector中可视化配置函数
- 支持全局函数和组件专属函数
- 函数绑定验证
- 生成标准OpenAI格式
- 缓存MethodInfo提升性能

#### 实现要点
- 序列化配置，支持Inspector编辑
- 支持拖拽绑定目标物体和方法
- 参数类型检查和验证
- 提供函数查找和执行接口

#### 关键方法
- `GetAllOpenAIFunctionsJsonStr()`: 获取OpenAI格式函数列表
- `FindFunction(string)`: 根据名称查找函数
- `InitializeAllFunctions()`: 初始化所有函数

## 三、数据结构设计

### 1. FunctionDefinition (函数定义)

```csharp
[System.Serializable]
public class FunctionDefinition
{
    public string functionName;
    public string functionDescription;
    public GameObject targetObject;
    public string targetMethodName;
    public List<FunctionParameter> parameters;
    [NonSerialized] public MethodInfo cachedMethod;
}
```

### 2. FunctionParameter (参数定义)

```csharp
[System.Serializable]
public class FunctionParameter
{
    public string name;
    public ParameterType type;
    public string description;
    public bool required;
    public float min;
    public float max;
    public string enumOptions;
}
```

### 3. ParameterType (参数类型枚举)

```csharp
public enum ParameterType
{
    String,
    Number,
    Integer,
    Boolean,
    Array,
    Object
}
```

## 四、通信协议设计

### 1. 函数调用格式 (JS → Unity)

```json
{
  "name": "function_name",
  "parameters": {
    "param1": "value1",
    "param2": 123
  }
}
```

### 2. 上下文更新格式 (Unity → JS)

```json
{
  "sceneDescription": "当前场景描述",
  "roleDescription": "智能体角色描述",
  "responseRequirements": "响应要求",
  "functionCalling": true,
  "functions": [
    {
      "name": "function1",
      "description": "函数描述",
      "parameters": {
        "type": "object",
        "properties": {
          "param1": {
            "type": "string",
            "description": "参数描述"
          }
        },
        "required": ["param1"]
      }
    }
  ]
}
```

### 3. 执行结果格式 (Unity → JS)

```json
{
  "functionName": "function_name",
  "isSuccess": true,
  "result": "执行结果",
  "timestamp": "1234567890"
}
```

### 4. 配置更新格式 (Unity → JS)

```json
{
  "serverUrl": "ws://localhost:8080/ws",
  "reconnectAttempts": 3,
  "reconnectInterval": 5,
  "requireTTS": true,
  "enableSTT": true,
  "ttsModel": "cosyvoice-v3-flash",
  "sttModel": "paraformer-realtime-v2",
  "enableSRS": false,
  "functionCalling": true,
  "vadParams": {
    "silenceThreshold": 0.01,
    "silenceDurationMs": 500,
    "activationThreshold": 0.05
  }
}
```

## 五、编辑器扩展设计

### AgentFunctionDefinitionEditor.cs

#### 功能
- 增强Inspector界面，提供更友好的函数配置体验
- 实现目标物体方法的下拉选择
- 提供参数配置的可视化界面
- 实时验证函数绑定的有效性

#### 核心功能
- 方法自动查找和下拉选择
- 参数类型验证
- 一键生成OpenAI格式预览
- 错误提示和警告

## 六、集成流程

### 1. 场景设置

1. **创建AgentBridge实例**
   - 在场景中创建空物体，命名为"AgentBridge"
   - 挂载`AgentBridge.cs`脚本
   - 确保场景加载时此物体不被销毁

2. **创建AgentContext实例**
   - 在每个需要智能体交互的场景中创建空物体，命名为"AgentContext"
   - 挂载`AgentContext.cs`脚本
   - 配置场景描述和角色信息

3. **创建ClientConfigDeclaration实例**
   - 在场景中创建空物体，命名为"ClientConfig"
   - 挂载`ClientConfigDeclaration.cs`脚本
   - 配置通信参数和功能开关

4. **创建函数定义**
   - 在ClientConfig物体上挂载`AgentFunctionDefinitionComponent.cs`脚本
   - 在Inspector中配置函数定义

### 2. 函数配置流程

1. **添加函数**
   - 在`AgentFunctionDefinitionComponent`的`functions`列表中点击"+"
   - 填写函数名称和描述

2. **绑定目标物体和方法**
   - 拖拽目标GameObject到`targetObject`字段
   - 在`targetMethodName`字段中输入方法名
   - 或使用编辑器扩展的下拉选择功能

3. **配置参数**
   - 在`parameters`列表中添加参数
   - 填写参数名称、类型、描述和必填性
   - 配置参数的范围和枚举选项（可选）

4. **验证配置**
   - 点击编辑器扩展中的"验证"按钮
   - 检查控制台输出的警告和错误

### 3. 运行时流程

1. **初始化**
   - 场景加载时，AgentBridge自动初始化
   - ClientConfigDeclaration初始化函数定义
   - AgentContext激活并发送上下文

2. **函数调用处理**
   - JS发送函数调用到Unity
   - AgentBridge接收并转发给ClientConfigDeclaration
   - ClientConfigDeclaration解析并执行函数
   - 执行结果回传给JS

3. **上下文更新**
   - 场景切换时，新场景的AgentContext激活
   - 自动发送新的上下文信息到JS
   - JS更新智能体的上下文配置

## 七、依赖项

### 1. 核心依赖
- **SimpleJSON.cs**: 轻量级JSON解析库，用于处理JSON数据

### 2. 可选依赖
- **Unity WebGL Templates**: 自定义WebGL模板，优化集成体验
- **DOTween**: 可选，用于平滑过渡效果

## 八、性能优化

### 1. 启动性能
- 延迟初始化非关键组件
- 异步加载资源
- 缓存常用数据

### 2. 运行时性能
- 缓存MethodInfo，避免重复反射
- 批处理函数调用
- 减少GC分配
- 使用对象池

### 3. 内存优化
- 避免字符串拼接
- 复用JSON对象
- 及时释放不再使用的资源

## 九、错误处理和日志

### 1. 错误处理
- 全局异常捕获
- 详细的错误信息
- 错误码定义
- 降级处理机制

### 2. 日志系统
- 分级日志（Debug/Info/Warning/Error）
- 开发模式详细日志
- 生产模式简洁日志
- 关键操作日志记录

## 十、测试计划

### 1. 单元测试
- 测试函数定义组件的初始化
- 测试函数执行器的参数解析
- 测试通信桥接的消息传递

### 2. 集成测试
- 测试完整的函数调用流程
- 测试上下文更新机制
- 测试多场景切换

### 3. 性能测试
- 测试函数调用的响应时间
- 测试内存使用情况
- 测试并发函数调用

## 十一、部署和集成

### 1. WebGL构建
- 使用自定义WebGL模板（可选）
- 配置构建参数
- 优化构建大小

### 2. 与智能体前端集成
- 复制构建输出到智能体前端项目
- 配置前端加载Unity实例
- 测试端到端通信

### 3. 部署到服务器
- 构建优化后的WebGL项目
- 部署到Web服务器
- 配置CORS和安全设置

## 十二、开发时间表

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 准备阶段 | 创建项目结构和依赖项 | 1天 |
| 核心组件开发 | 实现AgentBridge和通信协议 | 2天 |
| 上下文管理 | 实现AgentContext和ClientConfigDeclaration | 2天 |
| 函数定义系统 | 实现AgentFunctionDefinitionComponent | 3天 |
| 编辑器扩展 | 实现Inspector增强功能 | 2天 |
| 集成测试 | 测试完整流程和性能 | 2天 |
| 文档和示例 | 编写文档和示例场景 | 1天 |
| 总计 | | 13天 |

## 十三、技术风险和应对策略

### 1. 技术风险
- WebGL平台的限制
- JSON解析性能
- 反射调用的性能开销
- 跨域通信问题

### 2. 应对策略
- 使用轻量级JSON库
- 缓存反射结果
- 优化通信协议
- 配置适当的CORS设置

## 十四、扩展和未来规划

### 1. 功能扩展
- 支持更多参数类型
- 实现函数调用的异步执行
- 添加函数调用的权限控制
- 支持函数调用的队列管理

### 2. 工具链增强
- 自动化函数定义生成
- 函数调用监控和分析
- 智能体交互的可视化工具

### 3. 跨平台支持
- 扩展到其他平台（如移动端）
- 支持不同的通信协议
- 适配不同的智能体后端

## 十五、结论

本开发计划提供了完整的Unity智能体集成组件设计和实现方案，支持：

1. **可视化函数定义**：通过Inspector界面轻松配置函数
2. **标准OpenAI格式**：自动生成符合规范的Function Calling格式
3. **高效函数执行**：通过反射和缓存提升性能
4. **无缝通信集成**：与JS智能体前端完美对接
5. **多场景支持**：每个场景可独立配置上下文和函数

这套方案完全适配WebGL平台，可直接集成到现有的智能体前端项目中，为用户提供丰富的智能体交互体验。