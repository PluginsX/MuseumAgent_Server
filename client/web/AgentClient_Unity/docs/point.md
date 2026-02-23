结合你 Unity 2022 WebGL 的开发环境、Inspector 可视化编辑需求，以及 OpenAI Function Calling 标准，我为你设计一套**可直接落地、可视化配置、自动映射执行**的函数定义与执行组件方案。核心解决：**如何在 Inspector 拖拽绑定 C# 函数**、**如何自动生成 OpenAI 格式**、**如何解析 JSON 执行实际函数**。

这套方案基于 Unity 反射 + 序列化 + 委托，完全适配你现有的架构，且支持**全局公共函数**和**组件专属函数**两类场景。

---

## 一、核心设计原则
1. **可视化配置**：无需写代码，在 Inspector 中通过「拖拽目标物体 + 选择函数」完成声明。
2. **自动标准化**：函数定义组件自动将配置的 C# 函数转换为 OpenAI Function Calling JSON 格式。
3. **动态执行**：通过反射 + 委托，将 JSON 中的函数调用映射到实际 C# 函数并传参执行。
4. **双场景支持**：区分「全局单例函数」（如全局场景管理）和「组件专属函数」（如某个文物的交互函数）。

---

## 二、第一步：定义基础数据结构（序列化 + OpenAI 兼容）
首先创建 3 个核心序列化类，用于**Inspector 配置**、**JSON 序列化**、**OpenAI 格式映射**，同时兼容你需要的两类函数。

### 1. 函数参数定义（适配 OpenAI Schema）
支持常用值类型（string/int/float/bool），对应 OpenAI 的 `properties` 字段，可在 Inspector 中配置每个参数的描述和必填性。
```csharp
using UnityEngine;
using System;

// 单个参数的定义（序列化，可在Inspector编辑）
[Serializable]
public class AgentFunctionParam
{
    [Header("参数基础配置")]
    public string paramName; // 对应C#函数的参数名（必须一致！）
    public string description; // OpenAI描述
    public bool isRequired = true; // OpenAI是否必填

    [Header("参数类型（与C#函数一致）")]
    public ParamType paramType; // 参数类型枚举

    // 转换为OpenAI的Property格式
    public JSONObject ToOpenAIProperty()
    {
        var prop = new JSONObject();
        prop.AddField("type", GetOpenAIType(paramType));
        prop.AddField("description", description);
        return prop;
    }

    // C#类型转OpenAI类型
    private string GetOpenAIType(ParamType type)
    {
        return type switch
        {
            ParamType.String => "string",
            ParamType.Int => "integer",
            ParamType.Float => "number",
            ParamType.Bool => "boolean",
            _ => "string"
        };
    }
}

// 参数类型枚举（覆盖Unity常用函数参数）
public enum ParamType
{
    String,
    Int,
    Float,
    Bool
}
```

### 2. 核心：函数定义类（支持全局/组件函数，序列化配置）
这是「函数定义组件」的核心数据单元，支持**拖拽目标物体**、**选择函数**、**配置参数**，自动关联 C# 实际函数。
```csharp
using UnityEngine;
using System;
using System.Reflection;
using System.Collections.Generic;

// 单个函数的完整定义（序列化，Inspector核心配置）
[Serializable]
public class AgentFunctionDefinition
{
    [Header("=== 基础标识（OpenAI核心） ===")]
    public string functionName; // 自定义函数名（建议与C#函数名一致）
    public string functionDescription; // OpenAI函数描述

    [Header("=== C# 函数绑定（关键） ===")]
    public GameObject targetObject; // 函数所在的物体（全局函数填全局单例物体）
    public string targetMethodName; // 要执行的C#函数名（自动筛选，或手动填写）

    [Header("=== 函数参数配置（与C#参数一一对应） ===")]
    public List<AgentFunctionParam> paramList = new List<AgentFunctionParam>();

    // 缓存：反射得到的C#方法信息（避免重复反射）
    [HideInInspector] public MethodInfo cachedMethod;

    #region 核心方法：初始化（验证并缓存C#方法）
    /// <summary>
    /// 初始化：验证绑定的C#函数是否存在，缓存MethodInfo
    /// 建议在Awake/OnEnable中调用
    /// </summary>
    /// <returns>是否初始化成功</returns>
    public bool Init()
    {
        // 校验必填项
        if (targetObject == null || string.IsNullOrEmpty(targetMethodName))
        {
            Debug.LogError($"函数[{functionName}]未绑定目标物体或方法名！");
            return false;
        }

        // 获取目标物体的所有组件（支持组件专属函数）
        Component[] components = targetObject.GetComponents<Component>();
        foreach (var comp in components)
        {
            if (comp == null) continue;

            // 查找匹配的方法：公共方法、非静态（组件函数）/静态（全局函数）
            MethodInfo method = comp.GetType().GetMethod(
                targetMethodName,
                BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static
            );

            if (method != null)
            {
                cachedMethod = method;
                // 自动校验参数数量是否匹配（可选，增强鲁棒性）
                ValidateParamCount(method.GetParameters().Length);
                return true;
            }
        }

        Debug.LogError($"物体[{targetObject.name}]上未找到公共方法[{targetMethodName}]！");
        return false;
    }
    #endregion

    #region 辅助：校验参数数量
    private void ValidateParamCount(int csharpParamCount)
    {
        if (paramList.Count != csharpParamCount)
        {
            Debug.LogWarning($"函数[{functionName}]的配置参数数量({paramList.Count})与C#方法参数数量({csharpParamCount})不匹配！");
        }
    }
    #endregion

    #region 核心方法：转换为OpenAI Function Calling格式
    /// <summary>
    /// 自动生成符合OpenAI标准的Function JSON
    /// </summary>
    public JSONObject ToOpenAIFunction()
    {
        var funcJson = new JSONObject();
        funcJson.AddField("name", functionName);
        funcJson.AddField("description", functionDescription);

        // 构建parameters
        var parameters = new JSONObject();
        parameters.AddField("type", "object");

        // 构建properties
        var properties = new JSONObject();
        foreach (var param in paramList)
        {
            properties.AddField(param.paramName, param.ToOpenAIProperty());
        }
        parameters.AddField("properties", properties);

        // 构建required
        var required = new JSONObject(JSONObject.Type.ARRAY);
        foreach (var param in paramList)
        {
            if (param.isRequired)
            {
                required.Add(param.paramName);
            }
        }
        parameters.AddField("required", required);

        funcJson.AddField("parameters", parameters);
        return funcJson;
    }
    #endregion

    #region 核心方法：执行C#函数（接收JSON参数）
    /// <summary>
    /// 解析JSON参数，执行绑定的C#函数
    /// </summary>
    /// <param name="paramJson">OpenAI返回的parameters JSON</param>
    /// <returns>执行结果（可返回给智能体）</returns>
    public string ExecuteFunction(JSONObject paramJson)
    {
        if (cachedMethod == null)
        {
            if (!Init()) return $"执行失败：函数[{functionName}]初始化失败！";
        }

        try
        {
            // 1. 解析参数：将JSON转换为C#方法所需的参数数组
            object[] csharpParams = ParseParams(paramJson);

            // 2. 执行方法：区分静态方法（全局）和实例方法（组件）
            object result = cachedMethod.IsStatic 
                ? cachedMethod.Invoke(null, csharpParams) 
                : cachedMethod.Invoke(GetTargetComponent(), csharpParams);

            // 3. 返回执行结果（转为字符串，方便回传给JS/智能体）
            return result == null ? "执行成功" : result.ToString();
        }
        catch (Exception e)
        {
            string errorMsg = $"执行函数[{functionName}]失败：{e.Message}";
            Debug.LogError(errorMsg);
            return errorMsg;
        }
    }
    #endregion

    #region 辅助：解析JSON参数为C#参数数组
    private object[] ParseParams(JSONObject paramJson)
    {
        List<object> paramList = new List<object>();
        foreach (var param in this.paramList)
        {
            // 从JSON中获取参数值（按paramName匹配）
            if (!paramJson.HasField(param.paramName))
            {
                if (param.isRequired)
                {
                    throw new ArgumentNullException(param.paramName, $"必填参数[{param.paramName}]缺失！");
                }
                // 非必填参数：添加默认值
                paramList.Add(GetDefaultValue(param.paramType));
                continue;
            }

            // 转换为对应C#类型
            JSONObject valueJson = paramJson[param.paramName];
            object value = ConvertJsonToValue(valueJson, param.paramType);
            paramList.Add(value);
        }
        return paramList.ToArray();
    }
    #endregion

    #region 辅助：获取目标组件（实例方法用）
    private Component GetTargetComponent()
    {
        return cachedMethod.DeclaringType == null 
            ? null 
            : targetObject.GetComponent(cachedMethod.DeclaringType);
    }
    #endregion

    #region 辅助：JSON值转C#类型
    private object ConvertJsonToValue(JSONObject json, ParamType type)
    {
        return type switch
        {
            ParamType.String => json.str,
            ParamType.Int => (int)json.n,
            ParamType.Float => (float)json.n,
            ParamType.Bool => json.b,
            _ => json.str
        };
    }
    #endregion

    #region 辅助：获取参数默认值
    private object GetDefaultValue(ParamType type)
    {
        return type switch
        {
            ParamType.String => string.Empty,
            ParamType.Int => 0,
            ParamType.Float => 0f,
            ParamType.Bool => false,
            _ => null
        };
    }
    #endregion
}
```

> 依赖说明：上述代码使用了 `JSONObject`（Unity 常用的轻量级 JSON 解析库），你可以直接导入 **SimpleJSON** 或 Unity 内置的 `JsonUtility` 适配（下文会提供兼容方案）。

---

## 三、第二步：函数定义组件（可视化配置 + 自动生成 OpenAI 格式）
这是你架构中的「函数定义组件」，挂载在「智能体上下文组件」上，支持**多函数配置**，并提供「一键生成 OpenAI 函数列表」的接口，供桥接组件发送给 JS。

### 1. 函数定义组件代码
```csharp
using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 函数定义组件：可视化配置C#函数，自动生成OpenAI Function Calling格式
/// 挂载在AgentContext物体上
/// </summary>
public class AgentFunctionDefinitionComponent : MonoBehaviour
{
    [Header("=== 函数列表（支持全局/组件函数） ===")]
    public List<AgentFunctionDefinition> functionList = new List<AgentFunctionDefinition>();

    [Header("=== 调试选项 ===")]
    public bool autoInitOnEnable = true; // 启用时自动初始化

    // 所属的上下文组件
    private AgentContext _parentContext;

    #region 生命周期
    private void Awake()
    {
        _parentContext = GetComponent<AgentContext>();
    }

    private void OnEnable()
    {
        if (autoInitOnEnable)
        {
            InitAllFunctions();
        }
    }
    #endregion

    #region 核心：初始化所有函数
    /// <summary>
    /// 初始化所有配置的函数（验证并缓存C#方法）
    /// </summary>
    public void InitAllFunctions()
    {
        foreach (var func in functionList)
        {
            func.Init();
        }
        Debug.Log($"[{gameObject.name}] 函数定义组件初始化完成，共配置{functionList.Count}个函数");
    }
    #endregion

    #region 核心：获取所有函数的OpenAI格式列表
    /// <summary>
    /// 生成供JS智能体使用的OpenAI Function列表（JSON数组）
    /// </summary>
    public JSONObject GetAllOpenAIFunctions()
    {
        var funcArray = new JSONObject(JSONObject.Type.ARRAY);
        foreach (var func in functionList)
        {
            funcArray.Add(func.ToOpenAIFunction());
        }
        return funcArray;
    }

    /// <summary>
    /// 重载：生成JSON字符串（方便直接传给JS）
    /// </summary>
    public string GetAllOpenAIFunctionsJsonStr()
    {
        return GetAllOpenAIFunctions().ToString();
    }
    #endregion

    #region 辅助：根据函数名查找定义（供执行器调用）
    public AgentFunctionDefinition FindFunctionByName(string functionName)
    {
        return functionList.Find(f => f.functionName == functionName);
    }
    #endregion
}
```

### 2. Inspector 可视化配置步骤（关键！）
无需写代码，通过 3 步完成「全局/组件函数」的声明：

| 步骤 | 操作说明 | 全局函数示例（如场景管理） | 组件函数示例（如文物交互） |
| :--- | :--- | :--- | :--- |
| 1 | 新增函数 | 在 `functionList` 中点击「+」，添加一个 `AgentFunctionDefinition` | 同上 |
| 2 | 绑定C#函数 | 1. **拖拽目标物体**：全局函数拖「GlobalManager」单例；组件函数拖具体文物物体<br>2. **填写`targetMethodName`**：输入C#函数名（如`SwitchScene`/`ShowCulturalRelic`） | 1. 拖拽「MuseumSceneManager」<br>2. 填写`SwitchScene` | 1. 拖拽「BronzeVase」文物物体<br>2. 填写`PlayIntroduction` |
| 3 | 配置参数 | 按C#函数参数，添加`AgentFunctionParam`，填写**参数名（与C#一致）**、描述、类型、必填性 | 添加参数`sceneName`（String，必填，描述："要切换的场景名称"） | 添加参数`playType`（Int，必填，描述："1=语音介绍，2=动画演示"） |
| 4 | 完成 | 启用组件，自动初始化校验 | 初始化成功，可生成OpenAI格式 | 初始化成功，可生成OpenAI格式 |

---

## 四、第三步：函数执行器组件（解析 JSON + 执行实际 C# 函数）
这是你架构中的「函数执行器」，挂载在「智能体上下文组件」上，接收 JS 转发的 JSON 函数调用，**查找函数定义** → **解析参数** → **执行 C# 函数**，并支持将执行结果回传给智能体。

### 1. 函数执行器代码
```csharp
using UnityEngine;
using System;

/// <summary>
/// 函数执行器：解析JS传来的函数调用JSON，执行实际C#函数
/// 挂载在AgentContext物体上，与AgentFunctionDefinitionComponent关联
/// </summary>
public class AgentFunctionExecutor : MonoBehaviour
{
    [Header("=== 依赖组件 ===")]
    public AgentFunctionDefinitionComponent functionDefinitionComp;

    [Header("=== 回调配置 ===")]
    public bool autoNotifyResultToAgent = true; // 自动将执行结果回传给智能体

    // 所属的上下文组件
    private AgentContext _parentContext;
    // 桥接组件（用于回传结果）
    private AgentBridge _agentBridge;

    #region 生命周期
    private void Awake()
    {
        _parentContext = GetComponent<AgentContext>();
        _agentBridge = AgentBridge.Instance;

        // 自动绑定依赖组件（如果未手动指定）
        if (functionDefinitionComp == null)
        {
            functionDefinitionComp = GetComponent<AgentFunctionDefinitionComponent>();
        }
    }
    #endregion

    #region 核心：接收并执行函数调用（由AgentBridge调用）
    /// <summary>
    /// 接收JS转发的函数调用JSON
    /// JSON格式：{ "name": "函数名", "parameters": { "参数1": 值1, "参数2": 值2 } }
    /// </summary>
    /// <param name="functionCallJsonStr">JS传来的JSON字符串</param>
    public void ExecuteFunctionCall(string functionCallJsonStr)
    {
        if (string.IsNullOrEmpty(functionCallJsonStr))
        {
            Debug.LogError("函数调用JSON为空！");
            return;
        }

        try
        {
            // 1. 解析函数调用JSON
            JSONObject functionCallJson = new JSONObject(functionCallJsonStr);
            if (!functionCallJson.HasField("name") || !functionCallJson.HasField("parameters"))
            {
                throw new Exception("函数调用JSON格式错误：缺少name或parameters字段！");
            }

            string functionName = functionCallJson["name"].str;
            JSONObject paramJson = functionCallJson["parameters"];

            // 2. 查找函数定义
            AgentFunctionDefinition funcDef = functionDefinitionComp.FindFunctionByName(functionName);
            if (funcDef == null)
            {
                string error = $"未找到函数定义：{functionName}";
                Debug.LogError(error);
                NotifyResultToAgent(functionName, false, error);
                return;
            }

            // 3. 执行C#函数
            string result = funcDef.ExecuteFunction(paramJson);
            bool isSuccess = !result.Contains("失败");

            // 4. 自动回传执行结果给智能体（可选）
            if (autoNotifyResultToAgent)
            {
                NotifyResultToAgent(functionName, isSuccess, result);
            }
        }
        catch (Exception e)
        {
            string errorMsg = $"解析/执行函数调用失败：{e.Message}";
            Debug.LogError(errorMsg);
            NotifyResultToAgent("未知函数", false, errorMsg);
        }
    }
    #endregion

    #region 辅助：回传执行结果给智能体（通过桥接组件）
    private void NotifyResultToAgent(string functionName, bool isSuccess, string result)
    {
        // 构建结果JSON（供JS智能体接收）
        var resultJson = new JSONObject();
        resultJson.AddField("functionName", functionName);
        resultJson.AddField("isSuccess", isSuccess);
        resultJson.AddField("result", result);
        resultJson.AddField("timestamp", DateTimeOffset.Now.ToUnixTimeMilliseconds());

        // 调用桥接组件，回传给JS
        _agentBridge.NotifyFunctionExecuteResult(resultJson.ToString());
    }
    #endregion
}
```

### 2. 与桥接组件的联动（补充桥接组件的回传方法）
在之前的 `AgentBridge.cs` 中添加回传执行结果的方法，供执行器调用：
```csharp
// AgentBridge.cs 中新增
/// <summary>
/// 向JS回传函数执行结果
/// </summary>
public void NotifyFunctionExecuteResult(string resultJsonStr)
{
    Application.ExternalCall("agentOnFunctionExecuted", resultJsonStr);
}
```

同时在 JS 端添加接收结果的全局方法（对接你的智能体客户端）：
```js
// JS 全局方法：接收Unity函数执行结果
window.agentOnFunctionExecuted = function(resultJsonStr) {
    const result = JSON.parse(resultJsonStr);
    // 调用智能体客户端，提交函数执行结果（让智能体生成后续回复）
    agentClient.submitFunctionResult({
        functionName: result.functionName,
        success: result.isSuccess,
        result: result.result
    });
};
```

---

## 五、关键避坑与优化点（必看！）
### 1. 关于 JSON 解析库的适配
上述代码使用了 `JSONObject`（SimpleJSON），如果你想改用 Unity 内置的 `JsonUtility`，只需修改**参数解析**和**序列化**部分，核心逻辑不变。示例（替换 `ExecuteFunction` 中的参数解析）：
```csharp
// 改用JsonUtility解析参数（需定义对应的参数类）
private object[] ParseParamsWithJsonUtility(string paramJsonStr, List<AgentFunctionParam> paramList)
{
    // 简单示例：通过反射动态解析（或提前生成参数类）
    // 实际项目中，建议为每个函数定义参数类，或继续使用SimpleJSON（更灵活）
    var paramDict = JsonUtility.FromJson<Dictionary<string, object>>(paramJsonStr);
    List<object> csharpParams = new List<object>();
    foreach (var param in paramList)
    {
        csharpParams.Add(paramDict[param.paramName]);
    }
    return csharpParams.ToArray();
}
```

### 2. 全局函数的特殊处理
全局函数（如 `GlobalAudioManager.PlayBGM()`）建议设计为**静态方法**，绑定目标物体时，可选择任意挂载了该静态类的物体（或空物体），初始化时会通过 `BindingFlags.Static` 找到方法。

### 3. Inspector 函数选择优化（进阶）
如果觉得手动填写 `targetMethodName` 麻烦，可通过**编辑器拓展**实现「下拉选择目标物体的所有公共方法」，大幅提升效率。核心思路：
```csharp
// 编辑器拓展示例（放在Editor文件夹）
[CustomPropertyDrawer(typeof(AgentFunctionDefinition))]
public class AgentFunctionDefinitionDrawer : PropertyDrawer
{
    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        // 1. 绘制基础属性
        // 2. 当targetObject改变时，获取其所有公共方法，生成下拉列表
        // 3. 将选中的方法名赋值给targetMethodName
    }
}
```

### 4. 性能优化
- **缓存 MethodInfo**：首次初始化时缓存，避免每次执行都反射，提升运行时性能。
- **参数校验**：在 Editor 模式下添加「一键校验」按钮，提前发现参数不匹配问题，避免运行时报错。

---

## 六、完整工作流（函数定义 → 执行）
1. **C# 编写实际函数**：全局函数（静态）或组件函数（实例）。
2. **Inspector 配置**：在 `AgentFunctionDefinitionComponent` 中添加函数，拖拽绑定物体 + 填写方法名 + 配置参数。
3. **上下文激活**：Unity 切换场景，激活 `AgentContext`，自动初始化函数定义，生成 OpenAI 格式并发送给 JS。
4. **智能体下发函数调用**：用户提问后，智能体返回 `function call` JSON，JS 转发给 Unity 桥接组件。
5. **执行器处理**：执行器解析 JSON → 查找函数定义 → 反射执行 C# 函数 → 回传执行结果给智能体。
6. **智能体生成回复**：根据执行结果，智能体生成自然语言回复，完成闭环。

---

这套方案完全贴合你的架构设计，解决了「可视化配置」「自动标准化」「动态执行」三大核心问题，你可以直接复制代码到 Unity 中，结合你的 `AgentContext` 和 `AgentBridge` 组件即可落地。

如果需要，我可以帮你生成**编辑器拓展代码**（实现 Inspector 下拉选择函数）和**示例场景**（包含全局函数、组件函数的完整演示）。