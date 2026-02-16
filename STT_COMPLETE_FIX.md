# STT 识别失败问题完整修复

## 问题总结

客户端发送的语音数据，服务器 STT 完全无法识别。经过排查，发现了两个关键问题：

### 问题1：日志方法名错误 ✅ 已修复

**位置**: `src/services/stt_service.py` 第 107 行  
**错误**: 调用了 `logger.stt.warning()`，但 `ModuleLogger` 只有 `warn()` 方法  
**影响**: 导致整个 STT 流程崩溃，抛出 `AttributeError`  
**修复**: 将 `logger.stt.warning()` 改为 `logger.stt.warn()`

### 问题2：PCM 格式未转换 ✅ 已修复

**位置**: `src/services/stt_service.py` 第 165-175 行  
**错误**: 客户端发送的是裸 PCM 数据，但代码没有转换为 WAV 格式  
**影响**: DashScope SDK 不支持裸 PCM，导致识别失败  
**修复**: 在识别前检测 PCM 格式并自动转换为 WAV

## 详细分析

### 客户端发送的音频格式

客户端 (`AudioService.js`) 发送的音频数据：
- **格式**: 裸 PCM（Raw PCM）
- **采样率**: 16kHz
- **位深度**: 16bit
- **声道**: 单声道（Mono）
- **字节序**: 小端序（Little Endian）

```javascript
// AudioService.js - 录音处理
const pcmData = new Int16Array(inputData.length);
for (let i = 0; i < inputData.length; i++) {
    const s = Math.max(-1, Math.min(1, inputData[i]));
    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
}
// 发送 pcmData.buffer (裸 PCM 数据)
```

### DashScope SDK 支持的格式

阿里云 DashScope 的 `paraformer-realtime-v2` 模型支持：
- ✅ WAV
- ✅ MP3
- ✅ Opus
- ✅ OGG
- ❌ **不支持裸 PCM**

### 原代码的问题

```python
# 原代码（错误）
if audio_format_hint:
    audio_format = audio_format_hint.lower()  # 'pcm'
    file_suffix = f'.{audio_format}'          # '.pcm'
    # ... 直接使用 PCM 格式调用 DashScope
    recognition = Recognition(
        model=self.stt_model,
        format=audio_format,  # ❌ 'pcm' - 不支持！
        sample_rate=16000,
        callback=SimpleRecognitionCallback()
    )
```

虽然代码中有 `_convert_pcm_to_wav()` 方法，但从未被调用！

## 修复方案

### 修复代码

```python
# 修复后的代码
if audio_format_hint:
    audio_format = audio_format_hint.lower()
    file_suffix = f'.{audio_format}'
    self.logger.stt.info(f"Using provided audio format hint: {audio_format}")
else:
    audio_format, file_suffix = self._detect_audio_format(audio_data)

# 🔧 关键修复：如果是 PCM 格式，必须转换为 WAV
if audio_format == 'pcm':
    self.logger.stt.info("Converting PCM to WAV format for DashScope compatibility")
    audio_data = self._convert_pcm_to_wav(audio_data)
    audio_format = 'wav'
    file_suffix = '.wav'

# 现在使用 WAV 格式调用 DashScope ✅
recognition = Recognition(
    model=self.stt_model,
    format=audio_format,  # ✅ 'wav' - 支持！
    sample_rate=16000,
    callback=SimpleRecognitionCallback()
)
```

### WAV 转换逻辑

`_convert_pcm_to_wav()` 方法会添加 44 字节的 WAV 文件头：

```python
def _convert_pcm_to_wav(self, pcm_data: bytes) -> bytes:
    import struct
    
    # WAV 文件参数
    sample_rate = 16000
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data)
    file_size = 36 + data_size
    
    # 构建 WAV 文件头（44字节）
    wav_header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',           # ChunkID
        file_size,         # ChunkSize
        b'WAVE',           # Format
        b'fmt ',           # Subchunk1ID
        16,                # Subchunk1Size (PCM)
        1,                 # AudioFormat (PCM)
        num_channels,      # NumChannels
        sample_rate,       # SampleRate
        byte_rate,         # ByteRate
        block_align,       # BlockAlign
        bits_per_sample,   # BitsPerSample
        b'data',           # Subchunk2ID
        data_size          # Subchunk2Size
    )
    
    return wav_header + pcm_data
```

## 工作流程

### 修复前（失败）

```
客户端发送 PCM 数据
    ↓
服务器接收 (audio_format_hint='pcm')
    ↓
直接使用 PCM 格式调用 DashScope
    ↓
DashScope 不支持 PCM ❌
    ↓
识别失败，返回空字符串
    ↓
客户端收到 "抱歉，我没有听清楚您说什么。"
```

### 修复后（成功）

```
客户端发送 PCM 数据
    ↓
服务器接收 (audio_format_hint='pcm')
    ↓
检测到 PCM 格式
    ↓
调用 _convert_pcm_to_wav() 转换
    ↓
添加 44 字节 WAV 文件头
    ↓
使用 WAV 格式调用 DashScope ✅
    ↓
识别成功，返回文本
    ↓
客户端收到正确的识别结果
```

## 日志输出

修复后，你应该能看到这样的日志：

```
[STT] [INFO] Using provided audio format hint: pcm
[STT] [INFO] Converting PCM to WAV format for DashScope compatibility
[STT] [INFO] Converted PCM to WAV: 32000 bytes PCM -> 32044 bytes WAV
[STT] [INFO] Starting speech recognition | {"audio_size": 32044, "format": "wav", "file_suffix": ".wav"}
[STT] [INFO] PCM audio duration: 1.000 seconds
[STT] [INFO] Audio data header (first 16 bytes): 52494646...
[STT] [INFO] STT recognition request sent | {"audio_size": 32044, "format": "wav", "model": "paraformer-realtime-v2"}
[STT] [INFO] STT recognition response received | {"recognized_text": "你好"}
[STT] [INFO] STT识别完成: 你好
```

## 测试验证

### 测试步骤

1. 重启服务器
2. 打开客户端 http://localhost:18000/index.html
3. 点击话筒按钮
4. 说话："你好"
5. 观察服务器日志

### 预期结果

✅ 看到 "Converting PCM to WAV format" 日志  
✅ 看到 "STT recognition response received" 日志  
✅ 看到识别出的文本  
✅ 客户端收到正确的回复

### 如果仍然失败

检查以下几点：

1. **API 密钥配置**
   ```json
   // config.json
   {
     "stt": {
       "api_key": "sk-xxx",  // 确保配置了有效的 API 密钥
       "model": "paraformer-realtime-v2"
     }
   }
   ```

2. **音频时长**
   - 如果音频 < 0.5 秒，可能识别失败
   - 日志会显示: "Audio duration too short: 0.123s < 0.5s"

3. **音频内容**
   - 如果全是静音（零值），识别会失败
   - 日志会显示: "zero_ratio=100.00%"

4. **网络连接**
   - 确保服务器能访问阿里云 DashScope API
   - 检查防火墙和代理设置

## 修改的文件

1. **src/services/stt_service.py**
   - 第 107 行: `logger.stt.warning()` → `logger.stt.warn()`
   - 第 165-175 行: 添加 PCM 到 WAV 的自动转换逻辑

## 总结

这两个问题都是关键性的：

1. **日志错误**导致整个 STT 流程崩溃
2. **格式不兼容**导致 DashScope SDK 无法识别

修复后，STT 应该能正常工作了！🎉

