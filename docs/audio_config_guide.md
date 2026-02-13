# 音频服务配置说明

## TTS（文本转语音）配置

在 `config/config.json` 文件中，TTS服务支持以下配置选项：

```json
{
  "tts": {
    "base_url": "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
    "api_key": "your-api-key-here",
    "model": "cosyvoice-v3-plus",
    "voice": "HanLi",                           // 音色名称
    "format": "MP3_22050HZ_MONO_256KBPS"       // 音频格式
  }
}
```

### 配置项说明

- `base_url`: TTS服务的WebSocket基础URL
- `api_key`: 用于认证的API密钥
- `model`: 使用的TTS模型名称
- `voice`: 语音合成的音色名称（如 "HanLi", "Zhiyan" 等）
- `format`: 输出音频的格式规格

### 支持的音频格式

常见的音频格式包括：
- `MP3_22050HZ_MONO_256KBPS`
- `MP3_24000HZ_MONO_32KBPS`
- `WAV_16000HZ_MONO`
- `PCM_16000HZ_MONO`

### 支持的音色

不同的TTS模型支持不同的音色，具体请参考阿里云DashScope文档。

## STT（语音转文本）配置

```json
{
  "stt": {
    "base_url": "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
    "api_key": "your-api-key-here",
    "model": "paraformer-realtime-v2"
  }
}
```