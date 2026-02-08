using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using UnityEngine.Networking;
using System;

namespace MuseumAgent
{
    [Serializable]
    public class FunctionParameterProperty
    {
        public string type;
        public string description;
        public string[] enum_values;
    }

    [Serializable]
    public class FunctionParameters
    {
        public string type;
        public Dictionary<string, FunctionParameterProperty> properties;
        public string[] required;
    }

    [Serializable]
    public class FunctionDefinition
    {
        public string type;
        public FunctionData function;

        public FunctionDefinition(string name, string description, FunctionParameters parameters)
        {
            this.type = "function";
            this.function = new FunctionData
            {
                name = name,
                description = description,
                parameters = parameters
            };
        }
    }

    [Serializable]
    public class FunctionData
    {
        public string name;
        public string description;
        public FunctionParameters parameters;
    }

    [Serializable]
    public class ClientMetadata
    {
        public string client_type;
        public string client_id;
        public string platform;
        public string client_version;
        public string ip_address;
    }

    [Serializable]
    public class ClientRegistrationRequest
    {
        public ClientMetadata client_metadata;
        public List<FunctionDefinition> functions;
    }

    [Serializable]
    public class ClientRegistrationResponse
    {
        public string session_id;
        public string expires_at;
        public string server_timestamp;
        public string[] supported_features;
    }

    [Serializable]
    public class HeartbeatResponse
    {
        public string status;
        public string timestamp;
        public bool session_valid;
    }

    [Serializable]
    public class AgentParseRequest
    {
        public string user_input;
        public string client_type;
        public string spirit_id;
        public string scene_type;
    }

    [Serializable]
    public class AgentParseResponse
    {
        public int code;
        public string msg;
        public object data;
    }

    [Serializable]
    public class ApiResponse<T>
    {
        public int code;
        public string msg;
        public T data;
    }

    public class MuseumAgent_Client : MonoBehaviour
    {
        [Header("服务器API配置")]
        [Tooltip("服务器基础URL")]
        public string serverBaseUrl = "http://localhost:8000";

        [Tooltip("会话注册端点")]
        public string sessionRegisterEndpoint = "/api/session/register";

        [Tooltip("会话心跳端点")]
        public string sessionHeartbeatEndpoint = "/api/session/heartbeat";

        [Tooltip("会话注销端点")]
        public string sessionUnregisterEndpoint = "/api/session/unregister";

        [Tooltip("智能体解析端点")]
        public string agentParseEndpoint = "/api/agent/parse";

        [Header("客户端基本信息")]
        [Tooltip("客户端类型")]
        public string clientType = "unity";

        [Tooltip("客户端ID")]
        public string clientId = "unity_client_001";

        [Tooltip("平台")]
        public string platform = "unity";

        [Tooltip("客户端版本")]
        public string clientVersion = "1.0.0";

        [Header("函数定义")]
        [Tooltip("客户端支持的函数定义列表")]
        public List<FunctionDefinition> functionDefinitions = new List<FunctionDefinition>();

        [Header("心跳配置")]
        [Tooltip("心跳间隔（秒）")]
        public float heartbeatInterval = 30f;

        [Tooltip("自动启动心跳")]
        public bool autoStartHeartbeat = true;

        [Header("调试")]
        [Tooltip("启用调试日志")]
        public bool enableDebugLog = true;

        private string sessionId;
        private bool isSessionActive = false;
        private Coroutine heartbeatCoroutine;
        private DateTime sessionExpiresAt;

        public string SessionId => sessionId;
        public bool IsSessionActive => isSessionActive;

        private void Start()
        {
            if (autoStartHeartbeat)
            {
                RegisterSession();
            }
        }

        private void OnDestroy()
        {
            StopHeartbeat();
            UnregisterSession();
        }

        public async void RegisterSession()
        {
            try
            {
                var request = new ClientRegistrationRequest
                {
                    client_metadata = new ClientMetadata
                    {
                        client_type = clientType,
                        client_id = clientId,
                        platform = platform,
                        client_version = clientVersion,
                        ip_address = GetLocalIPAddress()
                    },
                    functions = functionDefinitions
                };

                string jsonData = JsonUtility.ToJson(request, true);
                string url = serverBaseUrl + sessionRegisterEndpoint;

                if (enableDebugLog)
                {
                    Debug.Log($"[MuseumAgent] 注册会话: {url}");
                    Debug.Log($"[MuseumAgent] 请求数据: {jsonData}");
                }

                using (UnityWebRequest webRequest = new UnityWebRequest(url, "POST"))
                {
                    byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
                    webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw);
                    webRequest.downloadHandler = new DownloadHandlerBuffer();
                    webRequest.SetRequestHeader("Content-Type", "application/json");

                    await SendWebRequestAsync(webRequest);

                    if (webRequest.result == UnityWebRequest.Result.Success)
                    {
                        string responseJson = webRequest.downloadHandler.text;
                        if (enableDebugLog)
                        {
                            Debug.Log($"[MuseumAgent] 注册成功: {responseJson}");
                        }

                        var response = JsonUtility.FromJson<ClientRegistrationResponse>(responseJson);
                        sessionId = response.session_id;
                        sessionExpiresAt = DateTime.Parse(response.expires_at);
                        isSessionActive = true;

                        if (enableDebugLog)
                        {
                            Debug.Log($"[MuseumAgent] 会话ID: {sessionId}");
                            Debug.Log($"[MuseumAgent] 会话过期时间: {sessionExpiresAt}");
                        }

                        StartHeartbeat();
                        OnSessionRegistered?.Invoke(sessionId);
                    }
                    else
                    {
                        Debug.LogError($"[MuseumAgent] 注册失败: {webRequest.error}");
                        OnSessionRegisterFailed?.Invoke(webRequest.error);
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[MuseumAgent] 注册异常: {ex.Message}");
                OnSessionRegisterFailed?.Invoke(ex.Message);
            }
        }

        public async void SendHeartbeat()
        {
            if (!isSessionActive || string.IsNullOrEmpty(sessionId))
            {
                Debug.LogWarning("[MuseumAgent] 会话未激活，无法发送心跳");
                return;
            }

            try
            {
                string url = serverBaseUrl + sessionHeartbeatEndpoint;

                using (UnityWebRequest webRequest = new UnityWebRequest(url, "POST"))
                {
                    webRequest.SetRequestHeader("session_id", sessionId);
                    webRequest.downloadHandler = new DownloadHandlerBuffer();

                    await SendWebRequestAsync(webRequest);

                    if (webRequest.result == UnityWebRequest.Result.Success)
                    {
                        string responseJson = webRequest.downloadHandler.text;
                        if (enableDebugLog)
                        {
                            Debug.Log($"[MuseumAgent] 心跳成功: {responseJson}");
                        }

                        var response = JsonUtility.FromJson<HeartbeatResponse>(responseJson);
                        if (!response.session_valid)
                        {
                            Debug.LogWarning("[MuseumAgent] 会话已失效");
                            isSessionActive = false;
                            StopHeartbeat();
                            OnSessionExpired?.Invoke();
                        }
                        else
                        {
                            OnHeartbeatSent?.Invoke();
                        }
                    }
                    else
                    {
                        Debug.LogError($"[MuseumAgent] 心跳失败: {webRequest.error}");
                        OnHeartbeatFailed?.Invoke(webRequest.error);
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[MuseumAgent] 心跳异常: {ex.Message}");
                OnHeartbeatFailed?.Invoke(ex.Message);
            }
        }

        public void UnregisterSession()
        {
            if (!isSessionActive || string.IsNullOrEmpty(sessionId))
            {
                return;
            }

            try
            {
                string url = serverBaseUrl + sessionUnregisterEndpoint;

                StartCoroutine(UnregisterSessionCoroutine(url));
            }
            catch (Exception ex)
            {
                Debug.LogError($"[MuseumAgent] 注销异常: {ex.Message}");
            }
        }

        private IEnumerator UnregisterSessionCoroutine(string url)
        {
            using (UnityWebRequest webRequest = new UnityWebRequest(url, "DELETE"))
            {
                webRequest.SetRequestHeader("session_id", sessionId);
                webRequest.downloadHandler = new DownloadHandlerBuffer();

                yield return webRequest.SendWebRequest();

                if (webRequest.result == UnityWebRequest.Result.Success)
                {
                    if (enableDebugLog)
                    {
                        Debug.Log($"[MuseumAgent] 注销成功: {webRequest.downloadHandler.text}");
                    }
                    isSessionActive = false;
                    OnSessionUnregistered?.Invoke();
                }
                else
                {
                    Debug.LogError($"[MuseumAgent] 注销失败: {webRequest.error}");
                }
            }
        }

        public async void ParseAgentInput(string userInput, string sceneType = "public", string spiritId = "")
        {
            if (!isSessionActive || string.IsNullOrEmpty(sessionId))
            {
                Debug.LogError("[MuseumAgent] 会话未激活，无法解析输入");
                OnParseFailed?.Invoke("会话未激活");
                return;
            }

            try
            {
                var request = new AgentParseRequest
                {
                    user_input = userInput,
                    client_type = clientType,
                    spirit_id = spiritId,
                    scene_type = sceneType
                };

                string jsonData = JsonUtility.ToJson(request, true);
                string url = serverBaseUrl + agentParseEndpoint;

                if (enableDebugLog)
                {
                    Debug.Log($"[MuseumAgent] 解析输入: {url}");
                    Debug.Log($"[MuseumAgent] 请求数据: {jsonData}");
                }

                using (UnityWebRequest webRequest = new UnityWebRequest(url, "POST"))
                {
                    byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
                    webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw);
                    webRequest.downloadHandler = new DownloadHandlerBuffer();
                    webRequest.SetRequestHeader("Content-Type", "application/json");
                    webRequest.SetRequestHeader("session_id", sessionId);

                    await SendWebRequestAsync(webRequest);

                    if (webRequest.result == UnityWebRequest.Result.Success)
                    {
                        string responseJson = webRequest.downloadHandler.text;
                        if (enableDebugLog)
                        {
                            Debug.Log($"[MuseumAgent] 解析成功: {responseJson}");
                        }

                        var response = JsonUtility.FromJson<AgentParseResponse>(responseJson);
                        if (response.code == 200)
                        {
                            OnParseSuccess?.Invoke(response.data);
                        }
                        else
                        {
                            Debug.LogError($"[MuseumAgent] 解析失败: {response.msg}");
                            OnParseFailed?.Invoke(response.msg);
                        }
                    }
                    else
                    {
                        Debug.LogError($"[MuseumAgent] 解析失败: {webRequest.error}");
                        OnParseFailed?.Invoke(webRequest.error);
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[MuseumAgent] 解析异常: {ex.Message}");
                OnParseFailed?.Invoke(ex.Message);
            }
        }

        private void StartHeartbeat()
        {
            StopHeartbeat();
            heartbeatCoroutine = StartCoroutine(HeartbeatCoroutine());
        }

        private void StopHeartbeat()
        {
            if (heartbeatCoroutine != null)
            {
                StopCoroutine(heartbeatCoroutine);
                heartbeatCoroutine = null;
            }
        }

        private IEnumerator HeartbeatCoroutine()
        {
            while (isSessionActive)
            {
                yield return new WaitForSeconds(heartbeatInterval);
                SendHeartbeat();
            }
        }

        private async Task SendWebRequestAsync(UnityWebRequest webRequest)
        {
            var operation = webRequest.SendWebRequest();
            while (!operation.isDone)
            {
                await Task.Yield();
            }
        }

        private string GetLocalIPAddress()
        {
            string localIP = "127.0.0.1";
            try
            {
                var host = System.Net.Dns.GetHostEntry(System.Net.Dns.GetHostName());
                foreach (var ip in host.AddressList)
                {
                    if (ip.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork)
                    {
                        localIP = ip.ToString();
                        break;
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[MuseumAgent] 获取IP地址失败: {ex.Message}");
            }
            return localIP;
        }

        public void AddFunctionDefinition(string name, string description, FunctionParameters parameters)
        {
            var functionDef = new FunctionDefinition(name, description, parameters);
            functionDefinitions.Add(functionDef);
        }

        public void ClearFunctionDefinitions()
        {
            functionDefinitions.Clear();
        }

        public void ReconnectSession()
        {
            StopHeartbeat();
            UnregisterSession();
            RegisterSession();
        }

        public delegate void SessionRegisteredHandler(string sessionId);
        public delegate void SessionRegisterFailedHandler(string error);
        public delegate void SessionExpiredHandler();
        public delegate void SessionUnregisteredHandler();
        public delegate void HeartbeatSentHandler();
        public delegate void HeartbeatFailedHandler(string error);
        public delegate void ParseSuccessHandler(object data);
        public delegate void ParseFailedHandler(string error);

        public event SessionRegisteredHandler OnSessionRegistered;
        public event SessionRegisterFailedHandler OnSessionRegisterFailed;
        public event SessionExpiredHandler OnSessionExpired;
        public event SessionUnregisteredHandler OnSessionUnregistered;
        public event HeartbeatSentHandler OnHeartbeatSent;
        public event HeartbeatFailedHandler OnHeartbeatFailed;
        public event ParseSuccessHandler OnParseSuccess;
        public event ParseFailedHandler OnParseFailed;
    }
}
