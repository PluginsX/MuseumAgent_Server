# 开发者文档

## 项目结构

```
semantic_retrieval_client/
├── __init__.py          # 包初始化文件
├── client.py           # 主客户端类
├── models.py           # 数据模型定义
├── exceptions.py       # 异常类定义
└── (其他模块文件...)
```

## 主要组件

### Client (client.py)

`SemanticRetrievalClient` 是主要的客户端类，提供与语义检索系统 API 交互的方法。

关键功能：
- 资料管理：`get_artifacts()`, `create_artifact()`, `update_artifact()`, `delete_artifact()`
- 智能检索：`search()`
- 系统服务：`health_check()`, `get_system_info()`, `get_system_metrics()`, `rebuild_index()`
- 配置管理：`get_config()`, `update_config()`, `test_llm_config()`, `test_embedding_config()`
- 日志管理：`get_server_logs()`, `get_database_logs()`

### Models (models.py)

定义了与 API 交互所需的数据模型：

- `Artifact`: 资料模型
- `ArtifactCreate`: 创建资料请求模型
- `ArtifactUpdate`: 更新资料请求模型
- `SearchRequest`: 搜索请求模型
- `SearchResult`: 搜索结果模型
- `HealthStatus`: 健康状态模型
- `SystemInfo`: 系统信息模型
- `SystemMetrics`: 系统指标模型
- `ConfigTestResult`: 配置测试结果模型

### Exceptions (exceptions.py)

定义了客户端异常类：

- `ClientError`: 客户端错误基类
- `APIError`: API 错误
- `ConnectionError`: 连接错误
- `TimeoutError`: 超时错误

## 使用示例

### 基本用法

```python
from semantic_retrieval_client import SemanticRetrievalClient

# 创建客户端实例
client = SemanticRetrievalClient(
    base_url="http://localhost:8080/api/v1",
    api_key="your-api-key-here"
)

# 执行操作
artifacts = client.get_artifacts(page=1, size=10)
```

### 异常处理

```python
from semantic_retrieval_client.exceptions import APIError, ConnectionError, TimeoutError

try:
    result = client.search("查询内容", top_k=5)
except APIError as e:
    print(f"API 错误: {e.status_code} - {e.message}")
except ConnectionError as e:
    print(f"连接错误: {e}")
except TimeoutError as e:
    print(f"超时错误: {e}")
```

## 贡献指南

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 构建和发布

### 构建包

```bash
# 安装构建工具
pip install build

# 构建包
python -m build
```

### 上传到 PyPI

```bash
# 安装上传工具
pip install twine

# 上传包
python -m twine upload dist/*
```

## 测试

运行测试套件：

```bash
# 安装测试依赖
pip install -e ".[test]"

# 运行测试
pytest
```