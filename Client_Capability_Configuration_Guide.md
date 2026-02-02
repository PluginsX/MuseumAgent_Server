# 博物馆智能体客户端指令集配置详解

## 🎯 您的核心问题解答

### ❓ "不同客户端的指令集和提示词模板是怎么配置的？在哪里配置？"

### ✅ 答案：统一在 `config/config.json` 中配置

## 📁 配置文件结构解析

### 1. 核心配置文件位置
```
项目根目录/
├── config/
│   └── config.json          ← 指令集和提示词配置中心
├── src/
│   ├── core/
│   │   └── command_generator.py  ← 指令生成逻辑
│   └── models/
│       ├── request_models.py     ← 请求数据模型
│       └── response_models.py    ← 响应数据模型
```

### 2. 指令集配置详解

**文件：`config/config.json`**
```json
{
  "artifact_knowledge_base": {
    "valid_operations": [
      "zoom_pattern",      // ← 这里定义所有支持的指令
      "restore_scene",     // ← 所有客户端共享这个指令集
      "introduce",         
      "spirit_interact",   
      "query_param"        
    ]
  },
  "llm": {
    "prompt_template": "你是博物馆文物智能解析专家...返回字段：operation（文物操作指令，字符串，可选值：zoom_pattern、restore_scene、introduce、spirit_interact、query_param）..."
  }
}
```

## 🔄 客户端能力声明机制

### 客户端通过请求参数声明自己的能力：

```javascript
// Web3D客户端声明
{
  "user_input": "放大查看蟠龙纹样",
  "client_type": "web3d",        // 声明客户端类型
  "scene_type": "study"          // 声明使用场景
}

// 器灵桌面宠物声明  
{
  "user_input": "和蟠龙盖罍打个招呼",
  "client_type": "spirit",       // 声明客户端类型
  "scene_type": "leisure"        // 声明使用场景
}
```

## 🎮 不同客户端的能力映射实现

### 1. Web3D客户端能力配置
```json
// 在文物知识库中配置Web3D专用参数
{
  "artifact_name": "蟠龙盖罍",
  "operation_params": {
    "zoom_pattern": {
      "supported": true,
      "zoom_levels": [1.5, 2.0, 3.0],
      "animation_duration": 2000
    },
    "restore_scene": {
      "supported": true,
      "available_scenes": ["excavation", "museum_display"],
      "lighting_presets": ["daylight", "museum_light"]
    }
  }
}
```

### 2. 器灵桌面宠物能力配置
```json
// 在文物知识库中配置器灵专用参数
{
  "artifact_name": "蟠龙盖罍", 
  "operation_params": {
    "spirit_interact": {
      "supported": true,
      "animations": ["greeting", "explain", "point"],
      "voice_styles": ["scholar", "storyteller"],
      "emotions": ["curious", "proud", "mysterious"]
    }
  }
}
```

## 🧠 智能指令路由机制

### 核心处理逻辑在 `command_generator.py` 中：

```python
def generate_standard_command(self, user_input: str, scene_type: str = "public") -> Dict[str, Any]:
    # 1. LLM解析用户意图，输出操作指令
    llm_result = self.llm_client.parse_user_input(user_input, scene_type)
    # 输出示例: {"operation": "zoom_pattern", "artifact_name": "蟠龙盖罍"}
    
    # 2. 知识库校验操作合法性
    operation = llm_result["operation"]
    if not self.knowledge_base.validate_operation(operation):
        raise ValueError(f"操作指令不合法")
    
    # 3. 获取该文物针对不同客户端的参数配置
    artifact_data = self.knowledge_base.get_standard_artifact_data(artifact_name)
    
    # 4. 返回标准化指令（包含客户端特定参数）
    return {
        "artifact_id": artifact_data["artifact_id"],
        "artifact_name": artifact_data["artifact_name"], 
        "operation": operation,
        "operation_params": artifact_data["operation_params"].get(operation, {}),
        "keywords": llm_result["keywords"]
    }
```

## 🎯 场景化提示词配置

### 不同场景使用不同的提示词模板：

```python
# LLM客户端中的场景处理
def generate_prompt(self, user_input: str, scene_type: str = "public") -> str:
    base_template = self.prompt_template
    
    # 根据场景类型调整提示词重点
    scene_prompts = {
        "study": "请提供学术性、详细的技术分析...",
        "leisure": "请用生动有趣的方式介绍...",
        "public": "请提供简洁明了的介绍..."
    }
    
    scene_instruction = scene_prompts.get(scene_type, "")
    return base_template.format(
        scene_type=scene_type,
        scene_instruction=scene_instruction,
        user_input=user_input
    )
```

## 🔧 新增客户端支持的完整流程

### 步骤1：扩展指令集
```json
// config/config.json
{
  "artifact_knowledge_base": {
    "valid_operations": [
      "zoom_pattern",
      "restore_scene", 
      "introduce",
      "spirit_interact",
      "query_param",
      "new_3d_interaction"    // ← 新增指令
    ]
  }
}
```

### 步骤2：更新提示词模板
```json
{
  "llm": {
    "prompt_template": "...可选值：zoom_pattern、restore_scene、introduce、spirit_interact、query_param、new_3d_interaction..."
  }
}
```

### 步骤3：配置文物参数
```sql
-- 在知识库中为文物添加新指令的参数
UPDATE museum_artifact_info 
SET operation_params = '{"new_3d_interaction": {"effect": "glow", "duration": 3000}}'
WHERE artifact_name = '蟠龙盖罍';
```

### 步骤4：客户端实现对应功能
```javascript
// 新客户端处理新增指令
function handleNew3DInteraction(command) {
  if (command.operation === 'new_3d_interaction') {
    // 实现新的3D交互效果
    applyGlowEffect(command.operation_params.effect);
  }
}
```

## 📊 客户端能力矩阵

| 客户端类型 | 支持的基础指令 | 专有能力 | 场景适配 |
|------------|----------------|----------|----------|
| **Web3D展示** | zoom_pattern, restore_scene, introduce, query_param | 3D渲染、场景切换、纹理高亮 | study/public |
| **器灵宠物** | spirit_interact, introduce, query_param | 角色动画、语音合成、情感表达 | leisure/public |
| **移动应用** | introduce, query_param | 离线缓存、个性化推荐 | all scenes |
| **API调用者** | all operations | 数据获取、批量处理 | developer |

## 🔍 实际调用示例

### Web3D客户端调用：
```javascript
// 请求
{
  "user_input": "我想仔细看看蟠龙盖罍的纹样",
  "client_type": "web3d",
  "scene_type": "study"
}

// 服务端响应
{
  "code": 200,
  "data": {
    "artifact_name": "蟠龙盖罍",
    "operation": "zoom_pattern", 
    "operation_params": {
      "zoom_area": "dragon_pattern",
      "highlight_color": "#FF0000",
      "animation_duration": 2000
    }
  }
}
```

### 器灵客户端调用：
```javascript
// 请求
{
  "user_input": "蟠龙盖罍，介绍一下你自己",
  "client_type": "spirit", 
  "scene_type": "leisure"
}

// 服务端响应  
{
  "code": 200,
  "data": {
    "artifact_name": "蟠龙盖罍",
    "operation": "spirit_interact",
    "operation_params": {
      "animation": "self_introduction",
      "voice_style": "storyteller",
      "emotion": "proud"
    }
  }
}
```

## 🎉 核心优势总结

1. **统一配置管理**：所有指令集都在一个JSON文件中管理
2. **动态扩展能力**：新增功能只需修改配置，无需代码改动
3. **场景智能适配**：同一指令在不同场景下有不同的表现
4. **客户端解耦**：客户端只需声明能力，具体实现由服务端协调
5. **标准化交互**：所有客户端使用相同的API接口和数据格式

这就是为什么说这是一个**真正的MCP服务架构** - 通过标准化的协议和动态的配置，实现了不同能力客户端的统一服务！