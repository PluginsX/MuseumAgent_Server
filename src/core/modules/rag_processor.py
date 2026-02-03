# -*- coding: utf-8 -*-
"""
RAG处理器模块
专门负责向量检索和文物信息获取
"""

from typing import Dict, Any, List
from ..chroma_service import ChromaService
from ..knowledge_base import ArtifactKnowledgeBase
from ...common.log_formatter import log_step, log_communication


class RAGProcessor:
    """RAG检索处理器"""
    
    def __init__(self):
        """初始化RAG处理器"""
        self.chroma_service = ChromaService()
        self.knowledge_base = ArtifactKnowledgeBase()
    
    def perform_retrieval(self, user_input: str, top_k: int = 3) -> Dict[str, Any]:
        """
        执行RAG检索
        
        Args:
            user_input: 用户输入
            top_k: 返回最相关的top_k个结果
            
        Returns:
            包含检索结果的字典
        """
        # 记录开始步骤
        print(log_step('RAG', 'START', f'执行向量检索 (Top-K: {top_k})', 
                      {'query': user_input, 'top_k': top_k}))
        
        # 记录向量数据库通信
        print(log_communication('RAG', 'SEND', 'ChromaDB Vector Store', 
                               {'query_text': user_input, 'top_k': top_k}))
        
        # 1. 执行向量相似度搜索
        search_results = self.chroma_service.search(
            query_text=user_input,
            top_k=top_k
        )
        
        # 记录接收结果
        print(log_communication('RAG', 'RECEIVE', 'ChromaDB Vector Store', 
                               search_results, 
                               {'result_count': len(search_results)}))
        
        print(log_step('RAG', 'PROCESS', f'检索完成，找到 {len(search_results)} 个相关文档'))
        
        # 2. 提取相关文物信息
        relevant_artifacts = []
        for result in search_results:
            metadata = result.get('metadata', {})
            artifact_id = metadata.get('artifact_id')
            artifact_name = metadata.get('artifact_name')
            document = result.get('document', '')
            distance = result.get('distance', 0)
            
            print(log_step('RAG', 'DEBUG', f'处理检索结果', 
                          {'artifact_name': artifact_name, 'artifact_id': artifact_id, 'distance': distance}))
            
            if artifact_name:  # 只需要文物名称即可
                try:
                    # 获取详细文物信息
                    artifact_info = self.knowledge_base.get_standard_artifact_data(artifact_name)
                    relevant_artifacts.append({
                        'artifact_id': artifact_id or f"auto_{hash(artifact_name)}",  # 自动生成ID
                        'artifact_name': artifact_name,
                        'document': document,
                        'distance': distance,
                        'info': artifact_info
                    })
                except Exception as e:
                    print(log_step('RAG', 'ERROR', f'获取文物详情失败: {artifact_name}', 
                                 {'error': str(e)}))
                    # 即使获取详情失败，也保留基本信息
                    relevant_artifacts.append({
                        'artifact_id': artifact_id or f"auto_{hash(artifact_name)}",
                        'artifact_name': artifact_name,
                        'document': document,
                        'distance': distance,
                        'info': {}
                    })
            else:
                print(log_step('RAG', 'WARNING', '跳过无效检索结果', 
                              {'missing_fields': ['artifact_name'] if not artifact_name else []}))
        
        return {
            'search_results': search_results,
            'relevant_artifacts': relevant_artifacts,
            'total_found': len(relevant_artifacts)
        }
    
    def get_artifact_details(self, artifact_name: str) -> Dict[str, Any]:
        """
        获取文物详细信息
        
        Args:
            artifact_name: 文物名称
            
        Returns:
            文物详细信息字典
        """
        try:
            return self.knowledge_base.get_standard_artifact_data(artifact_name)
        except Exception as e:
            print(f"[RAG] 获取文物详情失败: {e}")
            return {}