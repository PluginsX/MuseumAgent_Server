# -*- coding: utf-8 -*-
"""
Embedding 服务调用模块 - OpenAI Embedding API 兼容格式
"""
import os
from typing import List, Union

import requests

from src.common.config_utils import get_global_config
from src.common.log_formatter import log_step, log_communication


class EmbeddingClient:
    """OpenAI 兼容格式 Embedding 客户端"""
    
    def __init__(self) -> None:
        """从全局配置读取 Embedding 参数"""
        config = get_global_config()
        emb_config = config.get("embedding", {})
        
        self.base_url = (
            os.getenv("EMBEDDING_BASE_URL") or emb_config.get("base_url", "")
        ).rstrip("/")
        self.api_key = os.getenv("EMBEDDING_API_KEY") or emb_config.get("api_key", "")
        self.model = (
            os.getenv("EMBEDDING_MODEL") or emb_config.get("model", "text-embedding-v4")
        )
        self.parameters = emb_config.get("parameters", {})
        
        server_config = config.get("server", {})
        self.timeout = server_config.get("request_timeout", 30)
    
    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        调用 OpenAI 兼容的 Embeddings API
        
        POST {base_url}/embeddings
        
        Args:
            texts: 单个文本或文本列表
        
        Returns:
            向量列表，每个文本对应一个 float 列表
        
        Raises:
            RuntimeError: 当 API 响应格式不符合 OpenAI 标准时
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError(
                "Embedding 未配置 base_url 或 api_key，请在 config.json 或环境变量中设置"
            )
        
        if isinstance(texts, str):
            texts = [texts]
        
        print(log_communication('EMBEDDING', 'SEND', 'Embedding Service', 
                               {'text_count': len(texts), 
                                'first_text_preview': texts[0][:50] if texts else ''}))
        
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }
        
        dimensions = self.parameters.get("dimensions")
        if dimensions is not None:
            payload["dimensions"] = dimensions
            
        # 添加编码格式参数
        encoding_format = self.parameters.get("encoding_format")
        if encoding_format is not None:
            payload["encoding_format"] = encoding_format
        
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            print(log_step('EMBEDDING', 'ERROR', f'网络请求异常: {str(e)}'))
            raise RuntimeError(f"Embedding 请求异常: {str(e)}") from e
        
        if resp.status_code != 200:
            err_body = resp.text
            try:
                err_json = resp.json()
                err_body = err_json.get("error", {}).get("message", err_body)
            except Exception:
                pass
            print(log_step('EMBEDDING', 'ERROR', f'API调用失败', 
                          {'status_code': resp.status_code, 'error': err_body}))
            raise RuntimeError(
                f"Embedding API 调用失败 [code={resp.status_code}]: {err_body}"
            )
        
        # 验证响应格式
        try:
            data = resp.json()
        except Exception as e:
            print(log_step('EMBEDDING', 'ERROR', f'响应不是有效的JSON格式: {str(e)}'))
            raise RuntimeError(f"Embedding API 返回的响应不是有效的 JSON 格式: {str(e)}") from e
        
        # 验证 OpenAI 标准格式：必须包含 data 字段
        if "data" not in data:
            print(log_step('EMBEDDING', 'ERROR', '响应缺少data字段'))
            raise RuntimeError(
                "Embedding API 响应格式错误：缺少 'data' 字段。"
                "OpenAI Embeddings API 标准格式应为: {\"data\": [{\"embedding\": [...]}]}"
            )
        
        emb_list = data.get("data", [])
        
        # 验证 data 字段是否为数组
        if not isinstance(emb_list, list):
            print(log_step('EMBEDDING', 'ERROR', f'data字段类型错误: {type(emb_list)}'))
            raise RuntimeError(
                f"Embedding API 响应格式错误：'data' 字段必须是数组类型，实际类型为 {type(emb_list).__name__}"
            )
        
        # 验证每个数据项的格式
        for i, item in enumerate(emb_list):
            if not isinstance(item, dict):
                print(log_step('EMBEDDING', 'ERROR', f'数据项{i}不是字典类型'))
                raise RuntimeError(
                    f"Embedding API 响应格式错误：data[{i}] 必须是字典类型，实际类型为 {type(item).__name__}"
                )
            
            if "embedding" not in item:
                print(log_step('EMBEDDING', 'ERROR', f'数据项{i}缺少embedding字段'))
                raise RuntimeError(
                    f"Embedding API 响应格式错误：data[{i}] 缺少 'embedding' 字段。"
                    "OpenAI Embeddings API 标准格式应为: {\"embedding\": [...]}"
                )
            
            embedding = item["embedding"]
            
            # 验证 embedding 是否为列表
            if not isinstance(embedding, list):
                print(log_step('EMBEDDING', 'ERROR', f'数据项{i}的embedding不是列表类型'))
                raise RuntimeError(
                    f"Embedding API 响应格式错误：data[{i}].embedding 必须是数组类型，实际类型为 {type(embedding).__name__}"
                )
            
            # 验证 embedding 中的每个元素是否为数字
            for j, value in enumerate(embedding):
                if not isinstance(value, (int, float)):
                    print(log_step('EMBEDDING', 'ERROR', 
                                f'数据项{i}的embedding[{j}]不是数字类型: {type(value)}'))
                    raise RuntimeError(
                        f"Embedding API 响应格式错误：data[{i}].embedding[{j}] 必须是数字类型，实际类型为 {type(value).__name__}"
                    )
        
        # 按 index 排序（部分 API 可能乱序返回）
        emb_list.sort(key=lambda x: x.get("index", 0))
        
        # 安全获取维度信息
        dimension = 0
        if emb_list and emb_list[0].get('embedding'):
            dimension = len(emb_list[0]['embedding'])
        
        print(log_communication('EMBEDDING', 'RECEIVE', 'Embedding Service', 
                               {'vector_count': len(emb_list), 
                                'dimension': dimension}))
        
        # 安全返回嵌入向量
        return [item.get("embedding", []) for item in emb_list]
