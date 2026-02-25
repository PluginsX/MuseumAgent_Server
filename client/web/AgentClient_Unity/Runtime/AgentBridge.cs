using UnityEngine;
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Museum.Debug;

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
    
    [Header("=== 启动选项 ===")]
    public bool autoUpdateContext = true;
    
    [Header("=== 调试输出 ===")]
    public UnityEngine.UI.Text functionCallOutputText; // Text (Legacy) 对象，用于输出前端函数调用的原始JSON数据

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }
    
    void Start()
    {
        // 自动加载当前上下文
        if (currentContext != null && autoUpdateContext)
        {
            UpdateContext();
        }
    }

    // 向前端注册Unity实例
    public void RegisterToJS()
    {
        Log.Print("AgentBridge", "debug", $"向前端注册Unity实例: {gameObject.name}");
        try
        {
            RegisterUnityInstance();
            Log.Print("AgentBridge", "debug", "注册Unity实例到前端成功");
        }
        catch (Exception e)
        {
            Log.Print("AgentBridge", "error", $"注册Unity实例到前端失败: {e.Message}");
        }
    }

    // 接收前端的函数调用
    public void OnFunctionCall(string functionCallJson)
    {
        Log.Print("AgentBridge", "debug", $"接收前端的函数调用: {functionCallJson}");
        try
        {
            // 输出原始JSON数据到Text对象（累积追加）
            if (functionCallOutputText != null)
            {
                functionCallOutputText.text += functionCallJson + "\n\n";
                Log.Print("AgentBridge", "debug", "函数调用原始JSON数据已累积追加到Text对象");
            }
            
            // 检查当前上下文是否存在
            if (currentContext == null)
            {
                Log.Print("AgentBridge", "error", "当前上下文为null，无法处理函数调用");
                return;
            }
            
            // 检查函数定义组件是否存在
            if (currentContext.functionDefinition == null)
            {
                Log.Print("AgentBridge", "error", "函数定义组件为null，无法处理函数调用");
                return;
            }
            
            // 直接转发原始的函数调用JSON字符串给函数定义组件处理
            Log.Print("AgentBridge", "debug", "转发函数调用给函数定义组件处理");
            currentContext.functionDefinition.HandleFunctionCall(functionCallJson);
            Log.Print("AgentBridge", "debug", "函数调用转发成功");
        }
        catch (Exception e)
        {
            Log.Print("AgentBridge", "error", $"处理函数调用错误: {e.Message}");
        }
    }

    // 向前端发送上下文更新
    public void UpdateContext(string contextJson)
    {
        Log.Print("AgentBridge", "debug", $"向前端发送上下文更新: {contextJson}");
        try
        {
            UpdateContextFromUnity(contextJson);
            Log.Print("AgentBridge", "debug", "上下文更新发送成功");
        }
        catch (Exception e)
        {
            Log.Print("AgentBridge", "error", $"发送上下文更新失败: {e.Message}");
        }
    }
    
    // 向前端发送上下文更新（无参数重载版本），默认使用当前引用的上下文
    public void UpdateContext()
    {
        // 检查当前上下文是否存在且有效
        if (currentContext != null)
        {
            Log.Print("AgentBridge", "debug", "使用当前上下文向前端发送更新");
            try
            {
                // 直接调用当前上下文的BuildContextJson方法获取上下文JSON
                string contextJson = currentContext.BuildContextJson();
                if (!string.IsNullOrEmpty(contextJson))
                {
                    UpdateContextFromUnity(contextJson);
                    Log.Print("AgentBridge", "debug", "上下文更新发送成功");
                }
                else
                {
                    Log.Print("AgentBridge", "warn", "当前上下文构建的JSON为空，无法发送更新");
                }
            }
            catch (System.Exception e)
            {
                Log.Print("AgentBridge", "error", $"发送上下文更新失败: {e.Message}");
            }
        }
        else
        {
            Log.Print("AgentBridge", "error", "当前上下文为null，无法发送更新");
        }
    }

    // 向前端回传函数执行结果
    public void NotifyFunctionExecuteResult(string resultJson)
    {
        Log.Print("AgentBridge", "debug", $"向前端回传函数执行结果: {resultJson}");
        try
        {
            NotifyFunctionResultFromUnity(resultJson);
            Log.Print("AgentBridge", "debug", "函数执行结果回传成功");
        }
        catch (Exception e)
        {
            Log.Print("AgentBridge", "error", $"回传函数执行结果失败: {e.Message}");
        }
    }
    
    // 方法1：向前端转发用户消息(等同于用户发消息)
    public void ForwardUserMessage(string message)
    {
        Log.Print("AgentBridge", "debug", $"向前端转发用户消息: {message}");
        try
        {
            ForwardUserMessageFromUnity(message);
            Log.Print("AgentBridge", "debug", "用户消息转发成功");
        }
        catch (Exception e)
        {
            Log.Print("AgentBridge", "error", $"转发用户消息失败: {e.Message}");
        }
    }
    
    // 方法1：切换上下文组件(传入智能体上下文组件)
    public void SwitchContext(AgentContext newContext)
    {
        Log.Print("AgentBridge", "debug", $"切换上下文组件: {newContext?.name}");
        try
        {
            if (newContext != null)
            {
                Log.Print("AgentBridge", "debug", "激活新上下文");
                currentContext = newContext;
                // 使用新的无参数重载方法更新上下文
                UpdateContext();
                Log.Print("AgentBridge", "debug", $"上下文切换成功，当前上下文: {currentContext?.name}");
            }
            else
            {
                Log.Print("AgentBridge", "error", "新上下文为null，无法切换");
            }
        }
        catch (Exception e)
        {
            Log.Print("AgentBridge", "error", $"切换上下文失败: {e.Message}");
        }
    }
    

    
    // 方法2：发送用户消息
    public void SendUserMessage(string message)
    {
        Log.Print("AgentBridge", "debug", $"发送用户消息: {message}");
        try
        {
            ForwardUserMessage(message);
            Log.Print("AgentBridge", "debug", "用户消息发送成功");
        }
        catch (Exception e)
        {
            Log.Print("AgentBridge", "error", $"发送用户消息失败: {e.Message}");
        }
    }
}