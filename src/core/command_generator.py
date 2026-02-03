# -*- coding: utf-8 -*-
"""
标准化指令生成模块（重构版）- 作为各专业模块的协调器
"""
from datetime import datetime
from typing import Any, Dict

from src.core.dynamic_llm_client import DynamicLLMClient
from src.core.modules.rag_processor import RAGProcessor
from src.core.modules.prompt_builder import PromptBuilder
from src.core.modules.response_parser import ResponseParser
from src.session.session_manager import session_manager
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
        生成通用化标准化指令（协调器模式）
        
        Args:
            user_input: 用户自然语言输入
            scene_type: 场景类型
            session_id: 会话ID（用于动态指令集）
        
        Returns:
            标准化指令字典
        """
        print(f"[Coordinator] 开始协调处理流程")
        print(f"[DEBUG] CommandGenerator - use_dynamic_llm: {self.use_dynamic_llm}, session_id: {session_id}")
        
        # 参数验证
        if not self.use_dynamic_llm:
            raise RuntimeError("系统配置错误：必须启用动态LLM模式")
            
        if not session_id:
            raise ValueError("缺少会话ID：所有请求必须在有效会话上下文中执行")
        
        # 1. 协调RAG检索
        print(f"[Coordinator] 步骤1: 协调RAG检索")
        rag_context = self._perform_rag_retrieval(user_input, top_k=3)
        rag_context["timestamp"] = datetime.now().isoformat()
        
        # 2. 协调提示词构建
        print(f"[Coordinator] 步骤2: 协调提示词构建")
        rag_instruction = self._build_rag_instruction(rag_context)
        
        # 3. 获取会话指令集
        session_ops = session_manager.get_operations_for_session(session_id) or ["general_chat"]
        
        # 4. 构建最终提示词
        print(f"[Coordinator] 步骤3: 构建最终提示词")
        final_prompt = self.prompt_builder.build_final_prompt(
            user_input=user_input,
            scene_type=scene_type,
            valid_operations=session_ops,
            rag_instruction=rag_instruction
        )
        
        # 5. 调用LLM
        print(f"[Coordinator] 步骤4: 调用LLM处理")
        llm_raw = self.llm_client._chat_completions(final_prompt)
        
        # 6. 解析响应（简化版）
        print(f"[Coordinator] 步骤5: 解析LLM响应")
        print(f"[DEBUG] LLM返回原始内容长度: {len(llm_raw)} 字符")
        llm_data = self.response_parser.parse_llm_response(llm_raw)
        print(f"[DEBUG] 解析后的数据: {llm_data}")
        
        # 7. 构建最终指令
        print(f"[Coordinator] 步骤6: 构建标准化指令")
        command = self.response_parser.build_standard_command(llm_data, rag_context)
        
        print(f"[Coordinator] 处理完成，共检索到 {rag_context.get('total_found', 0)} 个相关文物")
        return command
