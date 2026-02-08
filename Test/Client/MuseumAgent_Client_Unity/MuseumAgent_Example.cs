using UnityEngine;
using UnityEngine.UI;

namespace MuseumAgent
{
    public class MuseumAgent_Example : MonoBehaviour
    {
        [Header("UI引用")]
        [Tooltip("输入框")]
        public InputField inputField;

        [Tooltip("发送按钮")]
        public Button sendButton;

        [Tooltip("结果显示文本")]
        public Text resultText;

        [Tooltip("状态显示文本")]
        public Text statusText;

        [Header("配置")]
        [Tooltip("自动发送示例请求")]
        public bool autoSendExample = false;

        [Tooltip("示例请求延迟（秒）")]
        public float exampleDelay = 2f;

        private MuseumAgent_Client museumAgent;

        private void Start()
        {
            museumAgent = GetComponent<MuseumAgent_Client>();
            if (museumAgent == null)
            {
                Debug.LogError("[MuseumAgent_Example] 未找到MuseumAgent_Client组件");
                return;
            }

            SetupEventListeners();
            SetupUI();

            if (autoSendExample)
            {
                Invoke("SendExampleRequest", exampleDelay);
            }
        }

        private void OnDestroy()
        {
            RemoveEventListeners();
        }

        private void SetupEventListeners()
        {
            museumAgent.OnSessionRegistered += OnSessionRegistered;
            museumAgent.OnSessionRegisterFailed += OnSessionRegisterFailed;
            museumAgent.OnSessionExpired += OnSessionExpired;
            museumAgent.OnSessionUnregistered += OnSessionUnregistered;
            museumAgent.OnHeartbeatSent += OnHeartbeatSent;
            museumAgent.OnHeartbeatFailed += OnHeartbeatFailed;
            museumAgent.OnParseSuccess += OnParseSuccess;
            museumAgent.OnParseFailed += OnParseFailed;

            if (sendButton != null)
            {
                sendButton.onClick.AddListener(OnSendButtonClick);
            }
        }

        private void RemoveEventListeners()
        {
            if (museumAgent != null)
            {
                museumAgent.OnSessionRegistered -= OnSessionRegistered;
                museumAgent.OnSessionRegisterFailed -= OnSessionRegisterFailed;
                museumAgent.OnSessionExpired -= OnSessionExpired;
                museumAgent.OnSessionUnregistered -= OnSessionUnregistered;
                museumAgent.OnHeartbeatSent -= OnHeartbeatSent;
                museumAgent.OnHeartbeatFailed -= OnHeartbeatFailed;
                museumAgent.OnParseSuccess -= OnParseSuccess;
                museumAgent.OnParseFailed -= OnParseFailed;
            }

            if (sendButton != null)
            {
                sendButton.onClick.RemoveListener(OnSendButtonClick);
            }
        }

        private void SetupUI()
        {
            UpdateStatus("初始化中...");
            UpdateResult("等待输入...");
        }

        private void OnSendButtonClick()
        {
            if (inputField != null && !string.IsNullOrEmpty(inputField.text))
            {
                SendUserInput(inputField.text);
                inputField.text = "";
            }
            else
            {
                Debug.LogWarning("[MuseumAgent_Example] 输入为空");
            }
        }

        private void SendUserInput(string userInput)
        {
            if (museumAgent == null)
            {
                Debug.LogError("[MuseumAgent_Example] MuseumAgent_Client组件未初始化");
                return;
            }

            if (!museumAgent.IsSessionActive)
            {
                Debug.LogWarning("[MuseumAgent_Example] 会话未激活，正在尝试注册...");
                museumAgent.RegisterSession();
                return;
            }

            UpdateStatus("正在处理请求...");
            museumAgent.ParseAgentInput(userInput, "public", "");
        }

        private void SendExampleRequest()
        {
            if (museumAgent != null && museumAgent.IsSessionActive)
            {
                SendUserInput("介绍一下这个文物");
            }
        }

        private void OnSessionRegistered(string sessionId)
        {
            UpdateStatus($"会话已注册: {sessionId}");
            Debug.Log($"[MuseumAgent_Example] 会话注册成功: {sessionId}");
        }

        private void OnSessionRegisterFailed(string error)
        {
            UpdateStatus($"会话注册失败: {error}");
            Debug.LogError($"[MuseumAgent_Example] 会话注册失败: {error}");
        }

        private void OnSessionExpired()
        {
            UpdateStatus("会话已过期");
            Debug.LogWarning("[MuseumAgent_Example] 会话已过期");
        }

        private void OnSessionUnregistered()
        {
            UpdateStatus("会话已注销");
            Debug.Log("[MuseumAgent_Example] 会话已注销");
        }

        private void OnHeartbeatSent()
        {
            Debug.Log("[MuseumAgent_Example] 心跳已发送");
        }

        private void OnHeartbeatFailed(string error)
        {
            Debug.LogError($"[MuseumAgent_Example] 心跳失败: {error}");
        }

        private void OnParseSuccess(object data)
        {
            UpdateStatus("请求处理成功");
            UpdateResult(JsonUtility.ToJson(data, true));
            Debug.Log($"[MuseumAgent_Example] 解析成功: {JsonUtility.ToJson(data, true)}");
        }

        private void OnParseFailed(string error)
        {
            UpdateStatus($"请求处理失败: {error}");
            UpdateResult($"错误: {error}");
            Debug.LogError($"[MuseumAgent_Example] 解析失败: {error}");
        }

        private void UpdateStatus(string status)
        {
            if (statusText != null)
            {
                statusText.text = status;
            }
        }

        private void UpdateResult(string result)
        {
            if (resultText != null)
            {
                resultText.text = result;
            }
        }

        public void ManualRegisterSession()
        {
            if (museumAgent != null)
            {
                museumAgent.RegisterSession();
            }
        }

        public void ManualSendHeartbeat()
        {
            if (museumAgent != null)
            {
                museumAgent.SendHeartbeat();
            }
        }

        public void ManualUnregisterSession()
        {
            if (museumAgent != null)
            {
                museumAgent.UnregisterSession();
            }
        }

        public void ManualReconnectSession()
        {
            if (museumAgent != null)
            {
                museumAgent.ReconnectSession();
            }
        }
    }
}
