#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(AgentContext))]
public class AgentContextEditor : Editor
{
    public override void OnInspectorGUI()
    {
        AgentContext context = (AgentContext)target;
        
        // 绘制场景信息字段
        EditorGUILayout.PropertyField(serializedObject.FindProperty("sceneDescription"));
        EditorGUILayout.PropertyField(serializedObject.FindProperty("roleDescription"));
        EditorGUILayout.PropertyField(serializedObject.FindProperty("responseRequirements"));
        
        // 绘制enableFunctionCalling字段
        EditorGUILayout.PropertyField(serializedObject.FindProperty("enableFunctionCalling"));
        
        // 只有当enableFunctionCalling为true时，才显示functionDefinition字段
        if (context.enableFunctionCalling)
        {
            EditorGUILayout.PropertyField(serializedObject.FindProperty("functionDefinition"));
        }
        
        // 应用修改
        serializedObject.ApplyModifiedProperties();
    }
}
#endif