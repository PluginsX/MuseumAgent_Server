#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using AgentClient.Runtime;

[CustomEditor(typeof(AgentContext))]
public class AgentContextEditor : Editor
{
    // 用于存储生成的上下文数据预览
    private string contextPreview = "";
    
    // 预览区域展开状态
    private bool previewExpanded = false;
    
    public override void OnInspectorGUI()
    {
        AgentContext context = (AgentContext)target;
        // 绘制自动注册相关字段
        EditorGUILayout.PropertyField(serializedObject.FindProperty("agentBridge"));
        EditorGUILayout.PropertyField(serializedObject.FindProperty("autoRegisterOnStart"));

        // 绘制角色描述字段
        EditorGUILayout.PropertyField(serializedObject.FindProperty("roleDescription"));
        // 绘制响应要求字段
        EditorGUILayout.PropertyField(serializedObject.FindProperty("responseRequirements"));
        // 绘制场景描述字段
        EditorGUILayout.PropertyField(serializedObject.FindProperty("sceneDescription"));
        // 补充描述列表编辑器
        SerializedProperty additionalDescProp = serializedObject.FindProperty("additionalDescriptions");
        EditorGUILayout.PropertyField(additionalDescProp, true);

        EditorGUILayout.Space();

        // 绘制enableFunctionCalling字段
        EditorGUILayout.PropertyField(serializedObject.FindProperty("enableFunctionCalling"));
        
        // 只有当enableFunctionCalling为true时，才显示functionDefinition字段
        if (context.enableFunctionCalling)
        {
            EditorGUILayout.PropertyField(serializedObject.FindProperty("functionDefinition"));
        }

        EditorGUILayout.Space();


        
        // 应用修改
        serializedObject.ApplyModifiedProperties();

        // 添加预览区域
        GUILayout.Space(10);
        


        // 按钮行
        GUILayout.BeginHorizontal();

        if (GUILayout.Button("上下文数据构建预览", GUILayout.ExpandWidth(false)))
        {
            // 获取关联的函数定义组件
            var functionDef = context.enableFunctionCalling ? context.functionDefinition : null;
            System.Collections.Generic.List<object> functionList = new System.Collections.Generic.List<object>();
            
            if (functionDef != null)
            {
                functionList = functionDef.GetAllFunctions();
            }

            // 构建合并后的场景描述
            string mergedSceneDescription = context.GetMergedSceneDescription();

            // 构建完整的上下文数据
            var contextData = new System.Collections.Generic.Dictionary<string, object>
            {
                { "sceneDescription", mergedSceneDescription },
                { "roleDescription", context.roleDescription },
                { "responseRequirements", context.responseRequirements },
                { "functionCalling", functionList },
                { "functions", functionList } // 兼容支持
            };
            
            contextPreview = CommonUtils.SerializeToFormattedJson(contextData);
            Debug.Log("上下文数据预览:\n" + contextPreview);
        }

        if (GUILayout.Button("清空", GUILayout.ExpandWidth(false)))
        {
            contextPreview = "";
        }

        GUI.enabled = !string.IsNullOrEmpty(contextPreview);
        if (GUILayout.Button("复制", GUILayout.ExpandWidth(false)))
        {
            EditorGUIUtility.systemCopyBuffer = contextPreview;
            Debug.Log("上下文数据已复制到剪切板");
        }
        GUI.enabled = true;

        GUILayout.EndHorizontal();
        // 可点击的折叠/展开标题
        if (GUILayout.Button($"{(previewExpanded ? "▼" : "▶")} 上下文数据构建预览", EditorStyles.boldLabel))
        {
            previewExpanded = !previewExpanded;
        }
        // 文本显示框（根据展开状态显示）
        if (previewExpanded)
        {
            int lineCount = Mathf.Max(5, contextPreview.Split('\n').Length);
            float textAreaHeight = lineCount * 16f;
            contextPreview = GUILayout.TextArea(contextPreview, GUILayout.Height(textAreaHeight));
        }
    }
}
#endif