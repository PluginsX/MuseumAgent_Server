# -*- coding: utf-8 -*-
"""
LLM客户端（重构版）
仅负责HTTP API调用，不参与提示词构建
"""
import asyncio
from typing import Dict, Any, AsyncGenerator, Optional
import json
import aiohttp
import requests

from ..common.config_utils import get_global_config
from ..common.enhanced_logger import get_enhanced_logger
from ..services.interrupt_manager import get_interrupt_manager


class DynamicLLMClient:
    """LLM客户端 - 仅负责API调用"""
    
    def __init__(self):
        """初始化LLM客户端"""
        self.logger = get_enhanced_logger()
        self._load_config()
        self.logger.sys.info("DynamicLLMClient initialized (API-only mode)")
    
    def _load_config(self):
        """从配置文件加载LLM连接参数和API参数"""
        config = get_global_config()
        llm_config = config.get("llm", {})
        
        # 连接参数
        self.base_url = llm_config.get("base_url", "").rstrip("/")
        self.api_key = llm_config.get("api_key", "")
        
        # 超时配置
        server_config = config.get("server", {})
        self.timeout = server_config.get("request_timeout", 30)
        
        if not self.base_url or not self.api_key:
            self.logger.sys.warn("LLM base_url or api_key not configured")
    
    def chat_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步调用LLM Chat Completions API
        
        Args:
            payload: 完整的API请求payload（由PromptBuilder构建）
        
        Returns:
            LLM API响应
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM未配置base_url或api_key")
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        self.logger.llm.info("Sending request to LLM API", {
            "endpoint": url,
            "has_functions": "functions" in payload,
            "messages_count": len(payload.get("messages", []))
        })
        
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            self.logger.llm.error("LLM request exception", {"error": str(e)})
            raise RuntimeError(f"LLM请求异常: {str(e)}") from e
        
        if resp.status_code != 200:
            err_body = resp.text
            try:
                err_json = resp.json()
                err_body = err_json.get("error", {}).get("message", err_body)
            except Exception:
                pass
            self.logger.llm.error("LLM API call failed", {
                "status_code": resp.status_code,
                "error": err_body
            })
            raise RuntimeError(f"LLM API调用失败 [code={resp.status_code}]: {err_body}")
        
        response_data = resp.json()
        
        self.logger.llm.info("Received response from LLM API", {
            "has_choices": len(response_data.get("choices", [])) > 0
        })
        
        return response_data
    
    async def chat_completion_stream(
        self,
        payload: Dict[str, Any],
        cancel_event: Optional[asyncio.Event] = None,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        异步流式调用LLM Chat Completions API
        
        Args:
            payload: 完整的API请求payload（由PromptBuilder构建）
            cancel_event: 取消事件（可选）
            session_id: 会话ID（用于中断管理）
        
        Yields:
            流式响应片段，格式：
            - {"type": "text", "content": "..."}
            - {"type": "function_call", "name": "...", "arguments": {...}}
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM未配置base_url或api_key")
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # 启用流式输出
        payload["stream"] = True
        
        self.logger.llm.info("Sending streaming request to LLM API", {
            "endpoint": url,
            "has_functions": "functions" in payload
        })
        
        # 函数调用累积变量
        function_call_name = None
        function_call_arguments = ""
        function_call_yielded = False
        
        try:
            async with aiohttp.ClientSession() as session:
                # 注册到中断管理器
                if session_id:
                    interrupt_manager = get_interrupt_manager()
                    interrupt_manager.register_llm(session_id, session)
                
                async with session.post(url, headers=headers, json=payload, timeout=self.timeout) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.llm.error("LLM API call failed", {
                            "status_code": resp.status,
                            "error": error_text
                        })
                        raise RuntimeError(f"LLM API调用失败 [code={resp.status}]: {error_text}")
                    
                    async for line in resp.content:
                        # 检查取消信号
                        if cancel_event and cancel_event.is_set():
                            self.logger.llm.info("LLM stream cancelled by user")
                            try:
                                resp.close()
                            except Exception:
                                pass
                            return
                        
                        if line:
                            line_str = line.decode("utf-8").strip()
                            if line_str.startswith("data: "):
                                data_str = line_str[6:]
                                
                                if data_str == "[DONE]":
                                    # 处理未完成的函数调用
                                    if function_call_name and function_call_arguments and not function_call_yielded:
                                        try:
                                            arguments_json = json.loads(function_call_arguments)
                                            yield {
                                                "type": "function_call",
                                                "name": function_call_name,
                                                "arguments": arguments_json
                                            }
                                        except json.JSONDecodeError as e:
                                            self.logger.llm.warn("Failed to parse function arguments", {
                                                "error": str(e)
                                            })
                                    break
                                
                                try:
                                    data = json.loads(data_str)
                                    choices = data.get("choices", [])
                                    
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        
                                        # 处理文本内容
                                        content = delta.get("content", "")
                                        if content:
                                            yield {
                                                "type": "text",
                                                "content": content
                                            }
                                        
                                        # 处理函数调用
                                        function_call = delta.get("function_call")
                                        if function_call:
                                            # 累积函数名称
                                            if "name" in function_call and function_call["name"]:
                                                function_call_name = function_call["name"]
                                            
                                            # 累积函数参数
                                            if "arguments" in function_call:
                                                function_call_arguments += function_call["arguments"]
                                            
                                            # 尝试解析并yield完整的函数调用
                                            if function_call_name and function_call_arguments and not function_call_yielded:
                                                try:
                                                    arguments_json = json.loads(function_call_arguments)
                                                    yield {
                                                        "type": "function_call",
                                                        "name": function_call_name,
                                                        "arguments": arguments_json
                                                    }
                                                    function_call_yielded = True
                                                except json.JSONDecodeError:
                                                    # 参数还未完整，继续累积
                                                    pass
                                
                                except json.JSONDecodeError:
                                    continue
        
        except Exception as e:
            self.logger.llm.error("LLM stream exception", {"error": str(e)})
            raise RuntimeError(f"LLM流式请求异常: {str(e)}") from e

