using UnityEngine;
using System.Collections.Generic;
using LitJson;

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
    private Dictionary<string, object> lastSentContext = null;
    
    // 构建上下文JSON数据
    private string BuildContextJson()
    {
        // 获取关联的函数定义组件
        var functionDef = enableFunctionCalling ? functionDefinition : null;
        List<object> functionList = new List<object>();
        
        if (functionDef != null)
        {
            functionList = functionDef.GetAllFunctions();
        }

        // 构建完整的上下文数据
        Dictionary<string, object> currentContext = new Dictionary<string, object>
        {
            { "sceneDescription", sceneDescription },
            { "roleDescription", roleDescription },
            { "responseRequirements", responseRequirements },
            { "functionCalling", functionList },
            { "functions", functionList } // 兼容支持
        };

        // 计算差异更新
        string jsonToSend = CalculateDeltaUpdate(currentContext);
        
        // 更新上次发送的上下文
        lastSentContext = currentContext;

        return jsonToSend;
    }
    
    // 计算差异更新
    private string CalculateDeltaUpdate(Dictionary<string, object> currentContext)
    {
        // 如果是第一次发送，发送完整数据
        if (lastSentContext == null)
        {
            return JsonMapper.ToJson(currentContext);
        }
        
        // 创建差异对象
        Dictionary<string, object> delta = new Dictionary<string, object>();
        
        // 检查场景描述是否有变化
        if (!lastSentContext.ContainsKey("sceneDescription") || 
            lastSentContext["sceneDescription"].ToString() != currentContext["sceneDescription"].ToString())
        {
            delta["sceneDescription"] = currentContext["sceneDescription"];
        }
        
        // 检查角色描述是否有变化
        if (!lastSentContext.ContainsKey("roleDescription") || 
            lastSentContext["roleDescription"].ToString() != currentContext["roleDescription"].ToString())
        {
            delta["roleDescription"] = currentContext["roleDescription"];
        }
        
        // 检查响应要求是否有变化
        if (!lastSentContext.ContainsKey("responseRequirements") || 
            lastSentContext["responseRequirements"].ToString() != currentContext["responseRequirements"].ToString())
        {
            delta["responseRequirements"] = currentContext["responseRequirements"];
        }
        
        // 检查函数调用是否有变化
        if (!lastSentContext.ContainsKey("functionCalling") || 
            !AreFunctionListsEqual((List<object>)lastSentContext["functionCalling"], (List<object>)currentContext["functionCalling"]))
        {
            delta["functionCalling"] = currentContext["functionCalling"];
            delta["functions"] = currentContext["functions"]; // 同时更新functions字段
        }
        
        // 如果没有变化，返回空对象
        if (delta.Count == 0)
        {
            return "{}";
        }
        
        // 使用LitJSON序列化差异数据
        return JsonMapper.ToJson(delta);
    }
    
    // 比较两个函数列表是否相等
    private bool AreFunctionListsEqual(List<object> list1, List<object> list2)
    {
        if (list1.Count != list2.Count)
            return false;
        
        for (int i = 0; i < list1.Count; i++)
        {
            string json1 = JsonMapper.ToJson(list1[i]);
            string json2 = JsonMapper.ToJson(list2[i]);
            if (json1 != json2)
                return false;
        }
        
        return true;
    }
}
