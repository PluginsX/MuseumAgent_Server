# -*- coding: utf-8 -*-
"""
响应解析器模块
负责解析LLM返回的JSON响应
"""

import json
from typing import Dict, Any
from ...common.enhanced_logger import get_enhanced_logger


class ResponseParser:
    """LLM响应解析器（简化版）"""
    
    def __init__(self):
        """初始化解析器"""
        self.logger = get_enhanced_logger()
    
    def parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """
        简化解析LLM响应
        
        Args:
            llm_response: LLM返回的响应字符串
            
        Returns:
            解析后的字典或包装后的标准结构
        """
        self.logger.func.info('Starting to parse LLM response', 
                      {'response_length': len(llm_response)})
        
        # 尝试解析JSON
        try:
            result = self._simple_json_extract(llm_response)
            if result:
                self.logger.func.info('JSON parsing successful', 
                              {'fields': list(result.keys())})
                return result
        except Exception as e:
            self.logger.func.error('JSON parsing failed', {'error': str(e)})
        
        # 解析失败，直接包装为标准结构
        self.logger.func.warn('Parsing failed, wrapping as standard structure')
        return self._wrap_as_standard_response(llm_response)
    
    @staticmethod
    def _simple_json_extract(text: str) -> Dict[str, Any]:
        """简单的JSON提取"""
        text = text.strip()
        
        # 方法1：直接解析
        try:
            result = json.loads(text)
            # 验证必要字段
            if isinstance(result, dict) and 'operation' in result:
                return result
        except json.JSONDecodeError:
            pass
        
        # 方法2：去除markdown代码块
        if "```json" in text:
            json_text = text.split("```json")[1].split("```")[0].strip()
            try:
                result = json.loads(json_text)
                if isinstance(result, dict) and 'operation' in result:
                    return result
            except json.JSONDecodeError:
                pass
        elif "```" in text:
            json_text = text.split("```")[1].split("```")[0].strip()
            try:
                result = json.loads(json_text)
                if isinstance(result, dict) and 'operation' in result:
                    return result
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _wrap_as_standard_response(self, raw_response: str) -> Dict[str, Any]:
        """将原始响应包装为标准结构"""
        return {
            "artifact_name": None,
            "operation": "general_chat",
            "operation_params": {},
            "keywords": ["format_error"],
            "tips": None,
            "response": raw_response,  # 直接使用原始LLM响应
            "wrapped": True,
            "processing_note": "原始响应格式不符合要求，已包装为标准对话格式"
        }
    
    @staticmethod
    def _extract_json_from_response(text: str) -> Dict[str, Any]:
        """从响应中提取JSON"""
        text = text.strip()
        
        # 记录原始响应用于调试
        print(f"[DEBUG] LLM原始响应: {repr(text[:200])}{'...' if len(text) > 200 else ''}")
        print(f"[DEBUG] 响应长度: {len(text)} 字符")
        
        # 方法1：直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 方法2：去除markdown代码块
        if "```json" in text:
            json_text = text.split("```json")[1].split("```")[0].strip()
            print(f"[DEBUG] 检测到markdown代码块，提取内容长度: {len(json_text)} 字符")
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        elif "```" in text:
            json_text = text.split("```")[1].split("```")[0].strip()
            print(f"[DEBUG] 检测到代码块标记，提取内容长度: {len(json_text)} 字符")
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        
        # 方法3：正则表达式提取JSON对象
        import re
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                result = json.loads(match)
                # 验证是否包含必要字段
                if isinstance(result, dict) and 'operation' in result:
                    print(f"[DEBUG] 通过正则表达式提取JSON成功")
                    return result
            except json.JSONDecodeError:
                continue
        
        raise ValueError("无法从响应中提取有效的JSON格式")
    
    @staticmethod
    def _create_default_response() -> Dict[str, Any]:
        """创建默认响应结构"""
        return {
            "artifact_name": None,
            "operation": "general_chat",
            "keywords": ["error"],
            "response": "抱歉，我暂时无法处理您的请求。请稍后重试。",
            "error": "JSON解析失败"
        }
    
    @staticmethod
    def extract_core_fields(llm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取核心字段
        
        Args:
            llm_data: 解析后的LLM数据
            
        Returns:
            包含核心字段的字典
        """
        # 提取核心字段
        artifact_name = llm_data.get("artifact_name") or llm_data.get("artifactName")
        operation = llm_data.get("operation")
        keywords = llm_data.get("keywords") or []
        
        # 确保operation字段存在（格式验证）
        if not operation:
            operation = "general_chat"  # 默认回退到通用对话
            
        operation = str(operation).strip()
        
        return {
            "artifact_name": artifact_name,
            "operation": operation,
            "keywords": keywords
        }
    
    @staticmethod
    def build_standard_command(llm_data: Dict[str, Any], rag_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        构建标准化指令
        
        Args:
            llm_data: 解析后的LLM数据
            rag_context: RAG上下文信息（可选）
            
        Returns:
            标准化指令字典
        """
        core_fields = ResponseParser.extract_core_fields(llm_data)
        
        command = {
            "artifact_id": llm_data.get("artifact_id"),
            "artifact_name": core_fields["artifact_name"],
            "operation": core_fields["operation"],
            "operation_params": llm_data.get("operation_params", {}),
            "keywords": core_fields["keywords"],
            "tips": llm_data.get("tips"),
            "response": llm_data.get("response", "")
        }
        
        # 添加RAG上下文信息（如果提供）
        if rag_context:
            command["rag_context"] = {
                "retrieved_count": rag_context.get("total_found", 0),
                "enhanced_prompt_used": True,
                "retrieval_timestamp": rag_context.get("timestamp")
            }
        
        return command