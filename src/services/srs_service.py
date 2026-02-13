# -*- coding: utf-8 -*-
"""
SRS服务接口
使用SRS标准API与语义检索系统通信
"""
import json
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

from src.common.enhanced_logger import get_enhanced_logger
from src.common.config_utils import get_global_config


class SRSService:
    """SRS服务接口"""
    
    def __init__(self):
        """初始化SRS服务"""
        self.logger = get_enhanced_logger()
        self.config = get_global_config()
        self.srs_config = self.config.get("semantic_retrieval", {})
        
        # SRS客户端配置
        self.base_url = self.srs_config.get("base_url", "")
        self.api_key = self.srs_config.get("api_key", "")
        self.timeout = self.srs_config.get("timeout", 300)
        self.search_params = self.srs_config.get("search_params", {})
    
    async def search_artifacts(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索资料接口
        
        Args:
            request: 搜索请求
            
        Returns:
            搜索结果
        """
        self.logger.info("开始SRS资料搜索")
        
        try:
            # 构建搜索请求
            search_request = {
                "query": request.get("query", ""),
                "top_k": request.get("top_k", self.search_params.get("top_k", 3)),
                "threshold": request.get("threshold", self.search_params.get("threshold", 0.35)),
                "category_filter": request.get("category_filter", [])
            }
            
            # 添加认证头
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # 记录请求
            self.logger.rag.info('SRS search request sent', 
                                   {'query': search_request['query'][:50]})
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/search/retrieve",
                    json=search_request,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.rag.info('SRS search response received', 
                                               {'result_count': len(result.get('artifacts', []))})
                        
                        return {
                            "code": 200,
                            "msg": "搜索成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        
                        self.logger.rag.error(f'SRS search failed', 
                                      {'status': response.status, 'error': error_text})
                        
                        return {
                            "code": 500,
                            "msg": f"SRS搜索失败: {error_text}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"SRS搜索异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"SRS搜索异常: {str(e)}",
                "data": None
            }
    
    async def get_artifacts(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取资料列表接口
        
        Args:
            request: 获取资料列表请求
            
        Returns:
            资料列表
        """
        self.logger.info("开始SRS获取资料列表")
        
        try:
            # 构建查询参数
            params = {
                "page": request.get("page", 1),
                "size": request.get("size", 10),
                "keyword": request.get("keyword", ""),
                "category": request.get("category", "")
            }
            
            # 过滤空参数
            filtered_params = {k: v for k, v in params.items() if v}
            
            # 添加认证头
            headers = {
                "X-API-Key": self.api_key
            }
            
            # 记录请求
            self.logger.rag.info('SRS get artifacts list request sent', 
                                   {'params': filtered_params})
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/artifacts",
                    params=filtered_params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.rag.info('SRS artifacts list response received', 
                                               {'artifacts_count': len(result.get('artifacts', []))})
                        
                        return {
                            "code": 200,
                            "msg": "获取资料列表成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        
                        self.logger.rag.error(f'Get artifacts list failed', 
                                      {'status': response.status, 'error': error_text})
                        
                        return {
                            "code": 500,
                            "msg": f"获取资料列表失败: {error_text}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"获取SRS资料列表异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"获取SRS资料列表异常: {str(e)}",
                "data": None
            }
    
    async def get_artifact_by_id(self, artifact_id: str) -> Dict[str, Any]:
        """
        根据ID获取资料接口
        
        Args:
            artifact_id: 资料ID
            
        Returns:
            资料详情
        """
        self.logger.info(f"开始SRS获取资料详情: {artifact_id}")
        
        try:
            # 添加认证头
            headers = {
                "X-API-Key": self.api_key
            }
            
            # 记录请求
            self.logger.rag.info('SRS get artifact detail request sent', 
                                   {'artifact_id': artifact_id})
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/artifacts/{artifact_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.rag.info('SRS artifact detail response received', 
                                               {'artifact_id': result.get('id')})
                        
                        return {
                            "code": 200,
                            "msg": "获取资料详情成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        
                        self.logger.rag.error(f'Get artifact detail failed', 
                                      {'status': response.status, 'error': error_text, 'artifact_id': artifact_id})
                        
                        return {
                            "code": 500,
                            "msg": f"获取资料详情失败: {error_text}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"获取SRS资料详情异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"获取SRS资料详情异常: {str(e)}",
                "data": None
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查接口
        
        Returns:
            健康状态
        """
        self.logger.info("开始SRS健康检查")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.rag.info('SRS health check response received', 
                                               {'status': result.get('status')})
                        
                        return {
                            "code": 200,
                            "msg": "健康检查成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        
                        self.logger.rag.error(f'Health check failed', 
                                      {'status': response.status, 'error': error_text})
                        
                        return {
                            "code": 500,
                            "msg": f"健康检查失败: {error_text}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"SRS健康检查异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"SRS健康检查异常: {str(e)}",
                "data": None
            }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        获取系统指标接口
        
        Returns:
            系统指标
        """
        self.logger.info("开始SRS获取系统指标")
        
        try:
            # 添加认证头
            headers = {
                "X-API-Key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/metrics",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.rag.info('SRS system metrics response received', 
                                               {'artifact_count': result.get('artifact_count')})
                        
                        return {
                            "code": 200,
                            "msg": "获取系统指标成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        
                        self.logger.rag.error(f'Get system metrics failed', 
                                      {'status': response.status, 'error': error_text})
                        
                        return {
                            "code": 500,
                            "msg": f"获取系统指标失败: {error_text}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"获取SRS系统指标异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"获取SRS系统指标异常: {str(e)}",
                "data": None
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息接口
        
        Returns:
            系统信息
        """
        self.logger.info("开始SRS获取系统信息")
        
        try:
            # 添加认证头
            headers = {
                "X-API-Key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/info",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        self.logger.rag.info('SRS system info response received', 
                                               {'app_name': result.get('app_name')})
                        
                        return {
                            "code": 200,
                            "msg": "获取系统信息成功",
                            "data": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        
                        self.logger.rag.error(f'Get system info failed', 
                                      {'status': response.status, 'error': error_text})
                        
                        return {
                            "code": 500,
                            "msg": f"获取系统信息失败: {error_text}",
                            "data": None
                        }
        
        except Exception as e:
            self.logger.sys.error(f"获取SRS系统信息异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"获取SRS系统信息异常: {str(e)}",
                "data": None
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接接口
        
        Returns:
            连接测试结果
        """
        self.logger.info("开始SRS连接测试")
        
        try:
            # 尝试健康检查
            health_result = await self.health_check()
            
            if health_result["code"] == 200:
                return {
                    "code": 200,
                    "msg": "SRS连接测试成功",
                    "data": {
                        "connected": True,
                        "base_url": self.base_url,
                        "health_status": health_result.get("data", {}).get("status")
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "code": 500,
                    "msg": "SRS连接测试失败",
                    "data": {
                        "connected": False,
                        "error": health_result.get("msg")
                    },
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            self.logger.sys.error(f"SRS连接测试异常: {str(e)}")
            return {
                "code": 500,
                "msg": f"SRS连接测试异常: {str(e)}",
                "data": {
                    "connected": False,
                    "error": str(e)
                }
            }