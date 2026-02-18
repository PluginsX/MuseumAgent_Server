# 博物馆智能体 服务器-客户端通信协议

> 本协议为博物馆智能体项目专用，规范 Web 客户端与智能体服务器之间的 WebSocket 通信。

---

## 一、业务背景与协议目标

### 1.1 核心业务

博物馆智能体服务器基于专有资料库的语义检索系统(SRS)，结合用户提问与客户端提供的函数定义(Function Calling)，通过外部 LLM 服务生成综合回复。

### 1.2 设计原则

1. **统一报文结构**：C→S 服务请求、S→C 业务响应各采用一种报文结构，通过字段区分具体内容；
2. **请求-响应可关联**：每条请求携带 `request_id`，响应原样回显，支持多路并发；
3. **流式与完整数据统一建模**：完整数据视为单分片流式数据（`stream_seq=0` 且下一片为 `-1`）；
4. **语音数据二元传输**：JSON 承载控制与文本，语音 PCM 支持 Base64 内嵌或独立二进制帧；
5. **会话属性可更新**：RequireTTS、FunctionCalling 可在请求中按需更新，覆盖会话内缓存。

---

## 二、底层通信

| 项目 | 说明 |
|------|------|
| 协议 | WebSocket（推荐 wss） |
| 文本帧 | JSON 控制与业务数据 |
| 二进制帧 | 语音 PCM 数据（`voice_mode=BINARY` 时使用） |
| 连接路径 | `/ws/agent/stream` |

---

## 三、报文公共结构

### 3.1 公共字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | 是 | 协议版本，如 `"1.0"` |
| `msg_type` | string | 是 | 消息类型 |
| `session_id` | string | 视场景 | 会话 ID；REGISTER 时为空，HEALTH_CHECK 可选，其余必填 |
| `payload` | object | 是 | 业务数据，结构由 `msg_type` 决定 |
| `timestamp` | number | 是 | 毫秒时间戳 |

### 3.2 请求-响应关联

服务请求(REQUEST)与业务响应(RESPONSE)通过 `request_id` 关联：

- 客户端在 REQUEST 的 `payload` 中填写 `request_id`；
- 服务端在 RESPONSE 的 `payload` 中回显相同 `request_id`。

---

## 四、客户端→服务器（C→S）

### 4.1 消息类型

| msg_type | 说明 |
|----------|------|
| REGISTER | 会话注册（认证 + 客户端属性） |
| REQUEST | 服务请求（文本 / 流式语音，可更新会话属性） |
| INTERRUPT | 中断当前请求 |
| SESSION_QUERY | 会话信息查询 |
| SHUTDOWN | 主动结束会话 |
| HEARTBEAT_REPLY | 心跳回信 |
| HEALTH_CHECK | 服务端健康检查 |

### 4.2 REGISTER（会话注册）

**时机**：建立 WebSocket 连接后第一条业务报文。

**payload：**

```json
{
  "auth": {
    "type": "API_KEY",
    "api_key": "xxx"
  },
  "platform": "WEB",
  "require_tts": false,
  "enable_srs": true,
  "function_calling": [
    {
      "name": "get_exhibit_info",
      "description": "查询文物详情",
      "parameters": [
        { "name": "exhibit_id", "type": "string" }
      ]
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| auth | object | 是 | 认证信息 |
| auth.type | string | 是 | `API_KEY` 或 `ACCOUNT` |
| auth.api_key | string | type=API_KEY 时 | API 密钥 |
| auth.account | string | type=ACCOUNT 时 | 账号 |
| auth.password | string | type=ACCOUNT 时 | 密码 |
| platform | string | 是 | `WEB` / `APP` / `MINI_PROGRAM` / `TV` |
| require_tts | boolean | 是 | 是否要求语音回复 |
| enable_srs | boolean | 否 | 是否启用增强检索（默认 true） |
| function_calling | array | 是 | 函数定义列表，可为空数组 |

### 4.3 REQUEST（服务请求）

**统一结构**：文本请求、流式语音请求及会话属性更新均使用此结构，通过字段取值区分用途。

**payload：**

```json
{
  "request_id": "req_xxx",
  "data_type": "TEXT",
  "stream_flag": false,
  "stream_seq": 0,
  "require_tts": true,
  "enable_srs": true,
  "function_calling_op": "REPLACE",
  "function_calling": [],
  "content": {
    "voice_mode": "BASE64",
    "text": "这件文物的年代是？"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| request_id | string | 是 | 请求唯一标识，客户端生成 |
| data_type | string | 是 | `TEXT` 或 `VOICE` |
| stream_flag | boolean | 是 | 是否流式；TEXT 固定 false，VOICE 固定 true |
| stream_seq | number | 是 | 流式分片序号：0 起，-1 表示最后一片 |
| require_tts | boolean | 否 | 若提供则更新会话中的 RequireTTS |
| enable_srs | boolean | 否 | 若提供则更新会话中的 EnableSRS |
| function_calling_op | string | 否 | 若更新函数：`REPLACE` / `ADD` / `UPDATE` / `DELETE` |
| function_calling | array | 否 | 与 `function_calling_op` 配套的函数列表 |
| content | object | 是 | 数据内容 |
| content.text | string | data_type=TEXT 时 | 完整文本 |
| content.voice_mode | string | data_type=VOICE 时 | `BASE64` 或 `BINARY` |
| content.voice | string | VOICE 且 BASE64 时 | Base64 编码的 PCM |

#### 4.3.1 文本请求

- `data_type`: `TEXT`
- `stream_flag`: `false`
- `stream_seq`: `0`
- `content.text`: 完整用户输入

#### 4.3.2 语音请求（Base64）

- `data_type`: `VOICE`
- `stream_flag`: `false`（整段语音一次发送）
- `stream_seq`: `0`
- `content.voice_mode`: `BASE64`
- `content.voice`: Base64 编码的 PCM 数据

#### 4.3.3 语音请求（流式，BINARY）

语音 PCM 通过独立二进制帧传输，JSON 仅作控制：

1. **起始帧**：发送 REQUEST JSON  
   - `data_type`: `VOICE`  
   - `stream_flag`: `true`  
   - `stream_seq`: `0`  
   - `content.voice_mode`: `BINARY`  
   - `content.voice`: 不填或空

2. **数据帧**：连续发送若干 WebSocket 二进制帧，顺序拼接为完整 PCM

3. **结束帧**：再发一条 REQUEST JSON  
   - `data_type`: `VOICE`  
   - `stream_flag`: `true`  
   - `stream_seq`: `-1`  
   - `content.voice_mode`: `BINARY`  
   - `request_id` 与起始帧相同

同一 `request_id` 的起始帧、二进制帧、结束帧视为一次完整语音请求。

#### 4.3.4 仅更新会话属性

- `data_type`: `TEXT`（占位）
- `stream_flag`: `false`
- `stream_seq`: `0`
- `content.text`: 空字符串 `""`
- 通过 `require_tts`、`enable_srs` 和/或 `function_calling_op` + `function_calling` 更新会话

服务端按字段存在性覆盖会话中对应属性。

### 4.4 INTERRUPT（中断请求）

**时机**：用户在智能体回复过程中发送新消息，或主动停止当前回复。

**用途**：通知服务端立即停止正在处理的请求，释放资源（LLM 生成、TTS 合成等）。

**payload：**

```json
{
  "interrupt_request_id": "req_xxx",
  "reason": "USER_NEW_INPUT"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| interrupt_request_id | string | 否 | 要中断的请求ID；为空则中断该会话的所有进行中请求 |
| reason | string | 是 | 中断原因：`USER_NEW_INPUT`（用户新输入）/ `USER_STOP`（用户主动停止）/ `CLIENT_ERROR`（客户端错误） |

**说明：**

- 客户端通常在检测到用户新输入（文本输入、VAD 检测到语音）时自动发送
- 服务端收到后立即设置取消信号，停止 LLM/TTS 等异步任务
- 服务端返回 INTERRUPT_ACK 确认，并发送最后一帧 RESPONSE（标记 `interrupted: true`）

### 4.5 SESSION_QUERY

**payload：**

```json
{
  "query_fields": ["function_calling", "require_tts", "platform", "create_time", "remaining_seconds"]
}
```

`query_fields` 为空或不提供时，返回全部会话信息。

### 4.6 SHUTDOWN

**payload：**

```json
{
  "reason": "用户主动退出"
}
```

### 4.7 HEARTBEAT_REPLY

**payload：**

```json
{
  "client_status": "ONLINE"
}
```

### 4.8 HEALTH_CHECK

**payload：**

```json
{
  "check_fields": ["cpu_usage", "conn_count", "status"]
}
```

`check_fields` 为空或不提供时，返回全部健康信息。本报文可不带 `session_id`。

---

## 五、服务器→客户端（S→C）

### 5.1 消息类型

| msg_type | 说明 |
|----------|------|
| REGISTER_ACK | 注册成功确认 |
| RESPONSE | 业务响应（文本 / 语音 / 函数调用，可组合） |
| INTERRUPT_ACK | 中断确认 |
| SESSION_INFO | 会话信息 |
| SHUTDOWN | 服务器发起结束 |
| HEARTBEAT | 心跳 |
| HEALTH_CHECK_ACK | 健康检查回复 |
| SESSION_WARN | 会话即将超时提醒 |
| ERROR | 错误 |

### 5.2 REGISTER_ACK

注册成功时返回，失败时使用 ERROR。

**payload：**

```json
{
  "status": "SUCCESS",
  "message": "会话创建成功",
  "session_id": "sess_xxx",
  "session_timeout_seconds": 3600
}
```

| 字段 | 说明 |
|------|------|
| session_timeout_seconds | 会话超时时长（秒） |

### 5.3 RESPONSE（业务响应）

**统一结构**：流式文本、流式语音、函数调用可同时出现在同一报文中，客户端按类型分流展示（如不同消息气泡）。

**payload：**

```json
{
  "request_id": "req_xxx",
  "text_stream_seq": 0,
  "voice_stream_seq": 0,
  "function_call": {
    "name": "get_exhibit_info",
    "parameters": { "exhibit_id": "1001" }
  },
  "content": {
    "text": "您好，这件文物制作于清代。",
    "voice": "base64_audio_data"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| request_id | string | 是 | 回显请求 ID |
| text_stream_seq | number | 否 | 文本流序号，-1 表示文本流结束 |
| voice_stream_seq | number | 否 | 语音流序号，-1 表示语音流结束 |
| interrupted | boolean | 否 | 是否被中断（仅在最后一帧且被中断时为 true） |
| interrupt_reason | string | 否 | 中断原因（当 interrupted=true 时提供） |
| function_call | object | 否 | 需客户端执行的函数调用 |
| function_call.name | string | 是 | 函数名 |
| function_call.parameters | object | 是 | 参数键值对 |
| content | object | 否 | 文本/语音内容 |
| content.text | string | 有文本时 | 文本片段 |
| content.voice | string | 有语音时 | Base64 编码 PCM |

#### 5.3.1 流式规则

- 文本流：`text_stream_seq` 从 0 递增，最后一帧为 `-1`
- 语音流：`voice_stream_seq` 从 0 递增，最后一帧为 `-1`
- 单条报文中可同时携带文本分片、语音分片和 `function_call`
- `function_call` 通常出现在首条 RESPONSE，客户端按收到顺序处理
- 语音统一以 Base64 置于 `content.voice`，便于与文本、函数调用同帧传输

#### 5.3.2 RequireTTS 与响应类型

- `require_tts=false`：仅返回文本
- `require_tts=true`：除文本外追加语音，文本与语音流可交错

#### 5.3.3 中断标记

当请求被中断时，服务端发送最后一帧 RESPONSE，标记为中断：

```json
{
  "request_id": "req_xxx",
  "text_stream_seq": -1,
  "voice_stream_seq": -1,
  "interrupted": true,
  "interrupt_reason": "USER_NEW_INPUT",
  "content": {}
}
```

客户端收到后应：
1. 停止音频播放
2. 清理该请求的 UI 状态
3. 标记该消息为"已中断"（可选显示）

### 5.4 INTERRUPT_ACK（中断确认）

**payload：**

```json
{
  "interrupted_request_ids": ["req_xxx", "req_yyy"],
  "status": "SUCCESS",
  "message": "已中断 2 个请求"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| interrupted_request_ids | array | 被中断的请求ID列表 |
| status | string | `SUCCESS`（全部成功）/ `PARTIAL`（部分成功）/ `FAILED`（失败） |
| message | string | 描述信息 |

**说明：**

- 服务端收到 INTERRUPT 后立即返回此确认
- 如果指定的请求不存在或已完成，返回空列表和 FAILED 状态
- 客户端可根据此确认判断中断是否成功

### 5.5 SESSION_INFO

**payload：**

```json
{
  "status": "SUCCESS",
  "message": "查询成功",
  "session_data": {
    "platform": "WEB",
    "require_tts": true,
    "enable_srs": true,
    "function_calling": [],
    "create_time": 1740000000000,
    "remaining_seconds": 3000
  }
}
```

| session_data 字段 | 说明 |
|-------------------|------|
| platform | 客户端平台 |
| require_tts | 当前 TTS 需求 |
| enable_srs | 当前增强检索开关 |
| function_calling | 当前函数列表 |
| create_time | 会话创建时间戳（毫秒） |
| remaining_seconds | 剩余有效时长（秒） |

### 5.6 SHUTDOWN（服务器发起）

**payload：**

```json
{
  "reason": "会话超时"
}
```

### 5.7 HEARTBEAT

**payload：**

```json
{
  "remaining_seconds": 3000
}
```

### 5.8 HEALTH_CHECK_ACK

**payload：**

```json
{
  "health_status": {
    "cpu_usage": 20,
    "conn_count": 50,
    "status": "HEALTHY"
  }
}
```

### 5.9 SESSION_WARN

**payload：**

```json
{
  "warn_type": "EXPIRE_SOON",
  "remaining_seconds": 300,
  "message": "会话即将在 5 分钟后超时，请发送请求刷新"
}
```

### 5.10 ERROR

**payload：**

```json
{
  "error_code": "SESSION_INVALID",
  "error_msg": "会话不存在或已超时",
  "error_detail": "",
  "retryable": false,
  "request_id": "req_xxx"
}
```

`request_id` 在可关联到具体请求时填写。

#### 错误码

| 错误码 | 场景 | retryable |
|--------|------|-----------|
| AUTH_FAILED | 注册认证失败 | true |
| SESSION_INVALID | 会话无效或超时 | false |
| STREAM_SEQ_ERROR | 流式序号异常 | true |
| PAYLOAD_TOO_LARGE | 数据过大 | false |
| SERVER_BUSY | 服务过载 | true |
| MALFORMED_PAYLOAD | 报文格式错误 | false |
| INTERNAL_ERROR | 服务端内部错误 | true |
| REQUEST_TIMEOUT | 处理超时 | true |

---

## 六、核心流程

### 6.1 注册

1. 客户端建立 WebSocket 连接
2. 发送 REGISTER（`session_id` 为空）
3. 服务端校验用户（SQLite 等），创建会话
4. 成功：返回 REGISTER_ACK，失败：返回 ERROR(`AUTH_FAILED`)，并关闭连接

### 6.2 服务请求与响应

1. 客户端发送 REQUEST（含 `request_id`）
2. 服务端先处理会话属性更新（`require_tts`、`enable_srs`、`function_calling`）
3. 文本：直接使用；语音：流式转发 STT，等待完整文本（关闭中间结果）
4. 根据会话 `enable_srs` 决定是否调用 SRS 做语义检索（若为 false 则跳过）
5. 构建提示词：用户输入 + 函数定义 + SRS 结果（如有），调用 LLM
6. 按会话 `require_tts` 决定是否流式调用 TTS
7. 以 RESPONSE 流式返回文本/语音/`function_call`，`request_id` 回显

### 6.3 心跳

- 服务端定时（如 30s）发送 HEARTBEAT
- 客户端回复 HEARTBEAT_REPLY
- 服务端据此刷新会话超时；超时前一段时间可发送 SESSION_WARN

### 6.4 打断机制

**流程：**

1. 用户在智能体回复过程中发送新消息（或主动停止）
2. 客户端立即：
   - 停止音频播放
   - 发送 INTERRUPT（指定 `interrupt_request_id` 或留空中断所有）
3. 服务端收到后：
   - 设置取消信号（`asyncio.Event`）
   - LLM/TTS 等异步任务检查信号并停止
   - 返回 INTERRUPT_ACK 确认
   - 发送最后一帧 RESPONSE（`interrupted: true`）
4. 客户端收到确认后：
   - 清理旧请求的 UI 状态
   - 开始处理新请求

**示例时序：**

```
Client                          Server
  |                               |
  |------ REQUEST(req_1) -------->|
  |<----- RESPONSE(seq:0) --------|
  |<----- RESPONSE(seq:1) --------|
  |                               |
  | [用户发送新消息]               |
  |                               |
  |------ INTERRUPT(req_1) ------>| [设置 cancel_event]
  | [停止音频播放]                 |
  |                               |
  |<--- INTERRUPT_ACK ------------|
  |<--- RESPONSE(seq:-1,          |
  |     interrupted:true) --------|
  |                               |
  |------ REQUEST(req_2) -------->| [处理新请求]
  |<----- RESPONSE(seq:0) --------|
```

### 6.5 结束

- 任一方发送 SHUTDOWN 后，对方可直接关闭 WebSocket

---

## 七、实现说明

### 7.1 客户端行为

- 收到 RESPONSE 时按 `request_id` 归并到对应请求
- 根据 `text_stream_seq`、`voice_stream_seq` 区分文本流、语音流，并按 `-1` 判断结束
- 对 `function_call` 按到达顺序执行，通常首条 RESPONSE 即包含
- 文本、语音、函数调用可分别渲染为不同类型消息气泡

### 7.2 服务端行为

- REQUEST 中若提供 `require_tts`、`enable_srs` 或 `function_calling_op` + `function_calling`，立即覆盖会话缓存
- 语音请求：STT 流式输入、完整输出；仅在拿到完整文本后根据 `enable_srs` 决定是否调用 SRS，然后调用 LLM
- TTS：LLM 文本流式输出 → 流式 TTS，支持异步收发以降低延迟
- 语音回复以 Base64 写入 `content.voice`，与文本、函数调用同报文中返回

### 7.3 语音格式

- PCM：16kHz，16bit，单声道（具体以 SRS/STT/TTS 配置为准）
- Base64 编码采用 UTF-8 字符串
