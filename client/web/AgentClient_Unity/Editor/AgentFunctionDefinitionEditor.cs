#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using System.Reflection;
using System.Collections.Generic;

[CustomPropertyDrawer(typeof(FunctionDefinition))]
public class FunctionDefinitionDrawer : PropertyDrawer
{
    // 使用字典来存储每个属性的展开状态，避免多个属性共享同一个状态
    private static Dictionary<string, bool> expandedStates = new Dictionary<string, bool>();
    
    // 使用字典来存储每个属性的搜索关键词
    private static Dictionary<string, string> searchKeywords = new Dictionary<string, string>();

    private bool IsExpanded(string key)
    {
        if (!expandedStates.ContainsKey(key))
        {
            expandedStates[key] = true;
        }
        return expandedStates[key];
    }

    private void SetExpanded(string key, bool value)
    {
        expandedStates[key] = value;
    }

    private string GetSearchKeyword(string key)
    {
        if (!searchKeywords.ContainsKey(key))
        {
            searchKeywords[key] = "";
        }
        return searchKeywords[key];
    }

    private void SetSearchKeyword(string key, string value)
    {
        searchKeywords[key] = value;
    }

    // 根据搜索关键词过滤方法列表
    private List<string> FilterMethodNames(List<string> methodNames, string keyword)
    {
        if (string.IsNullOrEmpty(keyword))
        {
            return methodNames;
        }

        List<string> filteredNames = new List<string>();
        foreach (string methodName in methodNames)
        {
            if (methodName.ToLower().Contains(keyword.ToLower()))
            {
                filteredNames.Add(methodName);
            }
        }
        return filteredNames;
    }

    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        EditorGUI.BeginProperty(position, label, property);

        // 使用属性路径作为唯一键
        string propertyPath = property.propertyPath;

        // 计算行高和间距
        float lineHeight = EditorGUIUtility.singleLineHeight;
        float spacing = EditorGUIUtility.standardVerticalSpacing;

        // 绘制展开/折叠按钮
        Rect foldoutRect = new Rect(position.x, position.y, position.width, lineHeight);
        bool expanded = IsExpanded(propertyPath);
        expanded = EditorGUI.Foldout(foldoutRect, expanded, new GUIContent("函数: " + property.FindPropertyRelative("functionName").stringValue), true);
        SetExpanded(propertyPath, expanded);

        if (expanded)
        {
            // 缩进
            position.x += 15;
            position.width -= 15;

            // 绘制函数名称
            Rect nameRect = new Rect(position.x, position.y + lineHeight + spacing, position.width, lineHeight);
            EditorGUI.PropertyField(nameRect, property.FindPropertyRelative("functionName"), new GUIContent("名称"));

            // 绘制函数描述
            Rect descRect = new Rect(position.x, position.y + 2 * (lineHeight + spacing), position.width, lineHeight);
            EditorGUI.PropertyField(descRect, property.FindPropertyRelative("functionDescription"), new GUIContent("描述"));

            // 绘制目标物体
            Rect targetObjRect = new Rect(position.x, position.y + 3 * (lineHeight + spacing), position.width, lineHeight);
            EditorGUI.PropertyField(targetObjRect, property.FindPropertyRelative("targetObject"), new GUIContent("目标物体"));

            // 获取目标物体
            SerializedProperty targetObjProp = property.FindPropertyRelative("targetObject");
            GameObject targetObj = targetObjProp.objectReferenceValue as GameObject;

            // 绘制目标方法
            Rect methodRect = new Rect(position.x, position.y + 4 * (lineHeight + spacing), position.width, lineHeight);
            SerializedProperty methodNameProp = property.FindPropertyRelative("targetMethodName");

            if (targetObj != null)
            {
                // 获取目标物体上的所有公共方法
                List<string> methodNames = GetPublicMethodNames(targetObj);

                if (methodNames.Count > 0)
                {
                    // 获取当前属性的搜索关键词
                    string searchPropertyPath = property.propertyPath;
                    string searchKeyword = GetSearchKeyword(searchPropertyPath);
                    
                    // 过滤方法列表
                    List<string> filteredMethodNames = FilterMethodNames(methodNames, searchKeyword);
                    
                    // 计算当前选择的索引（通过方法名匹配）
                    int selectedIndex = 0;
                    string currentMethodName = methodNameProp.stringValue;
                    if (!string.IsNullOrEmpty(currentMethodName))
                    {
                        for (int i = 0; i < filteredMethodNames.Count; i++)
                        {
                            string methodSignature = filteredMethodNames[i];
                            int openParenIndex = methodSignature.IndexOf('(');
                            string methodNameInSignature = openParenIndex > 0 ? methodSignature.Substring(0, openParenIndex) : methodSignature;
                            
                            if (methodNameInSignature == currentMethodName)
                            {
                                selectedIndex = i;
                                break;
                            }
                        }
                    }
                    
                    // 绘制搜索框
                    Rect searchRect = new Rect(position.x, position.y + 4 * (lineHeight + spacing), position.width, lineHeight);
                    string newSearchKeyword = EditorGUI.TextField(searchRect, "搜索方法", searchKeyword);
                    if (newSearchKeyword != searchKeyword)
                    {
                        SetSearchKeyword(searchPropertyPath, newSearchKeyword);
                    }
                    
                    // 绘制方法选择下拉框
                    Rect popupRect = new Rect(position.x, position.y + 5 * (lineHeight + spacing), position.width, lineHeight);
                    int newSelectedIndex = EditorGUI.Popup(popupRect, "目标方法", selectedIndex, filteredMethodNames.ToArray());
                    
                    // 检查是否需要更新方法（当选择了不同的方法，或者搜索结果只有一个且与当前选择不同）
                    if ((newSelectedIndex != selectedIndex || filteredMethodNames.Count == 1) && filteredMethodNames.Count > 0)
                    {
                        string selectedMethodSignature = filteredMethodNames[newSelectedIndex];
                        
                        // 解析方法名（不包含参数部分）
                        int openParenIndex = selectedMethodSignature.IndexOf('(');
                        string methodNameOnly = openParenIndex > 0 ? selectedMethodSignature.Substring(0, openParenIndex) : selectedMethodSignature;
                        
                        // 检查方法名是否已更改
                        if (methodNameOnly != methodNameProp.stringValue)
                        {
                            // 只存储方法名到targetMethodName字段
                            methodNameProp.stringValue = methodNameOnly;
                            
                            // 解析方法签名，自动创建参数列表
                            CreateParametersFromMethodSignature(property, selectedMethodSignature, targetObj);
                            
                            // 应用修改
                            property.serializedObject.ApplyModifiedProperties();
                        }
                    }
                }
                else
                {
                    EditorGUI.PropertyField(methodRect, methodNameProp, new GUIContent("目标方法"));
                }
            }
            else
            {
                EditorGUI.PropertyField(methodRect, methodNameProp, new GUIContent("目标方法"));
            }

            // 绘制参数列表
            Rect paramsRect = new Rect(position.x, position.y + 6 * (lineHeight + spacing), position.width, lineHeight);
            EditorGUI.PropertyField(paramsRect, property.FindPropertyRelative("parameters"), new GUIContent("参数列表"), true);
        }

        EditorGUI.EndProperty();
    }

    public override float GetPropertyHeight(SerializedProperty property, GUIContent label)
    {
        float lineHeight = EditorGUIUtility.singleLineHeight;
        float spacing = EditorGUIUtility.standardVerticalSpacing;

        // 使用属性路径作为唯一键
        string propertyPath = property.propertyPath;
        bool expanded = IsExpanded(propertyPath);

        if (expanded)
        {
            // 基础属性高度（包括搜索框）
            float baseHeight = 6 * (lineHeight + spacing);

            // 参数列表高度
            SerializedProperty paramsProp = property.FindPropertyRelative("parameters");
            float paramsHeight = EditorGUI.GetPropertyHeight(paramsProp, true);

            return baseHeight + paramsHeight;
        }
        else
        {
            return lineHeight;
        }
    }

    // 获取目标物体上的所有公共方法名称
    private List<string> GetPublicMethodNames(GameObject targetObj)
    {
        List<string> methodNames = new List<string>();

        if (targetObj == null)
            return methodNames;

        // 获取物体上的所有组件
        Component[] components = targetObj.GetComponents<Component>();

        foreach (Component component in components)
        {
            if (component == null)
                continue;

            // 获取组件的所有公共方法
            MethodInfo[] methods = component.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static);

            foreach (MethodInfo method in methods)
            {
                // 排除继承自Object的方法
                if (method.DeclaringType != typeof(Object) && 
                    method.DeclaringType != typeof(Component) && 
                    method.DeclaringType != typeof(MonoBehaviour))
                {
                    string methodSignature = method.Name + "(";
                    ParameterInfo[] parameters = method.GetParameters();

                    for (int i = 0; i < parameters.Length; i++)
                    {
                        methodSignature += parameters[i].ParameterType.Name + " " + parameters[i].Name;
                        if (i < parameters.Length - 1)
                            methodSignature += ", ";
                    }

                    methodSignature += ")";
                    methodNames.Add(methodSignature);
                }
            }
        }

        return methodNames;
    }

    // 根据方法签名创建参数列表
    private void CreateParametersFromMethodSignature(SerializedProperty functionProp, string methodSignature, GameObject targetObj)
    {
        // 解析方法名和参数
        int openParenIndex = methodSignature.IndexOf('(');
        if (openParenIndex == -1)
            return;

        string methodName = methodSignature.Substring(0, openParenIndex);
        string paramsString = methodSignature.Substring(openParenIndex + 1, methodSignature.Length - openParenIndex - 2);
        
        // 自动填写函数名称，默认与方法名一致
        SerializedProperty functionNameProp = functionProp.FindPropertyRelative("functionName");
        if (string.IsNullOrEmpty(functionNameProp.stringValue))
        {
            functionNameProp.stringValue = methodName;
        }
        
        // 自动填写函数描述，默认描述为执行该方法
        SerializedProperty functionDescProp = functionProp.FindPropertyRelative("functionDescription");
        if (string.IsNullOrEmpty(functionDescProp.stringValue))
        {
            functionDescProp.stringValue = $"执行{methodName}方法";
        }

        // 查找对应的MethodInfo
        MethodInfo targetMethod = null;
        Component[] components = targetObj.GetComponents<Component>();

        foreach (Component component in components)
        {
            if (component == null)
                continue;

            MethodInfo[] methods = component.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static);
            foreach (MethodInfo method in methods)
            {
                if (method.Name == methodName)
                {
                    // 验证参数数量是否匹配
                    ParameterInfo[] parameters = method.GetParameters();
                    string[] paramTokens = paramsString.Split(new string[] { ", " }, System.StringSplitOptions.RemoveEmptyEntries);
                    
                    if (parameters.Length == paramTokens.Length)
                    {
                        targetMethod = method;
                        break;
                    }
                }
            }
            
            if (targetMethod != null)
                break;
        }

        if (targetMethod == null)
            return;

        // 获取参数列表属性
        SerializedProperty parametersProp = functionProp.FindPropertyRelative("parameters");
        parametersProp.ClearArray();

        // 根据MethodInfo创建参数列表
        ParameterInfo[] methodParams = targetMethod.GetParameters();
        for (int i = 0; i < methodParams.Length; i++)
        {
            ParameterInfo param = methodParams[i];
            
            // 添加新参数
            parametersProp.InsertArrayElementAtIndex(i);
            SerializedProperty paramProp = parametersProp.GetArrayElementAtIndex(i);
            
            // 设置参数名称
            paramProp.FindPropertyRelative("name").stringValue = param.Name;
            
            // 设置参数类型
            ParameterType paramType = ParameterType.String; // 默认类型
            if (param.ParameterType == typeof(int) || param.ParameterType == typeof(long) || param.ParameterType == typeof(short))
                paramType = ParameterType.Integer;
            else if (param.ParameterType == typeof(float) || param.ParameterType == typeof(double) || param.ParameterType == typeof(decimal))
                paramType = ParameterType.Number;
            else if (param.ParameterType == typeof(bool))
                paramType = ParameterType.Boolean;
            else if (param.ParameterType.IsArray)
                paramType = ParameterType.Array;
            else if (param.ParameterType.IsClass || param.ParameterType.IsValueType)
                paramType = ParameterType.Object;
            
            paramProp.FindPropertyRelative("type").enumValueIndex = (int)paramType;
            
            // 设置参数描述
            paramProp.FindPropertyRelative("description").stringValue = param.ParameterType.Name + "类型参数";
            
            // 设置必需性（所有参数默认为必需）
            paramProp.FindPropertyRelative("required").boolValue = true;
        }
    }
}

[CustomPropertyDrawer(typeof(FunctionParameter))]
public class FunctionParameterDrawer : PropertyDrawer
{
    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        EditorGUI.BeginProperty(position, label, property);

        // 计算行高和间距
        float lineHeight = EditorGUIUtility.singleLineHeight;
        float spacing = EditorGUIUtility.standardVerticalSpacing;

        // 绘制参数名称
        Rect nameRect = new Rect(position.x, position.y, position.width, lineHeight);
        EditorGUI.PropertyField(nameRect, property.FindPropertyRelative("name"), new GUIContent("名称"));

        // 绘制参数描述（另起一行）
        Rect descRect = new Rect(position.x, position.y + lineHeight + spacing, position.width, lineHeight);
        EditorGUI.PropertyField(descRect, property.FindPropertyRelative("description"), new GUIContent("描述"));

        // 绘制参数类型和必需性
        Rect typeRect = new Rect(position.x, position.y + 2 * (lineHeight + spacing), position.width / 2 - spacing / 2, lineHeight);
        EditorGUI.PropertyField(typeRect, property.FindPropertyRelative("type"), new GUIContent("类型"));

        Rect requiredRect = new Rect(position.x + position.width / 2 + spacing / 2, position.y + 2 * (lineHeight + spacing), position.width / 2 - spacing / 2, lineHeight);
        EditorGUI.PropertyField(requiredRect, property.FindPropertyRelative("required"), new GUIContent("是否必需"));

        // 绘制数值范围（仅对数字类型）
        SerializedProperty typeProp = property.FindPropertyRelative("type");
        ParameterType paramType = (ParameterType)typeProp.enumValueIndex;

        if (paramType == ParameterType.Number || paramType == ParameterType.Integer)
        {
            Rect minRect = new Rect(position.x, position.y + 3 * (lineHeight + spacing), position.width / 2 - spacing / 2, lineHeight);
            EditorGUI.PropertyField(minRect, property.FindPropertyRelative("min"), new GUIContent("最小值"));

            Rect maxRect = new Rect(position.x + position.width / 2 + spacing / 2, position.y + 3 * (lineHeight + spacing), position.width / 2 - spacing / 2, lineHeight);
            EditorGUI.PropertyField(maxRect, property.FindPropertyRelative("max"), new GUIContent("最大值"));
        }

        // 绘制枚举选项
        int enumRectOffset = (paramType == ParameterType.Number || paramType == ParameterType.Integer) ? 4 : 3;
        Rect enumRect = new Rect(position.x, position.y + enumRectOffset * (lineHeight + spacing), position.width, lineHeight);
        EditorGUI.PropertyField(enumRect, property.FindPropertyRelative("enumOptions"), new GUIContent("枚举选项（逗号分隔）"));

        EditorGUI.EndProperty();
    }

    public override float GetPropertyHeight(SerializedProperty property, GUIContent label)
    {
        float lineHeight = EditorGUIUtility.singleLineHeight;
        float spacing = EditorGUIUtility.standardVerticalSpacing;

        // 基础属性高度（名称、描述、类型+必需性）
        float baseHeight = 3 * (lineHeight + spacing);

        // 检查是否需要数值范围
        SerializedProperty typeProp = property.FindPropertyRelative("type");
        ParameterType paramType = (ParameterType)typeProp.enumValueIndex;

        if (paramType == ParameterType.Number || paramType == ParameterType.Integer)
        {
            baseHeight += lineHeight + spacing;
        }

        // 添加枚举选项行
        baseHeight += lineHeight + spacing;

        return baseHeight;
    }
}

[CustomEditor(typeof(AgentFunctionDefinition))]
public class AgentFunctionDefinitionEditor : Editor
{
    // 用于存储生成的OpenAI格式数据
    private string openAIFormatPreview = "";

    // JSON格式化方法
    private string FormatJson(string json)
    {
        try
        {
            // 简单的JSON格式化实现
            int indentLevel = 0;
            bool inQuotes = false;
            System.Text.StringBuilder sb = new System.Text.StringBuilder();

            foreach (char c in json)
            {
                switch (c)
                {
                    case '{':
                    case '[':
                        sb.Append(c);
                        if (!inQuotes)
                        {
                            sb.AppendLine();
                            indentLevel++;
                            sb.Append(new string(' ', indentLevel * 4));
                        }
                        break;
                    case '}':
                    case ']':
                        if (!inQuotes)
                        {
                            sb.AppendLine();
                            indentLevel--;
                            sb.Append(new string(' ', indentLevel * 4));
                        }
                        sb.Append(c);
                        break;
                    case ',':
                        sb.Append(c);
                        if (!inQuotes)
                        {
                            sb.AppendLine();
                            sb.Append(new string(' ', indentLevel * 4));
                        }
                        break;
                    case ':':
                        sb.Append(c);
                        if (!inQuotes)
                        {
                            sb.Append(' ');
                        }
                        break;
                    case '"':
                        sb.Append(c);
                        inQuotes = !inQuotes;
                        break;
                    default:
                        sb.Append(c);
                        break;
                }
            }

            return sb.ToString();
        }
        catch
        {
            // 如果解析失败，返回原始JSON
            return json;
        }
    }

    public override void OnInspectorGUI()
    {
        base.OnInspectorGUI();

        AgentFunctionDefinition component = (AgentFunctionDefinition)target;

        // 添加验证按钮
        if (GUILayout.Button("验证所有函数定义"))
        {
            ValidateFunctions(component);
        }

        // 添加按钮行
        GUILayout.BeginHorizontal();
        
        // 添加生成OpenAI格式预览按钮
        if (GUILayout.Button("生成OpenAI格式预览", GUILayout.ExpandWidth(false)))
        {
            string rawJson = component.GetAllOpenAIFunctionsJsonStr();
            openAIFormatPreview = FormatJson(rawJson);
            Debug.Log("OpenAI Function Calling格式预览:\n" + openAIFormatPreview);
        }
        
        // 添加清空按钮
        if (GUILayout.Button("清空", GUILayout.ExpandWidth(false)))
        {
            openAIFormatPreview = "";
        }
        
        // 添加复制按钮
        if (GUILayout.Button("复制", GUILayout.ExpandWidth(false)))
        {
            if (!string.IsNullOrEmpty(openAIFormatPreview))
            {
                EditorGUIUtility.systemCopyBuffer = openAIFormatPreview;
                Debug.Log("OpenAI格式已复制到剪切板");
            }
        }
        
        GUILayout.EndHorizontal();

        // 添加文本显示框，显示生成的OpenAI格式数据
        GUILayout.Space(10);
        GUILayout.Label("OpenAI Function Calling格式预览:");
        // 计算文本框高度，根据内容长度自适应
        int lineCount = Mathf.Max(5, openAIFormatPreview.Split('\n').Length);
        float textAreaHeight = lineCount * 16f; // 每行大约16像素
        openAIFormatPreview = GUILayout.TextArea(openAIFormatPreview, GUILayout.Height(textAreaHeight));
        GUILayout.Space(10);
    }

    // 验证所有函数定义
    private void ValidateFunctions(AgentFunctionDefinition component)
    {
        int validCount = 0;
        int invalidCount = 0;

        foreach (FunctionDefinition func in component.functions)
        {
            if (func != null)
            {
                bool isValid = func.Initialize();
                if (isValid)
                    validCount++;
                else
                    invalidCount++;
            }
        }

        Debug.Log($"函数定义验证完成: 有效={validCount}, 无效={invalidCount}");
    }
}
#endif