# -*- coding: utf-8 -*-
"""
指令生成器（重构版）- 协调各模块完成LLM请求
"""
import asyncio
from typing import Any, Dict, Optional

from src.core.dynamic_llm_client import DynamicLLMClient
from src.core.modules.semantic_retrieval_processor import SemanticRetrievalProcessor
from src.core.modules.prompt_builder import PromptBuilder
from src.core.modules.response_parser import ResponseParser
from src.session.strict_session_manager import strict_session_manager
from src.common.enhanced_logger import get_enhanced_logger


class CommandGenerator:
    """指令生成器 - 协调器模式"""
    
    def __init__(self) -> None:
        """初始化各专业模块"""
        self.logger = get_enhanced_logger()
        self.rag_processor = SemanticRetrievalProcessor()
        self.prompt_builder = PromptBuilder()
        self.llm_client = DynamicLLMClient()
        self.response_parser = ResponseParser()
        
        self.logger.sys.info("CommandGenerator initialized with new architecture")
    
    def _should_perform_rag(self, session_id: str) -> bool:
        """检查是否应该执行RAG检索"""
        session = strict_session_manager.get_session(session_id)
        if not session:
            return False
        
        enable_srs = session.client_metadata.get("enable_srs", True)
        return enable_srs
    
    async def stream_generate(
        self,
        user_input: str,
        session_id: str,
        cancel_event: Optional[asyncio.Event] = None
    ):
        """
        流式生成响应
        
        流程：
        1. 检查enable_srs，决定是否执行RAG
        2. 调用PromptBuilder构建payload
        3. 调用LLMClient执行请求
        4. 流式返回结果
        
        Args:
            user_input: 用户输入
            session_id: 会话ID
            cancel_event: 取消事件（可选）
        
        Yields:
            流式响应片段
        """
        self.logger.llm.info("Starting stream generation", {
            "session_id": session_id[:8],
            "user_input_length": len(user_input)
        })
        
        # 参数验证
        if not session_id:
            raise ValueError("缺少会话ID：所有请求必须在有效会话上下文中执行")
        
        # 1. RAG检索（如果启用）
        rag_context = None
        if self._should_perform_rag(session_id):
            self.logger.rag.info("Performing RAG retrieval (enable_srs=True)")
            rag_context = self.rag_processor.perform_retrieval(user_input, session_id=session_id)
        else:
            self.logger.rag.info("Skipping RAG retrieval (enable_srs=False)")
        
        # 2. 构建payload（所有提示词构建逻辑都在PromptBuilder中）
        payload = self.prompt_builder.build_llm_payload(
            session_id=session_id,
            user_input=user_input,
            rag_context=rag_context
        )
        
        # 3. 调用LLM流式生成
        self.logger.llm.info("Calling LLM stream API")
        async for chunk in self.llm_client.chat_completion_stream(payload, cancel_event, session_id):
            # 检查取消信号
            if cancel_event and cancel_event.is_set():
                self.logger.llm.info("Stream generation cancelled")
                return
            yield chunk
        
        self.logger.llm.info("Stream generation completed")
