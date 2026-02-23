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

    // 参数配置
    public List<FunctionParameter> parameters = new List<FunctionParameter>();

    // 缓存的方法信息
    [NonSerialized] public MethodInfo cachedMethod;

    // 初始化函数定义
    public bool Initialize()
    {
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
                    // 检查参数数量是否匹配
                    if (method.GetParameters().Length == parameters.Count)
                    {
                        cachedMethod = method;
                        return true;
                    }
                }
            }
        }

        Log.Print("AgentFunctionDefinition", "error", $"在物体[{targetObject.name}]上找不到方法[{targetMethodName}]");
        return false;
    }

    // 执行函数
    public object Execute(Dictionary<string, object> paramsDict)
    {
        if (cachedMethod == null && !Initialize())
        {
            return $"函数[{functionName}]初始化失败";
        }

        try
        {
            // 解析参数
            object[] args = ParseArguments(paramsDict);
            
            // 执行方法
            object result = cachedMethod.IsStatic 
                ? cachedMethod.Invoke(null, args)
                : cachedMethod.Invoke(GetTargetComponent(), args);

            return result ?? "执行成功";
        }
        catch (Exception e)
        {
            return $"执行错误: {e.Message}";
        }
    }

    // 解析参数
    private object[] ParseArguments(Dictionary<string, object> paramsDict)
    {
        List<object> args = new List<object>();
        
        for (int i = 0; i < parameters.Count; i++)
        {
            var param = parameters[i];
            string paramName = param.name;
            
            if (paramsDict.ContainsKey(paramName))
            {
                object value = paramsDict[paramName];
                args.Add(ConvertValue(value, param.type));
            }
            else if (param.required)
            {
                Log.Print("AgentFunctionDefinition", "error", $"必需参数[{paramName}]缺失");
                args.Add(GetDefaultValue(param.type));
            }
            else
            {
                args.Add(GetDefaultValue(param.type));
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
                 param.description.ToLower().Contains("vector3") || 
                 param.description.ToLower().Contains("三维坐标")))
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
                // 可以在这里添加验证逻辑
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
        foreach (var func in functions)
        {
            if (func != null)
            {
                func.Initialize();
            }
        }
    }
    
    // 处理前端的函数调用
    public void HandleFunctionCall(string functionCallJson)
    {
        try
        {
            // 解析JSON字符串，提取函数名和参数
            JsonData data = JsonMapper.ToObject(functionCallJson);
            string functionName = data["name"].ToString();
            Dictionary<string, object> paramsDict = ExtractParameters(data["parameters"]);
            
            // 查找对应的函数定义
            FunctionDefinition function = FindFunction(functionName);
            
            if (function != null)
            {
                // 执行函数
                object result = function.Execute(paramsDict);
                
                // 构建结果JSON
                string resultJson = BuildResultJson(functionName, result);
                
                // 向前端回传执行结果
                if (AgentBridge.Instance != null)
                {
                    AgentBridge.Instance.NotifyFunctionExecuteResult(resultJson);
                }
            }
            else
            {
                Log.Print("AgentFunctionDefinition", "error", $"未找到函数定义: {functionName}");
                
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
            Log.Print("AgentFunctionDefinition", "error", $"处理函数调用错误: {e.Message}");
            
            // 构建错误结果JSON
            string errorJson = BuildErrorResultJson("unknown", e.Message);
            if (AgentBridge.Instance != null)
            {
                AgentBridge.Instance.NotifyFunctionExecuteResult(errorJson);
            }
        }
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
            if (paramsData.IsObject)
            {
                IDictionary<string, JsonData> dict = paramsData as IDictionary<string, JsonData>;
                if (dict != null)
                {
                    foreach (string key in dict.Keys)
                    {
                        JsonData value = paramsData[key];
                        parameters[key] = ConvertJsonDataToObject(value);
                    }
                }
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
            IDictionary<string, JsonData> jsonDict = data as IDictionary<string, JsonData>;
            if (jsonDict != null)
            {
                foreach (string key in jsonDict.Keys)
                {
                    dict[key] = ConvertJsonDataToObject(data[key]);
                }
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
