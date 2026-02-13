# -*- coding: utf-8 -*-
"""
提示词构建器模块
负责构建各种类型的提示词
"""

from typing import Dict, Any, List
# FunctionDefinition已重命名为OpenAIFunctionDefinition
from ...models.function_calling_models import OpenAIFunctionDefinition
from ...common.config_utils import get_global_config
from ...common.enhanced_logger import get_enhanced_logger


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self):
        """初始化提示词构建器"""
        # 获取日志记录器
        self.logger = get_enhanced_logger()
        
        try:
            config = get_global_config()
            self.rag_templates = config.get('llm', {}).get('rag_templates', {})
            # 加载系统提示词配置
            self.system_prompts = config.get('llm', {}).get('system_prompts', {})
        except:
            # 后备方案
            self.rag_templates = {
                'enabled': '请参考以下相关文物信息来回答：{retrieved_context}',
                'disabled': ''
            }
            # 后备系统提示词，当配置文件加载失败或配置项缺失时，后备提示词确保系统不会崩溃：
            self.system_prompts = {
                'base': '你是辽宁省博物馆智能助手。你必须遵守以下规则：1. 每次响应都必须包含自然语言对话内容；2. 用专业友好的语言与用户交流；3. 保持对话的连贯性和可读性。请根据用户需求选择合适的函数并生成正确的参数。',
                'function_calling': '你是辽宁省博物馆智能助手。你必须遵守以下规则：1. 每次响应都必须包含自然语言对话内容；2. 在调用函数前要说明将要做什么；3. 用专业友好的语言与用户交流。\n\n可用函数：\n{functions_list}\n\n场景：{scene_type}\n{rag_instruction}\n\n用户输入：{user_input}\n\n请分析用户需求，选择合适的函数并生成正确参数，同时用自然语言解释你的操作。',
                'fallback': '你是辽宁省博物馆智能助手。你必须遵守以下规则：1. 每次响应都必须包含自然语言对话内容；2. 用专业友好的语言与用户交流；3. 保持对话的连贯性。\n\n场景：{scene_type}\n用户输入：{user_input}\n\n请用自然语言与用户进行友好交流，回答用户的问题。'
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
            self.logger.func.info('No relevant content retrieved, using disabled template', 
                          {'artifact_count': 0})
            return self.rag_templates.get('disabled', '')
        
        # 构建检索上下文
        context_parts = []
        for i, artifact in enumerate(relevant_artifacts[:2], 1):  # 最多使用前2个最相关的
            artifact_info = artifact.get('info', {})
            context_part = (
                f"{i}. 文物名称: {artifact.get('title', '未知')}\n"
                f"   文物ID: {artifact.get('id', '未知')}\n"
                f"   相关描述: {artifact.get('content', '')[:200]}...\n"
                f"   详细信息: {artifact_info.get('tips', '暂无详细信息')}\n"
            )
            context_parts.append(context_part)
        
        retrieved_context = "\n".join(context_parts)
        
        # 使用启用模板构建RAG指令
        rag_instruction = self.rag_templates.get('enabled', '').format(
            retrieved_context=retrieved_context
        )
        
        self.logger.func.info(f'RAG instruction built successfully', 
                      {'length': len(rag_instruction), 'artifact_count': len(relevant_artifacts)})
        return rag_instruction
    
    def build_final_prompt(self, user_input: str, scene_type: str, 
                          functions: List[Dict[str, Any]] = None, rag_instruction: str = "") -> str:
        """
        构建最终的完整提示词（基于Function Calling模式，配置驱动）
        
        Args:
            user_input: 用户输入
            scene_type: 场景类型
            functions: 函数定义列表（可选）
            rag_instruction: RAG指令部分
            
        Returns:
            完整的提示词字符串
        """
        try:
            # 根据是否有函数定义选择不同的提示词模板
            if functions and len(functions) > 0:
                # 有函数定义时使用函数调用模板
                return self.build_function_calling_prompt(user_input, scene_type, functions, rag_instruction)
            else:
                # 无函数定义时使用基础模板
                base_template = self.system_prompts.get('base', 
                    '你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。在调用函数的同时，请用自然语言与用户进行友好交流。')
                
                # 构建完整提示词
                full_prompt = f"""{base_template}

场景：{scene_type}
{rag_instruction}
用户输入：{user_input}

请用自然语言与用户进行友好交流，回答用户的问题。"""
                
                return full_prompt
        except Exception as e:
            self.logger.func.error('Configuration-driven prompt building failed, using fallback', 
                          {'error': str(e), 'user_input_preview': user_input[:50]})
            # 后备方案：使用简化但有效的提示词
            backup_prompt = (
                f"你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。在调用函数的同时，请用自然语言与用户进行友好交流。\n"
                f"\n"
                f"场景：{scene_type}\n"
                f"{rag_instruction}\n"
                f"用户输入：{user_input}\n"
                f"\n"
                f"请用自然语言与用户进行友好交流，回答用户的问题。"
            )
            self.logger.func.warn('Using fallback prompt', 
                          {'length': len(backup_prompt), 'reason': str(e), 'scene_type': scene_type, 'user_input_preview': user_input[:50]})
            return backup_prompt

    def build_function_calling_prompt(self, user_input: str, scene_type: str, 
                                    functions: List[Dict[str, Any]], rag_instruction: str = "") -> str:
        """
        构建函数调用格式的提示词（配置驱动）
        
        Args:
            user_input: 用户输入
            scene_type: 场景类型
            functions: 函数定义列表
            rag_instruction: RAG指令部分
            
        Returns:
            函数调用格式的提示词字符串
        """
        try:
            # 构建函数列表描述
            function_descriptions = []
            for func in functions:
                desc = f"- {func.get('name', 'unknown')}: {func.get('description', 'No description')}"
                function_descriptions.append(desc)
            
            functions_text = "\n".join(function_descriptions)
            
            # 使用配置中的系统提示词
            system_prompt_template = self.system_prompts.get('function_calling', 
                '你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。在调用函数的同时，请用自然语言与用户进行友好交流。\n\n可用函数：\n{functions_list}\n\n场景：{scene_type}\n{rag_instruction}\n\n用户输入：{user_input}\n\n请调用适当的函数并提供正确的参数，同时用自然语言回应用户。')
            
            # 安全的字符串替换
            system_prompt = system_prompt_template.replace('{functions_list}', functions_text)
            system_prompt = system_prompt.replace('{scene_type}', scene_type)
            system_prompt = system_prompt.replace('{rag_instruction}', rag_instruction or '')
            system_prompt = system_prompt.replace('{user_input}', user_input)
            
            return system_prompt
        except Exception as e:
            self.logger.func.error('Function calling prompt building failed', 
                                  {'error': str(e), 'user_input_preview': user_input[:50]})
            # 使用后备方案
            fallback_template = self.system_prompts.get('fallback',
                '你是辽宁省博物馆智能助手。请根据用户需求选择合适的函数并生成正确的参数。在调用函数的同时，请用自然语言与用户进行友好交流。\n\n场景：{scene_type}\n用户输入：{user_input}\n\n请调用适当的函数并提供正确的参数，同时用自然语言回应用户。')
            
            fallback_prompt = fallback_template.replace('{scene_type}', scene_type)
            fallback_prompt = fallback_prompt.replace('{user_input}', user_input)
            return fallback_prompt