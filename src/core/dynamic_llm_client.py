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
from ..session.session_manager import session_manager
from ..common.log_formatter import log_step, log_communication


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
    
    def generate_dynamic_prompt(self, session_id: str, user_input: str, 
                              scene_type: str = "public") -> str:
        """
        根据会话动态生成提示词
        """
        # 获取会话特定的操作指令集
        session_operations = session_manager.get_operations_for_session(session_id)
        
        # 如果没有有效会话，使用基础指令集
        if not session_operations:
            operations = self.base_operations
        else:
            operations = session_operations
        
        # 构造动态提示词（使用安全的字符串替换）
        dynamic_prompt = self.prompt_template.replace('{scene_type}', scene_type)
        dynamic_prompt = dynamic_prompt.replace('{user_input}', user_input)
        dynamic_prompt = dynamic_prompt.replace('{valid_operations}', ", ".join(operations))
        
        # 记录提示词生成日志
        print(f"[DynamicLLM] Session: {session_id}")
        print(f"[DynamicLLM] Operations: {operations}")
        print(f"[DynamicLLM] Prompt: {dynamic_prompt[:100]}...")
        
        return dynamic_prompt
    
    def parse_user_input_with_session(self, session_id: str, user_input: str, 
                                    scene_type: str = "public") -> str:
        """
        带会话支持的用户输入解析
        """
        # 生成动态提示词
        prompt = self.generate_dynamic_prompt(session_id, user_input, scene_type)
        
        # 调用LLM
        return self._chat_completions(prompt)
    
    def get_available_operations(self, session_id: str = None) -> List[str]:
        """
        获取可用操作指令集
        """
        if session_id:
            session_ops = session_manager.get_operations_for_session(session_id)
            if session_ops:
                return session_ops
        
        # fallback到基础指令集
        return self.base_operations.copy()
    
    def _chat_completions(self, prompt: str) -> str:
        """
        调用 OpenAI 兼容的 Chat Completions API
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM 未配置 base_url 或 api_key，请在 config.json 或环境变量中设置")
        
        print(log_step('LLM', 'SEND', '发送提示词到LLM', 
                      {'prompt_length': len(prompt), 'model': self.model}))
        
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
            print(log_step('LLM', 'INFO', '启用JSON格式强制约束'))
        except:
            print(log_step('LLM', 'WARNING', '当前模型不支持JSON格式强制，使用提示词约束'))
        
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
        print(log_communication('LLM', 'SEND', 'External LLM API', 
                               payload, {'endpoint': url}))
        
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            print(log_step('LLM', 'ERROR', 'LLM请求异常', {'error': str(e)}))
            raise RuntimeError(f"LLM 请求异常: {str(e)}") from e
        
        if resp.status_code != 200:
            err_body = resp.text
            try:
                err_json = resp.json()
                err_body = err_json.get("error", {}).get("message", err_body)
            except Exception:
                pass
            print(log_step('LLM', 'ERROR', f'LLM API调用失败', 
                          {'status_code': resp.status_code, 'error': err_body}))
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
        print(log_communication('LLM', 'RECEIVE', 'External LLM API', 
                               {'full_response': result, 'usage': data.get('usage', {})},
                               {'response_length': len(result)}))
        
        print(log_step('LLM', 'RECEIVE', '成功接收LLM响应', 
                      {'response_length': len(result)}))
        return result


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