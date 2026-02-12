# -*- coding: utf-8 -*-
"""
外部服务集成模块
统一管理与外部服务的集成，包括：
- 语言模型服务 (LLM)
- 语音合成服务 (TTS) 
- 语音识别服务 (STT)
- 语义检索服务 (SRS)
"""

# 统一导入接口
from .tts_service import UnifiedTTSService
from .stt_service import UnifiedSTTService
from .llm_service import LLMService
from .srs_service import SRSService

__all__ = [
    'UnifiedTTSService',
    'UnifiedSTTService', 
    'LLMService',
    'SRSService'
]