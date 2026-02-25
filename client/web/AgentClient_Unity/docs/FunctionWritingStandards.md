# 函数编写标准与实现策略

## 目标

通过自定义特性实现 OpenAI 标准函数定义所需的所有信息，并在 Inspector 中自动填充函数定义字段。

## 一、自定义特性设计

### 1. 函数级特性：`AIFunctionAttribute`

```csharp
using System;

[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public class AIFunctionAttribute : Attribute
{
    public string Name { get; set; }
    public string Description { get; set; }
    public string Category { get; set; }
    public string[] Tags { get; set; }
    public string Example { get; set; }

    public AIFunctionAttribute(string description)
    {
        Description = description;
    }
}
```

**用途**：标记函数并提供函数级别的元数据

**属性说明**：
- `Name`: 函数名称（可选，默认使用方法名）
- `Description`: 函数描述（必需）
- `Category`: 函数分类（可选）
- `Tags`: 函数标签数组（可选）
- `Example`: 使用示例（可选）

### 2. 参数级特性：`AIParameterAttribute`

```csharp
[AttributeUsage(AttributeTargets.Parameter, AllowMultiple = false)]
public class AIParameterAttribute : Attribute
{
    public string Description { get; set; }
    public float? Minimum { get; set; }
    public float? Maximum { get; set; }
    public string[] EnumOptions { get; set; }
    public string Unit { get; set; }
    public string Example { get; set; }

    public AIParameterAttribute(string description)
    {
        Description = description;
    }
}
```

**用途**：标记参数并提供参数级别的元数据

**属性说明**：
- `Description`: 参数描述（必需）
- `Minimum`: 最小值（可选，仅数值类型）
- `Maximum`: 最大值（可选，仅数值类型）
- `EnumOptions`: 枚举选项数组（可选）
- `Unit`: 单位（可选，如"度"、"米"、"秒"）
- `Example`: 使用示例（可选）

## 二、特性使用示例

### 示例 1：基本函数

```csharp
[AIFunction("设置光强度")]
public void Set_Intensity(
    [AIParameter("光强度值", Minimum = 0, Maximum = 10)] float intensity
)
{
    // 实现
}
```

### 示例 2：复杂函数

```csharp
[AIFunction(
    "累加旋转，自动处理角度边界确保始终在360度范围内",
    Category = "变换操作",
    Tags = new[] { "rotation", "transform" },
    Example = "Add_Rotation(90, 0, 0, 1000)"
)]
public void Add_Rotation(
    [AIParameter("Y轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float yaw,
    [AIParameter("X轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float pitch,
    [AIParameter("Z轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float roll,
    [AIParameter("动画时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒", Example = "1000")] float duration = 0
)
{
    // 实现
}
```

### 示例 3：Vector3 参数

```csharp
[AIFunction("设置物体位置")]
public void Set_Position(
    [AIParameter("目标位置坐标")] Vector3 position,
    [AIParameter("动画时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 0
)
{
    // 实现
}
```

### 示例 4：带枚举选项的参数

```csharp
[AIFunction("设置渲染模式")]
public void Set_RenderMode(
    [AIParameter("渲染模式", EnumOptions = new[] { "Solid", "Wireframe", "Points" })] string mode
)
{
    // 实现
}
```

## 三、Inspector 自动填充策略

### 3.1 触发时机

当用户在 Inspector 中：
1. 选择或更改 `targetObject`
2. 选择或更改 `targetMethodName`
3. 函数定义初始化时（`Initialize()` 方法）

### 3.2 自动填充逻辑

```csharp
public bool Initialize()
{
    if (targetObject == null || string.IsNullOrEmpty(targetMethodName))
    {
        return false;
    }

    Component[] components = targetObject.GetComponents<Component>();
    foreach (var component in components)
    {
        if (component == null) continue;

        MethodInfo[] methods = component.GetType().GetMethods(
            BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static
        );

        foreach (var method in methods)
        {
            if (method.Name == targetMethodName)
            {
                if (method.GetParameters().Length == parameters.Count)
                {
                    cachedMethod = method;
                    
                    // 自动从特性提取信息
                    ExtractMetadataFromAttributes(method);
                    
                    return true;
                }
            }
        }
    }

    return false;
}

private void ExtractMetadataFromAttributes(MethodInfo method)
{
    // 1. 提取函数级信息
    var funcAttr = method.GetCustomAttribute<AIFunctionAttribute>();
    if (funcAttr != null)
    {
        if (!string.IsNullOrEmpty(funcAttr.Name))
        {
            functionName = funcAttr.Name;
        }
        if (!string.IsNullOrEmpty(funcAttr.Description))
        {
            functionDescription = funcAttr.Description;
        }
    }
    
    // 2. 提取参数级信息
    ParameterInfo[] methodParams = method.GetParameters();
    for (int i = 0; i < methodParams.Length && i < parameters.Count; i++)
    {
        var paramInfo = methodParams[i];
        var functionParam = parameters[i];
        
        var paramAttr = paramInfo.GetCustomAttribute<AIParameterAttribute>();
        if (paramAttr != null)
        {
            if (!string.IsNullOrEmpty(paramAttr.Description))
            {
                functionParam.description = paramAttr.Description;
            }
            if (paramAttr.Minimum.HasValue)
            {
                functionParam.min = paramAttr.Minimum.Value;
            }
            if (paramAttr.Maximum.HasValue)
            {
                functionParam.max = paramAttr.Maximum.Value;
            }
            if (paramAttr.EnumOptions != null && paramAttr.EnumOptions.Length > 0)
            {
                functionParam.enumOptions = string.Join(",", paramAttr.EnumOptions);
            }
        }
    }
}
```

### 3.3 填充优先级

1. **特性信息**（最高优先级）
   - 从 `[AIFunction]` 和 `[AIParameter]` 特性获取
   
2. **手动配置**（中等优先级）
   - 用户在 Inspector 中手动填写的值
   
3. **默认值**（最低优先级）
   - 字段的默认值（如 `""`、`0`、`false`）

### 3.4 填充规则

- **只填充空值**：如果字段已经有值，不覆盖
- **保留手动修改**：用户手动修改的值优先级高于特性值
- **智能推断**：对于 Vector3 参数，自动添加 x、y、z 子属性描述

## 四、实现步骤

### 步骤 1：创建自定义特性类

在 `AgentFunctionDefinition.cs` 文件顶部添加：

```csharp
using System;

// AI 函数特性
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public class AIFunctionAttribute : Attribute
{
    public string Name { get; set; }
    public string Description { get; set; }
    public string Category { get; set; }
    public string[] Tags { get; set; }
    public string Example { get; set; }

    public AIFunctionAttribute(string description)
    {
        Description = description;
    }
}

// AI 参数特性
[AttributeUsage(AttributeTargets.Parameter, AllowMultiple = false)]
public class AIParameterAttribute : Attribute
{
    public string Description { get; set; }
    public float? Minimum { get; set; }
    public float? Maximum { get; set; }
    public string[] EnumOptions { get; set; }
    public string Unit { get; set; }
    public string Example { get; set; }

    public AIParameterAttribute(string description)
    {
        Description = description;
    }
}
```

### 步骤 2：修改 Initialize() 方法

在 `FunctionDefinition` 类的 `Initialize()` 方法中添加特性提取调用：

```csharp
public bool Initialize()
{
    Log.Print("AgentFunctionDefinition", "debug", $"开始初始化函数定义: {functionName}");
    
    if (targetObject == null || string.IsNullOrEmpty(targetMethodName))
    {
        Log.Print("AgentFunctionDefinition", "error", $"函数[{functionName}]未正确绑定目标物体或方法名！");
        return false;
    }

    Component[] components = targetObject.GetComponents<Component>();
    foreach (var component in components)
    {
        if (component == null) continue;

        MethodInfo[] methods = component.GetType().GetMethods(
            BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static
        );

        foreach (var method in methods)
        {
            if (method.Name == targetMethodName)
            {
                if (method.GetParameters().Length == parameters.Count)
                {
                    cachedMethod = method;
                    
                    // 从特性自动提取信息
                    ExtractMetadataFromAttributes(method);
                    
                    Log.Print("AgentFunctionDefinition", "debug", $"函数[{functionName}]初始化成功，绑定方法: {method.Name}");
                    return true;
                }
            }
        }
    }

    Log.Print("AgentFunctionDefinition", "error", $"函数[{functionName}]初始化失败，在物体[{targetObject.name}]上找不到方法[{targetMethodName}]");
    return false;
}
```

### 步骤 3：添加 ExtractMetadataFromAttributes() 方法

在 `FunctionDefinition` 类中添加特性提取方法：

```csharp
private void ExtractMetadataFromAttributes(MethodInfo method)
{
    try
    {
        // 提取函数级信息
        var funcAttr = method.GetCustomAttribute<AIFunctionAttribute>();
        if (funcAttr != null)
        {
            if (!string.IsNullOrEmpty(funcAttr.Name) && string.IsNullOrEmpty(functionName))
            {
                functionName = funcAttr.Name;
                Log.Print("AgentFunctionDefinition", "debug", $"从特性获取函数名: {functionName}");
            }
            if (!string.IsNullOrEmpty(funcAttr.Description) && string.IsNullOrEmpty(functionDescription))
            {
                functionDescription = funcAttr.Description;
                Log.Print("AgentFunctionDefinition", "debug", $"从特性获取函数描述: {functionDescription}");
            }
        }
        
        // 提取参数级信息
        ParameterInfo[] methodParams = method.GetParameters();
        for (int i = 0; i < methodParams.Length && i < parameters.Count; i++)
        {
            var paramInfo = methodParams[i];
            var functionParam = parameters[i];
            
            var paramAttr = paramInfo.GetCustomAttribute<AIParameterAttribute>();
            if (paramAttr != null)
            {
                bool hasUpdate = false;
                
                if (!string.IsNullOrEmpty(paramAttr.Description) && string.IsNullOrEmpty(functionParam.description))
                {
                    functionParam.description = paramAttr.Description;
                    Log.Print("AgentFunctionDefinition", "debug", $"从特性获取参数[{functionParam.name}]描述: {functionParam.description}");
                    hasUpdate = true;
                }
                
                if (paramAttr.Minimum.HasValue && functionParam.min == float.MinValue)
                {
                    functionParam.min = paramAttr.Minimum.Value;
                    Log.Print("AgentFunctionDefinition", "debug", $"从特性获取参数[{functionParam.name}]最小值: {functionParam.min}");
                    hasUpdate = true;
                }
                
                if (paramAttr.Maximum.HasValue && functionParam.max == float.MaxValue)
                {
                    functionParam.max = paramAttr.Maximum.Value;
                    Log.Print("AgentFunctionDefinition", "debug", $"从特性获取参数[{functionParam.name}]最大值: {functionParam.max}");
                    hasUpdate = true;
                }
                
                if (paramAttr.EnumOptions != null && paramAttr.EnumOptions.Length > 0 && string.IsNullOrEmpty(functionParam.enumOptions))
                {
                    functionParam.enumOptions = string.Join(",", paramAttr.EnumOptions);
                    Log.Print("AgentFunctionDefinition", "debug", $"从特性获取参数[{functionParam.name}]枚举选项: {functionParam.enumOptions}");
                    hasUpdate = true;
                }
                
                if (hasUpdate)
                {
                    Log.Print("AgentFunctionDefinition", "debug", $"参数[{functionParam.name}]从特性自动填充完成");
                }
            }
        }
    }
    catch (Exception e)
    {
        Log.Print("AgentFunctionDefinition", "error", $"从特性提取元数据失败: {e.Message}");
    }
}
```

### 步骤 4：测试特性功能

在 `Test_Transform.cs` 中添加特性：

```csharp
using UnityEngine;
using Museum.Debug;
using System.Collections;

public class Test_Transform : MonoBehaviour
{
    [AIFunction("累加旋转，自动处理角度边界确保始终在360度范围内")]
    public void Add_Rotation(
        [AIParameter("Y轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float yaw,
        [AIParameter("X轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float pitch,
        [AIParameter("Z轴旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float roll,
        [AIParameter("动画时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 0
    )
    {
        // 实现...
    }
    
    [AIFunction("沿着某个轴向旋转指定角度")]
    public void Add_Rotation(
        [AIParameter("旋转轴向（Vector3）")] Vector3 axis,
        [AIParameter("旋转角度（度）", Minimum = -360, Maximum = 360, Unit = "度")] float angle,
        [AIParameter("动画时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 0
    )
    {
        // 实现...
    }
    
    [AIFunction("累加位置偏移")]
    public void Add_Position(
        [AIParameter("位置偏移量（Vector3）")] Vector3 position,
        [AIParameter("动画时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 0
    )
    {
        // 实现...
    }
    
    [AIFunction("设置物体旋转角度")]
    public void Set_Rotation(
        [AIParameter("目标旋转角度（Vector3，欧拉角）")] Vector3 rotation,
        [AIParameter("动画时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 0
    )
    {
        // 实现...
    }
    
    [AIFunction("设置物体位置")]
    public void Set_Position(
        [AIParameter("目标位置坐标（Vector3）")] Vector3 position,
        [AIParameter("动画时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 0
    )
    {
        // 实现...
    }
    
    [AIFunction("设置物体缩放")]
    public void Set_Scale(
        [AIParameter("目标缩放比例（Vector3）")] Vector3 scale,
        [AIParameter("动画时长（毫秒），0表示直接设置", Minimum = 0, Unit = "毫秒")] float duration = 0
    )
    {
        // 实现...
    }
    
    // 协程方法保持不变...
}
```

## 五、使用流程

### 5.1 开发者使用流程

1. **编写函数**：在脚本中编写公共方法
2. **添加特性**：为函数和参数添加 `[AIFunction]` 和 `[AIParameter]` 特性
3. **配置函数定义**：在 Inspector 中选择目标物体和方法
4. **自动填充**：系统自动从特性提取信息填充函数定义
5. **手动调整**：如需要，可以手动调整自动填充的值

### 5.2 优势

1. **减少重复工作**：不需要在 Inspector 中重复输入描述
2. **保持一致性**：函数定义与代码实现保持一致
3. **易于维护**：修改特性即可更新函数定义
4. **类型安全**：编译时检查特性使用是否正确
5. **灵活可控**：可以随时手动覆盖自动填充的值

## 六、注意事项

1. **特性优先级**：自动填充只在字段为空或为默认值时进行
2. **手动覆盖**：用户手动修改的值不会被自动填充覆盖
3. **Vector3 处理**：Vector3 参数的 x、y、z 子属性描述仍使用固定模板
4. **日志记录**：所有自动填充操作都会记录日志，便于调试
5. **错误处理**：特性提取失败不会影响函数定义的正常使用
6. **函数重载**：不支持同名的函数重载，不同的函数版本应使用不同的函数名（例如：`Add_Rotation` 和 `Add_Rotation_ByAxis`）

## 七、扩展性

### 7.1 未来可扩展的特性

```csharp
[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
public class AIFunctionExampleAttribute : Attribute
{
    public string Input { get; set; }
    public string Output { get; set; }

    public AIFunctionExampleAttribute(string input, string output)
    {
        Input = input;
        Output = output;
    }
}

// 使用
[AIFunction("设置光强度")]
[AIFunctionExample("Set_Intensity(5.0)", "执行成功")]
public void Set_Intensity([AIParameter("光强度值", Minimum = 0, Maximum = 10)] float intensity)
{
    // 实现
}
```

### 7.2 多语言支持

```csharp
public class AIParameterAttribute : Attribute
{
    public string Description { get; set; }
    public Dictionary<string, string> LocalizedDescriptions { get; set; }

    public AIParameterAttribute(string description)
    {
        Description = description;
        LocalizedDescriptions = new Dictionary<string, string>
        {
            { "zh-CN", description },
            { "en-US", "" }
        };
    }
}
```

## 八、总结

通过自定义特性实现自动填充，可以：

1. ✅ 完整支持 OpenAI 函数定义标准
2. ✅ 自动提取函数和参数的所有元数据
3. ✅ 减少手动配置工作量
4. ✅ 保持代码与配置的一致性
5. ✅ 提供灵活的手动覆盖机制
6. ✅ 支持未来功能扩展

这个策略提供了完整的实现方案，可以根据实际需求逐步实施。
