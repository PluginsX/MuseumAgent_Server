using UnityEngine;
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Museum.Debug;
using AgentClient.Runtime;

public class AgentBridge : MonoBehaviour
{
    public static AgentBridge Instance { get; private set; }
    
    // 导入 jslib 函数
    [DllImport("__Internal")]
    private static extern int RegisterUnityInstance();
    
    [DllImport("__Internal")]
    private static extern int UpdateContextFromUnity(string contextJson);
    
    [DllImport("__Internal")]
    private static extern int NotifyFunctionResultFromUnity(string resultJson);
    
    [DllImport("__Internal")]
    private static extern int ForwardUserMessageFromUnity(string message);
    
    [Header("=== 当前上下文 ===")]
    public AgentContext currentContext;
    
    // 存储上次发送的全量上下文
    private string cachedSceneDescription = null;
    private string cachedRoleDescription = null;
    private string cachedResponseRequirements = null;
    private int cachedFunctionCount = -1;
    private bool hasCachedContext = false;
    
    [Header("=== 启动选项 ===")]
    public bool autoUpdateContext = true;
    
    [Header("=== 调试输出 ===")]
    public UnityEngine.UI.Text functionCallOutputText;
    
    private void LogToTextAndConsole(string category, string level, string message)
    {
        Log.Print(category, level, message);
        
        if (functionCallOutputText != null)
        {
            string timestamp = DateTime.Now.ToString("HH:mm:ss");
            string logEntry = $"[{timestamp}][{level.ToUpper()}] {message}\n";
            functionCallOutputText.text += logEntry;
        }
    }

    void Awake()
    {
        LogToTextAndConsole("AgentBridge", "debug", "Awake 初始化");
        
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
            LogToTextAndConsole("AgentBridge", "debug", "单例实例创建成功");
        }
        else
        {
            LogToTextAndConsole("AgentBridge", "warning", "检测到重复实例，销毁当前对象");
            Destroy(gameObject);
        }
    }
    
    void Start()
    {
        LogToTextAndConsole("AgentBridge", "debug", "Start 初始化");
        
        if (currentContext != null && autoUpdateContext)
        {
            LogToTextAndConsole("AgentBridge", "debug", $"自动更新上下文已启用，当前上下文: {currentContext.name}");
            UpdateContext();
        }
        else
        {
            if (currentContext == null)
            {
                LogToTextAndConsole("AgentBridge", "warning", "当前上下文为空");
            }
            if (!autoUpdateContext)
            {
                LogToTextAndConsole("AgentBridge", "debug", "自动更新上下文已禁用");
            }
        }
    }

    // 向前端注册Unity实例
    public void RegisterToJS()
    {
        LogToTextAndConsole("AgentBridge", "debug", "开始注册Unity实例到前端");
        
        if (Application.platform == RuntimePlatform.WebGLPlayer)
        {
            try
            {
                RegisterUnityInstance();
                LogToTextAndConsole("AgentBridge", "debug", "注册Unity实例到前端成功");
            }
            catch (Exception e)
            {
                LogToTextAndConsole("AgentBridge", "error", $"注册Unity实例到前端失败: {e.Message}");
            }
        }
        else
        {
            LogToTextAndConsole("AgentBridge", "debug", "非WebGL环境，跳过注册");
        }
    }

    // 接收前端的函数调用
    public void OnFunctionCall(string functionCallJson)
    {
        LogToTextAndConsole("AgentBridge", "debug", $"接收前端的函数调用: {functionCallJson}");
        try
        {
            if (functionCallOutputText != null)
            {
                functionCallOutputText.text += functionCallJson + "\n\n";
                LogToTextAndConsole("AgentBridge", "debug", "函数调用原始JSON数据已累积追加到Text对象");
            }
            
            if (currentContext == null)
            {
                LogToTextAndConsole("AgentBridge", "error", "当前上下文为null，无法处理函数调用");
                return;
            }
            
            if (currentContext.functionDefinition == null)
            {
                LogToTextAndConsole("AgentBridge", "error", "函数定义组件为null，无法处理函数调用");
                return;
            }
            
            LogToTextAndConsole("AgentBridge", "debug", "转发函数调用给函数定义组件处理");
            currentContext.functionDefinition.HandleFunctionCall(functionCallJson);
            LogToTextAndConsole("AgentBridge", "debug", "函数调用转发成功");
        }
        catch (Exception e)
        {
            LogToTextAndConsole("AgentBridge", "error", $"处理函数调用错误: {e.Message}");
        }
    }

    // 向前端发送上下文更新
    public void UpdateContext()
    {
        LogToTextAndConsole("AgentBridge", "debug", $"UpdateContext被调用，hasCachedContext: {hasCachedContext}");
        
        if (currentContext != null)
        {
            LogToTextAndConsole("AgentBridge", "debug", $"当前上下文: {currentContext.name}");
            
            try
            {
                string currentSceneDesc = currentContext.GetMergedSceneDescription();
                string currentRoleDesc = currentContext.roleDescription;
                string currentResponseReq = currentContext.responseRequirements;
                
                var functionDef = currentContext.enableFunctionCalling ? currentContext.functionDefinition : null;
                List<object> currentFunctionList = new List<object>();
                int currentFunctionCount = 0;
                if (functionDef != null)
                {
                    currentFunctionList = functionDef.GetAllFunctions();
                    currentFunctionCount = currentFunctionList.Count;
                }
                
                LogToTextAndConsole("AgentBridge", "debug", $"当前上下文 - 场景描述: {(currentSceneDesc != null ? "有值" : "null")}, 角色描述: {(currentRoleDesc != null ? "有值" : "null")}, 响应要求: {(currentResponseReq != null ? "有值" : "null")}, 函数数量: {currentFunctionCount}");
                
                if (!hasCachedContext)
                {
                    LogToTextAndConsole("AgentBridge", "debug", "第一次更新，直接全量更新");
                    string fullContextJson = CommonUtils.SerializeToJson(new Dictionary<string, object>
                    {
                        { "sceneDescription", currentSceneDesc },
                        { "roleDescription", currentRoleDesc },
                        { "responseRequirements", currentResponseReq },
                        { "functionCalling", currentFunctionList }
                    });
                    
                    if (Application.platform == RuntimePlatform.WebGLPlayer)
                    {
                        try
                        {
                            LogToTextAndConsole("AgentBridge", "debug", $"发送全量更新: {fullContextJson.Substring(0, Math.Min(100, fullContextJson.Length))}...");
                            UpdateContextFromUnity(fullContextJson);
                            LogToTextAndConsole("AgentBridge", "debug", "全量更新发送成功");
                        }
                        catch (Exception e)
                        {
                            LogToTextAndConsole("AgentBridge", "error", $"发送全量更新失败: {e.Message}");
                        }
                    }
                    else
                    {
                        LogToTextAndConsole("AgentBridge", "debug", $"非WebGL环境，模拟发送全量更新: {fullContextJson.Substring(0, Math.Min(100, fullContextJson.Length))}...");
                    }
                    
                    cachedSceneDescription = currentSceneDesc;
                    cachedRoleDescription = currentRoleDesc;
                    cachedResponseRequirements = currentResponseReq;
                    cachedFunctionCount = currentFunctionCount;
                    hasCachedContext = true;
                    LogToTextAndConsole("AgentBridge", "debug", $"已缓存全量上下文，hasCachedContext设置为: {hasCachedContext}");
                    LogToTextAndConsole("AgentBridge", "debug", $"缓存内容 - 场景描述: {(cachedSceneDescription != null ? "有值" : "null")}, 角色描述: {(cachedRoleDescription != null ? "有值" : "null")}, 响应要求: {(cachedResponseRequirements != null ? "有值" : "null")}, 函数数量: {cachedFunctionCount}");
                }
                else
                {
                    LogToTextAndConsole("AgentBridge", "debug", "再次更新，进行差异比较");
                    LogToTextAndConsole("AgentBridge", "debug", $"缓存内容 - 场景描述: {(cachedSceneDescription != null ? "有值" : "null")}, 角色描述: {(cachedRoleDescription != null ? "有值" : "null")}, 响应要求: {(cachedResponseRequirements != null ? "有值" : "null")}, 函数数量: {cachedFunctionCount}");
                    
                    bool sceneChanged = cachedSceneDescription != currentSceneDesc;
                    bool roleChanged = cachedRoleDescription != currentRoleDesc;
                    bool responseChanged = cachedResponseRequirements != currentResponseReq;
                    bool functionsChanged = cachedFunctionCount != currentFunctionCount;
                    
                    LogToTextAndConsole("AgentBridge", "debug", $"字段比较结果 - 场景描述: {(sceneChanged ? "改变" : "未变")}, 角色描述: {(roleChanged ? "改变" : "未变")}, 响应要求: {(responseChanged ? "改变" : "未变")}, 函数调用: {(functionsChanged ? "改变" : "未变")}");
                    
                    if (!sceneChanged && !roleChanged && !responseChanged && !functionsChanged)
                    {
                        LogToTextAndConsole("AgentBridge", "debug", "上下文完全相同，不做任何操作");
                        return;
                    }
                    
                    Dictionary<string, object> delta = new Dictionary<string, object>();
                    
                    if (sceneChanged)
                    {
                        delta["sceneDescription"] = currentSceneDesc;
                    }
                    
                    if (roleChanged)
                    {
                        delta["roleDescription"] = currentRoleDesc;
                    }
                    
                    if (responseChanged)
                    {
                        delta["responseRequirements"] = currentResponseReq;
                    }
                    
                    if (functionsChanged)
                    {
                        delta["functionCalling"] = currentFunctionList;
                    }
                    
                    string deltaJson = CommonUtils.SerializeToJson(delta);
                    
                    if (Application.platform == RuntimePlatform.WebGLPlayer)
                    {
                        try
                        {
                            LogToTextAndConsole("AgentBridge", "debug", $"发送差异更新: {deltaJson}");
                            UpdateContextFromUnity(deltaJson);
                            LogToTextAndConsole("AgentBridge", "debug", "差异更新发送成功");
                        }
                        catch (Exception e)
                        {
                            LogToTextAndConsole("AgentBridge", "error", $"发送差异更新失败: {e.Message}");
                        }
                    }
                    else
                    {
                        LogToTextAndConsole("AgentBridge", "debug", $"非WebGL环境，模拟发送差异更新: {deltaJson}");
                    }
                    
                    cachedSceneDescription = currentSceneDesc;
                    cachedRoleDescription = currentRoleDesc;
                    cachedResponseRequirements = currentResponseReq;
                    cachedFunctionCount = currentFunctionCount;
                    LogToTextAndConsole("AgentBridge", "debug", "已更新缓存上下文");
                    LogToTextAndConsole("AgentBridge", "debug", $"新缓存内容 - 场景描述: {(cachedSceneDescription != null ? "有值" : "null")}, 角色描述: {(cachedRoleDescription != null ? "有值" : "null")}, 响应要求: {(cachedResponseRequirements != null ? "有值" : "null")}, 函数数量: {cachedFunctionCount}");
                }
            }
            catch (System.Exception e)
            {
                LogToTextAndConsole("AgentBridge", "error", $"发送上下文更新失败: {e.Message}");
                LogToTextAndConsole("AgentBridge", "error", $"异常堆栈: {e.StackTrace}");
            }
        }
        else
        {
            LogToTextAndConsole("AgentBridge", "error", "当前上下文为null，无法发送更新");
        }
    }

    // 向前端回传函数执行结果
    public void NotifyFunctionExecuteResult(string resultJson)
    {
        LogToTextAndConsole("AgentBridge", "debug", $"回传函数执行结果: {resultJson}");
        
        if (Application.platform == RuntimePlatform.WebGLPlayer)
        {
            try
            {
                NotifyFunctionResultFromUnity(resultJson);
                LogToTextAndConsole("AgentBridge", "debug", "函数执行结果回传成功");
            }
            catch (Exception e)
            {
                LogToTextAndConsole("AgentBridge", "error", $"回传函数执行结果失败: {e.Message}");
            }
        }
        else
        {
            LogToTextAndConsole("AgentBridge", "debug", $"非WebGL环境，模拟回传函数执行结果: {resultJson}");
        }
    }
    
    public void ForwardUserMessage(string message)
    {
        LogToTextAndConsole("AgentBridge", "debug", $"转发用户消息: {message}");
        
        if (Application.platform == RuntimePlatform.WebGLPlayer)
        {
            try
            {
                ForwardUserMessageFromUnity(message);
                LogToTextAndConsole("AgentBridge", "debug", "用户消息转发成功");
            }
            catch (Exception e)
            {
                LogToTextAndConsole("AgentBridge", "error", $"转发用户消息失败: {e.Message}");
            }
        }
        else
        {
            LogToTextAndConsole("AgentBridge", "debug", $"非WebGL环境，模拟转发用户消息: {message}");
        }
    }
    
    public void SwitchContext(AgentContext newContext)
    {
        LogToTextAndConsole("AgentBridge", "debug", $"SwitchContext被调用，切换到: {newContext?.name}");
        currentContext = newContext;
    }
    
    public void SendUserMessage(string message)
    {
        LogToTextAndConsole("AgentBridge", "debug", $"SendUserMessage被调用: {message}");
        ForwardUserMessage(message);
    }
    

}