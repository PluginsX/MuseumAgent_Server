# API 参考文档

## SemanticRetrievalClient

主要的客户端类，提供与语义检索系统 API 交互的所有方法。

### 初始化

```python
client = SemanticRetrievalClient(
    base_url: str = "http://localhost:8080/api/v1",
    api_key: Optional[str] = None,
    timeout: int = 300
)
```

**参数：**
- `base_url` (str): API 基础 URL，默认为 "http://localhost:8080/api/v1"
- `api_key` (Optional[str]): API 密钥，可选
- `timeout` (int): 请求超时时间（秒），默认为 300 秒

---

## 资料管理方法

### get_artifacts

获取资料列表。

```python
def get_artifacts(
    page: int = 1,
    size: int = 10,
    keyword: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]
```

**参数：**
- `page` (int): 页码，默认为 1
- `size` (int): 每页数量，默认为 10
- `keyword` (Optional[str]): 搜索关键词，可选
- `category` (Optional[str]): 分类筛选，可选

**返回：**
- `Dict[str, Any]`: 包含资料列表的字典

### get_artifact

获取单个资料。

```python
def get_artifact(artifact_id: int) -> Artifact
```

**参数：**
- `artifact_id` (int): 资料 ID

**返回：**
- `Artifact`: Artifact 对象

### create_artifact

创建新资料。

```python
def create_artifact(artifact: ArtifactCreate) -> Artifact
```

**参数：**
- `artifact` (ArtifactCreate): ArtifactCreate 对象

**返回：**
- `Artifact`: 创建的 Artifact 对象

### update_artifact

更新资料。

```python
def update_artifact(artifact_id: int, artifact: ArtifactUpdate) -> Artifact
```

**参数：**
- `artifact_id` (int): 资料 ID
- `artifact` (ArtifactUpdate): ArtifactUpdate 对象

**返回：**
- `Artifact`: 更新后的 Artifact 对象

### delete_artifact

删除资料。

```python
def delete_artifact(artifact_id: int) -> None
```

**参数：**
- `artifact_id` (int): 资料 ID

---

## 智能检索方法

### search

执行向量检索。

```python
def search(
    query: str,
    top_k: int = 5,
    threshold: float = 0.5,
    category_filter: Optional[List[str]] = None
) -> SearchResult
```

**参数：**
- `query` (str): 搜索关键词
- `top_k` (int): 返回结果数量，默认为 5
- `threshold` (float): 相似度阈值，默认为 0.5
- `category_filter` (Optional[List[str]]): 分类筛选列表，可选

**返回：**
- `SearchResult`: SearchResult 对象

---

## 系统服务方法

### health_check

健康检查。

```python
def health_check() -> HealthStatus
```

**返回：**
- `HealthStatus`: HealthStatus 对象

### get_system_info

获取系统信息。

```python
def get_system_info() -> SystemInfo
```

**返回：**
- `SystemInfo`: SystemInfo 对象

### get_system_metrics

获取系统指标。

```python
def get_system_metrics() -> SystemMetrics
```

**返回：**
- `SystemMetrics`: SystemMetrics 对象

### rebuild_index

重建向量索引。

```python
def rebuild_index() -> Dict[str, str]
```

**返回：**
- `Dict[str, str]`: 包含操作结果的字典

---

## 配置管理方法

### get_config

获取系统配置。

```python
def get_config() -> Dict[str, Any]
```

**返回：**
- `Dict[str, Any]`: 系统配置字典

### update_config

更新系统配置。

```python
def update_config(config_data: Dict[str, Any]) -> ConfigUpdateResult
```

**参数：**
- `config_data` (Dict[str, Any]): 配置数据字典

**返回：**
- `ConfigUpdateResult`: ConfigUpdateResult 对象

### test_llm_config

测试 LLM 配置。

```python
def test_llm_config(
    service_type: str,
    base_url: str,
    api_key: str,
    model: str
) -> ConfigTestResult
```

**参数：**
- `service_type` (str): 服务类型
- `base_url` (str): API 基础 URL
- `api_key` (str): API 密钥
- `model` (str): 使用的模型

**返回：**
- `ConfigTestResult`: ConfigTestResult 对象

### test_embedding_config

测试 Embedding 配置。

```python
def test_embedding_config(
    service_type: str,
    base_url: str,
    api_key: str,
    model: str
) -> ConfigTestResult
```

**参数：**
- `service_type` (str): 服务类型
- `base_url` (str): API 基础 URL
- `api_key` (str): API 密钥
- `model` (str): 使用的模型

**返回：**
- `ConfigTestResult`: ConfigTestResult 对象

---

## 日志管理方法

### get_server_logs

获取服务器日志。

```python
def get_server_logs(lines: int = 100) -> List[str]
```

**参数：**
- `lines` (int): 日志行数，默认为 100

**返回：**
- `List[str]`: 日志行列表

### get_database_logs

获取数据库日志。

```python
def get_database_logs(lines: int = 100) -> List[str]
```

**参数：**
- `lines` (int): 日志行数，默认为 100

**返回：**
- `List[str]`: 日志行列表