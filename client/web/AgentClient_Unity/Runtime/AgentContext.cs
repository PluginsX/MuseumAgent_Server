using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class ContextData
{
    public string sceneDescription;
    public string roleDescription;
    public string responseRequirements;
    public bool functionCalling;
    public string functions;
}

public class AgentContext : MonoBehaviour
{
    [TextArea(3, 999)]
    public string sceneDescription = "当前场景描述";
    [TextArea(3, 999)]
    public string roleDescription = "智能体角色描述";
    [TextArea(3, 999)]
    public string responseRequirements = "响应要求";
    public bool enableFunctionCalling = true;
    public AgentFunctionDefinition functionDefinition;

    void Start()
    {
        // 检查函数定义组件
        CheckFunctionDefinitionComponent();
        
        // 激活当前上下文
        ActivateContext();
    }
    
    // 检查函数定义组件
    private void CheckFunctionDefinitionComponent()
    {
        // 只有当启用函数调用时，才检查函数定义组件
        if (enableFunctionCalling && functionDefinition == null)
        {
            functionDefinition = GetComponent<AgentFunctionDefinition>();
        }
    }

    // 激活当前上下文，向前端发送上下文信息
    public void ActivateContext()
    {
        if (AgentBridge.Instance != null)
        {
            string contextJson = BuildContextJson();
            AgentBridge.Instance.UpdateContext(contextJson);
        }
    }

    // 上次发送的上下文数据，用于计算差异
    private ContextData lastSentContext = null;
    
    // 构建上下文JSON数据
    private string BuildContextJson()
    {
        // 获取关联的函数定义组件
        var functionDef = enableFunctionCalling ? functionDefinition : null;
        string functionsJson = "[]"; // 默认空数组
        
        if (functionDef != null)
        {
            functionsJson = functionDef.GetAllOpenAIFunctionsJsonStr();
        }

        // 构建完整的上下文数据
        ContextData currentContext = new ContextData
        {
            sceneDescription = sceneDescription,
            roleDescription = roleDescription,
            responseRequirements = responseRequirements,
            functionCalling = enableFunctionCalling,
            functions = functionsJson
        };

        // 计算差异更新
        string jsonToSend = CalculateDeltaUpdate(currentContext);
        
        // 更新上次发送的上下文
        lastSentContext = currentContext;

        return jsonToSend;
    }
    
    // 计算差异更新
    private string CalculateDeltaUpdate(ContextData currentContext)
    {
        // 如果是第一次发送，发送完整数据
        if (lastSentContext == null)
        {
            return JsonUtility.ToJson(currentContext, true);
        }
        
        // 创建差异对象
        Dictionary<string, object> delta = new Dictionary<string, object>();
        
        // 检查场景描述是否有变化
        if (currentContext.sceneDescription != lastSentContext.sceneDescription)
        {
            delta["sceneDescription"] = currentContext.sceneDescription;
        }
        
        // 检查角色描述是否有变化
        if (currentContext.roleDescription != lastSentContext.roleDescription)
        {
            delta["roleDescription"] = currentContext.roleDescription;
        }
        
        // 检查响应要求是否有变化
        if (currentContext.responseRequirements != lastSentContext.responseRequirements)
        {
            delta["responseRequirements"] = currentContext.responseRequirements;
        }
        
        // 检查函数调用是否有变化
        if (currentContext.functionCalling != lastSentContext.functionCalling)
        {
            delta["functionCalling"] = currentContext.functionCalling;
        }
        
        // 检查函数定义是否有变化
        if (currentContext.functions != lastSentContext.functions)
        {
            delta["functions"] = currentContext.functions;
        }
        
        // 如果没有变化，返回空对象
        if (delta.Count == 0)
        {
            return "{}";
        }
        
        // 构建差异JSON
        return BuildDeltaJson(delta);
    }
    
    // 构建差异JSON
    private string BuildDeltaJson(Dictionary<string, object> delta)
    {
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        sb.Append("{");
        
        int count = 0;
        foreach (var kvp in delta)
        {
            if (count > 0)
            {
                sb.Append(",");
            }
            
            sb.Append($"\"{kvp.Key}\":");
            
            // 处理不同类型的值
            if (kvp.Value is string strValue)
            {
                // 特殊处理functions字段，因为它本身就是JSON字符串
                if (kvp.Key == "functions")
                {
                    sb.Append(strValue);
                }
                else
                {
                    sb.Append($"\"{strValue}\"");
                }
            }
            else if (kvp.Value is bool boolValue)
            {
                sb.Append(boolValue.ToString().ToLower());
            }
            else
            {
                sb.Append($"\"{kvp.Value}\"");
            }
            
            count++;
        }
        
        sb.Append("}");
        return sb.ToString();
    }
}