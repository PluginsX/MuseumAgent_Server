# -*- coding: utf-8 -*-
"""
ChromaDB 向量存储服务
"""
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from src.common.config_utils import get_global_config
from src.common.log_formatter import log_step
from src.core.embedding_client import EmbeddingClient


_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ChromaService:
    """ChromaDB 向量存储与检索"""

    COLLECTION_NAME = "artifact_texts"

    def __init__(self) -> None:
        try:
            config = get_global_config()
            kb = config.get("artifact_knowledge_base", {})
            path = kb.get("chroma_path") or "./data/chroma_db"
        except Exception:
            path = "./data/chroma_db"
        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(_project_root, path))
        os.makedirs(path, exist_ok=True)
        self._persist_dir = path
        self._client = None
        self._collection = None
        self._embedding_client = EmbeddingClient()

    def _get_client(self):
        """懒加载 Chroma 客户端"""
        if self._client is None:
            import chromadb
            from chromadb.config import Settings
            self._client = chromadb.PersistentClient(
                path=self._persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self):
        """获取或创建 artifact_texts 集合"""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Museum artifact text embeddings"},
            )
        return self._collection

    def embed_text(self, text: str) -> List[float]:
        """调用 Embedding 服务获取向量"""
        print(log_step('EMBEDDING', 'START', f'将文本向量化', 
                      {'text_length': len(text), 'preview': text[:50]}))
        
        try:
            vectors = self._embedding_client.embed(text)
            vector_result = vectors[0] if vectors else []
            print(log_step('EMBEDDING', 'SUCCESS', f'向量化完成', 
                          {'vector_dimension': len(vector_result)}))
            return vector_result
        except Exception as e:
            print(log_step('EMBEDDING', 'ERROR', f'向量化失败: {str(e)}'))
            raise

    def add(
        self,
        document: str,
        artifact_id: str,
        artifact_name: str,
        text_type: str = "description",
        source: str = "manual_input",
        doc_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata_extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        添加文档到向量库
        返回文档 ID
        """
        coll = self._get_collection()
        doc_id = doc_id or f"{artifact_id}_{text_type}_{uuid.uuid4().hex[:8]}"
        metadata = {
            "artifact_id": artifact_id,
            "artifact_name": artifact_name,
            "text_type": text_type,
            "source": source,
        }
        if metadata_extra:
            for k, v in metadata_extra.items():
                if v is not None and k not in metadata:
                    metadata[k] = str(v) if not isinstance(v, (str, int, float, bool)) else v
        if embedding is None:
            embedding = self.embed_text(document)
        coll.add(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
            embeddings=[embedding],
        )
        return doc_id

    def add_batch(
        self,
        documents: List[str],
        artifact_ids: List[str],
        artifact_names: List[str],
        text_types: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """批量添加"""
        n = len(documents)
        text_types = text_types or ["description"] * n
        ids = [f"{artifact_ids[i]}_{text_types[i]}_{uuid.uuid4().hex[:8]}" for i in range(n)]
        metadatas = [
            {
                "artifact_id": artifact_ids[i],
                "artifact_name": artifact_names[i],
                "text_type": text_types[i],
                "source": "manual_input",
            }
            for i in range(n)
        ]
        if embeddings is None:
            embeddings = []
            for doc in documents:
                emb = self.embed_text(doc)
                embeddings.append(emb)
        self._get_collection().add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return ids

    def get_by_artifact_id(self, artifact_id: str) -> List[Dict[str, Any]]:
        """获取某文物的所有向量记录"""
        coll = self._get_collection()
        res = coll.get(
            where={"artifact_id": artifact_id},
            include=["documents", "metadatas", "embeddings"],
        )
        out = []
        for i in range(len(res["ids"])):
            out.append({
                "id": res["ids"][i],
                "document": res["documents"][i] if res["documents"] else None,
                "metadata": res["metadatas"][i] if res["metadatas"] else {},
            })
        return out

    def delete(self, vector_id: str) -> None:
        """删除单条向量"""
        self._get_collection().delete(ids=[vector_id])

    def search(
        self,
        query_text: str,
        top_k: int = 5,
        artifact_id: Optional[str] = None,
        text_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """向量搜索"""
        print(log_step('RAG', 'VECTORIZE', f'准备向量化查询文本', 
                      {'query_length': len(query_text)}))
        
        query_embedding = self.embed_text(query_text)
        
        print(log_step('RAG', 'QUERY', f'执行向量相似度搜索', 
                      {'top_k': top_k, 'vector_dimension': len(query_embedding)}))
        
        where = {}
        if artifact_id:
            where["artifact_id"] = artifact_id
        if text_type:
            where["text_type"] = text_type
        coll = self._get_collection()
        res = coll.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where if where else None,
            include=["documents", "metadatas", "distances"],
        )
        out = []
        for i in range(len(res["ids"][0])):
            out.append({
                "id": res["ids"][0][i],
                "document": res["documents"][0][i] if res["documents"] else None,
                "metadata": res["metadatas"][0][i] if res["metadatas"] else {},
                "distance": res["distances"][0][i] if res.get("distances") else None,
            })
        
        print(log_step('RAG', 'RESULTS', f'搜索完成', 
                      {'found_count': len(out), 'top_distances': [item.get('distance') for item in out[:3]]}))
        
        return out

    def count(self) -> int:
        """集合内文档数量"""
        return self._get_collection().count()

    def stats(self) -> Dict[str, Any]:
        """统计信息"""
        coll = self._get_collection()
        count = coll.count()
        return {
            "total_vectors": count,
            "collection_name": self.COLLECTION_NAME,
        }

    def clear(self) -> None:
        """清空当前集合（删除后重建）"""
        client = self._get_client()
        try:
            client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
        self._collection = None
        self._get_collection()
