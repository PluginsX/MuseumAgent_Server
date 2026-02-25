#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(Test_FunctionCalling))]
public class Test_FunctionCallingEditor : Editor
{
    public override void OnInspectorGUI()
    {
        Test_FunctionCalling testScript = (Test_FunctionCalling)target;

        DrawDefaultInspector();

        EditorGUILayout.Space();
        EditorGUILayout.HelpBox("此组件用于测试函数调用功能，模拟前端发送函数调用数据。", MessageType.Info);

        EditorGUILayout.Space();

        if (GUILayout.Button("发送函数调用", GUILayout.Height(30)))
        {
            testScript.SendFunctionCall();
        }

        EditorGUILayout.Space();

        if (GUILayout.Button("重置为默认测试数据", GUILayout.Height(25)))
        {
            testScript.functionCallJson = "{\"name\":\"set_state\",\"parameters\":{\"enabled\":true,\"message\":\"测试消息\"}}";
            EditorUtility.SetDirty(target);
        }

        EditorGUILayout.Space();

        if (GUILayout.Button("生成测试函数调用示例", GUILayout.Height(25)))
        {
            ShowFunctionCallExamples(testScript);
        }
    }

    private void ShowFunctionCallExamples(Test_FunctionCalling testScript)
    {
        GenericMenu menu = new GenericMenu();

        menu.AddItem(new GUIContent("set_state (设置状态)"), false, () => 
        {
            testScript.functionCallJson = "{\"name\":\"set_state\",\"parameters\":{\"enabled\":true,\"message\":\"测试消息\"}}";
            EditorUtility.SetDirty(target);
        });

        menu.AddItem(new GUIContent("move_to (移动到位置)"), false, () => 
        {
            testScript.functionCallJson = "{\"name\":\"move_to\",\"parameters\":{\"position\":{\"x\":10.0,\"y\":0.0,\"z\":5.0}}}";
            EditorUtility.SetDirty(target);
        });

        menu.AddItem(new GUIContent("get_info (获取信息)"), false, () => 
        {
            testScript.functionCallJson = "{\"name\":\"get_info\",\"parameters\":{\"id\":123}}";
            EditorUtility.SetDirty(target);
        });

        menu.AddItem(new GUIContent("toggle_feature (切换功能)"), false, () => 
        {
            testScript.functionCallJson = "{\"name\":\"toggle_feature\",\"parameters\":{\"featureName\":\"auto_save\",\"enabled\":false}}";
            EditorUtility.SetDirty(target);
        });

        menu.ShowAsContext();
    }
}
#endif