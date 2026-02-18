# -*- coding: utf-8 -*-
"""
标准化指令生成模块（重构版）- 作为各专业模块的协调器
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict

from src.core.dynamic_llm_client import DynamicLLMClient
from src.core.modules.semantic_retrieval_processor import SemanticRetrievalProcessor
from src.core.modules.prompt_builder import PromptBuilder
from src.core.modules.response_parser import ResponseParser
from src.session.strict_session_manager import strict_session_manager
# RAG模块：在LLM处理之前执行检索增强


class CommandGenerator:
    """通用化指令生成器（协调器模式）"""
    
    def __init__(self, use_dynamic_llm: bool = True) -> None:
        """初始化各专业模块
        
        Args:
            use_dynamic_llm: 是否使用动态LLM客户端（支持会话感知）
        """
        # 强制使用动态LLM客户端（传统模式已移除）
        self.use_dynamic_llm = True
        self.llm_client = DynamicLLMClient()
        
        # 初始化各专业模块
        self.rag_processor = SemanticRetrievalProcessor()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
    
    def parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """
        解析LLM响应（委托给ResponseParser）
        """
        return self.response_parser.parse_llm_response(llm_response)
    
    def _perform_rag_retrieval(self, user_input: str, top_k: int = None) -> Dict[str, Any]:
        """
        执行RAG检索（委托给RAGProcessor）
        """
        return self.rag_processor.perform_retrieval(user_input, top_k)
    
    def _build_rag_instruction(self, rag_context: Dict[str, Any]) -> str:
        """
        构建RAG指令（委托给PromptBuilder）
        """
        return self.prompt_builder.build_rag_instruction(rag_context)
    
    def generate_standard_command(
        self,
        user_input: str,
        scene_type: str = "public",
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        生成标准化指令 - 严格基于OpenAI Function Calling标准
        完全移除传统操作集模式，只支持函数调用
        
        Args:
            user_input: 用户自然语言输入
            scene_type: 场景类型
            session_id: 会话ID（必须提供）
        
        Returns:
            标准化指令字典（基于函数调用结果）
        """
        print(f"[Coordinator] 开始OpenAI标准函数调用流程")
        
        # 参数验证
        if not session_id:
            raise ValueError("缺少会话ID：所有请求必须在有效会话上下文中执行")
        
        # 1. 检查会话的 EnableSRS 配置
        session = strict_session_manager.get_session(session_id)
        enable_srs = True  # 默认启用
        if session:
            enable_srs = session.client_metadata.get("enable_srs", True)
        
        print(f"[Coordinator] EnableSRS 配置: {enable_srs}")
        
        # 2. 根据 EnableSRS 决定是否执行 RAG 检索
        rag_context = None
        if enable_srs:
            print(f"[Coordinator] 步骤1: 执行 RAG 检索（EnableSRS=True）")
            rag_context = self._perform_rag_retrieval(user_input)
            rag_context["timestamp"] = datetime.now().isoformat()
        else:
            print(f"[Coordinator] 步骤1: 跳过 RAG 检索（EnableSRS=False）")
        
        # 3. 获取会话中的OpenAI标准函数定义
        print(f"[Coordinator] 步骤2: 获取函数定义（可能为空）")
        print(f"[Coordinator] Session ID: {session_id}")
        functions = strict_session_manager.get_functions_for_session(session_id)
        print(f"[Coordinator] 获取到的函数数量: {len(functions)}")
        if functions:
            print(f"[Coordinator] 函数列表: {[f.get('name') for f in functions]}")
        
        # 支持无函数定义的普通对话模式
        if not functions:
            print(f"[Coordinator] 检测到普通对话模式，跳过函数调用流程")
        else:
            print(f"[Coordinator] 检测到函数调用模式，函数数量: {len(functions)}")
        
        # 4. 构建RAG增强的提示词（基于Function Calling）
        print(f"[Coordinator] 步骤3: 构建基于Function Calling的提示词")
        rag_instruction = None
        if rag_context:
            rag_instruction = self._build_rag_instruction(rag_context)
        
        # 5. 生成OpenAI标准函数调用负载
        print(f"[Coordinator] 步骤4: 生成OpenAI标准函数调用请求")
        payload = self.llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input=user_input,
            scene_type=scene_type,
            rag_instruction=rag_instruction,
            functions=functions  # 从会话中获取的已验证函数定义
        )
        
        # 6. 调用LLM执行函数调用
        print(f"[Coordinator] 步骤5: 调用LLM处理函数调用")
        print(f"[DEBUG] 发送到LLM的请求负载:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        response = self.llm_client._chat_completions_with_functions(payload)
        
        # 输出LLM原始响应
        print(f"[DEBUG] 步骤5完成 - LLM原始响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 7. 直接转发LLM原始响应，不做任何处理
        print(f"[Coordinator] 步骤6: 直接转发LLM原始响应")
        
        # 输出即将返回的数据
        print(f"[DEBUG] 步骤6完成 - 即将返回给API层的数据:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 直接返回LLM的完整原始响应
        print(f"[Coordinator] 处理完成，直接转发LLM原始响应")
        return response
    
    async def stream_generate(
        self,
        user_input: str,
        session_id: str = None,
        scene_type: str = "public",
        cancel_event: 'asyncio.Event' = None
    ):
        """
        流式生成文本（异步生成器，支持取消）
        
        Args:
            user_input: 用户输入
            session_id: 会话ID
            scene_type: 场景类型
            cancel_event: 取消事件（可选）
        
        Yields:
            文本片段
        """
        print(f"[Coordinator] 开始流式生成")
        
        # 参数验证
        if not session_id:
            raise ValueError("缺少会话ID：所有请求必须在有效会话上下文中执行")
        
        # 1. 检查会话的 EnableSRS 配置
        session = strict_session_manager.get_session(session_id)
        enable_srs = True  # 默认启用
        if session:
            enable_srs = session.client_metadata.get("enable_srs", True)
        
        print(f"[Coordinator] EnableSRS 配置: {enable_srs}")
        
        # 2. 根据 EnableSRS 决定是否执行 RAG 检索
        rag_context = None
        if enable_srs:
            print(f"[Coordinator] 步骤1: 执行 RAG 检索（EnableSRS=True）")
            rag_context = self._perform_rag_retrieval(user_input)
            rag_context["timestamp"] = datetime.now().isoformat()
        else:
            print(f"[Coordinator] 步骤1: 跳过 RAG 检索（EnableSRS=False）")
        
        # 3. 获取会话中的 OpenAI 标准函数定义
        print(f"[Coordinator] 步骤2: 获取函数定义（可能为空）")
        functions = strict_session_manager.get_functions_for_session(session_id)
        
        # 支持无函数定义的普通对话模式
        if not functions:
            print(f"[Coordinator] 检测到普通对话模式，跳过函数调用流程")
        else:
            print(f"[Coordinator] 检测到函数调用模式，函数数量: {len(functions)}")
        
        # 4. 构建 RAG 增强的提示词（基于 Function Calling）
        print(f"[Coordinator] 步骤3: 构建基于 Function Calling 的提示词")
        rag_instruction = None
        if rag_context:
            rag_instruction = self._build_rag_instruction(rag_context)
        
        # 5. 生成 OpenAI 标准函数调用负载
        print(f"[Coordinator] 步骤4: 生成 OpenAI 标准函数调用请求")
        payload = self.llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input=user_input,
            scene_type=scene_type,
            rag_instruction=rag_instruction,
            functions=functions
        )
        
        # 6. 调用 LLM 流式生成（支持函数调用和取消）
        print(f"[Coordinator] 步骤5: 调用 LLM 流式生成")
        print(f"[DEBUG] 发送到 LLM 的请求负载:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        async for chunk in self.llm_client._chat_completions_with_functions_stream(payload, cancel_event):
            # ✅ 检查取消信号
            if cancel_event and cancel_event.is_set():
                print(f"[Coordinator] LLM 生成被取消")
                return
            yield chunk
