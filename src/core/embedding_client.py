# -*- coding: utf-8 -*-
"""
Embedding 服务调用模块 - OpenAI Embedding API 兼容格式
"""
import os
from typing import List, Union

import requests

from src.common.config_utils import get_global_config


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
        """
        if not self.base_url or not self.api_key:
            raise RuntimeError(
                "Embedding 未配置 base_url 或 api_key，请在 config.json 或环境变量中设置"
            )
        
        if isinstance(texts, str):
            texts = [texts]
        
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
        
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Embedding 请求异常: {str(e)}") from e
        
        if resp.status_code != 200:
            err_body = resp.text
            try:
                err_json = resp.json()
                err_body = err_json.get("error", {}).get("message", err_body)
            except Exception:
                pass
            raise RuntimeError(
                f"Embedding API 调用失败 [code={resp.status_code}]: {err_body}"
            )
        
        data = resp.json()
        emb_list = data.get("data", [])
        # 按 index 排序（部分 API 可能乱序返回）
        emb_list.sort(key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in emb_list]
