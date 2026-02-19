# -*- coding: utf-8 -*-
"""
LLM服务接口
使用OpenAI兼容API标准与外部LLM服务通信
"""
import json
import aiohttp
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from src.common.enhanced_logger import get_enhanced_logger
from src.common.config_utils import get_global_config
from src.services.interrupt_manager import get_interrupt_manager


class LLMService:
    """LLM服务接口"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.logger = get_enhanced_logger()
        self.interrupt_manager = get_interrupt_manager()
        self.config = get_global_config()
        self.llm_config = self.config.get("llm", {})
        
        # LLM客户端配置
        self.base_url = self.llm_config.get("base_url", "")
        self.api_key = self.llm_config.get("api_key", "")
        self.model = self.llm_config.get("model", "qwen-turbo")
        self.parameters = self.llm_config.get("parameters", {})
    
    async def chat_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        聊天补全接口（OpenAI兼容）
        
        Args:
            request: 聊天请求
            
        Returns:
            聊天响应
        """
        self.logger.info("开始LLM聊天补全请求")
        
        try:
            # 构建OpenAI兼容的请求
            payload = {
                "model": request.get("model", self.model),
                "messages": request.get("messages", []),
                "temperature": request.get("temperature", self.parameters.get("temperature", 0.1)),
                "max_tokens": request.get("max_tokens", self.parameters.get("max_tokens", 1024)),
                "top_p": request.get("top_p", self.parameters.get("top_p", 0.1)),
            }
            
            # 添加其他可选参数
            if "functions" in request:
                payload["functions"] = request["functions"]
            if "function_call" in request:
                payload["function_call"] = request["function_call"]
            if "stream" in request:
                payload["stream"] = request["stream"]
            
            # 添加认证头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 记录请求
            self.logger.llm.info('LLM chat completion request sent', 
                                   {'model': payload['model'], 'messages_count': len(payload['messages'])})
            
            async with aiohttp.ClientSession() as session:
                # ✅ 注册到中断管理器
                if session_id:
                    self.interrupt_manager.register_llm(session_id, session)
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.llm.info('LLM chat completion response received', 
                                               {'choices_count': len(result.get('choices', []))})
                        
                        return {
                            "code": 200,
                            "msg": "请求成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        try:
                            error_json = await response.json()
                            error_detail = error_json.get("error", {}).get("message", error_text)
                        except:
                            error_detail = error_text
                        
                        self.logger.llm.error(f'LLM chat completion failed', 
                                      {'status': response.status, 'error': error_detail})
                        
                        return {
                            "code": 500,
                            "msg": f"LLM聊天补全失败: {error_detail}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"LLM聊天补全异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"LLM聊天补全异常: {str(e)}",
                "data": None
            }
    
    async def chat_completion_stream(self, request: Dict[str, Any], session_id: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天补全接口（OpenAI兼容）
        
        Args:
            request: 聊天请求
            
        Yields:
            流式响应片段
        """
        try:
            # 构建OpenAI兼容的流式请求
            payload = {
                "model": request.get("model", self.model),
                "messages": request.get("messages", []),
                "temperature": request.get("temperature", self.parameters.get("temperature", 0.7)),
                "max_tokens": request.get("max_tokens", self.parameters.get("max_tokens", 1024)),
                "top_p": request.get("top_p", self.parameters.get("top_p", 0.9)),
                "stream": True  # 启用流式输出
            }
            
            # 添加其他可选参数
            if "functions" in request:
                payload["functions"] = request["functions"]
            if "function_call" in request:
                payload["function_call"] = request["function_call"]
            
            # 添加认证头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line.strip():
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    data_str = line_str[6:]  # 移除 "data: " 前缀
                                    if data_str == '[DONE]':
                                        break
                                    try:
                                        data = json.loads(data_str)
                                        
                                        # 发送数据块
                                        yield {
                                            "type": "llm_chunk",
                                            "data": data,
                                            "done": False
                                        }
                                    except json.JSONDecodeError:
                                        continue
                        yield {
                            "type": "llm_chunk",
                            "data": {},
                            "done": True
                        }
                    else:
                        error_text = await response.text()
                        yield {
                            "type": "error",
                            "message": f"流式聊天补全失败: {error_text}"
                        }
        except Exception as e:
            self.logger.sys.error(f"LLM流式聊天补全异常: {str(e)}")
            yield {
                "type": "error",
                "message": f"LLM流式聊天补全异常: {str(e)}"
            }
    
    async def function_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        函数调用接口（OpenAI兼容）
        
        Args:
            request: 函数调用请求
            
        Returns:
            函数调用结果
        """
        self.logger.info("开始LLM函数调用请求")
        
        try:
            # 验证必需参数
            if "messages" not in request:
                return {
                    "code": 400,
                    "msg": "缺少必需参数: messages",
                    "data": None
                }
            
            if "functions" not in request or not request["functions"]:
                return {
                    "code": 400,
                    "msg": "缺少必需参数: functions",
                    "data": None
                }
            
            # 构建函数调用请求
            payload = {
                "model": request.get("model", self.model),
                "messages": request["messages"],
                "functions": request["functions"],
                "function_call": request.get("function_call", "auto"),
                "temperature": request.get("temperature", self.parameters.get("temperature", 0.1)),
                "max_tokens": request.get("max_tokens", self.parameters.get("max_tokens", 1024)),
                "top_p": request.get("top_p", self.parameters.get("top_p", 0.1)),
            }
            
            # 添加认证头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 记录请求
            self.logger.llm.info('LLM function call request sent', 
                                   {'model': payload['model'], 'functions_count': len(payload['functions'])})
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 检查是否有函数调用
                        choices = result.get("choices", [])
                        if choices:
                            message = choices[0].get("message", {})
                            function_call = message.get("function_call")
                            
                            if function_call:
                                self.logger.llm.info("LLM function call response received", 
                                                       {'function_name': function_call.get('name')})
                                
                                return {
                                    "code": 200,
                                    "msg": "函数调用成功",
                                    "data": {
                                        "function_call": function_call,
                                        "raw_response": result
                                    },
                                    "timestamp": datetime.now().isoformat()
                                }
                            else:
                                self.logger.llm.info("LLM response (no function call) received", 
                                                       {'content_length': len(message.get('content', ''))})
                                
                                return {
                                    "code": 200,
                                    "msg": "普通响应",
                                    "data": {
                                        "content": message.get("content", ""),
                                        "raw_response": result
                                    },
                                    "timestamp": datetime.now().isoformat()
                                }
                        else:
                            return {
                                "code": 500,
                                "msg": "LLM响应中无有效选择",
                                "data": None
                            }
                    else:
                        error_text = await response.text()
                        try:
                            error_json = await response.json()
                            error_detail = error_json.get("error", {}).get("message", error_text)
                        except:
                            error_detail = error_text
                        
                        self.logger.llm.error(f"LLM function call failed", 
                                      {'status': response.status, 'error': error_detail})
                        
                        return {
                            "code": 500,
                            "msg": f"LLM函数调用失败: {error_detail}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"LLM函数调用异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"LLM函数调用异常: {str(e)}",
                "data": None
            }
    
    async def embedding(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        嵌入向量接口（OpenAI兼容）
        
        Args:
            request: 嵌入请求
            
        Returns:
            嵌入向量结果
        """
        self.logger.info("开始LLM嵌入向量请求")
        
        try:
            # 构建嵌入请求
            input_text = request.get("input", "")
            if isinstance(input_text, str):
                input_text = [input_text]
            
            payload = {
                "model": request.get("model", f"{self.model}-embedding"),  # 假设有一个对应的嵌入模型
                "input": input_text,
                "encoding_format": request.get("encoding_format", "float")
            }
            
            # 添加认证头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 记录请求
            self.logger.llm.info('LLM embedding request sent', 
                                   {'input_count': len(input_text)})
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/embeddings",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.llm.info("LLM embedding response received", 
                                               {'data_count': len(result.get('data', []))})
                        
                        return {
                            "code": 200,
                            "msg": "嵌入向量生成成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        try:
                            error_json = await response.json()
                            error_detail = error_json.get("error", {}).get("message", error_text)
                        except:
                            error_detail = error_text
                        
                        self.logger.llm.error(f"LLM embedding failed", 
                                      {'status': response.status, 'error': error_detail})
                        
                        return {
                            "code": 500,
                            "msg": f"LLM嵌入向量失败: {error_detail}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"LLM嵌入向量异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"LLM嵌入向量异常: {str(e)}",
                "data": None
            }
    
    async def model_list(self) -> Dict[str, Any]:
        """
        获取模型列表接口（OpenAI兼容）
        
        Returns:
            模型列表
        """
        self.logger.info("开始获取LLM模型列表")
        
        try:
            # 添加认证头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.llm.info("LLM model list response received",{'model_count': len(result.get('data', []))})
                        
                        return {
                            "code": 200,
                            "msg": "获取模型列表成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        
                        self.logger.llm.error(f"Failed to get model list", 
                                      {'status': response.status, 'error': error_text})
                        
                        return {
                            "code": 500,
                            "msg": f"获取模型列表失败: {error_text}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"获取LLM模型列表异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"获取LLM模型列表异常: {str(e)}",
                "data": None
            }