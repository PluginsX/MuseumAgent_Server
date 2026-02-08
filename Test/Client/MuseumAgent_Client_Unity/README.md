# MuseumAgent Unity 客户端组件

适用于 Unity 2022.3 的 MuseumAgent 智能体服务客户端组件。

## 功能特性

- 完整的 API 访问功能
- 会话管理（注册、心跳、注销）
- OpenAI 兼容的 Function Calling 支持
- 自动心跳机制
- 详细的调试日志
- 友好的 Inspector 界面
- 事件驱动的回调机制

## 文件说明

### MuseumAgent_Client.cs
主客户端脚本，实现与服务器的所有通信功能。

### MuseumAgent_Client_Editor.cs
Inspector 界面脚本，提供友好的配置界面。

### MuseumAgent_Example.cs
使用示例脚本，展示如何使用客户端组件。

## 安装步骤

1. 将以下文件复制到 Unity 项目的 `Assets/Scripts/` 目录：
   - `MuseumAgent_Client.cs`
   - `MuseumAgent_Client_Editor.cs`
   - `MuseumAgent_Example.cs`

2. 在 Unity 编辑器中等待脚本编译完成

## 使用方法

### 基本使用

1. 创建一个空的 GameObject
2. 添加 `MuseumAgent_Client` 组件
3. 在 Inspector 中配置服务器和客户端参数
4. 运行场景，客户端会自动注册会话

### 配置说明

#### 服务器 API 配置
- **服务器基础URL**: 服务器的基础URL地址（如：`http://localhost:8000`）
- **会话注册端点**: 会话注册的API端点（默认：`/api/session/register`）
- **会话心跳端点**: 会话心跳的API端点（默认：`/api/session/heartbeat`）
- **会话注销端点**: 会话注销的API端点（默认：`/api/session/unregister`）
- **智能体解析端点**: 智能体解析的API端点（默认：`/api/agent/parse`）

#### 客户端基本信息
- **客户端类型**: 客户端的类型标识（默认：`unity`）
- **客户端ID**: 客户端的唯一标识符（默认：`unity_client_001`）
- **平台**: 客户端运行的平台（默认：`unity`）
- **客户端版本**: 客户端的版本号（默认：`1.0.0`）

#### 函数定义
- **函数定义列表**: 客户端支持的函数定义列表，用于 Function Calling

#### 心跳配置
- **心跳间隔（秒）**: 发送心跳请求的间隔时间（默认：30秒）
- **自动启动心跳**: 是否在启动时自动开始发送心跳（默认：true）

#### 调试配置
- **启用调试日志**: 是否输出详细的调试日志（默认：true）

### 函数定义管理

#### 添加函数定义

在 Inspector 中：
1. 展开"函数定义"部分
2. 点击"添加函数定义"按钮
3. 填写函数信息：
   - 函数名称
   - 函数描述
   - 参数定义

#### 添加示例函数

点击"添加示例函数"按钮，会自动添加两个示例函数：
- `get_current_weather`: 获取指定城市的当前天气
- `introduce_artifact`: 介绍文物

#### 清空函数定义

点击"清空函数定义"按钮，删除所有函数定义。

### API 调用示例

#### 注册会话

```csharp
MuseumAgent_Client client = GetComponent<MuseumAgent_Client>();
client.RegisterSession();
```

#### 发送用户输入

```csharp
MuseumAgent_Client client = GetComponent<MuseumAgent_Client>();
client.ParseAgentInput("介绍一下这个文物", "public", "");
```

#### 手动发送心跳

```csharp
MuseumAgent_Client client = GetComponent<MuseumAgent_Client>();
client.SendHeartbeat();
```

#### 注销会话

```csharp
MuseumAgent_Client client = GetComponent<MuseumAgent_Client>();
client.UnregisterSession();
```

#### 重新连接会话

```csharp
MuseumAgent_Client client = GetComponent<MuseumAgent_Client>();
client.ReconnectSession();
```

### 事件监听

客户端提供以下事件：

```csharp
MuseumAgent_Client client = GetComponent<MuseumAgent_Client>();

// 会话注册成功
client.OnSessionRegistered += (sessionId) => {
    Debug.Log($"会话已注册: {sessionId}");
};

// 会话注册失败
client.OnSessionRegisterFailed += (error) => {
    Debug.LogError($"会话注册失败: {error}");
};

// 会话过期
client.OnSessionExpired += () => {
    Debug.LogWarning("会话已过期");
};

// 会话注销
client.OnSessionUnregistered += () => {
    Debug.Log("会话已注销");
};

// 心跳发送成功
client.OnHeartbeatSent += () => {
    Debug.Log("心跳已发送");
};

// 心跳发送失败
client.OnHeartbeatFailed += (error) => {
    Debug.LogError($"心跳失败: {error}");
};

// 解析成功
client.OnParseSuccess += (data) => {
    Debug.Log($"解析成功: {JsonUtility.ToJson(data, true)}");
};

// 解析失败
client.OnParseFailed += (error) => {
    Debug.LogError($"解析失败: {error}");
};
```

## 使用示例脚本

### 设置 UI

1. 创建一个 Canvas
2. 添加以下 UI 元素：
   - InputField（用于输入）
   - Button（用于发送）
   - Text（用于显示结果）
   - Text（用于显示状态）

2. 将 `MuseumAgent_Example` 组件添加到 GameObject
3. 在 Inspector 中分配 UI 引用

### 运行示例

1. 确保 MuseumAgent 服务端正在运行
2. 运行 Unity 场景
3. 在输入框中输入文本
4. 点击发送按钮
5. 查看结果显示

## 函数定义格式

函数定义遵循 OpenAI Function Calling 标准：

```json
{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "获取指定城市的当前天气",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，例如：北京"
                },
                "unit": {
                    "type": "string",
                    "description": "温度单位",
                    "enum_values": ["celsius", "fahrenheit"]
                }
            },
            "required": ["location"]
        }
    }
}
```

## 注意事项

1. **网络权限**: 确保项目有网络访问权限
2. **服务器地址**: 根据实际情况配置服务器地址
3. **会话管理**: 建议在应用退出时调用 `UnregisterSession()`
4. **错误处理**: 建议监听所有事件以处理各种情况
5. **调试模式**: 开发时启用调试日志，生产环境关闭

## 故障排除

### 连接失败
- 检查服务器地址是否正确
- 确认服务器是否正在运行
- 检查网络连接

### 会话注册失败
- 检查服务器日志
- 确认服务器配置正确
- 检查客户端参数

### 心跳失败
- 检查会话是否仍然有效
- 确认服务器正常运行
- 检查网络连接

## 版本要求

- Unity 2022.3 或更高版本
- .NET Standard 2.0 或更高版本

## 许可证

根据项目许可证使用。

## 支持

如有问题，请联系项目维护者。
