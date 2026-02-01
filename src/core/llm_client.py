# -*- coding: utf-8 -*-
"""
LLM服务调用模块 - OpenAI Compatible API 格式
"""
import json
import os
from typing import Any, Dict

import requests

from src.common.config_utils import get_global_config


class LLMClient:
    """OpenAI 兼容格式 LLM 客户端"""
    
    def __init__(self) -> None:
        """从全局配置读取 LLM 参数"""
        config = get_global_config()
        llm_config = config.get("llm", {})
        
        self.base_url = (os.getenv("LLM_BASE_URL") or llm_config.get("base_url", "")).rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY") or llm_config.get("api_key", "")
        self.model = os.getenv("LLM_MODEL") or llm_config.get("model", "qwen-turbo")
        self.parameters = llm_config.get("parameters", {})
        self.prompt_template = llm_config.get("prompt_template", "")
        
        server_config = config.get("server", {})
        self.timeout = server_config.get("request_timeout", 30)
    
    def generate_prompt(self, user_input: str, scene_type: str = "public") -> str:
        """填充提示词模板"""
        return self.prompt_template.format(
            scene_type=scene_type,
            user_input=user_input
        )
    
    def _chat_completions(self, prompt: str) -> str:
        """
        调用 OpenAI 兼容的 Chat Completions API
        
        POST {base_url}/chat/completions
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM 未配置 base_url 或 api_key，请在 config.json 或环境变量中设置")
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.parameters.get("temperature", 0.2),
            "max_tokens": self.parameters.get("max_tokens", 1024),
            "top_p": self.parameters.get("top_p", 0.9),
        }
        
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"LLM 请求异常: {str(e)}") from e
        
        if resp.status_code != 200:
            err_body = resp.text
            try:
                err_json = resp.json()
                err_body = err_json.get("error", {}).get("message", err_body)
            except Exception:
                pass
            raise RuntimeError(f"LLM API 调用失败 [code={resp.status_code}]: {err_body}")
        
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("LLM 响应中无 choices")
        
        msg = choices[0].get("message", {})
        text = msg.get("content", "")
        if not text or not str(text).strip():
            raise RuntimeError("LLM 返回内容为空")
        
        return str(text).strip()
    
    def parse_user_input(
        self,
        user_input: str,
        scene_type: str = "public"
    ) -> str:
        """解析用户输入，返回 LLM 的纯 JSON 响应字符串"""
        prompt = self.generate_prompt(user_input, scene_type)
        return self._chat_completions(prompt)
