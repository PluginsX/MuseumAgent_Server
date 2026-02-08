using UnityEngine;
using UnityEditor;
using System;
using System.IO;

namespace MuseumAgent.Editor
{
    public class AgentConfigWindow : EditorWindow
    {
        private static AgentConfigWindow window;
        private AgentConfig config;

        private Vector2 scrollPosition;

        public static void ShowWindow(AgentConfig currentConfig)
        {
            window = GetWindow<AgentConfigWindow>("智能体配置");
            window.minSize = new Vector2(500, 600);
            window.titleContent = new GUIContent("智能体配置");
            window.config = currentConfig != null ? currentConfig : new AgentConfig();
            window.ShowModal();
        }

        private void OnGUI()
        {
            EditorGUILayout.Space(10);
            EditorGUILayout.LabelField("服务器API配置", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);

            DrawServerConfig();
            DrawClientInfo();
            DrawHeartbeatConfig();
            DrawDebugConfig();

            EditorGUILayout.EndScrollView();

            EditorGUILayout.Space(10);
            DrawActionButtons();
        }

        private void DrawServerConfig()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            config.serverBaseUrl = EditorGUILayout.TextField(new GUIContent("服务器基础URL", "服务器的基础URL地址"), config.serverBaseUrl);
            config.sessionRegisterEndpoint = EditorGUILayout.TextField(new GUIContent("会话注册端点", "会话注册的API端点"), config.sessionRegisterEndpoint);
            config.sessionHeartbeatEndpoint = EditorGUILayout.TextField(new GUIContent("会话心跳端点", "会话心跳的API端点"), config.sessionHeartbeatEndpoint);
            config.sessionUnregisterEndpoint = EditorGUILayout.TextField(new GUIContent("会话注销端点", "会话注销的API端点"), config.sessionUnregisterEndpoint);
            config.agentParseEndpoint = EditorGUILayout.TextField(new GUIContent("智能体解析端点", "智能体解析的API端点"), config.agentParseEndpoint);

            EditorGUILayout.EndVertical();
            EditorGUILayout.Space(10);
        }

        private void DrawClientInfo()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            config.clientType = EditorGUILayout.TextField(new GUIContent("客户端类型", "客户端的类型标识"), config.clientType);
            config.clientId = EditorGUILayout.TextField(new GUIContent("客户端ID", "客户端的唯一标识符"), config.clientId);
            config.platform = EditorGUILayout.TextField(new GUIContent("平台", "客户端运行的平台"), config.platform);
            config.clientVersion = EditorGUILayout.TextField(new GUIContent("客户端版本", "客户端的版本号"), config.clientVersion);

            EditorGUILayout.EndVertical();
            EditorGUILayout.Space(10);
        }

        private void DrawHeartbeatConfig()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            config.heartbeatInterval = EditorGUILayout.FloatField(new GUIContent("心跳间隔（秒）", "发送心跳请求的间隔时间"), config.heartbeatInterval);
            config.autoStartHeartbeat = EditorGUILayout.Toggle(new GUIContent("自动启动心跳", "是否在启动时自动开始发送心跳"), config.autoStartHeartbeat);

            EditorGUILayout.EndVertical();
            EditorGUILayout.Space(10);
        }

        private void DrawDebugConfig()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            config.enableDebugLog = EditorGUILayout.Toggle(new GUIContent("启用调试日志", "是否输出详细的调试日志"), config.enableDebugLog);

            EditorGUILayout.EndVertical();
            EditorGUILayout.Space(10);
        }

        private void DrawActionButtons()
        {
            EditorGUILayout.BeginHorizontal();

            GUILayout.FlexibleSpace();

            if (GUILayout.Button("恢复默认配置", GUILayout.Height(30), GUILayout.Width(120)))
            {
                if (EditorUtility.DisplayDialog("确认", "确定要恢复默认配置吗？", "确定", "取消"))
                {
                    config = new AgentConfig();
                }
            }

            if (GUILayout.Button("取消", GUILayout.Height(30), GUILayout.Width(80)))
            {
                window.Close();
            }

            if (GUILayout.Button("保存", GUILayout.Height(30), GUILayout.Width(80)))
            {
                SaveConfig();
                window.Close();
            }

            GUILayout.FlexibleSpace();

            EditorGUILayout.EndHorizontal();
        }

        private void SaveConfig()
        {
            try
            {
                string configPath = GetConfigPath();
                string json = JsonUtility.ToJson(config, true);
                File.WriteAllText(configPath, json);
                Debug.Log("[AgentConfigWindow] 配置已保存");
                EditorUtility.DisplayDialog("成功", "配置已保存", "确定");
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AgentConfigWindow] 保存配置失败: {ex.Message}");
                EditorUtility.DisplayDialog("错误", $"保存配置失败: {ex.Message}", "确定");
            }
        }

        private string GetConfigPath()
        {
            return Path.Combine(Application.persistentDataPath, "AgentChatConfig.json");
        }
    }
}
