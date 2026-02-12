# -*- coding: utf-8 -*-
"""
服务模块组织结构
遵循高内聚、低耦合的设计原则

目录结构说明:
services/                 # 业务服务层
├── external_services.py  # 外部服务集成 (LLM, TTS, STT, SRS)
├── business_services.py  # 业务逻辑服务 (文本处理, 音频处理, 语音通话)
├── core_services.py      # 核心服务 (会话管理, 认证授权)
└── service_interfaces.py # 服务接口定义

各服务职责:
- UnifiedTTSService: 统一的文本转语音服务，支持流式和非流式
- UnifiedSTTService: 统一的语音转文本服务，支持流式和非流式  
- LLMServices: 语言模型服务接口
- SRSService: 语义检索服务接口
- TextProcessingService: 文本处理和业务逻辑编排
- AudioProcessingService: 音频处理和编排
- VoiceCallService: 语音通话管理
- SessionService: 用户会话和认证管理
"""

# 业务服务层 - 处理具体的业务逻辑
from .text_processing_service import TextProcessingService
from .audio_processing_service import AudioProcessingService
from .voice_call_service import VoiceCallService
from .session_service import SessionService

# 外部服务集成层 - 与外部系统交互
from .external_services import (
    UnifiedTTSService,
    UnifiedSTTService,
    LLMService,
    SRSService
)

# 服务接口定义
from .service_interfaces import (
    BaseService,
    TextProcessingServiceInterface,
    AudioProcessingServiceInterface,
    VoiceCallServiceInterface,
    LLMServicesInterface,
    SRSServiceInterface,
    TTSServiceInterface,
    STTServiceInterface,
    SessionServiceInterface
)

__all__ = [
    # 业务服务
    'TextProcessingService',
    'AudioProcessingService', 
    'VoiceCallService',
    'SessionService',
    
    # 外部服务
    'UnifiedTTSService',
    'UnifiedSTTService',
    'LLMService',
    'SRSService',
    
    # 服务接口
    'BaseService',
    'TextProcessingServiceInterface',
    'AudioProcessingServiceInterface',
    'VoiceCallServiceInterface',
    'LLMServicesInterface',
    'SRSServiceInterface',
    'TTSServiceInterface',
    'STTServiceInterface',
    'SessionServiceInterface'
]