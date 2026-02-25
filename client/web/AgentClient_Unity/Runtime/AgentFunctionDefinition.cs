using UnityEngine;
using System;
using System.Reflection;
using System.Collections.Generic;
using Museum.Debug;
using LitJson;

// 参数类型枚举
public enum ParameterType
{
    String,
    Number,
    Integer,
    Boolean,
    Array,
    Object
}

// 参数定义
[System.Serializable]
public class FunctionParameter
{
    public string name;
    public ParameterType type;
    public string description;
    public bool required = false;
    public float min = float.MinValue;
    public float max = float.MaxValue;
    public string enumOptions = ""; // 用逗号分隔的枚举选项
}

// 单个函数定义
[System.Serializable]
public class FunctionDefinition
{
    // 函数基本信息
    public string functionName;
    public string functionDescription;

    // 目标绑定
    public GameObject targetObject;
    public string targetMethodName;
    
    // 存储上一次的方法名，用于检测变化
    [NonSerialized] private string lastTargetMethodName;

    // 参数配置
    public List<FunctionParameter> parameters = new List<FunctionParameter>();

    // 缓存的方法信息
    [NonSerialized] public MethodInfo cachedMethod;

    // 从特性提取元数据
    private void ExtractMetadataFromAttributes(MethodInfo method)
    {
        try
        {
            // 提取函数级信息
            var funcAttr = method.GetCustomAttribute<AIFunctionAttribute>();
            if (funcAttr != null)
            {
                if (!string.IsNullOrEmpty(funcAttr.Name))
                {
                    functionName = funcAttr.Name;
                    Log.Print("AgentFunctionDefinition", "debug", $"从特性获取函数名: {functionName}");
                }
                else
                {
                    // 如果特性中没有设置名称，使用方法的实际名称
                    functionName = method.Name;
                    Log.Print("AgentFunctionDefinition", "debug", $"从方法名获取函数名: {functionName}");
                }
                if (!string.IsNullOrEmpty(funcAttr.Description))
                {
                    functionDescription = funcAttr.Description;
                    Log.Print("AgentFunctionDefinition", "debug", $"从特性获取函数描述: {functionDescription}");
                }
            }
            else
            {
                // 如果没有特性，使用方法的实际名称
                functionName = method.Name;
                Log.Print("AgentFunctionDefinition", "debug", $"从方法名获取函数名: {functionName}");
            }
            
            // 提取参数级信息
            ParameterInfo[] methodParams = method.GetParameters();
            for (int i = 0; i < methodParams.Length && i < parameters.Count; i++)
            {
                var paramInfo = methodParams[i];
                var functionParam = parameters[i];
                
                // 检查参数是否有默认值，如果有则设置为非必需
                if (paramInfo.HasDefaultValue)
                {
                    functionParam.required = false;
                    Log.Print("AgentFunctionDefinition", "debug", $"参数[{functionParam.name}]有默认值，设置为非必需");
                }
                else
                {
                    functionParam.required = true;
                    Log.Print("AgentFunctionDefinition", "debug", $"参数[{functionParam.name}]无默认值，设置为必需");
                }
                
                var paramAttr = paramInfo.GetCustomAttribute<AIParameterAttribute>();
                if (paramAttr != null)
                {
                    bool hasUpdate = false;
                    
                    if (!string.IsNullOrEmpty(paramAttr.Description))
                    {
                        functionParam.description = paramAttr.Description;
                        Log.Print("AgentFunctionDefinition", "debug", $"从特性获取参数[{functionParam.name}]描述: {functionParam.description}");
                        hasUpdate = true;
                    }
                    
                    if (paramAttr.Minimum != float.MinValue)
                    {
                        functionParam.min = paramAttr.Minimum;
                        Log.Print("AgentFunctionDefinition", "debug", $"从特性获取参数[{functionParam.name}]最小值: {functionParam.min}");
                        hasUpdate = true;
                    }
                    
                    if (paramAttr.Maximum != float.MaxValue)
                    {
                        functionParam.max = paramAttr.Maximum;
                        Log.Print("AgentFunctionDefinition", "debug", $"从特性获取参数[{functionParam.name}]最大值: {functionParam.max}");
                        hasUpdate = true;
                    }
                    
                    if (paramAttr.EnumOptions != null && paramAttr.EnumOptions.Length > 0)
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

    // 更新从特性中提取的信息（在编辑器中使用）
    public void UpdateFromAttributes()
    {
        // 检查targetMethodName是否变化
        if (targetMethodName == lastTargetMethodName)
        {
            // 方法名未变化，不执行更新，保留用户手动修改的信息
            return;
        }
        
        if (targetObject == null || string.IsNullOrEmpty(targetMethodName))
            return;

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
                    ExtractMetadataFromAttributes(method);
                    // 更新lastTargetMethodName，记录当前方法名
                    lastTargetMethodName = targetMethodName;
                    Log.Print("AgentFunctionDefinition", "debug", $"方法名变化，已从特性提取元数据: {targetMethodName}");
                    break;
                }
            }
        }
    }

    // 初始化函数定义
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

            // 查找公共方法
            MethodInfo[] methods = component.GetType().GetMethods(
                BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static
            );

            foreach (var method in methods)
            {
                if (method.Name == targetMethodName)
                {
                    // 从特性提取元数据
                    ExtractMetadataFromAttributes(method);
                    
                    // 检查参数数量是否匹配
                    if (method.GetParameters().Length == parameters.Count)
                    {
                        cachedMethod = method;
                        Log.Print("AgentFunctionDefinition", "debug", $"函数[{functionName}]初始化成功，绑定方法: {method.Name}");
                        return true;
                    }
                }
            }
        }

        Log.Print("AgentFunctionDefinition", "error", $"函数[{functionName}]初始化失败，在物体[{targetObject.name}]上找不到方法[{targetMethodName}]");
        return false;
    }

    // 执行函数
    public object Execute(Dictionary<string, object> paramsDict)
    {
        Log.Print("AgentFunctionDefinition", "debug", $"开始执行函数: {functionName}");
        
        if (cachedMethod == null && !Initialize())
        {
            Log.Print("AgentFunctionDefinition", "error", $"函数[{functionName}]初始化失败");
            return $"函数[{functionName}]初始化失败";
        }

        try
        {
            // 解析参数
            object[] args = ParseArguments(paramsDict);
            Log.Print("AgentFunctionDefinition", "debug", $"函数[{functionName}]参数解析完成，共{args.Length}个参数");
            
            // 执行方法
            object result = cachedMethod.IsStatic 
                ? cachedMethod.Invoke(null, args)
                : cachedMethod.Invoke(GetTargetComponent(), args);

            object finalResult = result ?? "执行成功";
            Log.Print("AgentFunctionDefinition", "debug", $"函数[{functionName}]执行完成");
            return finalResult;
        }
        catch (Exception e)
        {
            Log.Print("AgentFunctionDefinition", "error", $"函数[{functionName}]执行异常: {e.Message}");
            return $"执行错误: {e.Message}";
        }
    }

    // 解析参数
    private object[] ParseArguments(Dictionary<string, object> paramsDict)
    {
        List<object> args = new List<object>();
        ParameterInfo[] paramInfos = cachedMethod.GetParameters();
        
        for (int i = 0; i < parameters.Count && i < paramInfos.Length; i++)
        {
            var param = parameters[i];
            ParameterInfo paramInfo = paramInfos[i];
            string paramName = param.name;
            
            if (paramsDict.ContainsKey(paramName))
            {
                object value = paramsDict[paramName];
                args.Add(ConvertValue(value, param.type));
            }
            else if (param.required)
            {
                Log.Print("AgentFunctionDefinition", "error", $"必需参数[{paramName}]缺失");
                // 对于必需参数，使用类型默认值
                args.Add(GetDefaultValue(param.type));
            }
            else
            {
                // 对于可选参数，使用 C# 方法中定义的实际默认值
                if (paramInfo.HasDefaultValue)
                {
                    object defaultValue = paramInfo.DefaultValue;
                    // 处理值类型的特殊情况
                    if (paramInfo.ParameterType.IsValueType && defaultValue == null)
                    {
                        defaultValue = Activator.CreateInstance(paramInfo.ParameterType);
                    }
                    args.Add(defaultValue);
                    Log.Print("AgentFunctionDefinition", "debug", $"使用参数[{paramName}]的默认值: {defaultValue}");
                }
                else
                {
                    // 如果没有默认值，使用类型默认值
                    args.Add(GetDefaultValue(param.type));
                }
            }
        }

        return args.ToArray();
    }

    // 获取目标组件
    private Component GetTargetComponent()
    {
        return targetObject.GetComponent(cachedMethod.DeclaringType);
    }

    // 转换值到指定类型
    private object ConvertValue(object value, ParameterType paramType)
    {
        try
        {
            switch (paramType)
            {
                case ParameterType.String:
                    return value.ToString();
                case ParameterType.Integer:
                    return Convert.ToInt32(value);
                case ParameterType.Number:
                    return Convert.ToSingle(value);
                case ParameterType.Boolean:
                    return Convert.ToBoolean(value);
                case ParameterType.Object:
                    // 检查是否是Vector3结构（包含x、y、z三个属性）
                    if (value is Dictionary<string, object> objValue)
                    {
                        if (objValue.ContainsKey("x") && objValue.ContainsKey("y") && objValue.ContainsKey("z"))
                        {
                            // 尝试将x、y、z转换为float，然后创建Vector3对象
                            float x = Convert.ToSingle(objValue["x"]);
                            float y = Convert.ToSingle(objValue["y"]);
                            float z = Convert.ToSingle(objValue["z"]);
                            return new Vector3(x, y, z);
                        }
                    }
                    return value;
                default:
                    return value;
            }
        }
        catch (Exception e)
        {
            Log.Print("AgentFunctionDefinition", "error", $"转换参数值失败：{e.Message}");
            return GetDefaultValue(paramType);
        }
    }

    // 获取默认值
    private object GetDefaultValue(ParameterType type)
    {
        switch (type)
        {
            case ParameterType.String:
                return "";
            case ParameterType.Integer:
                return 0;
            case ParameterType.Number:
                return 0.0f;
            case ParameterType.Boolean:
                return false;
            default:
                return null;
        }
    }

    // 转换为函数定义对象
    public Dictionary<string, object> ToFunctionObject()
    {
        Dictionary<string, object> functionObj = new Dictionary<string, object>();
        functionObj["name"] = functionName;
        functionObj["description"] = functionDescription;
        
        Dictionary<string, object> parametersObj = new Dictionary<string, object>();
        parametersObj["type"] = "object";
        
        Dictionary<string, object> propertiesObj = new Dictionary<string, object>();
        List<string> requiredParams = new List<string>();
        
        foreach (var param in parameters)
        {
            Dictionary<string, object> paramObj = new Dictionary<string, object>();
            paramObj["type"] = GetJsonTypeName(param.type);
            paramObj["description"] = param.description;
            
            // 处理Vector3等复合类型（object类型）
            if (param.type == ParameterType.Object && 
                (param.name.ToLower().Contains("vector3") || 
                 param.name.ToLower().Contains("position") ||
                 param.name.ToLower().Contains("rotation") ||
                 param.name.ToLower().Contains("scale") ||
                 param.name.ToLower().Contains("axis") ||
                 param.name.ToLower().Contains("color") ||
                 param.description.ToLower().Contains("vector3") || 
                 param.description.ToLower().Contains("三维坐标") ||
                 param.description.ToLower().Contains("位置") ||
                 param.description.ToLower().Contains("旋转") ||
                 param.description.ToLower().Contains("缩放") ||
                 param.description.ToLower().Contains("轴向") ||
                 param.description.ToLower().Contains("颜色")))
            {
                // 为Vector3添加x/y/z子参数
                Dictionary<string, object> vectorProperties = new Dictionary<string, object>();
                
                Dictionary<string, object> xParam = new Dictionary<string, object>();
                xParam["type"] = "number";
                xParam["description"] = "X轴坐标值";
                vectorProperties["x"] = xParam;
                
                Dictionary<string, object> yParam = new Dictionary<string, object>();
                yParam["type"] = "number";
                yParam["description"] = "Y轴坐标值";
                vectorProperties["y"] = yParam;
                
                Dictionary<string, object> zParam = new Dictionary<string, object>();
                zParam["type"] = "number";
                zParam["description"] = "Z轴坐标值";
                vectorProperties["z"] = zParam;
                
                paramObj["properties"] = vectorProperties;
                paramObj["required"] = new List<string> { "x", "y", "z" };
            }
            else
            {
                // 添加数值范围约束
                if (param.type == ParameterType.Number || param.type == ParameterType.Integer)
                {
                    if (param.min != float.MinValue)
                        paramObj["minimum"] = param.min;
                    if (param.max != float.MaxValue)
                        paramObj["maximum"] = param.max;
                }

                // 添加枚举选项
                if (!string.IsNullOrEmpty(param.enumOptions))
                {
                    List<string> enumList = new List<string>();
                    string[] options = param.enumOptions.Split(',');
                    foreach (var option in options)
                    {
                        enumList.Add(option.Trim());
                    }
                    paramObj["enum"] = enumList;
                }
            }
            
            propertiesObj[param.name] = paramObj;
            if (param.required)
                requiredParams.Add(param.name);
        }
        
        parametersObj["properties"] = propertiesObj;
        parametersObj["required"] = requiredParams;
        functionObj["parameters"] = parametersObj;
        
        return functionObj;
    }

    // 获取JSON类型名
    private string GetJsonTypeName(ParameterType type)
    {
        switch (type)
        {
            case ParameterType.String:
                return "string";
            case ParameterType.Number:
                return "number";
            case ParameterType.Integer:
                return "integer";
            case ParameterType.Boolean:
                return "boolean";
            case ParameterType.Array:
                return "array";
            case ParameterType.Object:
                return "object";
            default:
                return "string";
        }
    }
}

// 函数定义列表
[System.Serializable]
public class FunctionDefinitions
{
    public List<FunctionDefinition> functions = new List<FunctionDefinition>();
}

public class AgentFunctionDefinition : MonoBehaviour
{
    // 函数定义列表
    public List<FunctionDefinition> functions = new List<FunctionDefinition>();

    void OnValidate()
    {
        // 在编辑器中验证函数定义
        foreach (var func in functions)
        {
            if (func != null)
            {
                func.UpdateFromAttributes();
            }
        }
    }

    void Start()
    {
        // 初始化所有函数定义
        InitializeAllFunctions();
    }

    // 获取所有函数的定义列表
    public List<object> GetAllFunctions()
    {
        List<object> functionList = new List<object>();
        foreach (var func in functions)
        {
            if (func != null)
            {
                functionList.Add(func.ToFunctionObject());
            }
        }
        return functionList;
    }

    // 获取所有OpenAI格式函数定义的JSON字符串
    public string GetAllOpenAIFunctionsJsonStr()
    {
        List<object> functionList = GetAllFunctions();
        return JsonMapper.ToJson(functionList);
    }

    // 根据名称查找函数
    public FunctionDefinition FindFunction(string functionName)
    {
        return functions.Find(f => f != null && f.functionName == functionName);
    }

    // 初始化所有函数
    public void InitializeAllFunctions()
    {
        Log.Print("AgentFunctionDefinition", "debug", $"开始初始化所有函数定义，共{functions.Count}个函数");
        
        int successCount = 0;
        int failCount = 0;
        
        foreach (var func in functions)
        {
            if (func != null)
            {
                if (func.Initialize())
                {
                    successCount++;
                }
                else
                {
                    failCount++;
                }
            }
        }
        
        Log.Print("AgentFunctionDefinition", "debug", $"函数定义初始化完成: 成功{successCount}个，失败{failCount}个");
    }
    
    // 处理前端的函数调用
    public void HandleFunctionCall(string functionCallJson)
    {
        Log.Print("AgentFunctionDefinition", "debug", "接收到函数调用请求");
        
        try
        {
            // 检查JSON字符串是否为空
            if (string.IsNullOrEmpty(functionCallJson))
            {
                Log.Print("AgentFunctionDefinition", "error", "函数调用JSON数据为空");
                string errorJson = BuildErrorResultJson("unknown", "函数调用JSON数据为空");
                if (AgentBridge.Instance != null)
                {
                    AgentBridge.Instance.NotifyFunctionExecuteResult(errorJson);
                }
                return;
            }

            Log.Print("AgentFunctionDefinition", "debug", $"函数调用数据: {functionCallJson}");

            // 解析JSON字符串，提取函数名和参数
            JsonData data = JsonMapper.ToObject(functionCallJson);

            // 检查是否为对象类型
            if (!data.IsObject)
            {
                Log.Print("AgentFunctionDefinition", "error", "函数调用JSON数据必须是对象类型，不能是数组或其他类型");
                string errorJson = BuildErrorResultJson("unknown", "函数调用JSON数据格式错误，必须是对象类型");
                if (AgentBridge.Instance != null)
                {
                    AgentBridge.Instance.NotifyFunctionExecuteResult(errorJson);
                }
                return;
            }

            // 检查是否包含name字段
            if (!data.Keys.Contains("name"))
            {
                Log.Print("AgentFunctionDefinition", "error", "函数调用JSON数据缺少name字段");
                string errorJson = BuildErrorResultJson("unknown", "函数调用JSON数据缺少name字段");
                if (AgentBridge.Instance != null)
                {
                    AgentBridge.Instance.NotifyFunctionExecuteResult(errorJson);
                }
                return;
            }

            string functionName = data["name"].ToString();
            Log.Print("AgentFunctionDefinition", "debug", $"解析函数名: {functionName}");

            // 检查是否包含parameters字段
            Dictionary<string, object> paramsDict = new Dictionary<string, object>();
            if (data.Keys.Contains("parameters"))
            {
                paramsDict = ExtractParameters(data["parameters"]);
                Log.Print("AgentFunctionDefinition", "debug", $"解析参数: {paramsDict.Count}个参数");
            }
            else
            {
                Log.Print("AgentFunctionDefinition", "debug", "函数调用无参数");
            }
            
            // 查找对应的函数定义
            FunctionDefinition function = FindFunction(functionName);
            
            if (function != null)
            {
                Log.Print("AgentFunctionDefinition", "debug", $"函数定义验证成功: {functionName}");
                
                // 执行函数
                object result = function.Execute(paramsDict);
                
                // 检查执行结果
                if (result is string && ((string)result).Contains("错误"))
                {
                    Log.Print("AgentFunctionDefinition", "error", $"函数执行失败: {functionName}, 原因: {result}");
                }
                else
                {
                    Log.Print("AgentFunctionDefinition", "debug", $"函数执行成功: {functionName}, 结果: {result}");
                }
                
                // 构建结果JSON
                string resultJson = BuildResultJson(functionName, result);
                
                // 向前端回传执行结果
                if (AgentBridge.Instance != null)
                {
                    AgentBridge.Instance.NotifyFunctionExecuteResult(resultJson);
                    Log.Print("AgentFunctionDefinition", "debug", "函数执行结果已回传");
                }
            }
            else
            {
                Log.Print("AgentFunctionDefinition", "error", $"函数定义验证失败: 未找到函数定义 {functionName}");
                
                // 构建错误结果JSON
                string errorJson = BuildErrorResultJson(functionName, "未找到函数定义");
                if (AgentBridge.Instance != null)
                {
                    AgentBridge.Instance.NotifyFunctionExecuteResult(errorJson);
                }
            }
        }
        catch (Exception e)
        {
            Log.Print("AgentFunctionDefinition", "error", $"处理函数调用异常: {e.Message}");
            
            // 构建错误结果JSON
            string errorJson = BuildErrorResultJson("unknown", e.Message);
            if (AgentBridge.Instance != null)
            {
                AgentBridge.Instance.NotifyFunctionExecuteResult(errorJson);
            }
        }
        
        Log.Print("AgentFunctionDefinition", "debug", "函数调用处理完成");
    }
    
    // 提取函数名
    public string ExtractFunctionName(string functionCallJson)
    {
        try
        {
            JsonData data = JsonMapper.ToObject(functionCallJson);
            return data["name"].ToString();
        }
        catch (Exception e)
        {
            Log.Print("AgentFunctionDefinition", "error", $"提取函数名失败: {e.Message}");
            return string.Empty;
        }
    }

    // 提取参数
    public Dictionary<string, object> ExtractParameters(string functionCallJson)
    {
        try
        {
            JsonData data = JsonMapper.ToObject(functionCallJson);
            return ExtractParameters(data["parameters"]);
        }
        catch (Exception e)
        {
            Log.Print("AgentFunctionDefinition", "error", $"提取参数失败: {e.Message}");
            return new Dictionary<string, object>();
        }
    }

    // 从JsonData中提取参数
    private Dictionary<string, object> ExtractParameters(JsonData paramsData)
    {
        Dictionary<string, object> parameters = new Dictionary<string, object>();
        try
        {
            // 检查paramsData是否为null或无效
            if (paramsData == null || paramsData.ToString() == "null")
            {
                Log.Print("AgentFunctionDefinition", "debug", "参数数据为null，返回空字典");
                return parameters;
            }

            // 检查是否为对象类型
            if (paramsData.IsObject)
            {
                // 直接使用 JsonData 的 Keys 属性遍历
                foreach (string key in paramsData.Keys)
                {
                    JsonData value = paramsData[key];
                    parameters[key] = ConvertJsonDataToObject(value);
                }
            }
            else
            {
                Log.Print("AgentFunctionDefinition", "debug", $"参数数据类型不是对象类型，返回空字典");
            }
        }
        catch (Exception e)
        {
            Log.Print("AgentFunctionDefinition", "error", $"提取参数失败: {e.Message}");
        }
        return parameters;
    }
    
    // 将JsonData转换为.NET对象
    private object ConvertJsonDataToObject(JsonData data)
    {
        // 处理null值
        if (data == null || data.ToString() == "null")
        {
            return null;
        }
        
        if (data.IsString)
            return data.ToString();
        if (data.IsBoolean)
            return (bool)data;
        if (data.IsInt)
            return (int)data;
        if (data.IsLong)
            return (long)data;
        if (data.IsDouble)
            return (double)data;
        if (data.IsArray)
        {
            List<object> list = new List<object>();
            for (int i = 0; i < data.Count; i++)
            {
                list.Add(ConvertJsonDataToObject(data[i]));
            }
            return list;
        }
        if (data.IsObject)
        {
            Dictionary<string, object> dict = new Dictionary<string, object>();
            // 直接使用 JsonData 的 Keys 属性遍历
            foreach (string key in data.Keys)
            {
                dict[key] = ConvertJsonDataToObject(data[key]);
            }
            return dict;
        }
        return data.ToString();
    }
    
    // 构建结果JSON
    private string BuildResultJson(string functionName, object result)
    {
        Dictionary<string, object> resultData = new Dictionary<string, object>
        {
            { "requestId", Guid.NewGuid().ToString() },
            { "functionName", functionName },
            { "success", !(result is string && ((string)result).Contains("错误")) },
            { "result", result },
            { "error", null }
        };
        return JsonMapper.ToJson(resultData);
    }
    
    // 构建错误结果JSON
    private string BuildErrorResultJson(string functionName, string errorMessage)
    {
        Dictionary<string, object> resultData = new Dictionary<string, object>
        {
            { "requestId", Guid.NewGuid().ToString() },
            { "functionName", functionName },
            { "success", false },
            { "result", null },
            { "error", errorMessage }
        };
        return JsonMapper.ToJson(resultData);
    }
}
