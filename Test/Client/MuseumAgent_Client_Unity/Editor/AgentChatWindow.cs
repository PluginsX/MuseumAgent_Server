using UnityEngine;
using UnityEditor;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.IO;
using System.Net;
using System.Threading.Tasks;

namespace MuseumAgent.Editor
{
    public class ChatMessage
    {
        public string role;
        public string content;
        public DateTime timestamp;
        public bool isFunctionCall;

        public ChatMessage(string role, string content, bool isFunctionCall = false)
        {
            this.role = role;
            this.content = content;
            this.timestamp = DateTime.Now;
            this.isFunctionCall = isFunctionCall;
        }
    }

    public class ChatSession
    {
        public string sessionId;
        public string name;
        public DateTime createdAt;
        public List<ChatMessage> messages;

        public ChatSession(string name)
        {
            this.name = name;
            this.createdAt = DateTime.Now;
            this.messages = new List<ChatMessage>();
        }
    }

    public class AgentConfig
    {
        public string serverBaseUrl = "http://localhost:8000";
        public string sessionRegisterEndpoint = "/api/session/register";
        public string sessionHeartbeatEndpoint = "/api/session/heartbeat";
        public string sessionUnregisterEndpoint = "/api/session/unregister";
        public string agentParseEndpoint = "/api/agent/parse";
        public string clientType = "editor_client";
        public string clientId = "editor_client_001";
        public string platform = "unity_editor";
        public string clientVersion = "1.0.0";
        public float heartbeatInterval = 30f;
        public bool autoStartHeartbeat = true;
        public bool enableDebugLog = true;
    }

    public class AgentChatWindow : EditorWindow
    {
        private static AgentChatWindow window;
        private AgentConfig config;
        private List<ChatSession> sessions;
        private int currentSessionIndex = -1;
        private string currentSessionId;
        private bool isSessionActive = false;
        private DateTime sessionExpiresAt;
        private Coroutine heartbeatCoroutine;
        private Vector2 scrollPosition;
        private Vector2 sidebarScrollPosition;
        private string inputText = "";
        private bool isSending = false;
        private string statusMessage = "未连接";
        private Color statusColor = Color.gray;

        private GUIStyle messageUserStyle;
        private GUIStyle messageAssistantStyle;
        private GUIStyle messageSystemStyle;
        private GUIStyle inputFieldStyle;
        private GUIStyle sidebarButtonStyle;
        private GUIStyle headerStyle;

        private Texture2D userIcon;
        private Texture2D assistantIcon;
        private Texture2D systemIcon;

        [MenuItem("Tools/MuseumAgent/聊天室")]
        public static void ShowWindow()
        {
            window = GetWindow<AgentChatWindow>("智能体聊天室");
            window.minSize = new Vector2(900, 600);
            window.titleContent = new GUIContent("智能体聊天室");
            window.Show();
        }

        private void OnEnable()
        {
            LoadConfig();
            LoadSessions();
            InitializeStyles();
            InitializeIcons();

            if (config.autoStartHeartbeat)
            {
                RegisterSession();
            }
        }

        private void OnDisable()
        {
            SaveConfig();
            SaveSessions();
            StopHeartbeat();
            UnregisterSession();
        }

        private void OnGUI()
        {
            if (messageUserStyle == null)
            {
                InitializeStyles();
            }

            DrawLayout();
        }

        private void InitializeStyles()
        {
            messageUserStyle = new GUIStyle(EditorStyles.label)
            {
                normal = { background = MakeTexture(2, 2, new Color(0.2f, 0.6f, 1f, 0.3f)) },
                padding = new RectOffset(10, 10, 8, 8),
                margin = new RectOffset(5, 5, 5, 5),
                wordWrap = true,
                richText = true,
                fontSize = 13
            };

            messageAssistantStyle = new GUIStyle(EditorStyles.label)
            {
                normal = { background = MakeTexture(2, 2, new Color(0.3f, 0.3f, 0.3f, 0.3f)) },
                padding = new RectOffset(10, 10, 8, 8),
                margin = new RectOffset(5, 5, 5, 5),
                wordWrap = true,
                richText = true,
                fontSize = 13
            };

            messageSystemStyle = new GUIStyle(EditorStyles.label)
            {
                normal = { background = MakeTexture(2, 2, new Color(0.8f, 0.6f, 0.2f, 0.3f)) },
                padding = new RectOffset(10, 10, 8, 8),
                margin = new RectOffset(5, 5, 5, 5),
                wordWrap = true,
                richText = true,
                fontSize = 12
            };

            inputFieldStyle = new GUIStyle(EditorStyles.textArea)
            {
                normal = { background = MakeTexture(2, 2, new Color(0.15f, 0.15f, 0.15f, 1f)) },
                padding = new RectOffset(10, 10, 10, 10),
                margin = new RectOffset(0, 0, 10, 0),
                fontSize = 13,
                richText = false
            };

            sidebarButtonStyle = new GUIStyle(EditorStyles.toolbarButton)
            {
                padding = new RectOffset(8, 8, 6, 6),
                fontSize = 12,
                alignment = TextAnchor.MiddleLeft
            };

            headerStyle = new GUIStyle(EditorStyles.boldLabel)
            {
                fontSize = 14,
                padding = new RectOffset(5, 5, 5, 5)
            };
        }

        private void InitializeIcons()
        {
            userIcon = MakeColorIcon(new Color(0.2f, 0.6f, 1f));
            assistantIcon = MakeColorIcon(new Color(0.3f, 0.8f, 0.3f));
            systemIcon = MakeColorIcon(new Color(0.8f, 0.6f, 0.2f));
        }

        private Texture2D MakeColorIcon(Color color)
        {
            int size = 32;
            Texture2D texture = new Texture2D(size, size);
            Color[] colors = new Color[size * size];
            for (int i = 0; i < colors.Length; i++)
            {
                colors[i] = color;
            }
            texture.SetPixels(colors);
            texture.Apply();
            return texture;
        }

        private Texture2D MakeTexture(int width, int height, Color col)
        {
            Color[] pix = new Color[width * height];
            for (int i = 0; i < pix.Length; i++)
            {
                pix[i] = col;
            }
            Texture2D result = new Texture2D(width, height);
            result.SetPixels(pix);
            result.Apply();
            return result;
        }

        private void DrawLayout()
        {
            EditorGUILayout.BeginHorizontal();

            DrawSidebar();
            DrawMainContent();

            EditorGUILayout.EndHorizontal();

            Repaint();
        }

        private void DrawSidebar()
        {
            EditorGUILayout.BeginVertical(GUILayout.Width(250));
            DrawSidebarHeader();
            DrawSessionsList();
            DrawSidebarActions();
            EditorGUILayout.EndVertical();
        }

        private void DrawSidebarHeader()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);
            EditorGUILayout.LabelField("会话管理", headerStyle);
            EditorGUILayout.EndVertical();
        }

        private void DrawSessionsList()
        {
            sidebarScrollPosition = EditorGUILayout.BeginScrollView(sidebarScrollPosition);

            for (int i = 0; i < sessions.Count; i++)
            {
                ChatSession session = sessions[i];
                bool isSelected = (i == currentSessionIndex);

                GUIStyle buttonStyle = isSelected ? 
                    new GUIStyle(sidebarButtonStyle) { normal = { background = MakeTexture(2, 2, new Color(0.3f, 0.5f, 0.8f, 0.5f)) } } :
                    sidebarButtonStyle;

                if (GUILayout.Button($"{session.name}\n{session.messages.Count} 条消息", buttonStyle, GUILayout.Height(50)))
                {
                    SwitchSession(i);
                }
            }

            EditorGUILayout.EndScrollView();
        }

        private void DrawSidebarActions()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            if (GUILayout.Button("新建会话", GUILayout.Height(30)))
            {
                CreateNewSession();
            }

            if (GUILayout.Button("配置设置", GUILayout.Height(30)))
            {
                OpenConfigWindow();
            }

            if (GUILayout.Button("清空所有会话", GUILayout.Height(30)))
            {
                if (EditorUtility.DisplayDialog("确认", "确定要清空所有会话吗？", "确定", "取消"))
                {
                    ClearAllSessions();
                }
            }

            EditorGUILayout.EndVertical();

            DrawConnectionStatus();
        }

        private void DrawConnectionStatus()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);
            EditorGUILayout.LabelField("连接状态", headerStyle);

            Color originalColor = GUI.color;
            GUI.color = statusColor;
            EditorGUILayout.LabelField(statusMessage);
            GUI.color = originalColor;

            EditorGUILayout.EndVertical();
        }

        private void DrawMainContent()
        {
            EditorGUILayout.BeginVertical(GUILayout.ExpandWidth(true));

            DrawChatArea();
            DrawInputArea();

            EditorGUILayout.EndVertical();
        }

        private void DrawChatArea()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox, GUILayout.ExpandHeight(true));

            if (currentSessionIndex >= 0 && currentSessionIndex < sessions.Count)
            {
                ChatSession currentSession = sessions[currentSessionIndex];
                scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition, GUILayout.ExpandHeight(true));

                foreach (ChatMessage message in currentSession.messages)
                {
                    DrawMessage(message);
                }

                EditorGUILayout.EndScrollView();
            }
            else
            {
                EditorGUILayout.HelpBox("选择或创建一个会话开始对话", MessageType.Info);
            }

            EditorGUILayout.EndVertical();
        }

        private void DrawMessage(ChatMessage message)
        {
            EditorGUILayout.BeginVertical(message.role == "user" ? messageUserStyle : 
                                   message.role == "system" ? messageSystemStyle : messageAssistantStyle);

            EditorGUILayout.BeginHorizontal();

            Texture2D icon = message.role == "user" ? userIcon :
                             message.role == "system" ? systemIcon : assistantIcon;

            if (icon != null)
            {
                GUILayout.Box(icon, GUILayout.Width(24), GUILayout.Height(24));
                GUILayout.Space(10);
            }

            EditorGUILayout.BeginVertical(GUILayout.ExpandWidth(true));
            EditorGUILayout.LabelField($"<b>{message.role}</b>", EditorStyles.miniLabel);
            EditorGUILayout.LabelField(message.timestamp.ToString("HH:mm:ss"), EditorStyles.miniLabel);
            EditorGUILayout.EndVertical();

            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(5);
            EditorGUILayout.LabelField(message.content);
            EditorGUILayout.Space(10);

            EditorGUILayout.EndVertical();
        }

        private void DrawInputArea()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            EditorGUI.BeginDisabledGroup(isSending || !isSessionActive);

            inputText = EditorGUILayout.TextArea(inputText, inputFieldStyle, GUILayout.Height(80));

            EditorGUILayout.BeginHorizontal();

            GUILayout.FlexibleSpace();

            if (GUILayout.Button("发送", GUILayout.Height(30), GUILayout.Width(100)))
            {
                SendMessage();
            }

            EditorGUI.EndDisabledGroup();

            EditorGUILayout.EndHorizontal();

            EditorGUILayout.EndVertical();
        }

        private void CreateNewSession()
        {
            string sessionName = $"会话 {sessions.Count + 1}";
            ChatSession newSession = new ChatSession(sessionName);
            sessions.Add(newSession);
            SwitchSession(sessions.Count - 1);
            SaveSessions();
        }

        private void SwitchSession(int index)
        {
            if (index >= 0 && index < sessions.Count)
            {
                currentSessionIndex = index;
                currentSessionId = sessions[index].sessionId;
                SaveSessions();
            }
        }

        private void ClearAllSessions()
        {
            sessions.Clear();
            currentSessionIndex = -1;
            currentSessionId = null;
            SaveSessions();
        }

        private void OpenConfigWindow()
        {
            AgentConfigWindow.ShowWindow(config);
        }

        private async void SendMessage()
        {
            if (string.IsNullOrEmpty(inputText.Trim()) || !isSessionActive)
            {
                return;
            }

            string messageContent = inputText.Trim();
            inputText = "";
            isSending = true;

            if (currentSessionIndex >= 0 && currentSessionIndex < sessions.Count)
            {
                ChatSession currentSession = sessions[currentSessionIndex];
                currentSession.messages.Add(new ChatMessage("user", messageContent));
                SaveSessions();
            }

            try
            {
                string response = await ParseAgentInputAsync(messageContent);

                if (currentSessionIndex >= 0 && currentSessionIndex < sessions.Count)
                {
                    ChatSession currentSession = sessions[currentSessionIndex];
                    currentSession.messages.Add(new ChatMessage("assistant", response));
                    SaveSessions();
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AgentChatWindow] 发送消息失败: {ex.Message}");
                EditorUtility.DisplayDialog("错误", $"发送消息失败: {ex.Message}", "确定");
            }
            finally
            {
                isSending = false;
            }
        }

        private async void RegisterSession()
        {
            try
            {
                statusMessage = "正在注册...";
                statusColor = Color.yellow;

                var request = new
                {
                    client_metadata = new
                    {
                        client_type = config.clientType,
                        client_id = config.clientId,
                        platform = config.platform,
                        client_version = config.clientVersion
                    },
                    functions = new object[0]
                };

                string jsonData = JsonUtility.ToJson(request, true);
                string url = config.serverBaseUrl + config.sessionRegisterEndpoint;

                string response = await SendWebRequestAsync(url, "POST", jsonData);

                if (config.enableDebugLog)
                {
                    Debug.Log($"[AgentChatWindow] 注册成功: {response}");
                }

                var responseObj = JsonUtility.FromJson<SessionResponse>(response);
                currentSessionId = responseObj.session_id;
                sessionExpiresAt = DateTime.Parse(responseObj.expires_at);
                isSessionActive = true;

                statusMessage = "已连接";
                statusColor = Color.green;

                if (currentSessionIndex >= 0 && currentSessionIndex < sessions.Count)
                {
                    sessions[currentSessionIndex].sessionId = currentSessionId;
                    SaveSessions();
                }

                StartHeartbeat();
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AgentChatWindow] 注册失败: {ex.Message}");
                statusMessage = "连接失败";
                statusColor = Color.red;
                isSessionActive = false;
            }
        }

        private async void UnregisterSession()
        {
            if (!isSessionActive || string.IsNullOrEmpty(currentSessionId))
            {
                return;
            }

            try
            {
                string url = config.serverBaseUrl + config.sessionUnregisterEndpoint;
                await SendWebRequestAsync(url, "DELETE", null, currentSessionId);

                if (config.enableDebugLog)
                {
                    Debug.Log("[AgentChatWindow] 注销成功");
                }

                isSessionActive = false;
                currentSessionId = null;
                statusMessage = "未连接";
                statusColor = Color.gray;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AgentChatWindow] 注销失败: {ex.Message}");
            }
        }

        private async void SendHeartbeat()
        {
            if (!isSessionActive || string.IsNullOrEmpty(currentSessionId))
            {
                return;
            }

            try
            {
                string url = config.serverBaseUrl + config.sessionHeartbeatEndpoint;
                string response = await SendWebRequestAsync(url, "POST", null, currentSessionId);

                if (config.enableDebugLog)
                {
                    Debug.Log($"[AgentChatWindow] 心跳成功: {response}");
                }

                var responseObj = JsonUtility.FromJson<HeartbeatResponse>(response);
                if (!responseObj.session_valid)
                {
                    Debug.LogWarning("[AgentChatWindow] 会话已失效");
                    isSessionActive = false;
                    StopHeartbeat();
                    statusMessage = "会话已过期";
                    statusColor = Color.red;
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AgentChatWindow] 心跳失败: {ex.Message}");
            }
        }

        private void StartHeartbeat()
        {
            StopHeartbeat();
            EditorApplication.delayCall += HeartbeatLoop;
        }

        private void StopHeartbeat()
        {
            EditorApplication.delayCall -= HeartbeatLoop;
        }

        private async void HeartbeatLoop()
        {
            while (isSessionActive)
            {
                await Task.Delay((int)(config.heartbeatInterval * 1000));
                if (isSessionActive)
                {
                    SendHeartbeat();
                }
            }
        }

        private async Task<string> ParseAgentInputAsync(string userInput)
        {
            var request = new
            {
                user_input = userInput,
                client_type = config.clientType,
                spirit_id = "",
                scene_type = "public"
            };

            string jsonData = JsonUtility.ToJson(request, true);
            string url = config.serverBaseUrl + config.agentParseEndpoint;

            return await SendWebRequestAsync(url, "POST", jsonData, currentSessionId);
        }

        private async Task<string> SendWebRequestAsync(string url, string method, string jsonData = null, string sessionId = null)
        {
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
            request.Method = method;
            request.ContentType = "application/json";

            if (!string.IsNullOrEmpty(sessionId))
            {
                request.Headers["session_id"] = sessionId;
            }

            if (!string.IsNullOrEmpty(jsonData) && method == "POST")
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
                request.ContentLength = bodyRaw.Length;
                using (Stream stream = await request.GetRequestStreamAsync())
                {
                    await stream.WriteAsync(bodyRaw, 0, bodyRaw.Length);
                }
            }

            using (HttpWebResponse response = (HttpWebResponse)await request.GetResponseAsync())
            using (Stream stream = response.GetResponseStream())
            using (StreamReader reader = new StreamReader(stream))
            {
                return await reader.ReadToEndAsync();
            }
        }

        private void LoadConfig()
        {
            string configPath = GetConfigPath();
            if (File.Exists(configPath))
            {
                try
                {
                    string json = File.ReadAllText(configPath);
                    config = JsonUtility.FromJson<AgentConfig>(json);
                }
                catch (Exception ex)
                {
                    Debug.LogError($"[AgentChatWindow] 加载配置失败: {ex.Message}");
                    config = new AgentConfig();
                }
            }
            else
            {
                config = new AgentConfig();
            }
        }

        private void SaveConfig()
        {
            try
            {
                string configPath = GetConfigPath();
                string json = JsonUtility.ToJson(config, true);
                File.WriteAllText(configPath, json);
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AgentChatWindow] 保存配置失败: {ex.Message}");
            }
        }

        private void LoadSessions()
        {
            string sessionsPath = GetSessionsPath();
            if (File.Exists(sessionsPath))
            {
                try
                {
                    string json = File.ReadAllText(sessionsPath);
                    var sessionsData = JsonUtility.FromJson<SessionsData>(json);
                    sessions = sessionsData.sessions ?? new List<ChatSession>();
                }
                catch (Exception ex)
                {
                    Debug.LogError($"[AgentChatWindow] 加载会话失败: {ex.Message}");
                    sessions = new List<ChatSession>();
                }
            }
            else
            {
                sessions = new List<ChatSession>();
            }
        }

        private void SaveSessions()
        {
            try
            {
                string sessionsPath = GetSessionsPath();
                var sessionsData = new SessionsData { sessions = sessions };
                string json = JsonUtility.ToJson(sessionsData, true);
                File.WriteAllText(sessionsPath, json);
            }
            catch (Exception ex)
            {
                Debug.LogError($"[AgentChatWindow] 保存会话失败: {ex.Message}");
            }
        }

        private string GetConfigPath()
        {
            return Path.Combine(Application.persistentDataPath, "AgentChatConfig.json");
        }

        private string GetSessionsPath()
        {
            return Path.Combine(Application.persistentDataPath, "AgentChatSessions.json");
        }

        [Serializable]
        private class SessionResponse
        {
            public string session_id;
            public string expires_at;
            public string server_timestamp;
            public string[] supported_features;
        }

        [Serializable]
        private class HeartbeatResponse
        {
            public string status;
            public string timestamp;
            public bool session_valid;
        }

        [Serializable]
        private class SessionsData
        {
            public List<ChatSession> sessions;
        }
    }
}
