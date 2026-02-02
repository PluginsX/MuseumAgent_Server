# -*- coding: utf-8 -*-
"""
动态LLM客户端
支持会话感知的指令集动态提示词生成
"""
from typing import List, Dict, Any
import json
from datetime import datetime

from .llm_client import LLMClient
from ..session.session_manager import session_manager


class DynamicLLMClient(LLMClient):
    """支持动态指令集的LLM客户端"""
    
    def __init__(self):
        super().__init__()
        # 缓存基础指令集（用于无会话情况下的fallback）
        self.base_operations = ["introduce", "query_param"]
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
            context_note = "（使用基础指令集，建议重新注册会话）"
        else:
            operations = session_operations
            context_note = f"（当前会话支持{len(operations)}个指令）"
        
        # 构造动态提示词
        dynamic_prompt = self.prompt_template.format(
            scene_type=scene_type,
            user_input=user_input,
            valid_operations=", ".join(operations),
            context_note=context_note
        )
        
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
        重写父类方法，添加会话感知的日志
        """
        print(f"[DynamicLLM] Sending prompt to LLM...")
        print(f"[DynamicLLM] Prompt length: {len(prompt)} chars")
        
        # 调用父类的实际实现
        result = super()._chat_completions(prompt)
        
        print(f"[DynamicLLM] Received response: {result[:100]}...")
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