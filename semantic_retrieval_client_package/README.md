# 语义检索系统 Python 客户端库

[![PyPI version](https://badge.fury.io/py/semantic-retrieval-client.svg)](https://badge.fury.io/py/semantic-retrieval-client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/semantic-retrieval-client.svg)](https://pypi.org/project/semantic-retrieval-client/)

本客户端库提供了与语义检索系统 API 交互的便捷方法，支持资料管理、智能检索、系统配置等功能。

## 🚀 功能特性

- **资料管理**：获取、创建、更新、删除资料
- **智能检索**：执行向量检索，获取相关资料
- **系统服务**：健康检查、系统信息、系统指标、重建向量索引
- **配置管理**：获取、更新系统配置，测试 LLM 和 Embedding 配置
- **日志管理**：获取服务器和数据库日志
- **完整的错误处理机制**

## 📦 安装

### PyPI 安装（推荐）

```bash
pip install semantic-retrieval-client
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/PluginsX/SemanticRetrievalSystem.git
cd SemanticRetrievalSystem/Client

# 安装
pip install -e .
```

## 💡 快速开始

```python
from semantic_retrieval_client import SemanticRetrievalClient

# 创建客户端实例
client = SemanticRetrievalClient(
    base_url="http://localhost:8080/api/v1",
    api_key="your-api-key-here"  # 可选
)

# 获取资料列表
artifacts = client.get_artifacts(page=1, size=10)

# 执行向量检索
search_results = client.search("青铜器的历史", top_k=5)

# 健康检查
health_status = client.health_check()
```

## 🔧 配置选项

- `base_url`: API 基础 URL，默认为 "http://localhost:8080/api/v1"
- `api_key`: API 密钥，可选
- `timeout`: 请求超时时间（秒），默认为 300 秒

## 📚 文档

- [API 参考文档](docs/API_REFERENCE.md)
- [开发者文档](docs/DEVELOPER.md)
- [安装和发布指南](INSTALLATION.md)

## 🧪 测试

```bash
# 运行测试
python test_package.py
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目！

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

该项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 📞 支持

如有问题或建议，请：

- 提交 GitHub Issue
- 查阅 API 文档
- 联系系统管理员

---

**作者**: Semantic Retrieval System Team  
**邮箱**: contact@semantic-retrieval-system.com  
**版本**: 1.0.0  
**Python 版本要求**: 3.9+