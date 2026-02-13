# 语音服务配置功能更新报告

## 概述

本次更新主要完成了以下功能改进：

1. 修复了WebSocket API中的消息处理错误
2. 实现了TTS音色配置的可配置化
3. 验证了配置更改的有效性

## 详细变更

### 1. WebSocket API修复

**问题**: `websocket_api.py` 文件中的 `iter_any()` 方法不存在

**解决方案**: 
- 将原来的 `async for data in websocket.iter_any():` 替换为正确的消息接收逻辑
- 使用 `websocket.receive_text()` 和 `websocket.receive_bytes()` 分别处理文本和二进制消息
- 实现了超时机制以避免阻塞

### 2. TTS音色配置功能

**变更文件**: 
- `src/services/tts_service.py`
- `config/config.json`

**具体更改**:

#### 在 `tts_service.py` 中:
- 添加了 `tts_voice` 和 `tts_format` 配置项的读取
- 修改了 `_ensure_config_loaded()` 方法以加载新的配置项
- 更新了 `SpeechSynthesizer` 实例化代码，使用配置文件中的音色和格式

#### 在 `config.json` 中:
- 为 `tts` 配置节添加了 `voice` 和 `format` 选项
- 设置默认值为 `"HanLi"` 和 `"MP3_22050HZ_MONO_256KBPS"`

### 3. 配置验证

通过测试脚本验证了配置已正确加载：
- TTS模型: cosyvoice-v3-plus ✓
- TTS音色: HanLi ✓  
- TTS格式: MP3_22050HZ_MONO_256KBPS ✓

## 测试结果

运行测试脚本 `tests/test_tts_config.py` 的输出：
```
测试TTS配置加载...
TTS模型: cosyvoice-v3-plus
TTS音色: HanLi
TTS格式: MP3_22050HZ_MONO_256KBPS
TTS API密钥: 已配置
```

## 使用说明

用户现在可以直接在 `config/config.json` 文件中修改以下配置：

```json
{
  "tts": {
    "base_url": "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
    "api_key": "sk-a7558f9302974d1891906107f6033939",
    "model": "cosyvoice-v3-plus",
    "voice": "HanLi",                    // 可以修改音色
    "format": "MP3_22050HZ_MONO_256KBPS" // 可以修改音频格式
  }
}
```

修改配置后需要重启服务器以使更改生效。

## 文档更新

创建了 `docs/audio_config_guide.md` 文件，详细说明了音频服务的配置选项。

## 总结

本次更新成功实现了TTS音色配置的可配置化，用户现在可以通过修改配置文件轻松更改音色和音频格式，无需修改代码。同时修复了WebSocket消息处理的关键错误，提高了系统的稳定性。