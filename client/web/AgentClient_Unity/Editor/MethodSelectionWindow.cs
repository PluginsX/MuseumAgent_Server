#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using System.Collections.Generic;
using System.Reflection;

public class MethodSelectionWindow : PopupWindowContent
{
    private string searchKeyword = "";
    private List<string> methodNames;
    private List<string> filteredMethodNames;
    private System.Action<string> onMethodSelected;
    private Vector2 scrollPosition;
    private float maxMethodNameWidth;
    private GameObject targetObject;

    public static void Show(Rect buttonRect, GameObject target, System.Action<string> callback)
    {
        MethodSelectionWindow window = new MethodSelectionWindow();
        window.targetObject = target;
        window.onMethodSelected = callback;
        window.methodNames = window.GetPublicMethodNames(target);
        window.filteredMethodNames = new List<string>(window.methodNames);
        
        // 计算最宽的方法名宽度
        window.CalculateMaxMethodNameWidth();

        PopupWindow.Show(buttonRect, window);
    }

    private List<string> GetPublicMethodNames(GameObject target)
    {
        List<string> methodNames = new List<string>();
        if (target == null) return methodNames;

        Component[] components = target.GetComponents<Component>();
        foreach (Component component in components)
        {
            if (component == null) continue;

            MethodInfo[] methods = component.GetType().GetMethods(
                BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static
            );

            foreach (MethodInfo method in methods)
            {
                // 跳过继承的Unity内置方法
                if (method.DeclaringType == typeof(MonoBehaviour) || 
                    method.DeclaringType == typeof(Component) || 
                    method.DeclaringType == typeof(Object))
                {
                    continue;
                }

                // 构建方法签名字符串
                string methodSignature = method.Name + "(";
                ParameterInfo[] parameters = method.GetParameters();
                for (int i = 0; i < parameters.Length; i++)
                {
                    ParameterInfo param = parameters[i];
                    methodSignature += param.ParameterType.Name + " " + param.Name;
                    if (i < parameters.Length - 1)
                    {
                        methodSignature += ", ";
                    }
                }
                methodSignature += ")";
                methodNames.Add(methodSignature);
            }
        }

        return methodNames;
    }

    // 计算最宽的方法名宽度
    private void CalculateMaxMethodNameWidth()
    {
        maxMethodNameWidth = 300; // 默认最小宽度
        GUIStyle buttonStyle = new GUIStyle(GUI.skin.button);
        
        if (methodNames != null)
        {
            foreach (string methodSignature in methodNames)
            {
                float width = buttonStyle.CalcSize(new GUIContent(methodSignature)).x;
                if (width > maxMethodNameWidth)
                {
                    maxMethodNameWidth = width;
                }
            }
        }
        
        // 添加一些边距
        maxMethodNameWidth += 40;
        // 限制最大宽度
        maxMethodNameWidth = Mathf.Min(maxMethodNameWidth, 600);
    }

    public override Vector2 GetWindowSize()
    {
        return new Vector2(maxMethodNameWidth, 300);
    }

    public override void OnGUI(Rect rect)
    {
        GUILayout.BeginVertical();
        GUILayout.Label("选择方法", EditorStyles.boldLabel);

        // 搜索框
        GUILayout.BeginHorizontal();
        GUILayout.Label("搜索:", GUILayout.Width(50));
        string newSearchKeyword = GUILayout.TextField(searchKeyword);
        if (newSearchKeyword != searchKeyword)
        {
            searchKeyword = newSearchKeyword;
            FilterMethods();
        }
        GUILayout.EndHorizontal();

        // 创建左对齐的按钮样式
        GUIStyle leftAlignedButtonStyle = new GUIStyle(GUI.skin.button);
        leftAlignedButtonStyle.alignment = TextAnchor.MiddleLeft;

        // 方法列表
        scrollPosition = GUILayout.BeginScrollView(scrollPosition);
        foreach (string methodSignature in filteredMethodNames)
        {
            if (GUILayout.Button(methodSignature, leftAlignedButtonStyle))
            {
                // 提取方法名（不包含参数部分）
                int openParenIndex = methodSignature.IndexOf('(');
                string methodNameOnly = openParenIndex > 0 ? methodSignature.Substring(0, openParenIndex) : methodSignature;
                onMethodSelected?.Invoke(methodNameOnly);
                editorWindow.Close();
            }
        }
        GUILayout.EndScrollView();

        // 无方法提示
        if (filteredMethodNames.Count == 0)
        {
            GUILayout.Label("未找到匹配的方法", EditorStyles.centeredGreyMiniLabel);
        }

        GUILayout.EndVertical();
    }

    private void FilterMethods()
    {
        if (string.IsNullOrEmpty(searchKeyword))
        {
            filteredMethodNames = new List<string>(methodNames);
        }
        else
        {
            filteredMethodNames = new List<string>();
            foreach (string methodName in methodNames)
            {
                if (methodName.ToLower().Contains(searchKeyword.ToLower()))
                {
                    filteredMethodNames.Add(methodName);
                }
            }
        }
    }
}
#endif
