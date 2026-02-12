# 基于语义的信息检索系统 Python 客户端库

本客户端库提供了与语义检索系统 API 交互的便捷方法，支持资料管理、智能检索、系统配置等功能。

## 功能特性

- **资料管理**：获取、创建、更新、删除资料
- **智能检索**：执行向量检索，获取相关资料
- **系统服务**：健康检查、系统信息、系统指标、重建向量索引
- **配置管理**：获取、更新系统配置，测试 LLM 和 Embedding 配置
- **日志管理**：获取服务器和数据库日志

## 安装方法

### 方法一：直接安装

```bash
# 进入 Client 目录
cd e:\Project\Python\SemanticRetrievalSystem\Client

# 安装客户端库
pip install -e .
```

### 方法二：作为依赖添加

在项目的 `requirements.txt` 文件中添加：

```
semantic-retrieval-client @ file:///e:/Project/Python/SemanticRetrievalSystem/Client
```

然后运行：

```bash
pip install -r requirements.txt
```

## 基本使用

### 1. 初始化客户端

```python
from semantic_retrieval_client import SemanticRetrievalClient

# 创建客户端实例
client = SemanticRetrievalClient(
    base_url="http://localhost:8080/api/v1",  # API 基础 URL
    api_key="your-api-key-here",  # 可选，API 密钥
    timeout=300  # 可选，请求超时时间（秒），默认为 300 秒
)
```

### 2. 资料管理

#### 获取资料列表

```python
# 获取资料列表
artifacts = client.get_artifacts(
    page=1,      # 页码
    size=10,     # 每页数量
    keyword="青铜器",  # 搜索关键词（可选）
    category="文物知识"  # 分类筛选（可选）
)

print(f"总资料数: {artifacts['total_count']}")
for artifact in artifacts['artifacts']:
    print(f"- {artifact['title']} (ID: {artifact['id']})")
```

#### 创建资料

```python
from semantic_retrieval_client.models import ArtifactCreate

# 创建新资料
new_artifact = ArtifactCreate(
    title="青铜器介绍",
    content="青铜器是中国古代文明的重要组成部分...",
    category="文物知识",
    tags=["青铜器", "文物"]
)

created_artifact = client.create_artifact(new_artifact)
print(f"创建成功！资料ID: {created_artifact.id}")
```

#### 更新资料

```python
from semantic_retrieval_client.models import ArtifactUpdate

# 更新资料
update_data = ArtifactUpdate(
    title="更新后的青铜器介绍",
    content="更新后的内容...",
    category="历史文化"
)

updated_artifact = client.update_artifact(artifact_id, update_data)
print(f"更新成功！")
```

#### 删除资料

```python
# 删除资料
client.delete_artifact(artifact_id)
print(f"删除成功！")
```

### 3. 智能检索

```python
# 执行向量检索
search_result = client.search(
    query="青铜器的历史",  # 搜索关键词
    top_k=5,            # 返回结果数量
    threshold=0.7,      # 相似度阈值
    category_filter=["文物知识", "历史文化"]  # 分类筛选（可选）
)

print(f"查询: {search_result.query}")
print(f"找到 {search_result.total_count} 条相关资料")
print(f"响应时间: {search_result.response_time:.2f} 秒")

for i, artifact in enumerate(search_result.artifacts, 1):
    similarity = artifact.get('similarity', 0)
    print(f"{i}. {artifact['title']} (相似度: {similarity:.2f})")
```

### 4. 系统服务

#### 健康检查

```python
# 健康检查
health_status = client.health_check()
print(f"状态: {health_status.status}")
print(f"时间戳: {health_status.timestamp}")
print("服务状态:")
for service, status in health_status.services.items():
    print(f"  - {service}: {status}")
```

#### 系统信息

```python
# 获取系统信息
system_info = client.get_system_info()
print(f"应用名称: {system_info.app_name}")
print(f"版本: {system_info.version}")
print(f"状态: {system_info.status}")
print(f"环境: {system_info.environment}")
```

#### 系统指标

```python
# 获取系统指标
system_metrics = client.get_system_metrics()
print(f"资料数量: {system_metrics.artifact_count}")
print(f"切片数量: {system_metrics.chunk_count}")
print(f"搜索次数: {system_metrics.search_count}")
print(f"运行时间: {system_metrics.uptime} 秒")
```

#### 重建向量索引

```python
# 重建向量索引
result = client.rebuild_index()
print(f"操作结果: {result['message']}")
```

### 5. 配置管理

#### 获取系统配置

```python
# 获取系统配置
config = client.get_config()
print("配置概览:")
if 'server' in config:
    print(f"  服务器: {config['server']['host']}:{config['server']['port']}")
if 'llm' in config:
    print(f"  LLM模型: {config['llm']['model']}")
if 'embedding' in config:
    print(f"  Embedding模型: {config['embedding']['model']}")
    print(f"  向量维度: {config['embedding']['dimensions']}")
```

#### 测试 LLM 配置

```python
# 测试 LLM 配置
test_result = client.test_llm_config(
    service_type="openai-compatible",
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2:7b"
)

print(f"连接状态: {test_result.connected}")
print(f"模型: {test_result.model}")
print(f"服务类型: {test_result.service_type}")
print(f"响应预览: {test_result.response_preview}")
```

#### 测试 Embedding 配置

```python
# 测试 Embedding 配置
test_result = client.test_embedding_config(
    service_type="openai-compatible",
    base_url="http://localhost:5000/v1",
    api_key="sk-ccahwXzZsrbLaXIidBQsnv8FVIbk8Y1BjgUdnFiHjFiuGSW3",
    model="Qwen3-Embedding-4B"
)

print(f"连接状态: {test_result.connected}")
print(f"模型: {test_result.model}")
print(f"服务类型: {test_result.service_type}")
print(f"向量维度: {test_result.dimensions}")
```

### 6. 日志管理

#### 获取服务器日志

```python
# 获取服务器日志
logs = client.get_server_logs(lines=50)  # 获取最近 50 行日志
print(f"服务器日志 (最近 {len(logs)} 行):")
for log in logs:
    print(log)
```

#### 获取数据库日志

```python
# 获取数据库日志
logs = client.get_database_logs(lines=50)  # 获取最近 50 行日志
print(f"数据库日志 (最近 {len(logs)} 行):")
for log in logs:
    print(log)
```

## 异常处理

客户端库定义了以下异常类，用于处理不同类型的错误：

- `APIError`：API 返回错误
- `ConnectionError`：连接失败
- `TimeoutError`：请求超时

使用示例：

```python
from semantic_retrieval_client.exceptions import APIError, ConnectionError, TimeoutError

try:
    # 执行 API 调用
    artifacts = client.get_artifacts()
except APIError as e:
    print(f"API 错误: {e.status_code} - {e.message}")
except ConnectionError as e:
    print(f"连接错误: {e}")
except TimeoutError as e:
    print(f"超时错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 高级配置

### 自定义会话

客户端使用 `requests.Session()` 来管理 HTTP 连接。如果需要自定义会话配置，可以通过继承 `SemanticRetrievalClient` 类并覆盖 `__init__` 方法来实现。

### 代理设置

如果需要通过代理访问 API，可以在创建客户端前设置环境变量：

```python
import os

# 设置 HTTP 代理
os.environ['HTTP_PROXY'] = 'http://proxy.example.com:8080'
os.environ['HTTPS_PROXY'] = 'http://proxy.example.com:8080'

# 然后创建客户端
client = SemanticRetrievalClient(base_url="http://localhost:8080/api/v1")
```

## 运行示例

客户端库包含一个示例脚本，展示了所有功能的使用方法：

```bash
# 运行示例脚本
python example_usage.py
```

## API 文档

完整的 API 文档请参考：
- [语义检索系统 API 服务使用教程](../Documents/api.md)

## 版本信息

- **当前版本**：1.0.0
- **Python 版本要求**：3.9+
- **依赖包**：
  - requests >= 2.28.0

## 许可证

MIT 许可证

## 联系方式

如有问题或建议，请联系：
- 系统管理员
- 或查阅服务器日志
