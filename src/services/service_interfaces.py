# -*- coding: utf-8 -*-
"""
服务接口定义
定义各个服务的职责边界和接口规范
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime


class BaseService(ABC):
    """基础服务抽象类"""
    
    @abstractmethod
    async def process(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        处理请求的通用方法
        
        Args:
            request: 请求数据
            token: 认证令牌
            
        Returns:
            处理结果
        """
        pass


class TextProcessingServiceInterface(BaseService):
    """文本处理服务接口"""
    
    @abstractmethod
    async def process_text(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        处理文本请求
        
        Args:
            request: 文本处理请求
            token: 认证令牌
            
        Returns:
            处理结果
        """
        pass


class AudioProcessingServiceInterface(BaseService):
    """音频处理服务接口"""
    
    @abstractmethod
    async def stt_convert(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        音频转文本
        
        Args:
            request: 音频转文本请求
            token: 认证令牌
            
        Returns:
            转换结果
        """
        pass
    
    @abstractmethod
    async def tts_convert(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        文本转音频
        
        Args:
            request: 文本转音频请求
            token: 认证令牌
            
        Returns:
            转换结果
        """
        pass


class VoiceCallServiceInterface(BaseService):
    """语音通话服务接口"""
    
    @abstractmethod
    async def start_call(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        启动语音通话
        
        Args:
            request: 通话启动请求
            token: 认证令牌
            
        Returns:
            通话启动结果
        """
        pass
    
    @abstractmethod
    async def process_audio_stream(self, audio_generator: AsyncGenerator[bytes, None], 
                                 call_id: str) -> AsyncGenerator[bytes, None]:
        """
        处理音频流
        
        Args:
            audio_generator: 音频数据生成器
            call_id: 通话ID
            
        Yields:
            处理后的音频数据
        """
        pass


class LLMServicesInterface(BaseService):
    """LLM服务接口"""
    
    @abstractmethod
    async def chat_completion(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        聊天补全
        
        Args:
            request: 聊天请求
            token: 认证令牌
            
        Returns:
            聊天响应
        """
        pass


class SRSServiceInterface(BaseService):
    """SRS服务接口"""
    
    @abstractmethod
    async def search_artifacts(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        搜索资料
        
        Args:
            request: 搜索请求
            token: 认证令牌
            
        Returns:
            搜索结果
        """
        pass


class TTSServiceInterface(ABC):
    """TTS服务接口"""
    
    @abstractmethod
    async def synthesize_text(self, text: str) -> Optional[bytes]:
        """
        合成文本为语音（非流式）
        
        Args:
            text: 要合成的文本
            
        Returns:
            音频数据
        """
        pass
    
    @abstractmethod
    async def stream_synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        流式语音合成
        
        Args:
            text: 要合成的文本
        
        Yields:
            音频数据块
        """
        pass


class STTServiceInterface(ABC):
    """STT服务接口"""
    
    @abstractmethod
    async def recognize_audio(self, audio_data: bytes) -> str:
        """
        识别音频为文本（非流式）
        
        Args:
            audio_data: 音频数据
            
        Returns:
            识别出的文本
        """
        pass
    
    @abstractmethod
    async def stream_recognize(self, audio_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
        """
        流式语音识别
        
        Args:
            audio_generator: 音频数据生成器
        
        Yields:
            识别出的文本片段
        """
        pass


class SessionServiceInterface(BaseService):
    """会话服务接口"""
    
    @abstractmethod
    async def login(self, credentials: Dict[str, str], token: str = None) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            credentials: 登录凭证
            token: 认证令牌（通常为空，因为这是认证入口）
            
        Returns:
            登录结果
        """
        pass
    
    @abstractmethod
    async def validate_session(self, session_id: str, token: str = None) -> Dict[str, Any]:
        """
        验证会话
        
        Args:
            session_id: 会话ID
            token: 认证令牌
            
        Returns:
            验证结果
        """
        pass