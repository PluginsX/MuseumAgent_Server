using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.Text;

namespace MuseumAgent
{
    [CustomEditor(typeof(MuseumAgent_Client))]
    public class MuseumAgent_Client_Editor : Editor
    {
        private SerializedProperty serverBaseUrlProp;
        private SerializedProperty sessionRegisterEndpointProp;
        private SerializedProperty sessionHeartbeatEndpointProp;
        private SerializedProperty sessionUnregisterEndpointProp;
        private SerializedProperty agentParseEndpointProp;
        private SerializedProperty clientTypeProp;
        private SerializedProperty clientIdProp;
        private SerializedProperty platformProp;
        private SerializedProperty clientVersionProp;
        private SerializedProperty functionDefinitionsProp;
        private SerializedProperty heartbeatIntervalProp;
        private SerializedProperty autoStartHeartbeatProp;
        private SerializedProperty enableDebugLogProp;

        private bool showFunctionDefinitions = true;
        private Vector2 scrollPosition;

        private void OnEnable()
        {
            serverBaseUrlProp = serializedObject.FindProperty("serverBaseUrl");
            sessionRegisterEndpointProp = serializedObject.FindProperty("sessionRegisterEndpoint");
            sessionHeartbeatEndpointProp = serializedObject.FindProperty("sessionHeartbeatEndpoint");
            sessionUnregisterEndpointProp = serializedObject.FindProperty("sessionUnregisterEndpoint");
            agentParseEndpointProp = serializedObject.FindProperty("agentParseEndpoint");
            clientTypeProp = serializedObject.FindProperty("clientType");
            clientIdProp = serializedObject.FindProperty("clientId");
            platformProp = serializedObject.FindProperty("platform");
            clientVersionProp = serializedObject.FindProperty("clientVersion");
            functionDefinitionsProp = serializedObject.FindProperty("functionDefinitions");
            heartbeatIntervalProp = serializedObject.FindProperty("heartbeatInterval");
            autoStartHeartbeatProp = serializedObject.FindProperty("autoStartHeartbeat");
            enableDebugLogProp = serializedObject.FindProperty("enableDebugLog");
        }

        public override void OnInspectorGUI()
        {
            serializedObject.Update();

            MuseumAgent_Client client = (MuseumAgent_Client)target;

            EditorGUILayout.Space(10);
            EditorGUILayout.LabelField("MuseumAgent 客户端配置", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            DrawServerConfig();
            DrawClientInfo();
            DrawHeartbeatConfig();
            DrawFunctionDefinitions();
            DrawDebugConfig();
            DrawStatusInfo();
            DrawActionButtons();

            serializedObject.ApplyModifiedProperties();
        }

        private void DrawServerConfig()
        {
            EditorGUILayout.LabelField("服务器API配置", EditorStyles.boldLabel);
            EditorGUILayout.PropertyField(serverBaseUrlProp, new GUIContent("服务器基础URL", "服务器的基础URL地址"));
            EditorGUILayout.PropertyField(sessionRegisterEndpointProp, new GUIContent("会话注册端点", "会话注册的API端点"));
            EditorGUILayout.PropertyField(sessionHeartbeatEndpointProp, new GUIContent("会话心跳端点", "会话心跳的API端点"));
            EditorGUILayout.PropertyField(sessionUnregisterEndpointProp, new GUIContent("会话注销端点", "会话注销的API端点"));
            EditorGUILayout.PropertyField(agentParseEndpointProp, new GUIContent("智能体解析端点", "智能体解析的API端点"));
            EditorGUILayout.Space(10);
        }

        private void DrawClientInfo()
        {
            EditorGUILayout.LabelField("客户端基本信息", EditorStyles.boldLabel);
            EditorGUILayout.PropertyField(clientTypeProp, new GUIContent("客户端类型", "客户端的类型标识"));
            EditorGUILayout.PropertyField(clientIdProp, new GUIContent("客户端ID", "客户端的唯一标识符"));
            EditorGUILayout.PropertyField(platformProp, new GUIContent("平台", "客户端运行的平台"));
            EditorGUILayout.PropertyField(clientVersionProp, new GUIContent("客户端版本", "客户端的版本号"));
            EditorGUILayout.Space(10);
        }

        private void DrawHeartbeatConfig()
        {
            EditorGUILayout.LabelField("心跳配置", EditorStyles.boldLabel);
            EditorGUILayout.PropertyField(heartbeatIntervalProp, new GUIContent("心跳间隔（秒）", "发送心跳请求的间隔时间"));
            EditorGUILayout.PropertyField(autoStartHeartbeatProp, new GUIContent("自动启动心跳", "是否在启动时自动开始发送心跳"));
            EditorGUILayout.Space(10);
        }

        private void DrawFunctionDefinitions()
        {
            EditorGUILayout.LabelField("函数定义", EditorStyles.boldLabel);

            if (functionDefinitionsProp.arraySize == 0)
            {
                EditorGUILayout.HelpBox("暂无函数定义，请添加函数定义以启用Function Calling功能", MessageType.Info);
            }

            showFunctionDefinitions = EditorGUILayout.Foldout(showFunctionDefinitions, "函数定义列表 (" + functionDefinitionsProp.arraySize + ")");
            if (showFunctionDefinitions)
            {
                EditorGUI.indentLevel++;
                scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition, GUILayout.Height(200));

                for (int i = 0; i < functionDefinitionsProp.arraySize; i++)
                {
                    SerializedProperty functionDefProp = functionDefinitionsProp.GetArrayElementAtIndex(i);
                    SerializedProperty functionProp = functionDefProp.FindPropertyRelative("function");

                    EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                    EditorGUILayout.PropertyField(functionProp.FindPropertyRelative("name"), new GUIContent("函数名称", "函数的名称"));
                    EditorGUILayout.PropertyField(functionProp.FindPropertyRelative("description"), new GUIContent("函数描述", "函数的描述信息"));

                    SerializedProperty parametersProp = functionProp.FindPropertyRelative("parameters");
                    if (parametersProp != null)
                    {
                        EditorGUILayout.LabelField("参数定义", EditorStyles.boldLabel);
                        DrawFunctionParameters(parametersProp);
                    }

                    if (GUILayout.Button("删除函数", GUILayout.Height(25)))
                    {
                        functionDefinitionsProp.DeleteArrayElementAtIndex(i);
                        break;
                    }

                    EditorGUILayout.EndVertical();
                    EditorGUILayout.Space(5);
                }

                EditorGUILayout.EndScrollView();
                EditorGUI.indentLevel--;
            }

            EditorGUILayout.Space(5);

            EditorGUILayout.BeginHorizontal();
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("添加函数定义", GUILayout.Height(30), GUILayout.Width(150)))
            {
                AddNewFunctionDefinition();
            }
            GUILayout.FlexibleSpace();
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(10);
        }

        private void DrawFunctionParameters(SerializedProperty parametersProp)
        {
            SerializedProperty typeProp = parametersProp.FindPropertyRelative("type");
            SerializedProperty propertiesProp = parametersProp.FindPropertyRelative("properties");
            SerializedProperty requiredProp = parametersProp.FindPropertyRelative("required");

            EditorGUILayout.PropertyField(typeProp, new GUIContent("参数类型", "参数的数据类型"));

            if (propertiesProp != null && propertiesProp.isArray)
            {
                EditorGUILayout.LabelField("属性列表", EditorStyles.boldLabel);
                EditorGUI.indentLevel++;

                for (int i = 0; i < propertiesProp.arraySize; i++)
                {
                    SerializedProperty propertyProp = propertiesProp.GetArrayElementAtIndex(i);
                    string propertyName = propertyProp.displayName;

                    EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                    EditorGUILayout.LabelField($"属性 {i + 1}: {propertyName}", EditorStyles.boldLabel);

                    EditorGUILayout.PropertyField(propertyProp.FindPropertyRelative("type"), new GUIContent("类型"));
                    EditorGUILayout.PropertyField(propertyProp.FindPropertyRelative("description"), new GUIContent("描述"));

                    SerializedProperty enumValuesProp = propertyProp.FindPropertyRelative("enum_values");
                    if (enumValuesProp != null && enumValuesProp.isArray)
                    {
                        EditorGUILayout.PropertyField(enumValuesProp, new GUIContent("枚举值", "枚举类型的可选值列表"));
                    }

                    if (GUILayout.Button("删除属性", GUILayout.Height(20)))
                    {
                        propertiesProp.DeleteArrayElementAtIndex(i);
                        break;
                    }

                    EditorGUILayout.EndVertical();
                    EditorGUILayout.Space(3);
                }

                EditorGUI.indentLevel--;
            }

            if (requiredProp != null && requiredProp.isArray)
            {
                EditorGUILayout.PropertyField(requiredProp, new GUIContent("必需参数", "必需的参数名称列表"));
            }
        }

        private void DrawDebugConfig()
        {
            EditorGUILayout.LabelField("调试配置", EditorStyles.boldLabel);
            EditorGUILayout.PropertyField(enableDebugLogProp, new GUIContent("启用调试日志", "是否输出详细的调试日志"));
            EditorGUILayout.Space(10);
        }

        private void DrawStatusInfo()
        {
            EditorGUILayout.LabelField("会话状态", EditorStyles.boldLabel);

            if (Application.isPlaying)
            {
                MuseumAgent_Client client = (MuseumAgent_Client)target;
                EditorGUILayout.LabelField($"会话ID: {(string.IsNullOrEmpty(client.SessionId) ? "未连接" : client.SessionId)}");
                EditorGUILayout.LabelField($"会话状态: {(client.IsSessionActive ? "已激活" : "未激活")}");
            }
            else
            {
                EditorGUILayout.HelpBox("进入播放模式以查看会话状态", MessageType.Info);
            }

            EditorGUILayout.Space(10);
        }

        private void DrawActionButtons()
        {
            EditorGUILayout.LabelField("操作", EditorStyles.boldLabel);

            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("注册会话", GUILayout.Height(30)))
            {
                if (Application.isPlaying)
                {
                    MuseumAgent_Client client = (MuseumAgent_Client)target;
                    client.RegisterSession();
                }
                else
                {
                    EditorUtility.DisplayDialog("提示", "请先进入播放模式", "确定");
                }
            }

            if (GUILayout.Button("发送心跳", GUILayout.Height(30)))
            {
                if (Application.isPlaying)
                {
                    MuseumAgent_Client client = (MuseumAgent_Client)target;
                    client.SendHeartbeat();
                }
                else
                {
                    EditorUtility.DisplayDialog("提示", "请先进入播放模式", "确定");
                }
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("注销会话", GUILayout.Height(30)))
            {
                if (Application.isPlaying)
                {
                    MuseumAgent_Client client = (MuseumAgent_Client)target;
                    client.UnregisterSession();
                }
                else
                {
                    EditorUtility.DisplayDialog("提示", "请先进入播放模式", "确定");
                }
            }

            if (GUILayout.Button("重新连接", GUILayout.Height(30)))
            {
                if (Application.isPlaying)
                {
                    MuseumAgent_Client client = (MuseumAgent_Client)target;
                    client.ReconnectSession();
                }
                else
                {
                    EditorUtility.DisplayDialog("提示", "请先进入播放模式", "确定");
                }
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("清空函数定义", GUILayout.Height(30)))
            {
                MuseumAgent_Client client = (MuseumAgent_Client)target;
                client.ClearFunctionDefinitions();
                serializedObject.Update();
            }

            if (GUILayout.Button("添加示例函数", GUILayout.Height(30)))
            {
                AddSampleFunctions();
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(10);
        }

        private void AddNewFunctionDefinition()
        {
            functionDefinitionsProp.arraySize++;
            SerializedProperty newFunctionProp = functionDefinitionsProp.GetArrayElementAtIndex(functionDefinitionsProp.arraySize - 1);

            SerializedProperty typeProp = newFunctionProp.FindPropertyRelative("type");
            typeProp.stringValue = "function";

            SerializedProperty functionProp = newFunctionProp.FindPropertyRelative("function");
            SerializedProperty nameProp = functionProp.FindPropertyRelative("name");
            SerializedProperty descriptionProp = functionProp.FindPropertyRelative("description");

            nameProp.stringValue = "new_function";
            descriptionProp.stringValue = "新函数的描述";

            serializedObject.ApplyModifiedProperties();
        }

        private void AddSampleFunctions()
        {
            MuseumAgent_Client client = (MuseumAgent_Client)target;

            var weatherParams = new FunctionParameters
            {
                type = "object",
                properties = new Dictionary<string, FunctionParameterProperty>
                {
                    {
                        "location",
                        new FunctionParameterProperty
                        {
                            type = "string",
                            description = "城市名称，例如：北京"
                        }
                    },
                    {
                        "unit",
                        new FunctionParameterProperty
                        {
                            type = "string",
                            description = "温度单位",
                            enum_values = new string[] { "celsius", "fahrenheit" }
                        }
                    }
                },
                required = new string[] { "location" }
            };

            client.AddFunctionDefinition("get_current_weather", "获取指定城市的当前天气", weatherParams);

            var introduceArtifactParams = new FunctionParameters
            {
                type = "object",
                properties = new Dictionary<string, FunctionParameterProperty>
                {
                    {
                        "artifact_id",
                        new FunctionParameterProperty
                        {
                            type = "string",
                            description = "文物ID"
                        }
                    },
                    {
                        "detail_level",
                        new FunctionParameterProperty
                        {
                            type = "string",
                            description = "详细程度",
                            enum_values = new string[] { "basic", "medium", "detailed" }
                        }
                    }
                },
                required = new string[] { "artifact_id" }
            };

            client.AddFunctionDefinition("introduce_artifact", "介绍文物", introduceArtifactParams);

            serializedObject.Update();
            EditorUtility.SetDirty(target);
        }
    }
}
