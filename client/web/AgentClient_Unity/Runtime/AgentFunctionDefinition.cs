using UnityEngine;
using System;
using System.Reflection;
using System.Collections.Generic;
using Museum.Debug;

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

    // 转换为OpenAI格式
    public string ToOpenAIFunction()
    {
        // 构建函数定义的JSON字符串
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        sb.Append("{");
        sb.Append($"\"name\":\"{functionName}\",");
        sb.Append($"\"description\":\"{functionDescription}\",");
        sb.Append("\"parameters\":{");
        sb.Append("\"type\":\"object\",");
        sb.Append("\"properties\":{");

        // 构建properties
        for (int i = 0; i < parameters.Count; i++)
        {
            var param = parameters[i];
            sb.Append($"\"{param.name}\":{{");
            sb.Append($"\"type\":\"{GetJsonTypeName(param.type)}\",");
            sb.Append($"\"description\":\"{param.description}\"");

            // 处理Vector3等复合类型（object类型）
            if (param.type == ParameterType.Object && param.name.ToLower().Contains("vector3") || param.description.ToLower().Contains("vector3") || param.description.ToLower().Contains("三维坐标"))
            {
                // 为Vector3添加x/y/z子参数
                sb.Append(",\"properties\":{");
                sb.Append("\"x\":{");
                sb.Append("\"type\":\"number\",");
                sb.Append("\"description\":\"X轴坐标值\"");
                sb.Append("},");
                sb.Append("\"y\":{");
                sb.Append("\"type\":\"number\",");
                sb.Append("\"description\":\"Y轴坐标值\"");
                sb.Append("},");
                sb.Append("\"z\":{");
                sb.Append("\"type\":\"number\",");
                sb.Append("\"description\":\"Z轴坐标值\"");
                sb.Append("}");
                sb.Append("},");
                sb.Append("\"required\":[\"x\",\"y\",\"z\"]");
            }
            else
            {
                // 添加数值范围约束
                if (param.type == ParameterType.Number || param.type == ParameterType.Integer)
                {
                    if (param.min != float.MinValue)
                        sb.Append($",\"minimum\":{param.min}");
                    if (param.max != float.MaxValue)
                        sb.Append($",\"maximum\":{param.max}");
                }

                // 添加枚举选项
                if (!string.IsNullOrEmpty(param.enumOptions))
                {
                    sb.Append(",\"enum\":[");
                    string[] options = param.enumOptions.Split(',');
                    for (int j = 0; j < options.Length; j++)
                    {
                        sb.Append($"\"{options[j].Trim()}\"");
                        if (j < options.Length - 1)
                            sb.Append(",");
                    }
                    sb.Append("]");
                }
            }

            sb.Append("}");
            if (i < parameters.Count - 1)
                sb.Append(",");
        }

        sb.Append("},");

        // 构建required
        sb.Append("\"required\":[");
        List<string> requiredParams = new List<string>();
        foreach (var param in parameters)
        {
            if (param.required)
                requiredParams.Add($"\"{param.name}\"");
        }
        sb.Append(string.Join(",", requiredParams));
        sb.Append("]");

        sb.Append("}");
        sb.Append("}");

        return sb.ToString();
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

    // 获取所有函数的OpenAI格式
    public string GetAllOpenAIFunctionsJsonStr()
    {
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        sb.Append("{");
        sb.Append("\"functions\":[");

        for (int i = 0; i < functions.Count; i++)
        {
            var func = functions[i];
            if (func != null)
            {
                sb.Append(func.ToOpenAIFunction());
                if (i < functions.Count - 1)
                    sb.Append(",");
            }
        }

        sb.Append("]");
        sb.Append("}");

        return sb.ToString();
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
            // 这里需要实现函数调用的解析和执行逻辑
            // 暂时使用简单的实现，后续可以根据需要进行扩展
            
            // 解析JSON字符串，提取函数名和参数
            string functionName = ExtractFunctionName(functionCallJson);
            Dictionary<string, object> paramsDict = ExtractParameters(functionCallJson);
            
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
            }
        }
        catch (Exception e)
        {
            Log.Print("AgentFunctionDefinition", "error", $"处理函数调用错误: {e.Message}");
        }
    }
    
    // 从JSON字符串中提取函数名
    private string ExtractFunctionName(string json)
    {
        // 简单的字符串解析，实际项目中可能需要使用更复杂的JSON解析
        int nameStart = json.IndexOf("\"name\":\"") + 7;
        int nameEnd = json.IndexOf('"', nameStart);
        return json.Substring(nameStart, nameEnd - nameStart);
    }
    
    // 从JSON字符串中提取参数
    private Dictionary<string, object> ExtractParameters(string json)
    {
        // 简单的字符串解析，实际项目中可能需要使用更复杂的JSON解析
        Dictionary<string, object> paramsDict = new Dictionary<string, object>();
        
        // 这里需要实现参数解析逻辑
        // 暂时返回空字典
        return paramsDict;
    }
    
    // 构建结果JSON
    private string BuildResultJson(string functionName, object result)
    {
        // 构建结果JSON字符串
        return $"{{\"function\":\"{functionName}\",\"result\":\"{result}\"}}";
    }
}