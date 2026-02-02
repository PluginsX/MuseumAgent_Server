# -*- coding: utf-8 -*-
"""
标准化指令生成模块 - 整合LLM与知识库结果，生成通用化标准化指令
"""
import json
from typing import Any, Dict

from src.core.dynamic_llm_client import DynamicLLMClient
# 知识库查询已移至RAG模块，在LLM处理之前执行


class CommandGenerator:
    """通用化指令生成器，整合LLM解析与知识库数据"""
    
    def __init__(self, use_dynamic_llm: bool = True) -> None:
        """实例化DynamicLLMClient与ArtifactKnowledgeBase
        
        Args:
            use_dynamic_llm: 是否使用动态LLM客户端（支持会话感知）
        """
        # 强制使用动态LLM客户端（传统模式已移除）
        self.use_dynamic_llm = True
        self.llm_client = DynamicLLMClient()
        # 知识库查询已移至RAG模块处理
    
    def parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """
        解析LLM纯JSON响应字符串为字典
        
        Args:
            llm_response: LLM返回的JSON字符串（可能包含markdown代码块）
        
        Returns:
            解析后的字典，包含 artifact_name, operation, keywords
        
        Raises:
            ValueError: JSON格式错误
        """
        text = llm_response.strip()
        
        # 去除可能的markdown代码块标记
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM响应JSON格式错误: {str(e)}") from e
    
    def generate_standard_command(
        self,
        user_input: str,
        scene_type: str = "public",
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        生成通用化标准化指令（核心业务逻辑）
        
        Args:
            user_input: 用户自然语言输入
            scene_type: 场景类型
            session_id: 会话ID（用于动态指令集）
        
        Returns:
            标准化指令字典，符合StandardCommand模型格式
        
        Raises:
            ValueError: 参数校验失败、LLM解析异常
            RuntimeError: 知识库查询失败、操作非法
        """
        # 1. 调用LLM解析用户输入（必须使用会话感知的动态LLM）
        print(f"[DEBUG] CommandGenerator - use_dynamic_llm: {self.use_dynamic_llm}, session_id: {session_id}")
        
        # 强制使用动态LLM客户端，必须有有效的会话ID
        if not self.use_dynamic_llm:
            raise RuntimeError("系统配置错误：必须启用动态LLM模式")
            
        if not session_id:
            raise ValueError("缺少会话ID：所有请求必须在有效会话上下文中执行")
        
        print(f"[DEBUG] 使用动态LLM客户端处理会话: {session_id}")
        llm_raw = self.llm_client.parse_user_input_with_session(
            session_id=session_id,
            user_input=user_input,
            scene_type=scene_type
        )
        
        # 2. 解析LLM JSON响应
        llm_data = self.parse_llm_response(llm_raw)
        print(f"[DEBUG] LLM原始响应数据: {llm_data}")
        print(f"[DEBUG] LLM响应中是否包含response字段: {'response' in llm_data}")
        
        # 3. 提取核心字段
        artifact_name = llm_data.get("artifact_name") or llm_data.get("artifactName")
        operation = llm_data.get("operation")
        keywords = llm_data.get("keywords") or []
        
        # 4. 确保operation字段存在（格式验证）
        if not operation:
            operation = "general_chat"  # 默认回退到通用对话
        
        operation = str(operation).strip()
        
        # 5. 直接返回LLM原始响应数据（透传模式）
        print(f"[DEBUG] 透传LLM原始响应数据")
        # 5. 确保必要的字段存在
        command = {
            "artifact_id": llm_data.get("artifact_id"),
            "artifact_name": llm_data.get("artifact_name"),
            "operation": operation,  # 使用验证后的operation
            "operation_params": llm_data.get("operation_params", {}),
            "keywords": keywords,
            "tips": llm_data.get("tips"),
            "response": llm_data.get("response", "")
        }
        print(f"[DEBUG] 透传的指令数据: {command}")
        
        return command
