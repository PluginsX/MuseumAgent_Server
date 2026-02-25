using UnityEngine;
using Museum.Debug;

public class Test_FunctionCalling : MonoBehaviour
{
    [Header("=== 测试配置 ===")]
    public AgentFunctionDefinition functionDefinition;
    
    [Header("=== 函数调用数据 ===")]
    [TextArea(5, 10)]
    public string functionCallJson = "{\"name\":\"set_state\",\"parameters\":{\"enabled\":true,\"message\":\"测试消息\"}}";
    
    [Header("=== 测试操作 ===")]
    public bool autoTestOnStart = false;

    void Start()
    {
        if (autoTestOnStart)
        {
            SendFunctionCall();
        }
    }

    public void SendFunctionCall()
    {
        if (functionDefinition == null)
        {
            Log.Print("Test_FunctionCalling", "error", "请先设置 AgentFunctionDefinition 组件引用！");
            return;
        }

        if (string.IsNullOrEmpty(functionCallJson))
        {
            Log.Print("Test_FunctionCalling", "error", "函数调用数据不能为空！");
            return;
        }

        Log.Print("Test_FunctionCalling", "debug", $"发送函数调用数据: {functionCallJson}");

        try
        {
            functionDefinition.HandleFunctionCall(functionCallJson);
            Log.Print("Test_FunctionCalling", "debug", "函数调用发送成功");
        }
        catch (System.Exception e)
        {
            Log.Print("Test_FunctionCalling", "error", $"函数调用失败: {e.Message}");
        }
    }
}