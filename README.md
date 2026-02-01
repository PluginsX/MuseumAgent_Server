# MuseumAgent_Server 博物馆智能体服务端

博物馆文物智能解析服务，基于 Python + FastAPI 开发，支持多客户端标准化对接。接收用户自然语言输入，通过 LLM 解析与文物知识库校验，返回标准化操作指令。

## 核心功能

- **智能解析**：对接阿里通义千问等 LLM，将用户自然语言解析为文物名称与操作指令
- **知识库校验**：基于 SQLite/MySQL 文物知识库，校验文物存在性并返回 3D 资源路径、操作参数等
- **标准化指令**：输出统一格式的 JSON 指令，适配器灵、博物馆官网、第三方应用等多端调用
- **高可用部署**：支持 supervisor 进程守护，日志分级存储，便于运维排查

## 技术栈

- **语言**：Python 3.8+
- **Web 框架**：FastAPI
- **配置**：JSON（主配置）+ INI（运维配置）
- **LLM**：dashscope（通义千问）
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
├── data/
│   └── museum_artifact.db  # SQLite 文物知识库
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

### 2. 配置 LLM API Key

编辑 `config/config.json`，将 `llm.api_key` 修改为你的通义千问 API Key：

```json
"llm": {
  "provider": "dashscope",
  "model": "qwen-turbo",
  "api_key": "your-own-llm-api-key",
  ...
}
```

或通过环境变量注入（推荐生产环境）：

```bash
export LLM_API_KEY=your-own-llm-api-key
```

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

- 健康检查：`http://localhost:8000/`
- API 文档：`http://localhost:8000/docs`
- 核心接口：`POST http://localhost:8000/api/agent/parse`

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

## 许可与贡献

本项目为博物馆智能体服务端，通用化设计，支持多客户端对接。
