# -*- coding: utf-8 -*-
"""
标准化指令生成模块 - 整合LLM与知识库结果，生成通用化标准化指令
"""
import json
from typing import Any, Dict

from src.core.llm_client import LLMClient
from src.core.knowledge_base import ArtifactKnowledgeBase


class CommandGenerator:
    """通用化指令生成器，整合LLM解析与知识库数据"""
    
    def __init__(self) -> None:
        """实例化LLMClient与ArtifactKnowledgeBase"""
        self.llm_client = LLMClient()
        self.knowledge_base = ArtifactKnowledgeBase()
    
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
        scene_type: str = "public"
    ) -> Dict[str, Any]:
        """
        生成通用化标准化指令（核心业务逻辑）
        
        Args:
            user_input: 用户自然语言输入
            scene_type: 场景类型
        
        Returns:
            标准化指令字典，符合StandardCommand模型格式
        
        Raises:
            ValueError: 参数校验失败、LLM解析异常
            RuntimeError: 知识库查询失败、操作非法
        """
        # 1. 调用LLM解析用户输入
        llm_raw = self.llm_client.parse_user_input(user_input, scene_type)
        
        # 2. 解析LLM JSON响应
        llm_data = self.parse_llm_response(llm_raw)
        
        # 3. 提取核心字段
        artifact_name = llm_data.get("artifact_name") or llm_data.get("artifactName")
        operation = llm_data.get("operation")
        keywords = llm_data.get("keywords") or []
        
        # 4. 空值校验
        if not artifact_name or not str(artifact_name).strip():
            raise ValueError("LLM解析结果中文物名称为空")
        if not operation or not str(operation).strip():
            raise ValueError("LLM解析结果中操作指令为空")
        if not isinstance(keywords, list):
            keywords = []
        
        artifact_name = str(artifact_name).strip()
        operation = str(operation).strip()
        
        # 5. 校验操作指令合法性
        if not self.knowledge_base.validate_operation(operation):
            valid_ops = self.knowledge_base.valid_operations
            raise ValueError(f"操作指令不合法，有效值为: {', '.join(valid_ops)}")
        
        # 6. 从知识库获取标准化文物数据
        artifact_data = self.knowledge_base.get_standard_artifact_data(artifact_name)
        
        # 7. 整合生成标准化指令
        command = {
            "artifact_id": artifact_data.get("artifact_id"),
            "artifact_name": artifact_data.get("artifact_name"),
            "operation": operation,
            "operation_params": artifact_data.get("operation_params") or {},
            "keywords": keywords,
            "tips": artifact_data.get("tips", "")
        }
        
        return command
