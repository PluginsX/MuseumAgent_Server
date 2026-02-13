# -*- coding: utf-8 -*-
"""
动态LLM客户端
支持会话感知的指令集动态提示词生成
"""
from typing import List, Dict, Any
import json
import os
import requests
from datetime import datetime

from ..common.config_utils import get_global_config
# 移除对已删除模块的导入
# from ..session.session_manager import session_manager
from src.common.enhanced_logger import get_enhanced_logger


class DynamicLLMClient:
    """支持动态指令集的LLM客户端（独立实现）"""
    
    def __init__(self):
        """初始化LLM配置"""
        config = get_global_config()
        llm_config = config.get("llm", {})
        
        self.base_url = (os.getenv("LLM_BASE_URL") or llm_config.get("base_url", "")).rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY") or llm_config.get("api_key", "")
        self.model = os.getenv("LLM_MODEL") or llm_config.get("model", "qwen-turbo")
        self.parameters = llm_config.get("parameters", {})
        self.prompt_template = llm_config.get("prompt_template", "")
        
        server_config = config.get("server", {})
        self.timeout = server_config.get("request_timeout", 30)
        
        # 缓存基础指令集（用于无会话情况下的fallback）
        self.base_operations = ["general_chat"]
        self.session_aware = True
        
        # 初始化日志记录器
        self.logger = get_enhanced_logger()
    
    def generate_dynamic_prompt(self, session_id: str, user_input: str, 
                              scene_type: str = "public") -> str:
        """
        根据会话生成提示词（已废弃，现在使用函数调用模式）
        """
        # 警告：此方法已废弃，应使用函数调用模式
        print(f"[DynamicLLM] 警告：调用了已废弃的generate_dynamic_prompt方法")
        
        # 返回基础提示词
        return f"场景：{scene_type}\n用户输入：{user_input}"
    
    def parse_user_input_with_session(self, session_id: str, user_input: str, 
                                    scene_type: str = "public") -> str:
        """
        带会话支持的用户输入解析
        """
        # 生成动态提示词
        prompt = self.generate_dynamic_prompt(session_id, user_input, scene_type)
        
        # 调用LLM
        return self._chat_completions(prompt)
    
    def get_available_functions(self, session_id: str = None) -> List[Dict[str, Any]]:
        """
        获取会话支持的OpenAI标准函数定义
        """
        if session_id:
            from ..session.strict_session_manager import strict_session_manager
            functions = strict_session_manager.get_functions_for_session(session_id)
            if functions:
                return functions
        
        # 返回空列表表示不支持函数调用
        return []
    
    def generate_function_calling_payload(self, session_id: str, user_input: str, 
                                        scene_type: str = "public", rag_instruction: str = "", 
                                        functions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成OpenAI标准函数调用格式的请求
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            scene_type: 场景类型
            rag_instruction: RAG检索结果
            functions: 从会话中获取的已验证函数定义列表
        
        Returns:
            符合OpenAI API标准的请求负载
        """
        # 构建系统消息 - 强制保持对话内容
        system_message = "你是智能助手。必须遵守以下规则：1. 每次响应都必须包含自然语言对话内容；2. 在调用函数时，要先解释将要做什么；3. 用友好自然的语言与用户交流。"
        user_message = f"场景：{scene_type}\n{rag_instruction}\n用户输入：{user_input}"
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        # 构建基础payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.parameters.get("temperature", 0.1),
            "max_tokens": self.parameters.get("max_tokens", 1024),
            "top_p": self.parameters.get("top_p", 0.1),
        }
        
        # 直接使用从会话中获取的已验证函数定义
        if functions and len(functions) > 0:
            # 会话中的函数已经经过验证，直接使用
            payload["functions"] = functions
            payload["function_call"] = "auto"
            print(f"[LLM] 已添加 {len(functions)} 个已验证的函数定义")
        else:
            # 无函数定义时使用普通对话模式
            print("[LLM] 未提供函数定义，使用普通对话模式")
            # 可以在这里添加特殊的系统提示词来引导普通对话
            messages[0]["content"] = f"{system_message}\n\n当前处于普通对话模式，请以友好、专业的态度回答用户问题。"
        
        return payload

    def _chat_completions_with_functions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用支持函数调用的Chat Completions API
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM 未配置 base_url 或 api_key，请在 config.json 或环境变量中设置")
        
        self.logger.llm.info('Sending function call request to LLM', 
                          {'model': self.model, 'has_functions': 'functions' in payload})
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # 记录发送的完整请求
        self.logger.llm.info('Sending request to External LLM API', 
                          {'payload': payload, 'endpoint': url})
        
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            self.logger.llm.error('LLM request exception', {'error': str(e)})
            raise RuntimeError(f"LLM 请求异常: {str(e)}") from e
        
        if resp.status_code != 200:
            err_body = resp.text
            try:
                err_json = resp.json()
                err_body = err_json.get("error", {}).get("message", err_body)
            except Exception:
                pass
            self.logger.llm.error('LLM API call failed', 
                          {'status_code': resp.status_code, 'error': err_body})
            raise RuntimeError(f"LLM API 调用失败 [code={resp.status_code}]: {err_body}")
        
        response_data = resp.json()
        
        # 记录接收到的完整响应
        self.logger.llm.info('Received response from External LLM API', 
                          {'response_size': len(str(response_data))})
        
        self.logger.llm.info('Successfully received LLM response', 
                          {'has_choices': len(response_data.get('choices', [])) > 0})
        return response_data

    def parse_function_call_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析OpenAI标准函数调用响应
        
        Args:
            response: OpenAI API响应
            
        Returns:
            标准化指令字典（始终包含对话内容）
        """
        choices = response.get("choices", [])
        if not choices:
            raise RuntimeError("LLM 响应中无 choices")
        
        msg = choices[0].get("message", {})
        function_call = msg.get("function_call")
        content = msg.get("content", "")
        
        # 直接使用LLM返回的内容，不添加后备机制
        # 如果content为空，则保持为空（用户可接受偶尔的这种情况）
        
        if function_call:
            # 严格解析OpenAI标准的函数调用
            function_name = function_call.get("name")
            arguments_str = function_call.get("arguments", "{}")
            
            # 解析arguments为JSON对象
            try:
                import json
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                print(f"[LLM] 警告：函数参数JSON解析失败: {e}")
                arguments = {}
            
            # 构建标准化响应（包含对话内容）
            result = {
                "command": function_name,
                "parameters": arguments,
                "type": "function_call",
                "format": "openai_standard",
                "response": content  # 始终包含对话内容
            }
            
            print(f"[LLM] 成功解析函数调用: {function_name} with {len(arguments)} 参数")
            return result
        else:
            # 没有函数调用时的处理
            return {
                "command": "general_chat",
                "response": content,
                "type": "direct_response",
                "format": "openai_standard"
            }

    def _chat_completions(self, prompt: str) -> str:
        """
        调用 OpenAI 兼容的 Chat Completions API
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM 未配置 base_url 或 api_key，请在 config.json 或环境变量中设置")
        
        self.logger.llm.info('Sending prompt to LLM', 
                          {'prompt_length': len(prompt), 'model': self.model})
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # 构建消息内容，添加系统提示词强制JSON格式
        system_message = "你是一个API助手。必须严格按照JSON格式回复，不要添加任何额外解释。"
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.parameters.get("temperature", 0.1),  # 降低温度增加确定性
            "max_tokens": self.parameters.get("max_tokens", 1024),
            "top_p": self.parameters.get("top_p", 0.1),  # 降低top_p增加一致性
        }
        
        # 添加JSON格式强制参数（如果模型支持）
        try:
            payload["response_format"] = {"type": "json_object"}
            self.logger.llm.info('Enabled JSON format constraint')
        except:
            self.logger.llm.warn('Current model does not support JSON format constraint, using prompt constraint')
        
        # 添加可选参数
        if self.parameters.get("stream") is not None:
            payload["stream"] = self.parameters["stream"]
        if self.parameters.get("seed") is not None:
            payload["seed"] = self.parameters["seed"]
        if self.parameters.get("presence_penalty") is not None:
            payload["presence_penalty"] = self.parameters["presence_penalty"]
        if self.parameters.get("frequency_penalty") is not None:
            payload["frequency_penalty"] = self.parameters["frequency_penalty"]
        if self.parameters.get("n") is not None:
            payload["n"] = self.parameters["n"]
        
        # 记录发送的完整请求
        self.logger.llm.info('Sending request to External LLM API', 
                          {'endpoint': url})
        
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            self.logger.llm.error('LLM request exception', {'error': str(e)})
            raise RuntimeError(f"LLM 请求异常: {str(e)}") from e
        
        if resp.status_code != 200:
            err_body = resp.text
            try:
                err_json = resp.json()
                err_body = err_json.get("error", {}).get("message", err_body)
            except Exception:
                pass
            self.logger.llm.error('LLM API call failed', 
                          {'status_code': resp.status_code, 'error': err_body})
            raise RuntimeError(f"LLM API 调用失败 [code={resp.status_code}]: {err_body}")
        
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("LLM 响应中无 choices")
        
        msg = choices[0].get("message", {})
        text = msg.get("content", "")
        if not text or not str(text).strip():
            raise RuntimeError("LLM 返回内容为空")
        
        result = str(text).strip()
        
        # 记录接收到的完整响应
        self.logger.llm.info('Received response from External LLM API', 
                          {'response_length': len(result)})
        
        self.logger.llm.info('Successfully received LLM response', 
                          {'response_length': len(result)})
        return result

    async def stream_chat_completions(self, messages: List[Dict[str, Any]]):
        """
        流式调用 OpenAI 兼容的 Chat Completions API
        
        Args:
            messages: 消息列表
        
        Yields:
            文本片段
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM 未配置 base_url 或 api_key，请在 config.json 或环境变量中设置")
        
        self.logger.llm.info('Sending streaming request to LLM', 
                          {'model': self.model, 'messages_count': len(messages)})
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.parameters.get("temperature", 0.7),
            "max_tokens": self.parameters.get("max_tokens", 1024),
            "top_p": self.parameters.get("top_p", 0.9),
            "stream": True  # 启用流式输出
        }
        
        # 记录发送的请求
        self.logger.llm.info('Sending request to External LLM API (Stream)', 
                          {'model': self.model, 'stream': True, 'endpoint': url})
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=self.timeout) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.llm.error('LLM API call failed', 
                                      {'status_code': resp.status, 'error': error_text})
                        raise RuntimeError(f"LLM API 调用失败 [code={resp.status}]: {error_text}")
                    
                    async for line in resp.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]
                                if data_str == '[DONE]':
                                    break
                                try:
                                    data = json.loads(data_str)
                                    choices = data.get('choices', [])
                                    if choices:
                                        delta = choices[0].get('delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            self.logger.llm.info('Received streaming data chunk', 
                                                                   {'content': content[:50]})
                                            yield content
                                except json.JSONDecodeError:
                                    pass
        except Exception as e:
            self.logger.llm.error('Streaming request exception', {'error': str(e)})
            raise RuntimeError(f"LLM 流式请求异常: {str(e)}") from e


# 使用示例和测试函数
def demonstrate_dynamic_client():
    """演示动态客户端的使用"""
    client = DynamicLLMClient()
    
    # 模拟会话ID
    test_session_id = "test-session-123"
    
    # 获取当前可用指令
    available_ops = client.get_available_operations(test_session_id)
    print(f"Available operations: {available_ops}")
    
    # 生成动态提示词示例
    sample_prompt = client.generate_dynamic_prompt(
        session_id=test_session_id,
        user_input="我想了解这件文物的历史",
        scene_type="study"
    )
    print(f"Generated prompt: {sample_prompt}")


def test_fallback_behavior():
    """测试fallback行为"""
    client = DynamicLLMClient()
    
    # 测试无会话的情况
    no_session_ops = client.get_available_operations(None)
    print(f"No session operations: {no_session_ops}")
    
    # 测试无效会话的情况
    invalid_session_ops = client.get_available_operations("invalid-session-id")
    print(f"Invalid session operations: {invalid_session_ops}")


if __name__ == "__main__":
    print("=== Dynamic LLM Client Demo ===")
    demonstrate_dynamic_client()
    
    print("\n=== Fallback Behavior Test ===")
    test_fallback_behavior()