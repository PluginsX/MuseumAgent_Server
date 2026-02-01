# -*- coding: utf-8 -*-
"""
LLM服务调用模块 - 封装不同提供商调用逻辑，处理异常
"""
import json
import os
from typing import Any, Dict, Optional

from src.common.config_utils import get_config_by_key, get_global_config


class LLMClient:
    """通用化LLM客户端，支持动态切换提供商"""
    
    def __init__(self) -> None:
        """从全局配置中读取LLM所有参数"""
        config = get_global_config()
        llm_config = config.get("llm", {})
        
        self.provider = llm_config.get("provider", "dashscope")
        self.model = llm_config.get("model", "qwen-turbo")
        self.api_key = os.getenv("LLM_API_KEY") or llm_config.get("api_key", "")
        self.parameters = llm_config.get("parameters", {})
        self.prompt_template = llm_config.get("prompt_template", "")
        
        # 请求超时（秒）
        server_config = config.get("server", {})
        self.timeout = server_config.get("request_timeout", 30)
    
    def generate_prompt(self, user_input: str, scene_type: str = "public") -> str:
        """
        填充提示词模板，生成完整LLM请求提示词
        
        Args:
            user_input: 用户自然语言输入
            scene_type: 场景类型
        
        Returns:
            完整提示词字符串
        """
        return self.prompt_template.format(
            scene_type=scene_type,
            user_input=user_input
        )
    
    def call_dashscope(self, prompt: str) -> str:
        """
        调用阿里通义千问（DashScope）API
        
        Args:
            prompt: 完整提示词
        
        Returns:
            LLM纯JSON响应字符串
        
        Raises:
            RuntimeError: API调用失败
        """
        try:
            import dashscope
            from dashscope import Generation
        except ImportError as e:
            raise RuntimeError("dashscope SDK未安装，请执行: pip install dashscope") from e
        
        if not self.api_key:
            raise RuntimeError("LLM API Key未配置，请在config.json或环境变量LLM_API_KEY中设置")
        
        dashscope.api_key = self.api_key
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = Generation.call(
                model=self.model,
                messages=messages,
                result_format="message",
                temperature=self.parameters.get("temperature", 0.2),
                max_tokens=self.parameters.get("max_tokens", 1024),
                top_p=self.parameters.get("top_p", 0.9),
                api_key=self.api_key,
            )
        except Exception as e:
            raise RuntimeError(f"DashScope API调用异常: {str(e)}") from e
        
        if response.status_code != 200:
            error_msg = f"API Key无效或额度不足" if response.status_code == 401 else response.message
            raise RuntimeError(f"DashScope API调用失败 [code={response.status_code}]: {error_msg}")
        
        # 提取响应文本（兼容 message 与 text 两种格式）
        try:
            if not hasattr(response, "output") or not response.output:
                raise RuntimeError("LLM响应格式异常：无有效输出内容")
            out = response.output
            if hasattr(out, "text") and out.text:
                text = out.text
            elif hasattr(out, "choices") and out.choices:
                msg = out.choices[0].message
                text = msg.get("content", "") or getattr(msg, "content", "") if msg else ""
            else:
                text = str(out)
        except (AttributeError, IndexError, KeyError) as e:
            raise RuntimeError(f"LLM响应格式异常: {str(e)}") from e
        
        if not text or not text.strip():
            raise RuntimeError("LLM返回内容为空")
        
        return text.strip()
    
    def call_openai(self, prompt: str) -> str:
        """
        调用OpenAI兼容API（预留）
        
        Args:
            prompt: 完整提示词
        
        Returns:
            LLM纯JSON响应字符串
        """
        raise NotImplementedError("OpenAI提供商尚未实现，请在config.json中配置provider为dashscope")
    
    def call_ernie(self, prompt: str) -> str:
        """
        调用文心一言API（预留）
        
        Args:
            prompt: 完整提示词
        
        Returns:
            LLM纯JSON响应字符串
        """
        raise NotImplementedError("文心一言提供商尚未实现，请在config.json中配置provider为dashscope")
    
    def parse_user_input(
        self,
        user_input: str,
        scene_type: str = "public"
    ) -> str:
        """
        根据配置的LLM提供商，解析用户输入并返回纯JSON响应字符串
        
        Args:
            user_input: 用户自然语言输入
            scene_type: 场景类型
        
        Returns:
            LLM解析的纯JSON字符串
        """
        prompt = self.generate_prompt(user_input, scene_type)
        
        if self.provider == "dashscope":
            return self.call_dashscope(prompt)
        elif self.provider == "openai":
            return self.call_openai(prompt)
        elif self.provider == "ernie":
            return self.call_ernie(prompt)
        else:
            raise RuntimeError(f"不支持的LLM提供商: {self.provider}，有效值为: dashscope, openai, ernie")
