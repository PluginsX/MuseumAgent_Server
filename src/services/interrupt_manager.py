# -*- coding: utf-8 -*-
"""
统一打断管理器
负责协调所有服务模块的中断操作
"""
import asyncio
from typing import Dict, Optional, Any
from src.common.enhanced_logger import get_enhanced_logger


class InterruptManager:
    """
    统一打断管理器
    
    职责：
    1. 管理每个会话的活跃任务引用
    2. 提供统一的中断接口
    3. 协调各个服务模块的中断操作
    """
    
    def __init__(self):
        self.logger = get_enhanced_logger()
        
        # 每个会话的活跃任务引用
        # 结构: {session_id: {
        #     "stt_session": SpeechSynthesizer实例,
        #     "srs_session": aiohttp.ClientSession实例,
        #     "llm_session": aiohttp.ClientSession实例,
        #     "tts_synthesizer": SpeechSynthesizer实例,
        #     "request_id": str
        # }}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def register_session(self, session_id: str, request_id: str):
        """
        注册新会话
        
        Args:
            session_id: 会话ID
            request_id: 请求ID
        """
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {}
        
        self.active_sessions[session_id]["request_id"] = request_id
        self.logger.ws.debug("Session registered in interrupt manager", {
            "session_id": session_id[:16],
            "request_id": request_id[:16]
        })
    
    def register_stt(self, session_id: str, recognition_instance):
        """
        注册STT识别实例
        
        Args:
            session_id: 会话ID
            recognition_instance: DashScope Recognition实例
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["stt_recognition"] = recognition_instance
            self.logger.stt.debug("STT recognition registered", {"session_id": session_id[:16]})
    
    def register_srs(self, session_id: str, http_session):
        """
        注册SRS HTTP会话
        
        Args:
            session_id: 会话ID
            http_session: aiohttp.ClientSession实例
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["srs_session"] = http_session
            self.logger.rag.debug("SRS session registered", {"session_id": session_id[:16]})
    
    def register_llm(self, session_id: str, http_session):
        """
        注册LLM HTTP会话
        
        Args:
            session_id: 会话ID
            http_session: aiohttp.ClientSession实例
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["llm_session"] = http_session
            self.logger.llm.debug("LLM session registered", {"session_id": session_id[:16]})
    
    def register_tts(self, session_id: str, synthesizer_instance):
        """
        注册TTS合成器实例
        
        Args:
            session_id: 会话ID
            synthesizer_instance: DashScope SpeechSynthesizer实例
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["tts_synthesizer"] = synthesizer_instance
            self.logger.tts.debug("TTS synthesizer registered", {"session_id": session_id[:16]})
    
    async def interrupt_stt(self, session_id: str) -> bool:
        """
        中断STT语音识别
        
        统一方法：关闭连接
        实现：调用 recognition.stop() 关闭 WebSocket 连接
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功中断
        """
        if session_id not in self.active_sessions:
            return False
        
        recognition = self.active_sessions[session_id].get("stt_recognition")
        if recognition:
            try:
                self.logger.stt.info("Interrupting STT (closing connection)", {"session_id": session_id[:16]})
                await asyncio.to_thread(recognition.stop)
                self.active_sessions[session_id].pop("stt_recognition", None)
                self.logger.stt.info("STT interrupted", {"session_id": session_id[:16]})
                return True
            except Exception as e:
                self.logger.stt.error("Failed to interrupt STT", {"error": str(e)})
                return False
        return False
    
    async def interrupt_srs(self, session_id: str) -> bool:
        """
        中断SRS语义检索
        
        统一方法：关闭连接
        实现：关闭 HTTP 会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功中断
        """
        if session_id not in self.active_sessions:
            return False
        
        http_session = self.active_sessions[session_id].get("srs_session")
        if http_session:
            try:
                self.logger.rag.info("Interrupting SRS (closing connection)", {"session_id": session_id[:16]})
                await http_session.close()
                self.active_sessions[session_id].pop("srs_session", None)
                self.logger.rag.info("SRS interrupted", {"session_id": session_id[:16]})
                return True
            except Exception as e:
                self.logger.rag.error("Failed to interrupt SRS", {"error": str(e)})
                return False
        return False
    
    async def interrupt_llm(self, session_id: str) -> bool:
        """
        中断LLM流式输出
        
        统一方法：关闭连接
        实现：关闭 HTTP 会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功中断
        """
        if session_id not in self.active_sessions:
            return False
        
        http_session = self.active_sessions[session_id].get("llm_session")
        if http_session:
            try:
                self.logger.llm.info("Interrupting LLM (closing connection)", {"session_id": session_id[:16]})
                await http_session.close()
                self.active_sessions[session_id].pop("llm_session", None)
                self.logger.llm.info("LLM interrupted", {"session_id": session_id[:16]})
                return True
            except Exception as e:
                self.logger.llm.error("Failed to interrupt LLM", {"error": str(e)})
                return False
        return False
    
    async def interrupt_tts(self, session_id: str) -> bool:
        """
        中断TTS语音合成
        
        统一方法：关闭连接
        实现：关闭 WebSocket 连接（通过删除引用触发）
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功中断
        """
        if session_id not in self.active_sessions:
            return False
        
        synthesizer = self.active_sessions[session_id].get("tts_synthesizer")
        if synthesizer:
            try:
                self.logger.tts.info("Interrupting TTS (closing connection)", {"session_id": session_id[:16]})
                self.active_sessions[session_id].pop("tts_synthesizer", None)
                self.logger.tts.info("TTS interrupted", {"session_id": session_id[:16]})
                return True
            except Exception as e:
                self.logger.tts.error("Failed to interrupt TTS", {"error": str(e)})
                return False
        return False
    
    async def interrupt_all(self, session_id: str) -> Dict[str, bool]:
        """
        中断所有流程（总中断函数）
        
        按顺序中断：
        1. STT（如果正在识别）
        2. SRS（如果正在检索）
        3. LLM（如果正在生成）
        4. TTS（如果正在合成）
        
        Args:
            session_id: 会话ID
            
        Returns:
            各模块的中断结果
        """
        self.logger.ws.info("Interrupting all processes for session", {"session_id": session_id[:16]})
        
        results = {
            "stt": await self.interrupt_stt(session_id),
            "srs": await self.interrupt_srs(session_id),
            "llm": await self.interrupt_llm(session_id),
            "tts": await self.interrupt_tts(session_id)
        }
        
        interrupted_count = sum(1 for v in results.values() if v)
        self.logger.ws.info("All processes interrupted", {
            "session_id": session_id[:16],
            "interrupted_count": interrupted_count,
            "results": results
        })
        
        return results
    
    def cleanup_session(self, session_id: str):
        """
        清理会话
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.active_sessions:
            self.active_sessions.pop(session_id)
            self.logger.ws.debug("Session cleaned up from interrupt manager", {"session_id": session_id[:16]})


# 全局单例
_interrupt_manager = None

def get_interrupt_manager() -> InterruptManager:
    """获取全局中断管理器实例"""
    global _interrupt_manager
    if _interrupt_manager is None:
        _interrupt_manager = InterruptManager()
    return _interrupt_manager

