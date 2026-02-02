# 博物馆智能体系统架构思维导图

```mermaid
graph TD
    A[博物馆智能体服务器] --> B[API网关层]
    A --> C[核心引擎层]
    A --> D[数据存储层]
    
    B --> B1[身份认证]
    B --> B2[请求路由]
    B --> B3[参数校验]
    B --> B4[日志记录]
    
    C --> C1[LLM智能解析引擎]
    C --> C2[知识库校验引擎]
    C --> C3[指令标准化引擎]
    C --> C4[向量化服务引擎]
    
    D --> D1[文物知识库<br/>SQLite/MySQL]
    D --> D2[向量数据库<br/>ChromaDB]
    D --> D3[应用数据库<br/>用户管理]
    
    C1 --> C1A[提示词模板管理]
    C1 --> C1B[场景适配处理]
    C1 --> C1C[语义理解解析]
    
    C2 --> C2A[文物数据查询]
    C2 --> C2B[操作合法性校验]
    C2 --> C2C[参数标准化]
    
    subgraph "客户端能力声明"
        E1[Web3D展示客户端] --> E1A[client_type: web3d]
        E1 --> E1B[scene_type: study/public]
        E1 --> E1C[支持: zoom_pattern, restore_scene]
        
        E2[器灵桌面宠物] --> E2A[client_type: spirit]
        E2 --> E2B[scene_type: leisure/public] 
        E2 --> E2C[支持: spirit_interact, introduce]
        
        E3[第三方应用] --> E3A[client_type: third]
        E3 --> E3B[scene_type: 根据需求]
        E3 --> E3C[支持: all operations]
    end
    
    subgraph "统一指令集配置"
        F1[config.json配置文件] --> F1A[valid_operations列表]
        F1 --> F1B[LLM提示词模板]
        F1 --> F1C[场景类型定义]
        
        F1A --> F1A1[zoom_pattern]
        F1A --> F1A2[restore_scene] 
        F1A --> F1A3[introduce]
        F1A --> F1A4[spirit_interact]
        F1A --> F1A5[query_param]
    end
    
    subgraph "智能处理流程"
        G1[用户自然语言输入] --> G2[LLM语义解析]
        G2 --> G3[提取文物名称和操作指令]
        G3 --> G4[知识库校验合法性]
        G4 --> G5[获取文物详细参数]
        G5 --> G6[生成标准化指令]
        G6 --> G7[返回客户端执行]
    end
    
    style A fill:#e1f5fe
    style C fill:#f3e5f5  
    style F1 fill:#e8f5e8
    style G1 fill:#fff3e0
```

## 🎯 核心工作机制总结

### 1. **MCP-like服务架构**
- 不同客户端 = 不同的"工具能力"
- 服务器 = 统一的"工具调度中心"
- 通过标准化协议实现能力发现和调用

### 2. **三层解耦设计**
```
客户端层(能力声明) 
    ↓
服务管理层(协议转换)
    ↓  
核心引擎层(智能处理)
```

### 3. **动态配置机制**
- 指令集：config.json统一管理
- 客户端能力：请求参数声明
- 场景适配：模板动态调整
- 参数配置：知识库按需加载

### 4. **标准化交互协议**
```json
// 请求格式统一
{
  "user_input": "用户说的话",
  "client_type": "客户端类型",
  "scene_type": "使用场景"
}

// 响应格式统一  
{
  "code": 200,
  "data": {
    "artifact_name": "文物名",
    "operation": "操作指令",
    "operation_params": { /* 客户端特定参数 */ }
  }
}
```

这种设计让您对MCP概念的理解完全正确 - 这就是一个面向文化教育领域的智能服务协调平台！