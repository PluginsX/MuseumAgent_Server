"""语义检索系统 Python 客户端库

本客户端库提供了与语义检索系统 API 交互的便捷方法，支持资料管理、智能检索、系统配置等功能。

使用示例：
```python
from semantic_retrieval_client import SemanticRetrievalClient

# 创建客户端实例
client = SemanticRetrievalClient(
    base_url="http://localhost:8080/api/v1",
    api_key="your-api-key-here"
)

# 获取资料列表
artifacts = client.get_artifacts(page=1, size=10)

# 执行向量检索
search_results = client.search("青铜器的历史", top_k=5)
```

版本: 1.0.0
"""

from .client import SemanticRetrievalClient
from .exceptions import ClientError, APIError
from .models import (
    Artifact, ArtifactCreate, ArtifactUpdate, 
    SearchRequest, SearchResult, HealthStatus,
    SystemInfo, SystemMetrics, ConfigTestResult
)

__version__ = "1.0.0"
__all__ = [
    "SemanticRetrievalClient",
    "ClientError",
    "APIError",
    "Artifact",
    "ArtifactCreate",
    "ArtifactUpdate",
    "SearchRequest",
    "SearchResult",
    "HealthStatus",
    "SystemInfo",
    "SystemMetrics",
    "ConfigTestResult"
]
