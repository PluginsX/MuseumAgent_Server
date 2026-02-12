# 语义检索系统API服务使用教程

本文档详细介绍了如何使用语义检索系统提供的外部API服务，包括调用流程、方法、数据格式和注意事项。

## 目录

1. [概述](#概述)
2. [服务启动](#服务启动)
3. [API端点](#api端点)
4. [认证方式](#认证方式)
5. [调用流程](#调用流程)
6. [数据格式](#数据格式)
7. [错误处理](#错误处理)
8. [注意事项](#注意事项)

## 概述

语义检索系统是一个智能知识检索与管理系统，提供RESTful API接口，支持资料管理、智能检索、系统配置等功能。系统基于FastAPI框架开发，默认监听8080端口。

## 服务启动

### 环境要求
- Python 3.9+
- 保证服务器端口（默认8080）开放

### 启动命令
```bash
cd e:/Project/Python/SemanticRetrievalSystem
python main.py
```

### 服务地址
- API基础URL: `http://localhost:8080/api/v1`
- API文档: `http://localhost:8080/docs`
- 健康检查: `http://localhost:8080/health`
- API根路径: `http://localhost:8080/api`

## API端点

### 1. 资料管理

#### 获取资料列表
- **方法**: `GET`
- **URL**: `/api/v1/artifacts`
- **参数**:
  - `page` (可选): 页码，默认为1
  - `size` (可选): 每页数量，默认为10
  - `keyword` (可选): 搜索关键词
  - `category` (可选): 分类筛选
- **响应**:
```json
{
  "artifacts": [
    {
      "id": 1,
      "title": "青铜器介绍",
      "content": "青铜器是中国古代文明的重要组成部分...",
      "category": "文物知识",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z",
      "is_active": true
    }
  ],
  "total_count": 1,
  "page": 1,
  "size": 10
}
```

#### 创建资料
- **方法**: `POST`
- **URL**: `/api/v1/artifacts`
- **请求体**:
```json
{
  "title": "新资料标题",
  "content": "资料内容",
  "category": "分类",
  "tags": ["标签1", "标签2"]
}
```
- **响应**:
```json
{
  "id": 1,
  "title": "新资料标题",
  "content": "资料内容",
  "category": "分类",
  "tags": ["标签1", "标签2"],
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "is_active": true
}
```

#### 更新资料
- **方法**: `PUT`
- **URL**: `/api/v1/artifacts/{id}`
- **请求体**:
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容",
  "category": "更新后的分类"
}
```

#### 删除资料
- **方法**: `DELETE`
- **URL**: `/api/v1/artifacts/{id}`
- **响应**: 204 No Content

#### 获取单个资料
- **方法**: `GET`
- **URL**: `/api/v1/artifacts/{id}`
- **响应**:
```json
{
  "id": 1,
  "title": "青铜器介绍",
  "content": "青铜器是中国古代文明的重要组成部分...",
  "category": "文物知识",
  "tags": ["青铜器", "文物"],
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "is_active": true
}
```

### 2. 智能检索

#### 向量检索
- **方法**: `POST`
- **URL**: `/api/v1/search/retrieve`
- **请求体**:
```json
{
  "query": "搜索关键词",
  "top_k": 5,
  "threshold": 0.5,
  "category_filter": ["分类1", "分类2"]
}
```
- **响应**:
```json
{
  "query": "搜索关键词",
  "artifacts": [
    {
      "id": 1,
      "title": "青铜器介绍",
      "content": "青铜器是中国古代文明的重要组成部分...",
      "category": "文物知识",
      "similarity": 0.85,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z",
      "is_active": true
    }
  ],
  "total_count": 1,
  "response_time": 0.123
}
```

### 3. 系统服务

#### 健康检查
- **方法**: `GET`
- **URL**: `/health`
- **响应**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "services": {
    "database": "connected",
    "vector_store": "connected",
    "llm_service": "configured",
    "embedding_service": "configured"
  }
}
```

#### 系统指标
- **方法**: `GET`
- **URL**: `/api/v1/metrics`
- **响应**:
```json
{
  "artifact_count": 100,
  "chunk_count": 500,
  "search_count": 1000,
  "uptime": 3600
}
```

#### 系统信息
- **方法**: `GET`
- **URL**: `/api/v1/info`
- **响应**:
```json
{
  "app_name": "语义检索系统",
  "version": "1.0.0",
  "status": "running",
  "environment": "development"
}
```

#### 重建向量索引
- **方法**: `POST`
- **URL**: `/api/v1/reindex`
- **响应**:
```json
{
  "message": "向量索引重建成功"
}
```

### 4. 配置管理

#### 获取系统配置
- **方法**: `GET`
- **URL**: `/api/v1/config`
- **响应**:
```json
{
  "data": {
    "server": {
      "host": "127.0.0.1",
      "port": 8080
    },
    "cors": {
      "origins": ["http://localhost:3000", "http://127.0.0.1:3000"]
    },
    "llm": {
      "service_type": "openai-compatible",
      "base_url": "http://localhost:11434/v1",
      "api_key": "ollama",
      "model": "qwen2:7b",
      "max_tokens": 4096
    },
    "embedding": {
      "service_type": "local",
      "base_url": "http://localhost:5000/v1",
      "api_key": "sk-ccahwXzZsrbLaXIidBQsnv8FVIbk8Y1BjgUdnFiHjFiuGSW3",
      "model": "Qwen3-Embedding-4B",
      "dimensions": 1024
    }
  }
}
```

#### 更新系统配置
- **方法**: `POST`
- **URL**: `/api/v1/config`
- **请求体**:
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "cors": {
    "origins": ["http://localhost:3000", "http://127.0.0.1:3000"]
  }
}
```
- **响应**:
```json
{
  "message": "配置更新成功",
  "data": {
    "server": {
      "host": "0.0.0.0",
      "port": 8080
    },
    "cors": {
      "origins": ["http://localhost:3000", "http://127.0.0.1:3000"]
    }
  }
}
```

#### 测试LLM配置
- **方法**: `POST`
- **URL**: `/api/v1/config/test-llm`
- **请求体**:
```json
{
  "service_type": "openai-compatible",
  "base_url": "http://localhost:11434/v1",
  "api_key": "ollama",
  "model": "qwen2:7b"
}
```
- **响应**:
```json
{
  "message": "LLM配置测试成功",
  "data": {
    "connected": true,
    "model": "qwen2:7b",
    "service_type": "openai-compatible",
    "response_preview": "测试成功"
  }
}
```

#### 测试Embedding配置
- **方法**: `POST`
- **URL**: `/api/v1/config/test-embedding`
- **请求体**:
```json
{
  "service_type": "openai-compatible",
  "base_url": "http://localhost:5000/v1",
  "api_key": "sk-ccahwXzZsrbLaXIidBQsnv8FVIbk8Y1BjgUdnFiHjFiuGSW3",
  "model": "Qwen3-Embedding-4B"
}
```
- **响应**:
```json
{
  "message": "Embedding配置测试成功",
  "data": {
    "connected": true,
    "model": "Qwen3-Embedding-4B",
    "service_type": "openai-compatible",
    "dimensions": 1024
  }
}
```

### 5. 日志管理

#### 获取服务器日志
- **方法**: `GET`
- **URL**: `/api/v1/logs/server`
- **参数**:
  - `lines` (可选): 日志行数，默认为100
- **响应**:
```json
{
  "logs": ["日志行1", "日志行2", ...]
}
```

#### 获取数据库日志
- **方法**: `GET`
- **URL**: `/api/v1/logs/database`
- **参数**:
  - `lines` (可选): 日志行数，默认为100
- **响应**:
```json
{
  "logs": ["日志行1", "日志行2", ...]
}
```

## 认证方式

当前版本的API服务支持以下认证方式：

### API密钥认证
- 在HTTP请求头中添加 `X-API-Key` 字段
- 值为预设的API密钥

示例：
```http
GET /api/v1/artifacts HTTP/1.1
Host: localhost:8080
X-API-Key: your-api-key-here
```

## 调用流程

1. **启动服务**: 确保语义检索系统正常运行
2. **获取API地址**: 记录服务器IP和端口
3. **准备请求**: 根据需要的API端点构造HTTP请求
4. **添加认证**: 如需要，添加API密钥到请求头
5. **发送请求**: 发送HTTP请求到对应端点
6. **处理响应**: 解析返回的JSON数据
7. **错误处理**: 检查HTTP状态码和错误信息

### 示例：获取资料列表
```python
import requests

# 设置基础URL和API密钥
base_url = "http://localhost:8080/api/v1"
headers = {
    "X-API-Key": "your-api-key-here",
    "Content-Type": "application/json"
}

# 发送GET请求获取资料列表
response = requests.get(
    f"{base_url}/artifacts",
    headers=headers,
    params={"page": 1, "size": 10}
)

# 检查响应状态
if response.status_code == 200:
    data = response.json()
    print(f"获取到 {data['total_count']} 条资料")
    for artifact in data['artifacts']:
        print(f"- {artifact['title']}")
else:
    print(f"请求失败: {response.status_code}")
```

### 示例：创建新资料
```python
import requests

base_url = "http://localhost:8080/api/v1"
headers = {
    "X-API-Key": "your-api-key-here",
    "Content-Type": "application/json"
}

# 准备新资料数据
new_artifact = {
    "title": "青铜器发展史",
    "content": "青铜器在中国历史上有着悠久的发展历程...",
    "category": "文物知识",
    "tags": ["青铜器", "历史", "文物"]
}

# 发送POST请求创建资料
response = requests.post(
    f"{base_url}/artifacts",
    headers=headers,
    json=new_artifact
)

# 检查响应
if response.status_code == 200:
    created_artifact = response.json()
    print(f"创建成功，ID: {created_artifact['id']}")
else:
    print(f"创建失败: {response.status_code}, {response.text}")
```

### 示例：执行向量检索
```python
import requests

base_url = "http://localhost:8080/api/v1"
headers = {
    "X-API-Key": "your-api-key-here",
    "Content-Type": "application/json"
}

# 准备检索请求
search_request = {
    "query": "青铜器的历史",
    "top_k": 5,
    "threshold": 0.7
}

# 发送POST请求执行检索
response = requests.post(
    f"{base_url}/search/retrieve",
    headers=headers,
    json=search_request
)

# 检查响应
if response.status_code == 200:
    search_result = response.json()
    print(f"检索完成，找到 {len(search_result['artifacts'])} 条相关资料")
    for i, artifact in enumerate(search_result['artifacts']):
        print(f"{i+1}. {artifact['title']} (相似度: {artifact['similarity']:.2f})")
else:
    print(f"检索失败: {response.status_code}, {response.text}")
```

## 数据格式

### 通用请求头
- `Content-Type`: `application/json`
- `X-API-Key`: API密钥（如果需要）

### 日期时间格式
- 所有日期时间使用ISO 8601格式: `YYYY-MM-DDTHH:MM:SSZ`

### 数字格式
- 整数: 直接使用数字
- 浮点数: 最多保留6位小数

### 响应格式
成功响应通常遵循以下格式：
```json
{
  "data": {...},
  "message": "操作成功",
  "code": 200
}
```

错误响应通常遵循以下格式：
```json
{
  "detail": "错误详情",
  "code": 400
}
```

## 错误处理

### HTTP状态码
- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `204 No Content`: 请求成功但无返回内容
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 认证失败
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

### 错误响应示例
```json
{
  "detail": "资料未找到",
  "code": 404
}
```

### 客户端错误处理建议
1. 检查HTTP状态码
2. 解析错误响应体
3. 根据错误类型采取相应措施
4. 实现重试机制（对于临时性错误）
5. 记录错误日志

## 注意事项

### 安全注意事项
1. **API密钥保护**: 严禁在客户端代码中硬编码API密钥
2. **HTTPS传输**: 在生产环境中使用HTTPS加密传输
3. **访问频率限制**: 避免过于频繁的API调用
4. **敏感数据**: 不要在API请求中传输敏感个人信息

### 性能注意事项
1. **批量操作**: 尽可能使用批量接口减少请求数量
2. **合理分页**: 使用适当的分页参数避免返回过多数据
3. **缓存策略**: 对于不经常变化的数据，实现适当的缓存策略
4. **连接复用**: 复用HTTP连接以提高性能

### 使用限制
1. **并发限制**: 服务器可能对并发连接数有限制
2. **数据大小**: 单次请求的数据大小不应超过限制
3. **频率限制**: 遵循服务器的API调用频率限制
4. **数据保留**: 了解服务器数据保留政策

### 最佳实践
1. **错误重试**: 实现指数退避算法进行错误重试
2. **超时设置**: 为API调用设置合理的超时时间（建议5分钟）
3. **日志记录**: 记录API调用日志以便调试
4. **版本兼容**: 关注API版本变化，确保兼容性

### 故障排除
1. **检查服务状态**: 确认服务器正在运行
2. **验证API密钥**: 确认API密钥正确有效
3. **查看API文档**: 检查请求格式是否符合文档要求
4. **查看服务器日志**: 检查服务器端是否有错误日志
5. **网络连通性**: 确认网络连接正常
6. **API端点检查**: 确认使用的API端点存在且路径正确

## 联系方式

如遇到API使用问题，请联系系统管理员或查阅服务器日志。