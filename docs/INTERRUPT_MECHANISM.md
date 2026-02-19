# 打断机制实现文档

## 概述

本文档详细说明了博物馆智能体服务器的打断机制实现。该机制确保当用户发送新请求时，服务器能够立即中断所有正在进行的旧任务，包括 STT、SRS、LLM 和 TTS。

## 核心设计原则

1. **立即响应**：新请求到达时，立即中断所有旧任务
2. **流式封口**：发送结束帧（`text_stream_seq=-1`, `voice_stream_seq=-1`）确保客户端正确关闭旧流
3. **资源清理**：断开所有网络连接，释放资源
4. **轻量级**：最小化性能开销

## 架构设计

### 1. 统一中断管理器 (`InterruptManager`)

位置：`src/services/interrupt_manager.py`

**职责：**
- 管理每个会话的活跃任务引用（STT、SRS、LLM、TTS）
- 提供统一的中断接口
- 协调各个服务模块的中断操作

**核心方法：**

```python
class InterruptManager:
    def register_session(session_id, request_id)  # 注册新会话
    def register_stt(session_id, recognition)     # 注册STT实例
    def register_srs(session_id, http_session)    # 注册SRS HTTP会话
    def register_llm(session_id, http_session)    # 注册LLM HTTP会话
    def register_tts(session_id, synthesizer)     # 注册TTS实例
    
    async def interrupt_stt(session_id)           # 中断STT
    async def interrupt_srs(session_id)           # 中断SRS
    async def interrupt_llm(session_id)           # 中断LLM
    async def interrupt_tts(session_id)           # 中断TTS
    
    async def interrupt_all(session_id)           # 中断所有流程（总函数）
    def cleanup_session(session_id)               # 清理会话
```

### 2. 各模块中断策略

#### STT（语音识别）中断

**方法：** 调用 `recognition.stop()` 关闭 WebSocket 连接

```python
async def interrupt_stt(self, session_id: str) -> bool:
    recognition = self.active_sessions[session_id].get("stt_recognition")
    if recognition:
        await asyncio.to_thread(recognition.stop)  # 阻塞调用，在线程中执行
        return True
    return False
```

**集成点：**
- `src/services/stt_service.py` 的 `stream_recognize()` 方法
- 启动识别后立即注册到中断管理器

#### SRS（语义检索）中断

**方法：** 关闭 `aiohttp.ClientSession`，断开 HTTP 连接

```python
async def interrupt_srs(self, session_id: str) -> bool:
    http_session = self.active_sessions[session_id].get("srs_session")
    if http_session:
        await http_session.close()  # 关闭HTTP会话
        return True
    return False
```

**集成点：**
- `src/core/modules/semantic_retrieval_processor.py` 的 `perform_retrieval()` 方法
- 注意：`semantic_retrieval_client` 内部使用 HTTP 会话，需要在客户端层面处理

#### LLM（大语言模型）中断

**方法：** 关闭 `aiohttp.ClientSession`，断开流式 HTTP 连接

```python
async def interrupt_llm(self, session_id: str) -> bool:
    http_session = self.active_sessions[session_id].get("llm_session")
    if http_session:
        await http_session.close()  # 关闭HTTP会话，中断流式输出
        return True
    return False
```

**集成点：**
- `src/core/dynamic_llm_client.py` 的 `_chat_completions_with_functions_stream()` 方法
- 创建 `aiohttp.ClientSession` 后立即注册到中断管理器

#### TTS（语音合成）中断

**方法：** 删除 `SpeechSynthesizer` 引用，标记中断

```python
async def interrupt_tts(self, session_id: str) -> bool:
    synthesizer = self.active_sessions[session_id].get("tts_synthesizer")
    if synthesizer:
        # DashScope SpeechSynthesizer 没有显式的 stop 方法
        # 通过删除引用来标记中断
        self.active_sessions[session_id].pop("tts_synthesizer", None)
        return True
    return False
```

**集成点：**
- `src/services/tts_service.py` 的 `stream_synthesize()` 方法
- 创建 `SpeechSynthesizer` 后立即注册到中断管理器
- 在生成循环中检查 `cancel_event`

### 3. 打断流程

#### 触发时机

新请求到达时，满足以下条件之一：
1. **文本消息**：直接触发打断
2. **语音消息**：
   - 流式语音的起始帧（`stream_seq == 0`）
   - 非流式语音

#### 执行步骤

在 `src/ws/agent_handler.py` 的 `_handle_request()` 方法中：

```python
# 1. 调用统一中断管理器，中断所有服务模块
interrupt_results = await interrupt_manager.interrupt_all(session_id)

# 2. 取消旧的 asyncio 任务
if session_id in active_tasks:
    old_task = active_tasks[session_id]
    if not old_task.done():
        old_task.cancel()

# 3. 发送结束帧，封口旧消息流
await manager.send_json(session_id, build_message("RESPONSE", {
    "request_id": "interrupted",
    "text_stream_seq": -1,
    "content": {}
}, session_id))

if require_tts:
    await manager.send_json(session_id, build_message("RESPONSE", {
        "request_id": "interrupted",
        "voice_stream_seq": -1,
        "content": {}
    }, session_id))
```

## 数据流图

```
新请求到达
    ↓
检查是否需要打断
    ↓
调用 interrupt_manager.interrupt_all(session_id)
    ├─→ interrupt_stt()  → recognition.stop()
    ├─→ interrupt_srs()  → http_session.close()
    ├─→ interrupt_llm()  → http_session.close()
    └─→ interrupt_tts()  → 删除 synthesizer 引用
    ↓
取消 asyncio.Task
    ↓
发送流式结束帧
    ├─→ text_stream_seq: -1
    └─→ voice_stream_seq: -1
    ↓
开始处理新请求
```

## 关键代码位置

### 核心文件

1. **中断管理器**
   - `src/services/interrupt_manager.py` - 统一中断管理器

2. **服务模块集成**
   - `src/services/stt_service.py` - STT 中断集成
   - `src/services/tts_service.py` - TTS 中断集成
   - `src/services/llm_service.py` - LLM 中断集成（未直接使用）
   - `src/core/dynamic_llm_client.py` - LLM 实际中断集成
   - `src/core/modules/semantic_retrieval_processor.py` - SRS 中断集成

3. **请求处理**
   - `src/ws/agent_handler.py` - 打断触发逻辑
   - `src/ws/request_processor.py` - 文本请求处理
   - `src/core/command_generator.py` - 命令生成器

### 参数传递链

为了支持中断，`session_id` 需要在整个调用链中传递：

```
agent_handler.py (_handle_request)
    ↓ session_id
request_processor.py (process_text_request_with_cancel)
    ↓ session_id
command_generator.py (stream_generate)
    ↓ session_id
dynamic_llm_client.py (_chat_completions_with_functions_stream)
    → 注册 LLM HTTP 会话

同时：
    ↓ session_id
tts_service.py (stream_synthesize)
    → 注册 TTS 合成器
```

## 测试验证

### 测试场景

1. **文本打断测试**
   - 发送长文本请求
   - 在 LLM 流式输出过程中发送新请求
   - 验证：旧请求立即停止，新请求立即开始

2. **语音打断测试**
   - 发送语音请求（触发 STT）
   - 在 STT 识别过程中发送新请求
   - 验证：STT 立即停止，新请求立即开始

3. **TTS 打断测试**
   - 发送需要 TTS 的文本请求
   - 在 TTS 合成过程中发送新请求
   - 验证：TTS 立即停止，新请求立即开始

4. **完整流程打断测试**
   - 发送语音请求（STT → SRS → LLM → TTS）
   - 在任意阶段发送新请求
   - 验证：所有流程立即停止，新请求立即开始

### 验证指标

- **响应延迟**：新请求到达后，服务器响应时间 < 100ms
- **流式封口**：客户端收到 `text_stream_seq=-1` 和 `voice_stream_seq=-1`
- **资源清理**：旧任务的网络连接全部关闭
- **无数据混合**：新旧消息数据不会混合

## 注意事项

1. **DashScope SDK 限制**
   - `SpeechSynthesizer` 没有显式的 `stop()` 方法
   - 通过删除引用和检查 `cancel_event` 来实现中断

2. **异步任务取消**
   - 使用 `asyncio.Task.cancel()` 取消任务
   - 在生成器中捕获 `asyncio.CancelledError`

3. **HTTP 会话管理**
   - 确保每个请求使用独立的 `aiohttp.ClientSession`
   - 中断时关闭会话，释放连接

4. **流式数据封口**
   - 必须发送结束帧（`seq=-1`）
   - 确保客户端正确关闭旧流

## 性能优化

1. **并行中断**：所有模块的中断操作并行执行
2. **快速响应**：中断操作不等待任务完成
3. **轻量级注册**：只存储必要的引用，不复制数据
4. **自动清理**：任务完成后自动清理注册信息

## 未来改进

1. **更细粒度的中断**：支持只中断特定模块
2. **中断优先级**：根据请求类型设置中断优先级
3. **中断统计**：记录中断次数和原因，用于分析
4. **优雅降级**：中断失败时的降级策略

---

**文档版本**：1.0  
**最后更新**：2026-02-19  
**维护者**：开发团队

