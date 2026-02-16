# STT 识别失败问题修复

## 问题描述

服务器端 STT（语音转文本）完全无法识别客户端发送的语音数据，控制台显示错误：

```
[12:34:50.235] [STT] [ERROR] STT failed | {"error": "'ModuleLogger' object has no attribute 'warning'"}
```

## 根本原因

在 `src/services/stt_service.py` 第 107 行，代码调用了 `logger.stt.warning()`，但是 `ModuleLogger` 类只提供了 `warn()` 方法，没有 `warning()` 方法。

### 代码位置

**文件**: `src/services/stt_service.py`  
**行号**: 107  
**错误代码**:
```python
self.logger.stt.warning(f"Unknown audio format, header: {header.hex()}, defaulting to mp3")
```

### ModuleLogger 可用方法

查看 `src/common/enhanced_logger.py` 中的 `ModuleLogger` 类定义：

```python
class ModuleLogger:
    """模块日志记录器 - 提供便捷的模块级日志记录"""
    
    def __init__(self, parent_logger: EnhancedLogger, module: Module):
        self.parent = parent_logger
        self.module = module
    
    def trace(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.trace(self.module, message, data)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.debug(self.module, message, data)
    
    def info(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.info(self.module, message, data)
    
    def warn(self, message: str, data: Optional[Dict[str, Any]] = None):  # ✅ 正确方法
        self.parent.warn(self.module, message, data)
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.error(self.module, message, data)
    
    def fatal(self, message: str, data: Optional[Dict[str, Any]] = None):
        self.parent.fatal(self.module, message, data)
```

**注意**: 方法名是 `warn()`，不是 `warning()`！

## 修复方案

将 `logger.stt.warning()` 改为 `logger.stt.warn()`：

```python
# 修复前（错误）
self.logger.stt.warning(f"Unknown audio format, header: {header.hex()}, defaulting to mp3")

# 修复后（正确）
self.logger.stt.warn(f"Unknown audio format, header: {header.hex()}, defaulting to mp3")
```

## 影响范围

这个错误导致整个 STT 识别流程崩溃：

1. 客户端发送语音数据
2. 服务器调用 `recognize_audio()` 方法
3. 在 `_detect_audio_format()` 中检测音频格式
4. 如果格式未知，尝试调用 `logger.stt.warning()`
5. **抛出 AttributeError 异常**
6. STT 识别失败，返回空字符串
7. 客户端收到 "抱歉，我没有听清楚您说什么。"

## 测试验证

修复后，重启服务器并测试：

1. 客户端点击话筒发送语音
2. 服务器应该能正常识别
3. 控制台应该显示：
   ```
   [STT] [INFO] Starting speech recognition | {"audio_size": xxx, "format": "pcm", ...}
   [STT] [INFO] PCM audio duration: x.xxx seconds
   [STT] [INFO] Audio data header (first 16 bytes): ...
   [STT] [INFO] STT recognition request sent | {"audio_size": xxx, ...}
   [STT] [INFO] STT recognition response received | {"recognized_text": "..."}
   ```

## 其他潜在问题

虽然这个日志错误是主要问题，但 STT 识别还可能遇到其他问题：

### 1. 音频格式问题
客户端发送的是裸 PCM 数据（16bit, 16kHz, mono），但 DashScope SDK 的 `paraformer-realtime-v2` 模型不支持裸 PCM，需要转换为 WAV 格式。

**解决方案**: 代码中已经实现了 `_convert_pcm_to_wav()` 方法，但需要确保在识别前调用。

### 2. 音频时长太短
如果音频时长 < 0.5 秒，可能导致识别失败。

**日志提示**:
```
[STT] [INFO] Audio duration too short: 0.123s < 0.5s, may cause recognition failure
```

### 3. 音频数据全是静音
如果音频数据全是零（静音），识别会失败。

**日志提示**:
```
[STT] [INFO] Audio data analysis: non_zero=0/32000, zero_ratio=100.00%
```

### 4. API 密钥未配置
如果 `config.json` 中没有配置 STT API 密钥，会抛出异常。

**错误信息**:
```
RuntimeError: STT 未配置 api_key，请在 config.json 中设置
```

## 建议

1. **统一日志方法名**: 建议在 `ModuleLogger` 中添加 `warning()` 作为 `warn()` 的别名，避免类似错误：
   ```python
   def warning(self, message: str, data: Optional[Dict[str, Any]] = None):
       """warning() 是 warn() 的别名，保持与标准 logging 模块一致"""
       self.warn(message, data)
   ```

2. **代码审查**: 检查其他文件是否也有类似的 `logger.xxx.warning()` 调用

3. **单元测试**: 为日志系统添加单元测试，确保所有方法都可用

## 修改文件

- `src/services/stt_service.py` (第 107 行)

## 状态

✅ **已修复** - 将 `logger.stt.warning()` 改为 `logger.stt.warn()`

