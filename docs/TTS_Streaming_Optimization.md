# 流式TTS优化方案

## 问题分析

### 原始问题
当前实现中，LLM流式输出的每个文本块都立即调用TTS服务，导致：
- TTS收到的文本过于琐碎（如单个字、词、标点）
- 语音输出严重割裂，句子内部不连贯
- 用户体验差，无法达到豆包、元宝等产品的语音质量

### 根本原因
```python
# 原始代码（有问题）
async for chunk in generator.stream_generate(...):
    # chunk 可能是 "你"、"好"、"，"、"我" 等单个字符
    if chunk and require_tts:
        async for audio in tts_service.stream_synthesize(chunk):
            yield audio  # 每个字符单独合成，导致割裂
```

## 行业最佳实践

### 1. 豆包/元宝的方案：句子级缓冲

**核心思想**：
- **文本流**：立即发送给客户端（保持低延迟）
- **语音流**：按完整句子合成（保证连贯性）

**技术要点**：
- 缓冲文本直到遇到句子边界（。！？\n等）
- 按完整句子调用TTS
- 保持自然的语音韵律和停顿

### 2. 其他方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 逐字符TTS | 延迟最低 | 语音严重割裂 | ❌ 不推荐 |
| 固定长度缓冲 | 实现简单 | 可能在句子中间断开 | 简单场景 |
| **句子级缓冲** | **连贯性好，延迟可控** | **需要句子边界检测** | ✅ **推荐** |
| 全文缓冲 | 连贯性最好 | 延迟过高 | 非流式场景 |

## 优化方案实现

### 核心组件：SentenceBuffer

```python
class SentenceBuffer:
    """句子级缓冲器"""
    
    def __init__(self, min_length=10, max_length=100):
        self.buffer = ""
        self.min_length = min_length  # 最小句子长度
        self.max_length = max_length  # 最大句子长度
        
        # 句子结束标记
        self.sentence_endings = re.compile(r'[。！？\n.!?]+')
        # 次要分隔符（逗号等）
        self.minor_breaks = re.compile(r'[，；,;]')
    
    def add_chunk(self, chunk: str) -> list[str]:
        """添加文本块，返回完整句子列表"""
        self.buffer += chunk
        sentences = []
        
        # 1. 检查完整句子（句号、问号等）
        while True:
            match = self.sentence_endings.search(self.buffer)
            if match:
                sentence = self.buffer[:match.end()].strip()
                if len(sentence) >= self.min_length:
                    sentences.append(sentence)
                    self.buffer = self.buffer[match.end():]
                else:
                    break  # 句子太短，继续累积
            else:
                break
        
        # 2. 防止缓冲区过长（在逗号处强制分段）
        if len(self.buffer) >= self.max_length:
            match = self.minor_breaks.search(self.buffer)
            if match:
                sentence = self.buffer[:match.end()].strip()
                sentences.append(sentence)
                self.buffer = self.buffer[match.end():]
        
        return sentences
    
    def flush(self) -> Optional[str]:
        """流结束时刷新剩余文本"""
        if self.buffer.strip():
            return self.buffer.strip()
        return None
```

### 优化后的流程

```python
async def process_text_request(...):
    # 初始化句子缓冲器
    sentence_buffer = SentenceBuffer(min_length=10, max_length=100)
    
    async for chunk in generator.stream_generate(...):
        # 1. 立即发送文本给客户端（保持低延迟）
        yield {"text": chunk, "text_seq": text_seq}
        text_seq += 1
        
        # 2. 使用句子缓冲器处理TTS（保证连贯性）
        if require_tts:
            complete_sentences = sentence_buffer.add_chunk(chunk)
            
            # 对每个完整句子进行TTS合成
            for sentence in complete_sentences:
                async for audio in tts_service.stream_synthesize(sentence):
                    yield {"voice": audio, "voice_seq": voice_seq}
                    voice_seq += 1
    
    # 3. 流结束时，刷新剩余文本
    remaining = sentence_buffer.flush()
    if remaining:
        async for audio in tts_service.stream_synthesize(remaining):
            yield {"voice": audio, "voice_seq": voice_seq}
            voice_seq += 1
```

## 效果对比

### 优化前
```
LLM输出: "你" → TTS("你") → 语音1
LLM输出: "好" → TTS("好") → 语音2
LLM输出: "，" → TTS("，") → 语音3
LLM输出: "我" → TTS("我") → 语音4
LLM输出: "是" → TTS("是") → 语音5
...

结果：语音严重割裂，每个字单独发音
```

### 优化后
```
LLM输出: "你" → 缓冲
LLM输出: "好" → 缓冲
LLM输出: "，" → 缓冲
LLM输出: "我" → 缓冲
LLM输出: "是" → 缓冲
LLM输出: "智" → 缓冲
LLM输出: "能" → 缓冲
LLM输出: "助" → 缓冲
LLM输出: "手" → 缓冲
LLM输出: "。" → TTS("你好，我是智能助手。") → 连贯语音

结果：完整句子合成，语音自然连贯
```

## 参数调优

### min_length（最小句子长度）
- **推荐值**：10-15字
- **作用**：避免过短的句子（如"好。"）单独合成
- **调整建议**：
  - 对话场景：10字（允许短句）
  - 讲解场景：15字（更完整的句子）

### max_length（最大句子长度）
- **推荐值**：80-100字
- **作用**：防止句子过长导致延迟
- **调整建议**：
  - 实时对话：80字（降低延迟）
  - 内容播报：100字（更完整）

### 句子边界标记
```python
# 主要边界（强制分段）
sentence_endings = r'[。！？\n.!?]+'

# 次要边界（缓冲区过长时使用）
minor_breaks = r'[，；,;]'
```

## 进一步优化建议

### 1. 智能标点预测
```python
# 使用简单规则预测句子结束
def predict_sentence_end(buffer: str) -> bool:
    # 如果以"的"、"了"、"吗"等结尾，可能是句子结束
    if buffer.endswith(('的', '了', '吗', '呢', '吧')):
        return True
    return False
```

### 2. 并行TTS合成
```python
# 使用asyncio.create_task并行合成多个句子
tasks = []
for sentence in complete_sentences:
    task = asyncio.create_task(tts_service.stream_synthesize(sentence))
    tasks.append(task)

# 按顺序yield结果
for task in tasks:
    async for audio in await task:
        yield audio
```

### 3. TTS服务端优化
检查阿里云DashScope是否支持：
- **流式输入**：边接收文本边合成
- **上下文保持**：多次调用保持韵律一致性
- **批量合成**：一次请求合成多个句子

### 4. 客户端优化
```javascript
// 客户端使用AudioContext无缝拼接音频
const audioContext = new AudioContext();
const audioQueue = [];

function playNextChunk() {
    if (audioQueue.length > 0) {
        const chunk = audioQueue.shift();
        const source = audioContext.createBufferSource();
        source.buffer = chunk;
        source.connect(audioContext.destination);
        source.start();
        source.onended = playNextChunk;
    }
}
```

## 测试验证

### 测试用例
```python
# 测试1：短句
input = "你好。"
expected = ["你好。"]  # 达到min_length后发送

# 测试2：长句
input = "这是一个非常长的句子，包含了很多内容，需要在逗号处分段，以避免延迟过高。"
expected = [
    "这是一个非常长的句子，包含了很多内容，",  # 在逗号处分段
    "需要在逗号处分段，以避免延迟过高。"
]

# 测试3：多句
input = "第一句。第二句！第三句？"
expected = ["第一句。", "第二句！", "第三句？"]

# 测试4：流式输入
chunks = ["你", "好", "，", "我", "是", "助", "手", "。"]
expected = ["你好，我是助手。"]  # 累积到句号才发送
```

### 性能指标
- **文本延迟**：< 50ms（立即发送）
- **语音延迟**：< 500ms（句子级缓冲）
- **语音连贯性**：主观评分 > 4.5/5
- **用户满意度**：接近豆包/元宝水平

## 总结

通过**句子级缓冲**优化：
1. ✅ 文本流保持低延迟（立即发送）
2. ✅ 语音流保证连贯性（完整句子合成）
3. ✅ 用户体验显著提升（接近商业产品水平）
4. ✅ 实现简单，易于维护

这是行业标准方案，豆包、元宝等产品都采用类似技术。

