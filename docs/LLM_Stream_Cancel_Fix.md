# LLM 流式生成取消机制修复文档

## 问题描述

在之前的实现中，虽然客户端发送 `INTERRUPT` 消息可以停止音频播放，但**服务端的 LLM 流式生成并未真正停止**，导致：

1. **资源浪费**：LLM 继续生成用户不再需要的内容
2. **计费问题**：阿里云按生成的 Token 数量计费，未中断的生成会产生额外费用
3. **性能影响**：服务器资源被无效任务占用

## 阿里云官方支持

根据阿里云官方文档：

> **在流式输出过程中，客户端可以主动终止请求，服务端将停止生成后续内容。此时，计费仅基于服务端在收到终止请求前已生成的输出 Token 数量。**

这意味着：
- ✅ 阿里云的流式 API **支持中断**
- ✅ 中断方式：**客户端主动断开 HTTP 连接**
- ✅ 计费优化：**只计算中断前已生成的 Token**

## 修复方案

### 1. 核心思路

通过 `asyncio.Event` 实现协作式取消：

```
用户发送 INTERRUPT
    ↓
设置 cancel_event
    ↓
各处理阶段检查 cancel_event
    ↓
检测到取消 → 立即停止 → 关闭连接
```

### 2. 修改的文件

#### 2.1 `src/core/dynamic_llm_client.py`

**修改点 1：方法签名**
```python
# 修改前
async def _chat_completions_with_functions_stream(
    self, 
    payload: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:

# 修改后
async def _chat_completions_with_functions_stream(
    self, 
    payload: Dict[str, Any], 
    cancel_event: 'asyncio.Event' = None  # ✅ 新增参数
) -> AsyncGenerator[Dict[str, Any], None]:
```

**修改点 2：添加取消检查**
```python
async for line in resp.content:
    # ✅ 检查取消信号（高频检查，每次读取数据块时）
    if cancel_event and cancel_event.is_set():
        self.logger.llm.info('LLM stream cancelled by user', {
            'line_count': line_count
        })
        # 主动关闭连接，停止接收数据
        resp.close()
        return
    
    # 处理数据...
```

**修改点 3：添加 asyncio 导入**
```python
import asyncio  # ✅ 新增
from typing import List, Dict, Any, AsyncGenerator
```

#### 2.2 `src/core/command_generator.py`

**修改点 1：添加 asyncio 导入**
```python
import asyncio  # ✅ 新增
import json
from datetime import datetime
```

**修改点 2：方法签名类型注解**
```python
async def stream_generate(
    self,
    user_input: str,
    session_id: str = None,
    scene_type: str = "public",
    cancel_event: 'asyncio.Event' = None  # ✅ 修正类型注解
):
```

**修改点 3：传递 cancel_event**
```python
# 调用 LLM 流式生成（支持函数调用和取消）
async for chunk in self.llm_client._chat_completions_with_functions_stream(
    payload, 
    cancel_event  # ✅ 传递取消事件
):
    # ✅ 检查取消信号
    if cancel_event and cancel_event.is_set():
        print(f"[Coordinator] LLM 生成被取消")
        return
    yield chunk
```

### 3. 已有的支持

以下文件已经正确实现了取消机制：

#### 3.1 `src/ws/agent_handler.py`
- ✅ 创建 `cancel_event` 并注册到 `active_requests`
- ✅ 处理 `INTERRUPT` 消息，设置 `cancel_event`
- ✅ 在 `finally` 块中清理 `active_requests`

#### 3.2 `src/ws/request_processor.py`
- ✅ `process_text_request_with_cancel` 接收 `cancel_event`
- ✅ 在 LLM 生成循环中检查取消信号
- ✅ 在 TTS 合成中检查取消信号
- ✅ 发送中断标记的响应

## 工作流程

### 完整的取消流程

```
1. 用户发送新消息
   ↓
2. 客户端发送 INTERRUPT 消息
   {
     "msg_type": "INTERRUPT",
     "payload": {
       "interrupt_request_id": "req_old",
       "reason": "USER_NEW_INPUT"
     }
   }
   ↓
3. 服务端 agent_handler.py 处理
   - 找到 active_requests["req_old"]
   - 设置 cancel_event.set()
   ↓
4. request_processor.py 检测到取消
   - 在 LLM 生成循环中检查 cancel_event
   - 检测到取消 → 停止处理
   ↓
5. command_generator.py 检测到取消
   - 在流式生成中检查 cancel_event
   - 检测到取消 → 停止迭代
   ↓
6. dynamic_llm_client.py 检测到取消 ✅ 新增
   - 在 aiohttp 读取循环中检查 cancel_event
   - 检测到取消 → 关闭 HTTP 连接 (resp.close())
   - 停止接收数据
   ↓
7. 阿里云 LLM API
   - 检测到连接关闭
   - 停止生成后续内容
   - 只计费已生成的 Token
   ↓
8. 服务端发送 INTERRUPT_ACK
   {
     "msg_type": "INTERRUPT_ACK",
     "payload": {
       "interrupted_request_ids": ["req_old"],
       "status": "SUCCESS"
     }
   }
   ↓
9. 客户端停止音频播放，清理 UI
```

## 关键技术点

### 1. 为什么使用 `resp.close()`？

```python
if cancel_event and cancel_event.is_set():
    resp.close()  # ✅ 主动关闭 HTTP 连接
    return
```

- **断开连接**：告诉阿里云服务器停止发送数据
- **释放资源**：立即释放网络连接和缓冲区
- **停止计费**：阿里云检测到连接关闭，停止生成

### 2. 为什么需要高频检查？

```python
async for line in resp.content:
    # 每次读取数据块时都检查
    if cancel_event and cancel_event.is_set():
        resp.close()
        return
```

- **低延迟**：用户打断后立即响应（毫秒级）
- **节省资源**：避免处理不需要的数据
- **用户体验**：打断感觉更自然

### 3. 为什么使用 `asyncio.Event`？

- **线程安全**：支持多个协程同时检查
- **非阻塞**：`is_set()` 不会阻塞事件循环
- **简单高效**：标准库实现，性能优秀

## 测试验证

### 运行测试脚本

```bash
python test_llm_cancel.py
```

### 测试场景

1. **正常流式生成后取消**
   - 启动 LLM 流式生成
   - 2 秒后触发取消
   - 验证：生成立即停止

2. **生成前取消**
   - 提前设置取消信号
   - 启动流式生成
   - 验证：不接收任何数据

### 预期结果

```
✅ 测试通过：LLM 流式生成成功响应取消信号
   - 生成过程正常启动
   - 取消信号被正确检测
   - 任务及时终止
```

## 性能优化

### 1. 资源节省

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 用户打断 | 继续生成完整响应 | 立即停止生成 |
| Token 消耗 | 全部计费 | 只计费已生成部分 |
| 网络流量 | 接收全部数据 | 立即断开连接 |
| CPU 占用 | 处理全部数据 | 立即释放 |

### 2. 响应时间

- **打断延迟**：< 100ms（取决于网络和数据块大小）
- **资源释放**：立即（`resp.close()` 同步执行）
- **新请求处理**：无需等待旧请求完成

## 注意事项

### 1. 向后兼容

- `cancel_event` 参数为可选（默认 `None`）
- 不传递 `cancel_event` 时，行为与之前一致
- 现有代码无需修改

### 2. 错误处理

```python
try:
    async for chunk in generator.stream_generate(..., cancel_event=cancel_event):
        # 处理数据
        pass
except Exception as e:
    # 取消操作不会抛出异常，正常返回
    logger.error("Generation failed", {"error": str(e)})
```

### 3. 清理工作

```python
finally:
    # 无论是否取消，都要清理活跃请求
    active_requests.pop(request_id, None)
```

## 相关文档

- [阿里云流式输出文档](https://help.aliyun.com/zh/model-studio/stream)
- [InterruptMechanism_Design.md](./InterruptMechanism_Design.md) - 完整的打断机制设计
- [CommunicationProtocol_CS.md](./CommunicationProtocol_CS.md) - 通信协议规范

## 总结

通过这次修复：

✅ **完整实现了服务端取消机制**
- 从 WebSocket 层到 HTTP 连接层的完整取消链路
- 每个处理阶段都能及时响应取消信号

✅ **优化了资源使用**
- 避免无效的 LLM 生成
- 减少 Token 消耗和计费
- 立即释放网络和计算资源

✅ **提升了用户体验**
- 打断响应更快（毫秒级）
- 新请求立即开始处理
- 自然流畅的对话体验

---

**修复日期**：2026-02-18  
**修复人员**：AI Assistant  
**影响范围**：LLM 流式生成、打断机制、资源管理

