# -*- coding: utf-8 -*-
"""
文本处理服务模块
全新重构版本 - 实现文本输入处理、LLM调用和SRS检索功能
遵循OpenAI兼容API标准与SRS标准API
"""
import json
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import aiohttp

from src.common.log_utils import get_logger
from src.common.log_formatter import log_step, log_communication
from src.common.config_utils import get_global_config


class TextProcessingService:
    """文本处理服务"""
    
    def __init__(self):
        """初始化文本处理服务"""
        self.logger = get_logger()
        self.config = get_global_config()
        self.llm_config = self.config.get("llm", {})
        self.srs_config = self.config.get("semantic_retrieval", {})
        
        # LLM客户端配置
        self.llm_base_url = self.llm_config.get("base_url", "")
        self.llm_api_key = self.llm_config.get("api_key", "")
        self.llm_model = self.llm_config.get("model", "qwen-turbo")
        
        # SRS客户端配置
        self.srs_base_url = self.srs_config.get("base_url", "")
        self.srs_api_key = self.srs_config.get("api_key", "")
        
    async def process_text(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        处理文本请求
        
        Args:
            request: 文本处理请求
            token: 认证令牌
            
        Returns:
            处理结果
        """
        self.logger.info(f"开始处理文本请求")
        
        try:
            # 获取请求参数
            user_input = request.get("content", "")
            scene_type = request.get("scene_type", "public")
            enable_tts = request.get("enable_tts", False)
            
            # 记录客户端消息接收
            ui_preview = user_input[:50] + ("..." if len(user_input) > 50 else "")
            print(log_communication('TEXT_SERVICE', 'RECEIVE', 'User Message', 
                                   request, 
                                   {'preview': ui_preview}))
            
            # 记录处理开始
            print(log_step('TEXT_SERVICE', 'START', '开始处理用户请求', 
                          {'scene_type': scene_type, 'enable_tts': enable_tts}))
            
            # 1. 执行SRS检索
            print(f"[TextService] 步骤1: 执行SRS检索")
            srs_results = await self._call_srs_search(user_input)
            
            # 2. 构建LLM请求
            print(f"[TextService] 步骤2: 构建LLM请求")
            llm_response = await self._call_llm(user_input, scene_type, srs_results)
            
            # 3. 如果需要TTS，调用TTS服务
            tts_audio = None
            if enable_tts:
                print(f"[TextService] 步骤3: 调用TTS服务")
                from src.services.tts_service import UnifiedTTSService
                tts_service = UnifiedTTSService()
                tts_audio = await tts_service.synthesize_text(llm_response.get("content", ""))
            
            # 4. 构建最终响应
            result = {
                "code": 200,
                "msg": "请求处理成功",
                "data": {
                    "text_response": llm_response,
                    "tts_audio": tts_audio,
                    "srs_results": srs_results
                },
                "timestamp": datetime.now().isoformat()
            }
            
            print(log_step('TEXT_SERVICE', 'SUCCESS', '文本处理完成', 
                          {'response_size': len(str(llm_response))}))
            return result
            
        except Exception as e:
            self.logger.error(f"文本处理失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"文本处理失败: {str(e)}",
                "data": None
            }
    
    async def _call_srs_search(self, query: str) -> Dict[str, Any]:
        """调用SRS服务进行检索"""
        try:
            search_request = {
                "query": query,
                "top_k": self.srs_config.get("search_params", {}).get("top_k", 3),
                "threshold": self.srs_config.get("search_params", {}).get("threshold", 0.35)
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.srs_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.srs_base_url}/search/retrieve",
                    json=search_request,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.srs_config.get("timeout", 300))
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(log_communication('SRS', 'RECEIVE', 'SRS检索结果', 
                                               {'result_count': len(result.get('artifacts', []))}))
                        return result
                    else:
                        error_text = await response.text()
                        print(log_step('SRS', 'ERROR', f'SRS检索失败', 
                                      {'status': response.status, 'error': error_text}))
                        return {"artifacts": [], "error": f"SRS检索失败: {error_text}"}
        except Exception as e:
            self.logger.error(f"SRS检索异常: {str(e)}")
            return {"artifacts": [], "error": f"SRS检索异常: {str(e)}"}
    
    async def _call_llm(self, user_input: str, scene_type: str, srs_results: Dict[str, Any]) -> Dict[str, Any]:
        """调用LLM服务"""
        try:
            # 构建系统消息
            system_message = f"你是博物馆智能助手。场景：{scene_type}。请根据以下检索到的信息回答用户问题。"
            if srs_results and srs_results.get("artifacts"):
                retrieved_info = "\n".join([artifact.get("content", "") for artifact in srs_results.get("artifacts", [])])
                system_message += f"\n相关信息：{retrieved_info}"
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
            
            payload = {
                "model": self.llm_model,
                "messages": messages,
                "temperature": self.llm_config.get("parameters", {}).get("temperature", 0.1),
                "max_tokens": self.llm_config.get("parameters", {}).get("max_tokens", 1024),
                "top_p": self.llm_config.get("parameters", {}).get("top_p", 0.1),
            }
            
            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        print(log_communication('LLM', 'RECEIVE', 'LLM响应', 
                                               {'content_length': len(content)}))
                        return {
                            "content": content,
                            "model": result.get("model"),
                            "usage": result.get("usage", {})
                        }
                    else:
                        error_text = await response.text()
                        print(log_step('LLM', 'ERROR', f'LLM调用失败', 
                                      {'status': response.status, 'error': error_text}))
                        raise Exception(f"LLM调用失败: {error_text}")
        except Exception as e:
            self.logger.error(f"LLM调用异常: {str(e)}")
            raise
    
    async def stream_process_text(self, request: Dict[str, Any], token: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理文本请求
        
        Args:
            request: 文本处理请求
            token: 认证令牌
            
        Yields:
            流式处理结果片段
        """
        try:
            # 获取请求参数
            user_input = request.get("content", "")
            scene_type = request.get("scene_type", "public")
            
            # 执行SRS检索
            srs_results = await self._call_srs_search(user_input)
            
            # 构建LLM请求（流式）
            system_message = f"你是博物馆智能助手。场景：{scene_type}。请根据以下检索到的信息回答用户问题。"
            if srs_results and srs_results.get("artifacts"):
                retrieved_info = "\n".join([artifact.get("content", "") for artifact in srs_results.get("artifacts", [])])
                system_message += f"\n相关信息：{retrieved_info}"
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
            
            payload = {
                "model": self.llm_model,
                "messages": messages,
                "temperature": self.llm_config.get("parameters", {}).get("temperature", 0.7),
                "max_tokens": self.llm_config.get("parameters", {}).get("max_tokens", 1024),
                "top_p": self.llm_config.get("parameters", {}).get("top_p", 0.9),
                "stream": True
            }
            
            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
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
                                        choices = data.get('choices', [])
                                        if choices:
                                            delta = choices[0].get('delta', {})
                                            content = delta.get('content', '')
                                            if content:
                                                yield {
                                                    "type": "text_chunk",
                                                    "content": content,
                                                    "done": False
                                                }
                                    except json.JSONDecodeError:
                                        continue
                        yield {
                            "type": "text_chunk",
                            "content": "",
                            "done": True
                        }
                    else:
                        error_text = await response.text()
                        yield {
                            "type": "error",
                            "message": f"流式处理失败: {error_text}"
                        }
        except Exception as e:
            self.logger.error(f"流式文本处理失败: {str(e)}")
            yield {
                "type": "error",
                "message": f"流式处理失败: {str(e)}"
            }
    
    async def batch_process_text(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """
        批量处理文本请求
        
        Args:
            request: 批量处理请求
            token: 认证令牌
            
        Returns:
            批量处理结果
        """
        try:
            texts = request.get("texts", [])
            results = []
            
            for text in texts:
                result = await self.process_text({"content": text}, token)
                results.append(result)
            
            return {
                "code": 200,
                "msg": "批量处理完成",
                "data": {
                    "results": results,
                    "processed_count": len(results)
                }
            }
        except Exception as e:
            self.logger.error(f"批量文本处理失败: {str(e)}")
            return {
                "code": 500,
                "msg": f"批量处理失败: {str(e)}",
                "data": None
            }