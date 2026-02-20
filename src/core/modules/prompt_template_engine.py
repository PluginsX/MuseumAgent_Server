# -*- coding: utf-8 -*-
"""
提示词模板引擎
负责从配置文件加载模板，并使用变量渲染生成最终提示词
"""
import re
from typing import Dict, List, Optional, Any
from src.common.config_utils import get_global_config
from src.common.enhanced_logger import get_enhanced_logger


class PromptTemplateEngine:
    """提示词模板引擎 - 负责模板解析和变量填充"""
    
    def __init__(self):
        """初始化模板引擎，从配置文件加载模板"""
        self.logger = get_enhanced_logger()
        self.templates = self._load_templates()
        self.logger.sys.info("PromptTemplateEngine initialized", {
            "templates_loaded": list(self.templates.keys())
        })
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """从配置文件加载所有模板"""
        try:
            config = get_global_config()
            templates = config.get("llm", {}).get("prompt_templates", {})
            
            if not templates:
                self.logger.sys.warn("No prompt templates found in config, using defaults")
                return self._get_default_templates()
            
            return templates
        except Exception as e:
            self.logger.sys.error(f"Failed to load templates from config: {e}")
            return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """获取默认模板（后备方案）"""
        return {
            "system_message": {
                "template": "{role_description}\n\n{response_requirements}\n\n{scene_description}\n\n当前场景下支持以下函数调用：\n{functions_description}",
                "variables": ["role_description", "response_requirements", "scene_description", "functions_description"]
            },
            "user_message_with_rag": {
                "template": "用户的问题是：{user_input}\n\n相关的资料包括：\n{retrieved_materials}",
                "variables": ["user_input", "retrieved_materials"]
            },
            "user_message_without_rag": {
                "template": "用户的问题是：{user_input}",
                "variables": ["user_input"]
            },
            "function_item_format": {
                "template": "• {name}: {description}",
                "variables": ["name", "description"]
            },
            "rag_material_format": {
                "template": "【{title}】\n{content}",
                "variables": ["title", "content"]
            }
        }
    
    def reload_templates(self):
        """重新加载模板（用于配置热更新）"""
        self.templates = self._load_templates()
        self.logger.sys.info("Templates reloaded", {
            "templates_count": len(self.templates)
        })
    
    def render_system_message(self, variables: Dict[str, str]) -> str:
        """
        渲染系统消息
        
        Args:
            variables: 包含以下变量的字典
                - role_description: 智能体角色描述
                - response_requirements: 智能体响应要求
                - scene_description: 场景描述
                - functions_description: 函数描述列表
        
        Returns:
            渲染后的系统消息字符串
        """
        template_config = self.templates.get("system_message", {})
        template = template_config.get("template", "")
        required_vars = template_config.get("variables", [])
        
        # 验证变量完整性
        missing_vars = [var for var in required_vars if var not in variables]
        if missing_vars:
            self.logger.sys.warn(f"Missing variables for system_message: {missing_vars}")
            # 为缺失的变量提供空字符串
            for var in missing_vars:
                variables[var] = ""
        
        # 渲染模板
        rendered = self._render_template(template, variables)
        
        self.logger.llm.info("System message rendered", {
            "length": len(rendered),
            "variables_used": list(variables.keys())
        })
        
        return rendered
    
    def render_user_message(self, variables: Dict[str, str], has_rag: bool = True) -> str:
        """
        渲染用户消息
        
        Args:
            variables: 包含以下变量的字典
                - user_input: 用户输入
                - retrieved_materials: RAG检索到的材料（可选）
            has_rag: 是否包含RAG检索结果
        
        Returns:
            渲染后的用户消息字符串
        """
        # 根据是否有RAG选择不同的模板
        template_name = "user_message_with_rag" if has_rag else "user_message_without_rag"
        template_config = self.templates.get(template_name, {})
        template = template_config.get("template", "")
        required_vars = template_config.get("variables", [])
        
        # 验证变量完整性
        missing_vars = [var for var in required_vars if var not in variables]
        if missing_vars:
            self.logger.sys.warn(f"Missing variables for {template_name}: {missing_vars}")
            for var in missing_vars:
                variables[var] = ""
        
        # 渲染模板
        rendered = self._render_template(template, variables)
        
        self.logger.llm.info("User message rendered", {
            "length": len(rendered),
            "has_rag": has_rag,
            "variables_used": list(variables.keys())
        })
        
        return rendered
    
    def render_functions_description(self, functions: List[Dict[str, Any]]) -> str:
        """
        渲染函数描述列表
        
        Args:
            functions: OpenAI标准函数定义列表
        
        Returns:
            格式化后的函数描述字符串
        """
        if not functions:
            return "（当前场景无可用函数）"
        
        template_config = self.templates.get("function_item_format", {})
        template = template_config.get("template", "• {name}: {description}")
        
        descriptions = []
        for func in functions:
            variables = {
                "name": func.get("name", "unknown"),
                "description": func.get("description", "无描述")
            }
            rendered = self._render_template(template, variables)
            descriptions.append(rendered)
        
        result = "\n".join(descriptions)
        
        self.logger.llm.info("Functions description rendered", {
            "function_count": len(functions),
            "length": len(result)
        })
        
        return result
    
    def render_rag_materials(self, materials: List[Dict[str, Any]]) -> str:
        """
        渲染RAG检索材料
        
        Args:
            materials: RAG检索到的材料列表
        
        Returns:
            格式化后的材料字符串
        """
        if not materials:
            return "（暂无相关资料）"
        
        template_config = self.templates.get("rag_material_format", {})
        template = template_config.get("template", "【{title}】\n{content}")
        
        rendered_materials = []
        for i, material in enumerate(materials, 1):
            variables = {
                "title": material.get("title", f"资料{i}"),
                "content": material.get("content", "")[:500]  # 限制长度
            }
            rendered = self._render_template(template, variables)
            rendered_materials.append(rendered)
        
        result = "\n\n".join(rendered_materials)
        
        self.logger.rag.info("RAG materials rendered", {
            "material_count": len(materials),
            "length": len(result)
        })
        
        return result
    
    def _render_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        使用变量渲染模板
        
        Args:
            template: 模板字符串，包含 {variable_name} 占位符
            variables: 变量字典
        
        Returns:
            渲染后的字符串
        """
        try:
            # 使用 str.format() 进行变量替换
            rendered = template.format(**variables)
            return rendered
        except KeyError as e:
            self.logger.sys.error(f"Template rendering failed: missing variable {e}")
            # 返回原始模板，避免崩溃
            return template
        except Exception as e:
            self.logger.sys.error(f"Template rendering failed: {e}")
            return template
    
    def validate_variables(self, template_name: str, variables: Dict[str, str]) -> bool:
        """
        验证变量完整性
        
        Args:
            template_name: 模板名称
            variables: 变量字典
        
        Returns:
            是否所有必需变量都存在
        """
        template_config = self.templates.get(template_name, {})
        required_vars = template_config.get("variables", [])
        
        missing_vars = [var for var in required_vars if var not in variables]
        
        if missing_vars:
            self.logger.sys.warn(f"Validation failed for {template_name}", {
                "missing_variables": missing_vars
            })
            return False
        
        return True

