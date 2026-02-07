# 语义检索客户端库 - 安装和发布指南

## 包结构概述

```
semantic_retrieval_client_package/
├── semantic_retrieval_client/     # 主包目录
│   ├── __init__.py               # 包初始化
│   ├── client.py                 # 主客户端类
│   ├── models.py                 # 数据模型
│   └── exceptions.py             # 异常定义
├── docs/                         # 文档目录
│   ├── API_REFERENCE.md          # API参考文档
│   └── DEVELOPER.md              # 开发者文档
├── tests/                        # 测试目录 (可选)
├── README.md                     # 项目说明
├── CHANGELOG.md                  # 变更日志
├── LICENSE                       # 许可证
├── requirements.txt              # 依赖列表
├── setup.py                      # setuptools配置
├── pyproject.toml                # 构建配置
├── MANIFEST.in                   # 包含文件清单
├── example_usage.py              # 使用示例
└── test_package.py               # 包测试脚本
```

## 构建和安装

### 本地开发模式安装

```bash
# 克隆或下载源代码后
cd semantic_retrieval_client_package

# 安装为开发模式（可编辑安装）
pip install -e .
```

### 从源码构建分发包

```bash
# 安装构建工具
pip install build

# 构建分发包
python -m build

# 构建完成后，会在 dist/ 目录下生成
# - semantic_retrieval_client-1.0.0.tar.gz (源码分发)
# - semantic_retrieval_client-1.0.0-py3-none-any.whl (wheel分发)
```

### 从Wheel文件安装

```bash
# 安装预构建的wheel包
pip install dist/semantic_retrieval_client-1.0.0-py3-none-any.whl
```

## 发布到PyPI

### 准备工作

1. 确保已安装twine:
```bash
pip install twine
```

2. 确保已登录PyPI账户（或TestPyPI用于测试）

### 发布到TestPyPI（推荐先测试）

```bash
# 上传到TestPyPI进行测试
python -m twine upload --repository testpypi dist/*
```

### 发布到PyPI

```bash
# 上传到正式PyPI
python -m twine upload dist/*
```

## 验证安装

```bash
# 测试导入
python -c "from semantic_retrieval_client import SemanticRetrievalClient; print('安装成功！')"

# 运行测试
python test_package.py
```

## 项目维护

### 版本更新

1. 修改 `__init__.py` 中的 `__version__` 变量
2. 更新 `setup.py` 和 `pyproject.toml` 中的版本号
3. 更新 `CHANGELOG.md` 中的版本记录
4. 重新构建包

### 添加依赖

在 `requirements.txt` 和 `pyproject.toml` 中同时更新依赖列表。

## 开发贡献

### 环境设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e ".[dev,test]"
```

### 代码规范

- 使用 black 格式化代码: `black .`
- 使用 isort 排序导入: `isort .`
- 使用 flake8 检查代码质量: `flake8 .`
- 使用 mypy 进行类型检查: `mypy .`

### 运行测试

```bash
# 运行单元测试
pytest

# 运行带覆盖率的测试
pytest --cov=semantic_retrieval_client
```

## 常见问题

### 构建错误

如果遇到构建错误，请确保：
1. 已安装最新版本的 setuptools 和 wheel
2. pyproject.toml 配置正确
3. 所有依赖项已正确声明

### 导入错误

如果遇到导入错误，请检查：
1. 包结构是否正确
2. __init__.py 文件是否包含正确的导出声明
3. 安装是否成功

## 许可证

MIT 许可证 - 详见 LICENSE 文件