"""语义检索系统客户端核心实现"""

import requests
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from .exceptions import APIError, ConnectionError, TimeoutError
from .models import (
    Artifact, ArtifactCreate, ArtifactUpdate, 
    SearchRequest, SearchResult, HealthStatus,
    SystemInfo, SystemMetrics, ConfigTestResult, ConfigUpdateResult
)


class SemanticRetrievalClient:
    """语义检索系统客户端
    
    提供与语义检索系统 API 交互的方法，支持资料管理、智能检索、系统配置等功能。
    """
    
    def __init__(self, base_url: str = "http://localhost:8080/api/v1", api_key: Optional[str] = None, timeout: int = 300):
        """初始化客户端
        
        Args:
            base_url: API 基础 URL，默认为 "http://localhost:8080/api/v1"
            api_key: API 密钥，可选
            timeout: 请求超时时间（秒），默认为 300 秒（5分钟）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        # 设置默认请求头
        self.headers = {
            "Content-Type": "application/json"
        }
        
        # 如果提供了 API 密钥，添加到请求头
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def _send_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """发送 HTTP 请求
        
        Args:
            method: HTTP 方法（GET, POST, PUT, DELETE）
            endpoint: API 端点
            data: 请求体数据
            params: 查询参数
            
        Returns:
            响应数据（字典格式）
            
        Raises:
            APIError: API 返回错误
            ConnectionError: 连接失败
            TimeoutError: 请求超时
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(
                    url, 
                    headers=self.headers, 
                    params=params, 
                    timeout=self.timeout
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    url, 
                    headers=self.headers, 
                    json=data, 
                    params=params, 
                    timeout=self.timeout
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    url, 
                    headers=self.headers, 
                    json=data, 
                    timeout=self.timeout
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    url, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")
            
            # 检查响应状态码
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", f"API 错误: {response.status_code}")
                except json.JSONDecodeError:
                    error_message = f"API 错误: {response.status_code} - {response.text}"
                raise APIError(response.status_code, error_message)
            
            # 对于 204 No Content 响应，返回空字典
            if response.status_code == 204:
                return {}
            
            # 解析响应数据
            return response.json()
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求超时，超过 {self.timeout} 秒")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"无法连接到 API 服务器: {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise APIError(500, f"请求失败: {str(e)}")
    
    # 资料管理方法
    def get_artifacts(self, page: int = 1, size: int = 10, keyword: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """获取资料列表
        
        Args:
            page: 页码，默认为 1
            size: 每页数量，默认为 10
            keyword: 搜索关键词，可选
            category: 分类筛选，可选
            
        Returns:
            包含资料列表的字典
        """
        params = {
            "page": page,
            "size": size
        }
        
        if keyword:
            params["keyword"] = keyword
        if category:
            params["category"] = category
        
        return self._send_request("GET", "artifacts", params=params)
    
    def get_artifact(self, artifact_id: int) -> Artifact:
        """获取单个资料
        
        Args:
            artifact_id: 资料 ID
            
        Returns:
            Artifact 对象
        """
        data = self._send_request("GET", f"artifacts/{artifact_id}")
        return Artifact(**data)
    
    def create_artifact(self, artifact: ArtifactCreate) -> Artifact:
        """创建新资料
        
        Args:
            artifact: ArtifactCreate 对象
            
        Returns:
            创建的 Artifact 对象
        """
        data = artifact.__dict__
        response_data = self._send_request("POST", "artifacts", data=data)
        return Artifact(**response_data)
    
    def update_artifact(self, artifact_id: int, artifact: ArtifactUpdate) -> Artifact:
        """更新资料
        
        Args:
            artifact_id: 资料 ID
            artifact: ArtifactUpdate 对象
            
        Returns:
            更新后的 Artifact 对象
        """
        data = {k: v for k, v in artifact.__dict__.items() if v is not None}
        response_data = self._send_request("PUT", f"artifacts/{artifact_id}", data=data)
        return Artifact(**response_data)
    
    def delete_artifact(self, artifact_id: int) -> None:
        """删除资料
        
        Args:
            artifact_id: 资料 ID
        """
        self._send_request("DELETE", f"artifacts/{artifact_id}")
    
    # 智能检索方法
    def search(self, query: str, top_k: int = 5, threshold: float = 0.5, category_filter: Optional[List[str]] = None) -> SearchResult:
        """执行向量检索
        
        Args:
            query: 搜索关键词
            top_k: 返回结果数量，默认为 5
            threshold: 相似度阈值，默认为 0.5
            category_filter: 分类筛选列表，可选
            
        Returns:
            SearchResult 对象
        """
        search_request = SearchRequest(
            query=query,
            top_k=top_k,
            threshold=threshold,
            category_filter=category_filter
        )
        
        data = search_request.__dict__
        response_data = self._send_request("POST", "search/retrieve", data=data)
        
        # 处理服务器返回的响应格式
        # 服务器返回的格式是 {"data": {"query": "...", "artifacts": [...], ...}}
        # 我们需要从 data 字段中提取 SearchResult 所需的字段
        if "data" in response_data:
            search_data = response_data["data"]
        else:
            search_data = response_data
        
        return SearchResult(**search_data)
    
    # 系统服务方法
    def health_check(self) -> HealthStatus:
        """健康检查
        
        Returns:
            HealthStatus 对象
        """
        # 健康检查接口在根路径，不是 /api/v1 下
        health_url = self.base_url.replace("/api/v1", "") + "/health"
        
        try:
            response = self.session.get(health_url, timeout=self.timeout)
            if response.status_code != 200:
                raise APIError(response.status_code, f"健康检查失败: {response.status_code}")
            
            data = response.json()
            return HealthStatus(**data)
        except requests.exceptions.RequestException as e:
            raise APIError(500, f"健康检查失败: {str(e)}")
    
    def get_system_info(self) -> SystemInfo:
        """获取系统信息
        
        Returns:
            SystemInfo 对象
        """
        data = self._send_request("GET", "info")
        return SystemInfo(**data)
    
    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标
        
        Returns:
            SystemMetrics 对象
        """
        data = self._send_request("GET", "metrics")
        return SystemMetrics(**data)
    
    def rebuild_index(self) -> Dict[str, str]:
        """重建向量索引
        
        Returns:
            包含操作结果的字典
        """
        return self._send_request("POST", "reindex")
    
    # 配置管理方法
    def get_config(self) -> Dict[str, Any]:
        """获取系统配置
        
        Returns:
            系统配置字典
        """
        data = self._send_request("GET", "config")
        return data.get("data", data)
    
    def update_config(self, config_data: Dict[str, Any]) -> ConfigUpdateResult:
        """更新系统配置
        
        Args:
            config_data: 配置数据字典
            
        Returns:
            ConfigUpdateResult 对象
        """
        data = self._send_request("POST", "config", data=config_data)
        return ConfigUpdateResult(**data)
    
    def test_llm_config(self, service_type: str, base_url: str, api_key: str, model: str) -> ConfigTestResult:
        """测试 LLM 配置
        
        Args:
            service_type: 服务类型
            base_url: API 基础 URL
            api_key: API 密钥
            model: 使用的模型
            
        Returns:
            ConfigTestResult 对象
        """
        data = {
            "service_type": service_type,
            "base_url": base_url,
            "api_key": api_key,
            "model": model
        }
        
        response_data = self._send_request("POST", "config/test-llm", data=data)
        return ConfigTestResult(**response_data.get("data", response_data))
    
    def test_embedding_config(self, service_type: str, base_url: str, api_key: str, model: str) -> ConfigTestResult:
        """测试 Embedding 配置
        
        Args:
            service_type: 服务类型
            base_url: API 基础 URL
            api_key: API 密钥
            model: 使用的模型
            
        Returns:
            ConfigTestResult 对象
        """
        data = {
            "service_type": service_type,
            "base_url": base_url,
            "api_key": api_key,
            "model": model
        }
        
        response_data = self._send_request("POST", "config/test-embedding", data=data)
        return ConfigTestResult(**response_data.get("data", response_data))
    
    # 日志管理方法
    def get_server_logs(self, lines: int = 100) -> List[str]:
        """获取服务器日志
        
        Args:
            lines: 日志行数，默认为 100
            
        Returns:
            日志行列表
        """
        data = self._send_request("GET", "logs/server", params={"lines": lines})
        return data.get("logs", [])
    
    def get_database_logs(self, lines: int = 100) -> List[str]:
        """获取数据库日志
        
        Args:
            lines: 日志行数，默认为 100
            
        Returns:
            日志行列表
        """
        data = self._send_request("GET", "logs/database", params={"lines": lines})
        return data.get("logs", [])
