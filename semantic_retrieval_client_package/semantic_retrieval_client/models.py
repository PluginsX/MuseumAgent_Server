"""客户端数据模型定义"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Artifact:
    """资料模型"""
    id: int
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class ArtifactCreate:
    """创建资料请求模型"""
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class ArtifactUpdate:
    """更新资料请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


@dataclass
class SearchRequest:
    """搜索请求模型"""
    query: str
    top_k: int = 5
    threshold: float = 0.5
    category_filter: Optional[List[str]] = None


@dataclass
class SearchResult:
    """搜索结果模型"""
    query: str
    artifacts: List[Dict[str, Any]]
    total_count: int
    response_time: float


@dataclass
class HealthStatus:
    """健康状态模型"""
    status: str
    timestamp: str
    services: Dict[str, str]


@dataclass
class SystemInfo:
    """系统信息模型"""
    app_name: str
    version: str
    status: str
    environment: str


@dataclass
class SystemMetrics:
    """系统指标模型"""
    artifact_count: int
    chunk_count: int
    search_count: int
    uptime: int


@dataclass
class ConfigTestResult:
    """配置测试结果模型"""
    connected: bool
    model: str
    service_type: str
    response_preview: Optional[str] = None
    dimensions: Optional[int] = None


@dataclass
class ConfigUpdateResult:
    """配置更新结果模型"""
    message: str
    data: Dict[str, Any]
