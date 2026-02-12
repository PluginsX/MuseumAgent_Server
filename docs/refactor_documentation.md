# 重构后系统架构说明

## 项目结构优化

经过重构，项目现在具有更清晰的模块化结构，遵循高内聚、低耦合的设计原则。

### 目录结构

```
MuseumAgent_Server/
├── main.py                 # 主程序入口
├── config/
│   └── config.json         # 配置文件
├── src/
│   ├── gateway/            # API网关层
│   │   └── api_gateway.py  # API网关实现
│   ├── services/           # 业务服务层
│   │   ├── __init__.py     # 服务模块组织结构
│   │   ├── external_services.py    # 外部服务集成 (LLM, TTS, STT, SRS)
│   │   ├── service_interfaces.py   # 服务接口定义
│   │   ├── text_processing_service.py    # 文本处理服务
│   │   ├── audio_processing_service.py   # 音频处理服务
│   │   ├── voice_call_service.py         # 语音通话服务
│   │   ├── session_service.py            # 会话管理服务
│   │   ├── llm_service.py                # LLM服务接口
│   │   ├── srs_service.py                # SRS服务接口
│   │   ├── tts_service.py                # 统一TTS服务
│   │   └── stt_service.py                # 统一STT服务
│   ├── api/                # API接口层
│   │   └── ...             # 各种API端点实现
│   ├── common/             # 公共组件层
│   │   └── ...             # 日志、配置、工具等
│   ├── core/               # 核心引擎层
│   │   └── ...             # LLM客户端、命令生成器等
│   └── db/                 # 数据库层
│       └── ...             # 数据模型和数据库操作
├── client/                 # 客户端代码
│   └── ...
├── tests/                  # 测试代码
└── docs/                   # 文档
```

## 服务职责边界

### 1. 外部服务层 (external_services)
- **UnifiedTTSService**: 统一的文本转语音服务，支持流式和非流式合成
- **UnifiedSTTService**: 统一的语音转文本服务，支持流式和非流式识别
- **LLMService**: 语言模型服务接口，封装与外部LLM的通信
- **SRSService**: 语义检索服务接口，封装与SRS系统的通信

### 2. 业务服务层 (business_logic)
- **TextProcessingService**: 文本处理和业务逻辑编排，协调LLM和SRS服务
- **AudioProcessingService**: 音频处理和编排，协调STT和TTS服务
- **VoiceCallService**: 语音通话管理，处理实时语音对话
- **SessionService**: 用户会话和认证管理

### 3. API网关层 (gateway)
- 统一入口点
- 认证与授权
- 请求路由
- 协议转换

## 重构亮点

### 1. 消除重复实现
- 原来的 `AliyunTTSClient` 和 `TTSService` 合并为统一的 `UnifiedTTSService`
- 原来的 `STTService` 功能得到增强，支持流式和非流式两种模式
- 所有TTS/STT功能集中在统一服务中，避免重复代码

### 2. 明确职责边界
- 外部服务层：纯粹的外部API集成，不包含业务逻辑
- 业务服务层：编排外部服务，实现业务逻辑
- API网关层：处理HTTP/WebSocket协议，身份验证

### 3. 接口规范化
- 定义了标准的服务接口
- 便于测试和替换实现
- 提高代码可维护性

### 4. 配置驱动
- 所有服务配置集中管理
- 支持运行时配置更新
- 环境适应性强

## 性能优化

### 1. 模块化设计
- 每个服务职责单一
- 降低模块间耦合度
- 提高代码可重用性

### 2. 异步处理
- 充分利用异步I/O
- 提高并发处理能力
- 优化资源利用率

### 3. 统一错误处理
- 标准化的错误响应格式
- 统一的日志记录格式
- 便于监控和调试

## 维护建议

1. **新增功能**：应遵循服务分层原则，新功能应添加到对应的服务层
2. **修改现有功能**：优先考虑在现有服务接口内扩展，保持接口稳定性
3. **性能优化**：可在不影响接口的情况下优化内部实现
4. **测试**：每层应有对应的单元测试和集成测试

通过这次重构，系统变得更加模块化、可维护和可扩展，为未来的功能开发奠定了坚实的基础。