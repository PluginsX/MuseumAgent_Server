# -*- coding: utf-8 -*-
"""向量化与知识库管理 API"""
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.common.auth_utils import get_current_user
from src.core.chroma_service import ChromaService
from src.core.embedding_client import EmbeddingClient

router = APIRouter(prefix="/api/admin/embedding", tags=["向量与知识库"])


class VectorizeRequest(BaseModel):
    text: str
    model: Optional[str] = None
    artifact_id: Optional[str] = None


class VectorizeBatchItem(BaseModel):
    id: str
    content: str


class VectorizeBatchRequest(BaseModel):
    texts: List[VectorizeBatchItem]
    model: Optional[str] = None


class StoreRequest(BaseModel):
    artifact_id: str
    text_content: str
    artifact_name: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class SearchRequest(BaseModel):
    query_text: str
    top_k: int = 5
    artifact_id: Optional[str] = None
    text_type: Optional[str] = None


def _chroma() -> ChromaService:
    return ChromaService()


@router.post("/vectorize")
def vectorize_text(
    body: VectorizeRequest,
    _: dict = Depends(get_current_user),
):
    """向量化单条文本"""
    try:
        client = EmbeddingClient()
        t0 = time.time()
        vectors = client.embed(body.text)
        elapsed = time.time() - t0
        dim = len(vectors[0]) if vectors else 0
        return {
            "text": body.text,
            "vector": vectors[0] if vectors else [],
            "model": client.model,
            "dimension": dim,
            "processing_time": round(elapsed, 3),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量化失败: {str(e)}")


@router.post("/vectorize/batch")
def vectorize_batch(
    body: VectorizeBatchRequest,
    _: dict = Depends(get_current_user),
):
    """批量向量化"""
    client = EmbeddingClient()
    texts = [t.content for t in body.texts]
    t0 = time.time()
    vectors = client.embed(texts)
    elapsed = time.time() - t0
    return {
        "count": len(vectors),
        "vectors": vectors,
        "model": client.model,
        "dimension": len(vectors[0]) if vectors else 0,
        "processing_time": round(elapsed, 3),
    }


@router.post("/store")
def store_vector(
    body: StoreRequest,
    _: dict = Depends(get_current_user),
):
    """存储向量化文本到 ChromaDB"""
    try:
        svc = _chroma()
        doc_id = svc.add(
            document=body.text_content,
            artifact_id=body.artifact_id,
            artifact_name=body.artifact_name or body.artifact_id,
            metadata_extra=body.metadata,
        )
        return {"id": doc_id, "artifact_id": body.artifact_id}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"存储失败: {str(e)}")


@router.get("/artifact/{artifact_id}")
def get_artifact_vectors(
    artifact_id: str,
    _: dict = Depends(get_current_user),
):
    """获取某文物的所有向量"""
    svc = _chroma()
    items = svc.get_by_artifact_id(artifact_id)
    return {"artifact_id": artifact_id, "vectors": items}


@router.delete("/vector/{vector_id}")
def delete_vector(
    vector_id: str,
    _: dict = Depends(get_current_user),
):
    """删除一条向量"""
    svc = _chroma()
    svc.delete(vector_id)
    return {"deleted": vector_id}


@router.post("/search")
def search_vectors(
    body: SearchRequest,
    _: dict = Depends(get_current_user),
):
    """向量搜索"""
    try:
        svc = _chroma()
        results = svc.search(
            query_text=body.query_text,
            top_k=body.top_k,
            artifact_id=body.artifact_id,
            text_type=body.text_type,
        )
        return {"results": results}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/stats")
def get_embedding_stats(_: dict = Depends(get_current_user)):
    """知识库统计"""
    try:
        svc = _chroma()
        return svc.stats()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.delete("/clear")
def clear_embedding(_: dict = Depends(get_current_user)):
    """清空向量库"""
    svc = _chroma()
    svc.clear()
    return {"message": "已清空"}
