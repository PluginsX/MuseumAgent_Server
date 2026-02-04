# -*- coding: utf-8 -*-
"""
标准化指令生成模块（重构版）- 作为各专业模块的协调器
"""
import json
from datetime import datetime
from typing import Any, Dict

from src.core.dynamic_llm_client import DynamicLLMClient
from src.core.modules.rag_processor import RAGProcessor
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
        self.rag_processor = RAGProcessor()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
    
    def parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """
        解析LLM响应（委托给ResponseParser）
        """
        return self.response_parser.parse_llm_response(llm_response)
    
    def _perform_rag_retrieval(self, user_input: str, top_k: int = 3) -> Dict[str, Any]:
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
        
        # 1. 协调RAG检索
        print(f"[Coordinator] 步骤1: 执行RAG检索")
        rag_context = self._perform_rag_retrieval(user_input, top_k=3)
        rag_context["timestamp"] = datetime.now().isoformat()
        
        # 2. 获取会话中的OpenAI标准函数定义
        print(f"[Coordinator] 步骤2: 获取函数定义（可能为空）")
        functions = strict_session_manager.get_functions_for_session(session_id)
        
        # 支持无函数定义的普通对话模式
        if not functions:
            print(f"[Coordinator] 检测到普通对话模式，跳过函数调用流程")
        else:
            print(f"[Coordinator] 检测到函数调用模式，函数数量: {len(functions)}")
        
        # 3. 构建RAG增强的提示词（基于Function Calling）
        print(f"[Coordinator] 步骤3: 构建基于Function Calling的提示词")
        rag_instruction = self._build_rag_instruction(rag_context)
        
        # 4. 生成OpenAI标准函数调用负载
        print(f"[Coordinator] 步骤4: 生成OpenAI标准函数调用请求")
        payload = self.llm_client.generate_function_calling_payload(
            session_id=session_id,
            user_input=user_input,
            scene_type=scene_type,
            rag_instruction=rag_instruction,
            functions=functions  # OpenAI标准函数定义
        )
        
        # 5. 调用LLM执行函数调用
        print(f"[Coordinator] 步骤5: 调用LLM处理函数调用")
        print(f"[DEBUG] 发送到LLM的请求负载:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        response = self.llm_client._chat_completions_with_functions(payload)
        
        # 输出LLM原始响应
        print(f"[DEBUG] 步骤5完成 - LLM原始响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 6. 直接转发LLM原始响应，不做任何处理
        print(f"[Coordinator] 步骤6: 直接转发LLM原始响应")
        
        # 输出即将返回的数据
        print(f"[DEBUG] 步骤6完成 - 即将返回给API层的数据:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 直接返回LLM的完整原始响应
        print(f"[Coordinator] 处理完成，直接转发LLM原始响应")
        return response
