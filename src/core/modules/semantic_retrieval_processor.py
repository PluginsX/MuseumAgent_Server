# -*- coding: utf-8 -*-
"""
语义检索处理器模块
负责与语义检索系统进行交互，执行RAG（检索增强生成）功能
该模块通过semantic_retrieval_client与远程语义检索系统通信，
不包含任何本地向量数据库或嵌入模型的实现。
"""

from typing import Dict, Any, List
from semantic_retrieval_client import SemanticRetrievalClient
from semantic_retrieval_client.exceptions import APIError
from ...common.config_utils import get_global_config
from ...common.enhanced_logger import get_enhanced_logger
from ...services.interrupt_manager import get_interrupt_manager


class SemanticRetrievalProcessor:
    """语义检索处理器"""
    
    def __init__(self):
        """初始化语义检索处理器"""
        # 获取日志记录器
        self.logger = get_enhanced_logger()
        self.interrupt_manager = get_interrupt_manager()
        
        try:
            config = get_global_config()
            # 从全局配置中获取语义检索系统的连接信息
            retrieval_config = config.get('semantic_retrieval', {})
            self.base_url = retrieval_config.get('base_url', 'http://localhost:12315/api/v1')
            self.api_key = retrieval_config.get('api_key', None)
            # 从search_params中获取搜索参数
            search_params = retrieval_config.get('search_params', {})
            self.top_k_default = search_params.get('top_k', 3)
            self.threshold_default = search_params.get('threshold', 0.5)
        except:
            # 后备配置
            self.base_url = 'http://localhost:12315/api/v1'
            self.api_key = None
            self.top_k_default = 3
            self.threshold_default = 0.5
        
        # 初始化语义检索客户端
        self.client = SemanticRetrievalClient(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    def reload_config(self) -> None:
        """
        重新加载配置
        """
        try:
            config = get_global_config()
            # 从全局配置中获取语义检索系统的连接信息
            retrieval_config = config.get('semantic_retrieval', {})
            self.base_url = retrieval_config.get('base_url', 'http://localhost:12315/api/v1')
            self.api_key = retrieval_config.get('api_key', None)
            # 从search_params中获取搜索参数
            search_params = retrieval_config.get('search_params', {})
            self.top_k_default = search_params.get('top_k', 3)
            self.threshold_default = search_params.get('threshold', 0.5)
            
            # 更新语义检索客户端
            self.client = SemanticRetrievalClient(
                base_url=self.base_url,
                api_key=self.api_key
            )
        except:
            # 后备配置
            pass
    
    def perform_retrieval(self, query: str, top_k: int = None, session_id: str = None) -> Dict[str, Any]:
        """
        执行语义检索
        
        Args:
            query: 检索查询
            top_k: 返回结果数量，默认使用配置值
            
        Returns:
            检索结果字典
        """
        # 重新加载配置，确保使用最新的值
        self.reload_config()
        
        if top_k is None:
            top_k = self.top_k_default
        
        try:
            self.logger.rag.info(f"Starting semantic retrieval, query: {query[:50]}...")
            
            # ✅ 注册到中断管理器（SRS客户端内部使用HTTP会话）
            # 注意：semantic_retrieval_client 可能不暴露内部的 session
            # 我们需要在客户端层面处理中断
            
            # 执行搜索 - 通过远程语义检索系统
            search_result = self.client.search(
                query=query,
                top_k=top_k,
                threshold=self.threshold_default
            )
            
            # 整理检索结果
            relevant_artifacts = []
            for artifact in search_result.artifacts:
                artifact_data = {
                    'id': artifact.get('id'),
                    'title': artifact.get('title'),
                    'content': artifact.get('content'),
                    'category': artifact.get('category'),
                    'similarity': artifact.get('similarity', 0),
                    'tags': artifact.get('tags', [])
                }
                relevant_artifacts.append(artifact_data)
            
            result = {
                'success': True,
                'query': search_result.query,
                'relevant_artifacts': relevant_artifacts,
                'total_count': search_result.total_count,
                'response_time': search_result.response_time
            }
            
            self.logger.rag.info(f"Semantic retrieval completed, found {len(relevant_artifacts)} relevant artifacts")
            return result
            
        except APIError as e:
            self.logger.rag.error(f"Semantic retrieval API error: {str(e)}")
            return {
                'success': False,
                'error': f'API错误: {str(e)}',
                'relevant_artifacts': [],
                'query': query
            }
        except Exception as e:
            self.logger.rag.error(f"Semantic retrieval unknown error occurred: {str(e)}")
            return {
                'success': False,
                'error': f'检索错误: {str(e)}',
                'relevant_artifacts': [],
                'query': query
            }
    
    def get_artifacts(self, page: int = 1, size: int = 10, keyword: str = None, category: str = None) -> Dict[str, Any]:
        """
        获取资料列表
        
        Args:
            page: 页码
            size: 每页数量
            keyword: 关键词筛选
            category: 分类筛选
            
        Returns:
            资料列表结果
        """
        try:
            result = self.client.get_artifacts(
                page=page,
                size=size,
                keyword=keyword,
                category=category
            )
            
            return {
                'success': True,
                'artifacts': result.get('artifacts', []),
                'total_count': result.get('total_count', 0),
                'current_page': result.get('current_page', page),
                'total_pages': result.get('total_pages', 1)
            }
        except APIError as e:
            return {
                'success': False,
                'error': f'API错误: {str(e)}',
                'artifacts': [],
                'total_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取资料错误: {str(e)}',
                'artifacts': [],
                'total_count': 0
            }