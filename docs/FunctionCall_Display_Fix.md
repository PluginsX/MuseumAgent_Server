# 函数调用气泡显示问题修复文档

## 问题描述

用户报告：当服务器触发函数调用时，Web 客户端没有创建函数调用消息气泡。

### 现象
- 服务器日志显示 LLM 正确返回了函数调用信息（如 `play_animation`）
- 服务器日志显示函数调用被正确解析
- 但客户端界面没有显示函数调用气泡

### 预期行为
客户端应该接收到三种类型的消息并分别创建对应气泡：
1. 流式文字 → 文本气泡
2. 流式语音 → 语音气泡
3. 函数调用 → 函数调用气泡

## 问题分析

### 服务器端流程
1. **LLM 返回函数调用**：阿里云 Qwen 模型正确返回函数调用信息
   ```json
   {
     "function_call": {
       "name": "play_animation",
       "arguments": "{\"animation_name\": \"jump\"}"
     }
   }
   ```

2. **dynamic_llm_client.py 处理**：
   - 流式接收函数调用的 name 和 arguments
   - 累积完整的 arguments 字符串
   - 尝试解析为 JSON
   - 成功后 yield `{'type': 'function_call', 'name': ..., 'arguments': ...}`

3. **request_processor.py 转发**：
   - 接收 CommandGenerator 的 chunk
   - 检测到 `type == 'function_call'`
   - 调用 `send_function_call()` 生成 payload
   - yield 给 agent_handler

4. **agent_handler.py 发送**：
   - 接收 payload
   - 包装为 RESPONSE 消息
   - 通过 WebSocket 发送给客户端

### 客户端端流程
1. **WebSocketClient.js 接收**：
   - `_handleResponse()` 处理 RESPONSE 消息
   - 检查 `payload.function_call`
   - 调用 `request.onFunctionCall(payload.function_call)`

2. **MessageService.js 处理**：
   - `onFunctionCall` 回调被触发
   - 生成新的消息 ID
   - 调用 `stateManager.addMessage()` 创建函数调用气泡
   - 触发 `Events.FUNCTION_CALL` 事件

### 发现的问题

**问题 1：函数名被空字符串覆盖**

在 `dynamic_llm_client.py` 的 `_chat_completions_with_functions_stream` 方法中：

```python
# 收集函数名称
if 'name' in function_call:
    function_call_name = function_call['name']  # ❌ 问题：空字符串会覆盖已有的函数名
```

**问题分析**：
1. 第一个 delta 包含函数名：`{"name": "play_animation", "arguments": ""}`
2. 后续 delta 只包含参数：`{"name": "", "arguments": "{\"animation_name\":"}`
3. 空字符串 `""` 覆盖了之前的 `"play_animation"`
4. 到 `[DONE]` 时，`function_call_name` 是空字符串，导致函数调用不被 yield

**日志证据**：
```
[19:45:30.884] [LLM] [INFO] Updated function call name | {"function_name": "play_animation"}
...
[19:45:30.885] [LLM] [INFO] Updated function call name | {"function_name": ""}  # ❌ 被覆盖
...
[19:45:31.003] [LLM] [INFO] No function call to process at [DONE]  # ❌ 因为 name 为空
```

**问题 2：函数调用可能被 yield 两次**

在同一方法中，函数调用可能在两个地方 yield：
1. 当参数完整且可以解析为 JSON 时
2. 在收到 `[DONE]` 标记时

虽然这不是导致不显示的主要原因，但需要添加标志避免重复 yield。

## 修复方案

### 修改文件：`src/core/dynamic_llm_client.py`

#### 1. 添加 `function_call_yielded` 标志

```python
function_call_name = None
function_call_arguments = ""
function_call_yielded = False  # 标记函数调用是否已经被yield
```

#### 2. 修复函数名被空字符串覆盖的问题（关键修复）

```python
# 收集函数名称（只在有值时更新，避免空字符串覆盖）
if 'name' in function_call and function_call['name']:  # ✅ 添加非空检查
    function_call_name = function_call['name']
    self.logger.llm.info('Updated function call name', {
        'function_name': function_call_name
    })
```

**修复说明**：
- 原代码：`if 'name' in function_call:` - 只要 key 存在就更新，即使值为空
- 修复后：`if 'name' in function_call and function_call['name']:` - 只在值非空时更新
- 这样可以保留第一次设置的函数名，不会被后续的空字符串覆盖

#### 3. 在成功 yield 后设置标志

```python
if function_call_name and function_call_arguments and not function_call_yielded:
    try:
        arguments_json = json.loads(function_call_arguments)
        self.logger.llm.info('Yielding function call', {
            'function_name': function_call_name,
            'arguments': arguments_json
        })
        yield {
            'type': 'function_call',
            'name': function_call_name,
            'arguments': arguments_json
        }
        function_call_yielded = True  # 标记已经yield
    except json.JSONDecodeError as e:
        pass
```

#### 4. 在 [DONE] 处检查标志

```python
if data_str == '[DONE]':
    if function_call_name and function_call_arguments and not function_call_yielded:
        try:
            arguments_json = json.loads(function_call_arguments)
            yield {
                'type': 'function_call',
                'name': function_call_name,
                'arguments': arguments_json
            }
            function_call_yielded = True
        except json.JSONDecodeError as e:
            pass
    break
```

## 测试验证

### 测试步骤
1. 重启服务器
2. 刷新客户端页面
3. 发送触发函数调用的消息，例如：
   - "你支持哪些函数调用"
   - "play_animation(jump)"
   - "play_animation(wave)"

### 预期结果
1. 服务器日志显示：
   ```
   [LLM] [INFO] Yielding function call | {"function_name": "play_animation", "arguments": {"animation_name": "jump"}}
   ```

2. 客户端控制台显示：
   ```
   [WebSocket] 收到函数调用: {name: "play_animation", parameters: {animation_name: "jump"}}
   ```

3. 客户端界面显示：
   - 创建函数调用气泡
   - 显示函数名称和参数
   - 气泡样式与文本/语音气泡不同

### 验证点
- ✅ 服务器正确 yield 函数调用（只 yield 一次）
- ✅ 客户端正确接收函数调用
- ✅ 客户端创建函数调用气泡
- ✅ 气泡显示正确的函数名称和参数
- ✅ 不会重复创建气泡

## 相关文件

### 服务器端
- `src/core/dynamic_llm_client.py` - LLM 客户端，处理流式响应
- `src/ws/request_processor.py` - 请求处理器，转发函数调用
- `src/ws/agent_handler.py` - WebSocket 处理器，发送消息
- `src/core/command_generator.py` - 命令生成器，协调 LLM 调用

### 客户端
- `client/web/Demo/src/core/WebSocketClient.js` - WebSocket 客户端
- `client/web/Demo/src/services/MessageService.js` - 消息服务
- `client/web/Demo/src/store/StateManager.js` - 状态管理器

## 注意事项

1. **函数调用只 yield 一次**：通过 `function_call_yielded` 标志确保
2. **参数必须完整**：只有当参数可以成功解析为 JSON 时才 yield
3. **兼容性**：修改不影响现有的文本和语音流处理
4. **日志完整**：保留所有日志以便调试

## 后续优化建议

1. **客户端气泡样式**：
   - 设计专门的函数调用气泡样式
   - 显示函数名称、参数、执行状态
   - 支持展开/折叠参数详情

2. **函数执行反馈**：
   - 显示函数执行中、成功、失败状态
   - 显示函数返回结果
   - 支持重试失败的函数调用

3. **函数调用历史**：
   - 记录所有函数调用
   - 支持查看历史调用记录
   - 支持导出调用日志

## 修复日期
2026-02-18

## 修复人员
AI Assistant

