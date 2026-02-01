# MuseumAgent_Server 博物馆智能体服务端

博物馆文物智能解析服务，基于 Python + FastAPI 开发，支持多客户端标准化对接。接收用户自然语言输入，通过 LLM 解析与文物知识库校验，返回标准化操作指令。

## 核心功能

- **智能解析**：对接 OpenAI 兼容 LLM（千问、GPT、DeepSeek 等），将用户自然语言解析为文物名称与操作指令
- **Embedding 服务**：OpenAI Embedding API 兼容格式，支持向量化与语义检索
- **知识库校验**：基于 SQLite/MySQL 文物知识库，校验文物存在性并返回 3D 资源路径、操作参数等
- **标准化指令**：输出统一格式的 JSON 指令，适配器灵、博物馆官网、第三方应用等多端调用
- **管理员控制面板**：`/Control` 提供 Web 管理界面，支持认证与验证码
- **SSL 支持**：支持 HTTPS 加密通信

## 技术栈

- **语言**：Python 3.8+
- **Web 框架**：FastAPI
- **配置**：JSON（主配置）+ INI（运维配置）
- **LLM**：OpenAI Compatible API（千问兼容模式、GPT、DeepSeek 等）
- **Embedding**：OpenAI Embedding API 兼容格式
- **数据库**：SQLite（默认）/ MySQL（可选）

## 项目结构

```
MuseumAgent_Server/
├── README.md
├── requirements.txt
├── main.py                 # 项目入口
├── config/
│   ├── config.json         # JSON 主配置
│   └── config.ini          # INI 运维配置
├── src/
│   ├── api/                # API 网关
│   │   └── agent_api.py    # /api/agent/parse 核心接口
│   ├── core/               # 核心业务
│   │   ├── llm_client.py       # LLM 调用
│   │   ├── knowledge_base.py   # 知识库
│   │   └── command_generator.py # 指令生成
│   ├── common/             # 公共工具
│   │   ├── config_utils.py
│   │   ├── log_utils.py
│   │   ├── response_utils.py
│   │   └── validate_utils.py
│   └── models/             # 数据模型
│       ├── request_models.py
│       └── response_models.py
├── control-panel/          # 控制面板前端（React + Vite + Ant Design）
├── data/
│   ├── museum_artifact.db  # SQLite 文物知识库
│   ├── museum_agent_app.db # 应用库（用户、配置历史等）
│   └── chroma_db/          # ChromaDB 向量库
├── logs/                   # 日志目录
├── tmp/                    # 临时文件
└── scripts/
    └── init_db.py          # 知识库初始化脚本
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

若使用国内镜像无法安装 dashscope，可指定官方源：

```bash
pip install -r requirements.txt -i https://pypi.org/simple
```

### 2. 配置 LLM 与 Embedding

编辑 `config/config.json`，配置 `llm` 和 `embedding`（均为 OpenAI 兼容格式）：

```json
"llm": {
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "api_key": "your-llm-api-key",
  "model": "qwen-turbo"
},
"embedding": {
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "api_key": "your-embedding-api-key",
  "model": "text-embedding-v4"
}
```

或通过环境变量注入（推荐生产环境）：`LLM_API_KEY`、`LLM_BASE_URL`、`EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL` 等。

### 3. 初始化知识库

首次运行前执行：

```bash
python scripts/init_db.py
```

### 4. 启动服务

```bash
python main.py
```

服务默认运行在 `http://0.0.0.0:8000`。

### 5. 验证

- 健康检查：`http://localhost:8000/` 或 `https://localhost:8000/`（启用 SSL 时）
- API 文档：`/docs`
- 核心接口：`POST /api/agent/parse`
- 管理员控制面板：`/Control`（默认账号 admin，密码 Admin@123，请及时修改）

## 接口说明

### POST /api/agent/parse

智能体解析接口，接收用户自然语言，返回标准化文物操作指令。

**请求体**（JSON）：

| 字段        | 类型   | 必填 | 说明                                   |
|-------------|--------|------|----------------------------------------|
| user_input  | string | 是   | 用户自然语言输入，1-2000 字符          |
| client_type | string | 否   | 客户端类型，用于日志统计               |
| spirit_id   | string | 否   | 器灵 ID                                |
| scene_type  | string | 否   | 场景类型：study/leisure/public，默认 public |

**响应体**（JSON）：

```json
{
  "code": 200,
  "msg": "请求处理成功",
  "data": {
    "artifact_id": "artifact_001",
    "artifact_name": "蟠龙盖罍",
    "operation": "introduce",
    "operation_params": {"zoom": 1.2},
    "keywords": ["纹样", "青铜"],
    "tips": "蟠龙盖罍是商周时期青铜礼器..."
  }
}
```

**调用示例**（Python）：

```python
import requests

url = "http://localhost:8000/api/agent/parse"
data = {
    "user_input": "讲讲蟠龙盖罍的纹样",
    "scene_type": "public"
}
response = requests.post(url, json=data, timeout=30)
result = response.json()
if result["code"] == 200:
    print("标准化指令：", result["data"])
else:
    print("请求失败：", result["msg"])
```

## 部署说明（阿里云 Ubuntu）

详见 `DevelopmentDocumentation.md` 第三部分「项目部署流程」，核心步骤：

1. 安装 Python 3.8+、supervisor
2. 上传项目代码并安装依赖
3. 配置 `config/config.json` 与 `config/config.ini`
4. 配置 supervisor 进程守护
5. 开放安全组端口（默认 8000）

## 配置说明

- **config.json**：核心业务配置（LLM、知识库、响应码等）
- **config.ini**：运维配置（日志路径、进程名、MySQL 等）

## 响应码

| 码   | 说明         |
|------|--------------|
| 200  | 成功         |
| 400  | 请求/业务失败 |
| 401  | 认证失败     |
| 404  | 未查询到相关文物 |

## 管理员控制面板（升级版）

访问 `https://服务器IP或域名/Control` 进入管理后台。

### 新版 SPA（React + Ant Design）

- **认证**：JWT，登录后请求头携带 `Authorization: Bearer <token>`
- **默认账号**：admin / Admin@123（首次启动自动创建于 SQLite `data/museum_agent_app.db`）
- **功能**：仪表盘、LLM/Embedding 配置、向量化与知识库（ChromaDB）、系统监控、用户管理

**构建前端**（可选，用于生产托管 SPA）：

```bash
cd control-panel
npm install
npm run build
```

构建完成后，后端会自动从 `control-panel/dist` 提供控制面板；若未构建，则回退到旧版 HTML 登录页。

### 旧版 HTML 面板

- **修改密码**：运行 `python scripts/gen_admin_password.py` 生成新哈希，填入 `config/config.ini` 的 `admin_password_hash`
- **验证码**：登录时需输入图形验证码，防止暴力破解

## SSL 配置

在 `config/config.json` 的 `server` 中：

- `ssl_enabled`: 是否启用 HTTPS
- `ssl_cert_file`: 证书文件路径（PEM 格式）
- `ssl_key_file`: 私钥文件路径

证书路径默认为 `./security/SSL/www.soulflaw.com_nginx/` 下的文件。

## 许可与贡献

本项目为博物馆智能体服务端，通用化设计，支持多客户端对接。
