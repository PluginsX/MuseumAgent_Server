# -*- coding: utf-8 -*-
"""
提示词构建器模块（重构版）
负责收集变量并调用模板引擎构建最终提示词
"""

from typing import Dict, Any, List, Optional
from src.common.config_utils import get_global_config
from src.common.enhanced_logger import get_enhanced_logger
from src.session.strict_session_manager import strict_session_manager
from .prompt_template_engine import PromptTemplateEngine


class PromptBuilder:
    """提示词构建器 - 负责收集变量并调用模板引擎"""
    
    def __init__(self):
        """初始化提示词构建器"""
        self.logger = get_enhanced_logger()
        self.template_engine = PromptTemplateEngine()
        self.logger.sys.info("PromptBuilder initialized with PromptTemplateEngine")
    
    def build_llm_payload(
        self,
        session_id: str,
        user_input: str,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建完整的LLM API请求payload
        
        流程：
        1. 从会话获取变量1、2、3
        2. 从函数定义生成变量4
        3. 从用户输入获取变量5
        4. 从RAG上下文获取变量6
        5. 调用模板引擎渲染系统消息和用户消息
        6. 从配置文件获取API参数
        7. 构建最终payload
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            rag_context: RAG检索上下文（可选）
        
        Returns:
            完整的LLM API请求payload
        """
        self.logger.llm.info("Building LLM payload", {
            "session_id": session_id[:8],
            "has_rag": bool(rag_context)
        })
        
        # 1. 收集所有变量
        variables = self._collect_variables(session_id, user_input, rag_context)
        
        # 2. 获取会话中的函数定义
        functions = strict_session_manager.get_functions_for_session(session_id)
        
        # 3. 渲染系统消息（使用变量1,2,3,4）
        system_message = self.template_engine.render_system_message({
            "role_description": variables["role_description"],
            "response_requirements": variables["response_requirements"],
            "scene_description": variables["scene_description"],
            "functions_description": variables["functions_description"]
        })
        
        # 4. 渲染用户消息（使用变量5,6）
        has_rag = bool(rag_context and rag_context.get("relevant_artifacts"))
        user_message = self.template_engine.render_user_message({
            "user_input": variables["user_input"],
            "retrieved_materials": variables.get("retrieved_materials", "")
        }, has_rag=has_rag)
        
        # 5. 构建messages数组
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        # 6. 从配置文件获取LLM API参数
        config = get_global_config()
        llm_config = config.get("llm", {})
        parameters = llm_config.get("parameters", {})
        
        # 7. 构建完整payload
        payload = {
            "model": llm_config.get("model", "qwen-turbo"),
            "messages": messages,
            "temperature": parameters.get("temperature", 0.1),
            "max_tokens": parameters.get("max_tokens", 1024),
            "top_p": parameters.get("top_p", 0.1),
        }
        
        # 8. 添加函数调用相关参数（如果有函数定义）
        if functions and len(functions) > 0:
            payload["functions"] = functions
            payload["function_call"] = "auto"
            self.logger.llm.info(f"Added {len(functions)} function definitions to payload")
        
        # 9. 添加其他可选参数
        if parameters.get("presence_penalty") is not None:
            payload["presence_penalty"] = parameters["presence_penalty"]
        if parameters.get("frequency_penalty") is not None:
            payload["frequency_penalty"] = parameters["frequency_penalty"]
        if parameters.get("n") is not None:
            payload["n"] = parameters["n"]
        if parameters.get("seed") is not None:
            payload["seed"] = parameters["seed"]
        
        self.logger.llm.info("LLM payload built successfully", {
            "system_message_length": len(system_message),
            "user_message_length": len(user_message),
            "has_functions": bool(functions),
            "function_count": len(functions) if functions else 0
        })
        
        return payload
    
    def _collect_variables(
        self,
        session_id: str,
        user_input: str,
        rag_context: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        收集所有变量
        
        Returns:
            包含所有6个变量的字典
        """
        session = strict_session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 变量1: 智能体角色描述
        role_description = self._get_role_description(session)
        
        # 变量2: 智能体响应要求
        response_requirements = self._get_response_requirements(session)
        
        # 变量3: 场景描述
        scene_description = self._get_scene_description(session)
        
        # 变量4: 函数描述
        functions = strict_session_manager.get_functions_for_session(session_id)
        functions_description = self._generate_functions_description(functions)
        
        # 变量5: 用户输入
        user_input_var = user_input
        
        # 变量6: 相关材料
        retrieved_materials = ""
        if rag_context:
            retrieved_materials = self._format_retrieved_materials(rag_context)
        
        variables = {
            "role_description": role_description,
            "response_requirements": response_requirements,
            "scene_description": scene_description,
            "functions_description": functions_description,
            "user_input": user_input_var,
            "retrieved_materials": retrieved_materials
        }
        
        self.logger.llm.info("Variables collected", {
            "role_description_length": len(role_description),
            "response_requirements_length": len(response_requirements),
            "scene_description_length": len(scene_description),
            "functions_count": len(functions) if functions else 0,
            "has_rag": bool(retrieved_materials)
        })
        
        return variables
    
    def _get_role_description(self, session) -> str:
        """从会话获取角色描述（变量1）"""
        system_prompt = session.client_metadata.get("system_prompt", {})
        role_description = system_prompt.get("role_description", "你是智能助手。")
        return role_description
    
    def _get_response_requirements(self, session) -> str:
        """从会话获取响应要求（变量2）"""
        system_prompt = session.client_metadata.get("system_prompt", {})
        response_requirements = system_prompt.get(
            "response_requirements",
            "请用友好、专业的语言回答问题。"
        )
        return response_requirements
    
    def _get_scene_description(self, session) -> str:
        """从会话获取场景描述（变量3）"""
        scene_context = session.client_metadata.get("scene_context", {})
        
        # 组合场景描述和场景特定提示
        scene_description = scene_context.get("scene_description", "当前场景：通用场景")
        scene_specific_prompt = scene_context.get("scene_specific_prompt", "")
        
        if scene_specific_prompt:
            return f"{scene_description}\n{scene_specific_prompt}"
        return scene_description
    
    def _generate_functions_description(self, functions: List[Dict[str, Any]]) -> str:
        """生成函数描述（变量4）"""
        if not functions:
            return "（当前场景无可用函数）"
        
        return self.template_engine.render_functions_description(functions)
    
    def _format_retrieved_materials(self, rag_context: Dict[str, Any]) -> str:
        """格式化检索材料（变量6）"""
        relevant_artifacts = rag_context.get("relevant_artifacts", [])
        
        if not relevant_artifacts:
            return ""
        
        return self.template_engine.render_rag_materials(relevant_artifacts)