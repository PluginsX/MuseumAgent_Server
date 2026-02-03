# -*- coding: utf-8 -*-
"""
提示词构建器模块
负责构建各种类型的提示词
"""

from typing import Dict, Any, List
from ...common.config_utils import get_global_config
from ...common.log_formatter import log_step


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self):
        """初始化提示词构建器"""
        try:
            config = get_global_config()
            self.rag_templates = config.get('llm', {}).get('rag_templates', {})
        except:
            # 后备方案
            self.rag_templates = {
                'enabled': '请参考以下相关文物信息来回答：{retrieved_context}',
                'disabled': ''
            }
    
    def build_rag_instruction(self, rag_context: Dict[str, Any]) -> str:
        """
        构建RAG指令部分
        
        Args:
            rag_context: RAG检索上下文
            
        Returns:
            RAG指令字符串
        """
        relevant_artifacts = rag_context.get('relevant_artifacts', [])
        
        if not relevant_artifacts:
            # 没有检索到相关内容，使用禁用模板
            print(log_step('PROMPT', 'INFO', '未检索到相关内容，使用禁用模板', 
                          {'artifact_count': 0}))
            return self.rag_templates.get('disabled', '')
        
        # 构建检索上下文
        context_parts = []
        for i, artifact in enumerate(relevant_artifacts[:2], 1):  # 最多使用前2个最相关的
            artifact_info = artifact.get('info', {})
            context_part = (
                f"{i}. 文物名称: {artifact['artifact_name']}\n"
                f"   文物ID: {artifact['artifact_id']}\n"
                f"   相关描述: {artifact['document'][:200]}...\n"
                f"   详细信息: {artifact_info.get('tips', '暂无详细信息')}\n"
            )
            context_parts.append(context_part)
        
        retrieved_context = "\n".join(context_parts)
        
        # 使用启用模板构建RAG指令
        rag_instruction = self.rag_templates.get('enabled', '').format(
            retrieved_context=retrieved_context
        )
        
        print(log_step('PROMPT', 'SUCCESS', f'构建RAG指令完成', 
                      {'length': len(rag_instruction), 'artifact_count': len(relevant_artifacts)}))
        return rag_instruction
    
    def build_final_prompt(self, user_input: str, scene_type: str, 
                          valid_operations: List[str], rag_instruction: str = "") -> str:
        """
        构建最终的完整提示词
        
        Args:
            user_input: 用户输入
            scene_type: 场景类型
            valid_operations: 可用操作列表
            rag_instruction: RAG指令部分
            
        Returns:
            完整的提示词字符串
        """
        try:
            config = get_global_config()
            base_prompt = config['llm']['prompt_template']
            
            # 安全的字符串替换，避免格式化错误
            final_prompt = base_prompt.replace('{rag_instruction}', rag_instruction or '')
            final_prompt = final_prompt.replace('{scene_type}', scene_type)
            final_prompt = final_prompt.replace('{user_input}', user_input)
            final_prompt = final_prompt.replace('{valid_operations}', ", ".join(valid_operations))
            
            return final_prompt
        except Exception as e:
            print(log_step('PROMPT', 'ERROR', '配置驱动提示词构建失败，使用后备方案', 
                          {'error': str(e)}))
            # 后备方案：使用简化但有效的提示词
            operations_str = ", ".join(valid_operations) if valid_operations else "general_chat"
            backup_prompt = (
                f"你是辽宁省博物馆智能助手。请严格按照JSON格式回复：\n"
                f"{{\n"
                f"  \"artifact_name\": \"文物名称或null\",\n"
                f"  \"operation\": \"{operations_str}中的指令或general_chat\",\n"
                f"  \"keywords\": [\"关键词\"],\n"
                f"  \"response\": \"回复内容\"\n"
                f"}}\n"
                f"用户输入：{user_input}，场景：{scene_type}"
            )
            print(log_step('PROMPT', 'WARNING', '使用后备提示词', 
                          {'length': len(backup_prompt), 'reason': str(e)}))
            return backup_prompt