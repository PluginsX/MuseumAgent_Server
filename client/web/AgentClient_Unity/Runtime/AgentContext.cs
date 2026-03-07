using UnityEngine;
using System.Collections.Generic;
using LitJson;
using Museum.Debug;

[System.Serializable]
public class AdditionalDescription
{
    public string key;
    public string value;
    
    public AdditionalDescription(string key, string value)
    {
        this.key = key;
        this.value = value;
    }
}

public class AgentContext : MonoBehaviour
{
    [Tooltip("AgentBridge 单例组件引用")]
    public AgentBridge agentBridge;
    [Tooltip("启动时自动注册到 AgentBridge")]
    public bool autoRegisterOnStart = false;
    [TextArea(3, 999)]
    public string sceneDescription = "当前场景描述";
    [TextArea(3, 999)]
    public string roleDescription = "智能体角色描述";
    [TextArea(3, 999)]
    public string responseRequirements = "响应要求";
    public bool enableFunctionCalling = true;
    public AgentFunctionDefinition functionDefinition;
    public List<AdditionalDescription> additionalDescriptions = new List<AdditionalDescription>();



    void Start()
    {
        CheckFunctionDefinitionComponent();
        
        if (autoRegisterOnStart)
        {
            AutoRegisterToBridge();
        }
    }
    
    private void OnValidate()
    {
        if (agentBridge == null)
        {
            agentBridge = AgentBridge.Instance;
        }
    }
    
    private void AutoRegisterToBridge()
    {
        if (agentBridge == null)
        {
            agentBridge = AgentBridge.Instance;
        }
        
        if (agentBridge == null)
        {
            Log.Print("AgentContext", "error", "未找到 AgentBridge 单例组件，无法自动注册");
            return;
        }
        
        agentBridge.SwitchContext(this);
        Log.Print("AgentContext", "debug", $"已自动注册到 AgentBridge: {name}");
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

    // 获取合并后的场景描述（包含补充描述）
    public string GetMergedSceneDescription()
    {
        if (additionalDescriptions == null || additionalDescriptions.Count == 0)
        {
            return sceneDescription;
        }
        
        // 基础描述
        string merged = sceneDescription;
        
        // 添加补充描述
        foreach (var desc in additionalDescriptions)
        {
            if (!string.IsNullOrEmpty(desc.key) && !string.IsNullOrEmpty(desc.value))
            {
                merged += $"\n{desc.key}: {desc.value}";
            }
        }
        
        return merged;
    }
    
    // 创建补充描述
    public void AdditionalDescription_Create(string key, string value)
    {
        if (string.IsNullOrEmpty(key))
        {
            Log.Print("AgentContext", "warn", "补充描述的键不能为空");
            return;
        }
        
        // 检查是否已存在相同键
        var existing = additionalDescriptions.Find(desc => desc.key == key);
        if (existing != null)
        {
            Log.Print("AgentContext", "warn", $"补充描述的键 '{key}' 已存在，请使用 Set 方法修改");
            return;
        }
        
        additionalDescriptions.Add(new AdditionalDescription(key, value));
        Log.Print("AgentContext", "debug", $"已添加补充描述: {key} = {value}");
    }
    
    // 删除补充描述
    public void AdditionalDescription_Delete(string key)
    {
        if (string.IsNullOrEmpty(key))
        {
            Log.Print("AgentContext", "warn", "补充描述的键不能为空");
            return;
        }
        
        int removedCount = additionalDescriptions.RemoveAll(desc => desc.key == key);
        if (removedCount > 0)
        {
            Log.Print("AgentContext", "debug", $"已删除补充描述: {key}");
        }
        else
        {
            Log.Print("AgentContext", "warn", $"未找到键为 '{key}' 的补充描述");
        }
    }
    
    // 获取补充描述
    public string AdditionalDescription_Get(string key)
    {
        if (string.IsNullOrEmpty(key))
        {
            Log.Print("AgentContext", "warn", "补充描述的键不能为空");
            return null;
        }
        
        var description = additionalDescriptions.Find(desc => desc.key == key);
        return description?.value;
    }
    
    // 修改补充描述
    public void AdditionalDescription_Set(string key, string newValue)
    {
        if (string.IsNullOrEmpty(key))
        {
            Log.Print("AgentContext", "warn", "补充描述的键不能为空");
            return;
        }
        
        var description = additionalDescriptions.Find(desc => desc.key == key);
        if (description == null)
        {
            Log.Print("AgentContext", "warn", $"未找到键为 '{key}' 的补充描述，无法修改");
            return;
        }
        
        string oldValue = description.value;
        description.value = newValue;
        Log.Print("AgentContext", "debug", $"已修改补充描述: {key} 从 '{oldValue}' 改为 '{newValue}'");
    }
    
    // 检查补充描述是否存在
    public bool AdditionalDescription_Contains(string key)
    {
        if (string.IsNullOrEmpty(key))
        {
            return false;
        }
        
        return additionalDescriptions.Exists(desc => desc.key == key);
    }
    
    // 获取所有补充描述的键
    public List<string> AdditionalDescription_GetAllKeys()
    {
        List<string> keys = new List<string>();
        foreach (var desc in additionalDescriptions)
        {
            if (!string.IsNullOrEmpty(desc.key))
            {
                keys.Add(desc.key);
            }
        }
        return keys;
    }
    
    // 清空所有补充描述
    public void AdditionalDescription_Clear()
    {
        int count = additionalDescriptions.Count;
        additionalDescriptions.Clear();
        Log.Print("AgentContext", "debug", $"已清空 {count} 个补充描述");
    }
    
    // 获取补充描述数量
    public int AdditionalDescription_Count()
    {
        return additionalDescriptions.Count;
    }
}
