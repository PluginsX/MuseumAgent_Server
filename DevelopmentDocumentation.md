# MuseumAgent_Server 智能体服务端（Python+JSON+INI）纯文字开发架构详细流程与内容
## 一、项目前置准备（开发/部署双端就绪，通用化适配多客户端）
### 1. 技术栈最终确认（无冗余，纯落地，通用化支撑多业务端调用）
- 核心开发语言：Python 3.8+（Ubuntu 20.04+原生支持，兼容所有依赖库，跨端适配性强）
- Web框架：FastAPI（高性能异步框架，自动生成API文档，轻量化适配阿里云服务器，支持高并发轻量请求）
- 配置解析：内置`json`模块（解析JSON主配置）、内置`configparser`模块（解析INI辅助配置），无第三方依赖，配置读取高效
- 网络请求：`requests`（通用HTTP请求，适配所有LLM服务商API）、`dashscope`/`openai`（主流LLM专属SDK，按需引入）
- 数据存储/校验：内置`sqlite3`（本地轻量知识库，快速部署）、`pymysql`（可选，远程MySQL扩展，支撑大数据量知识库）
- 数据格式校验：`pydantic`（请求/响应数据模型定义，自动校验格式，保证多客户端调用的数据规范性）
- 日志处理：内置`logging`+`RotatingFileHandler`（日志分级、按大小分割，便于多客户端调用的问题排查）
- 进程守护：`supervisor`（阿里云Ubuntu服务器进程常驻，异常自动重启，保障服务高可用）
- 依赖管理：`pip`+`requirements.txt`（统一管理第三方依赖，便于跨环境部署）

### 2. 项目目录结构（模块化解耦，通用化命名，适配多客户端调用，纯文字层级清晰）
项目根目录命名：`MuseumAgent_Server`
```
MuseumAgent_Server/
├── README.md（项目说明：核心功能、部署步骤、接口列表、调用规范，纯文字运维/开发友好，适配多客户端对接）
├── requirements.txt（第三方依赖列表，逐行列出包名+固定版本号，避免版本冲突，保障跨环境部署一致性）
├── main.py（项目唯一入口，初始化配置、日志、启动FastAPI服务，无业务逻辑，通用化启动）
├── config/（配置文件目录，统一管理，便于权限管控，通用化配置适配多客户端）
│   ├── config.json（JSON主配置：核心业务配置，有嵌套、多数据类型，支撑多LLM、多知识库配置）
│   └── config.ini（INI辅助配置：运维平级配置，支持注释，便于手动修改，适配服务器运维需求）
├── src/（核心源码目录，所有业务逻辑均在此，按模块拆分，低耦合高内聚，便于多客户端适配扩展）
│   ├── __init__.py（标识Python包，空文件即可）
│   ├── api/（API网关模块，对外暴露标准化接口，仅负责请求转发与响应封装，与业务逻辑解耦，适配多客户端调用）
│   │   ├── __init__.py
│   │   └── agent_api.py（通用智能体核心接口，定义`/api/agent/parse`标准化接口，承接所有客户端的请求）
│   ├── core/（核心业务模块，项目核心逻辑，负责调度各子模块，与客户端解耦，仅处理数据解析与指令生成）
│   │   ├── __init__.py
│   │   ├── llm_client.py（LLM服务调用模块，封装不同提供商调用逻辑，处理异常，通用化适配多LLM服务商）
│   │   ├── knowledge_base.py（文物知识库校验模块，封装数据库查询、操作合法性校验，通用化适配多类型知识库）
│   │   └── command_generator.py（标准化指令生成模块，整合LLM与知识库结果，生成通用化标准化指令，适配多客户端解析）
│   ├── common/（公共工具模块，封装通用功能，避免代码复用，所有模块均可调用，与业务无关）
│   │   ├── __init__.py
│   │   ├── config_utils.py（配置读取工具，加载JSON/INI配置，提供全局配置访问接口，避免重复读取文件）
│   │   ├── log_utils.py（日志工具，初始化日志配置，定义统一日志格式、存储路径、分割规则，适配多客户端调用日志追溯）
│   │   ├── response_utils.py（响应工具，封装标准化成功/失败响应，保证所有客户端解析一致性，无客户端专属格式）
│   │   └── validate_utils.py（校验工具，辅助`pydantic`完成复杂请求参数校验，通用化校验规则适配多客户端）
│   └── models/（数据模型模块，定义通用化请求/响应数据结构，保证多客户端调用的数据规范性，无客户端专属字段）
│       ├── __init__.py
│       ├── request_models.py（请求数据模型，基于`pydantic`定义通用字段、约束、描述，适配所有客户端的请求格式）
│       └── response_models.py（响应数据模型，定义通用化标准化指令、响应体结构，所有客户端均按此格式解析）
├── data/（数据存储目录，存储SQLite文物知识库，便于数据备份与迁移，通用化存储适配多客户端）
│   └── museum_artifact.db（SQLite数据库文件，存储文物ID、名称、3D资源路径、操作参数、简介等通用核心数据）
├── logs/（日志存储目录，自动生成，无需手动创建，按日志类型分割，适配多客户端调用的日志排查）
│   ├── museum_agent.log（普通运行日志，记录所有客户端的请求、处理流程、正常信息，按时间排序）
│   ├── museum_agent_error.log（错误日志，仅记录ERROR/CRITICAL级别信息，便于快速排障，与普通日志分离）
│   └── supervisor.log（supervisor进程日志，记录服务启动、重启、异常退出信息，保障服务运维）
└── tmp/（临时文件目录，存储进程PID文件，便于进程监控，避免端口占用，通用化运维适配）
    └── museum_agent.pid（进程PID文件，记录服务运行进程ID，唯一标识服务进程，便于运维管控）
```

### 3. 配置文件编写（JSON为主，INI为辅，通用化配置，无客户端专属内容，纯文字配置项清晰）
#### （1）JSON主配置（config/config.json）：核心业务配置，严格格式，支持嵌套/多数据类型，通用化适配多LLM、多知识库、多客户端
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": false,
    "cors_allow_origins": ["*"],
    "request_limit": 200,
    "request_timeout": 30
  },
  "llm": {
    "provider": "dashscope",
    "model": "qwen-turbo",
    "api_key": "your-own-llm-api-key",
    "parameters": {
      "temperature": 0.2,
      "max_tokens": 1024,
      "top_p": 0.9
    },
    "prompt_template": "你是博物馆文物智能解析专家，需严格按要求解析用户需求并返回纯JSON格式结果，无多余文字。返回字段：artifact_name（文物名称，字符串）、operation（文物操作指令，字符串，可选值：zoom_pattern、restore_scene、introduce、spirit_interact、query_param）、keywords（解析关键词，数组）。用户场景：{scene_type}，用户输入：{user_input}。"
  },
  "artifact_knowledge_base": {
    "type": "sqlite",
    "path": "./data/museum_artifact.db",
    "table_name": "museum_artifact_info",
    "valid_operations": ["zoom_pattern", "restore_scene", "introduce", "spirit_interact", "query_param"]
  },
  "response": {
    "success_code": 200,
    "fail_code": 400,
    "auth_fail_code": 401,
    "data_none_code": 404,
    "success_msg": "请求处理成功",
    "fail_msg": "请求处理失败",
    "auth_fail_msg": "接口认证失败",
    "data_none_msg": "未查询到相关文物数据"
  }
}
```
**配置通用化说明**：
1.  无任何客户端专属配置，仅定义核心业务规则，适配器灵、博物馆官网、其他文物展示应用等多端调用；
2.  扩展`request_limit`为200，提升并发支持能力，满足多客户端同时调用需求；
3.  新增响应码（`auth_fail_code`/`data_none_code`）与对应提示，细化响应结果，便于多客户端做差异化异常处理；
4.  扩展LLM操作指令（`query_param`），新增通用化参数查询指令，适配多客户端的不同功能需求；
5.  数据库文件与表名做通用化命名，脱离客户端专属标识，适配博物馆通用文物数据存储。

#### （2）INI辅助配置（config/config.ini）：运维平级配置，支持注释，语法松散，通用化运维，无客户端专属内容
```ini
[log]
; 日志存储路径，相对项目根目录，若不存在自动创建，通用化路径适配所有部署环境
log_path = ./logs/
; 日志级别：DEBUG/INFO/WARNING/ERROR/CRITICAL，默认INFO，DEBUG用于开发调试，INFO用于生产环境
log_level = INFO
; 单个日志文件最大大小（字节），10485760=10MB，按大小分割避免日志文件过大
log_max_size = 10485760
; 日志备份文件数量，保留最近7个，自动删除旧文件，平衡日志追溯与磁盘占用
log_backup_count = 7

[process]
; 进程名称，用于supervisor监控，通用化命名，唯一标识本服务
process_name = museum_agent_server
; PID文件存储路径，记录服务运行进程ID，避免端口占用
pid_file = ./tmp/museum_agent.pid

[database]
; MySQL配置（可选，用于扩展远程知识库），SQLite无需配置此项，通用化适配多类型数据库
mysql_host = 127.0.0.1
mysql_port = 3306
mysql_user = root
mysql_password = your-own-mysql-password
mysql_db = museum_artifact
; MySQL连接池配置，提升多客户端并发查询效率
mysql_pool_size = 10
mysql_pool_recycle = 3600

[server]
; 服务运维通用配置，用于后续扩展监控
monitor_enable = false
monitor_port = 8001
```
**配置通用化说明**：
1.  所有配置均为服务器运维通用项，无客户端专属配置，适配多客户端调用的运维需求；
2.  新增MySQL连接池配置，提升多客户端并发查询时的数据库性能，适配高并发场景；
3.  新增服务监控通用配置，为后续添加服务监控功能预留扩展，无需修改代码即可开启；
4.  进程、PID文件、数据库命名均做通用化处理，脱离客户端专属标识，便于服务独立部署与运维。

## 二、项目核心开发流程（按模块递进，纯文字步骤清晰，可直接落地，全程与客户端解耦，仅处理通用化数据与指令）
### 核心开发原则
1.  所有模块**无任何客户端专属代码/字段/逻辑**，仅处理通用化的「请求接收→数据解析→指令生成→响应返回」；
2.  标准化指令与响应格式**统一固定**，所有客户端均按此格式对接，服务端无需做任何适配性修改；
3.  模块间**低耦合高内聚**，核心业务逻辑与API网关、工具模块完全解耦，便于后续功能扩展与多客户端适配。

### 步骤1：编写公共工具模块（基础支撑，先搭建通用工具，再开发业务逻辑，与客户端、业务完全无关）
1.  **配置读取工具（src/common/config_utils.py）**
    - 定义全局变量`GLOBAL_CONFIG`（存储JSON核心配置）、`GLOBAL_INI_CONFIG`（存储INI运维配置），全局唯一，所有模块统一调用；
    - 编写`load_config()`函数：按路径读取JSON/INI配置文件，处理**文件不存在、格式错误、配置项缺失**等异常，抛出清晰错误信息，便于排障；读取后初始化全局配置，项目启动时仅执行一次，避免重复IO操作；
    - 编写`get_global_config()`、`get_global_ini_config()`函数：提供全局配置只读访问接口，避免其他模块修改配置，保证配置一致性；
    - 编写`get_config_by_key()`函数：提供按层级键获取配置的快捷方法，如`get_config_by_key("llm", "provider")`，简化配置读取代码。

2.  **日志工具（src/common/log_utils.py）**
    - 编写`init_logger()`函数：从INI配置中读取日志参数，自动创建日志目录（若不存在）；
    - 定义**统一日志格式**：包含「时间、模块名、函数名、行号、日志级别、内容」，便于多客户端调用的日志追溯与问题定位；
    - 添加3个日志处理器：控制台处理器（开发调试）、普通文件处理器（所有客户端运行日志）、错误文件处理器（单独存储错误日志），处理器级别与配置一致，错误日志仅记录ERROR/CRITICAL级别；
    - 使用`RotatingFileHandler`按大小分割日志，按配置保留备份数量，自动清理旧日志，避免磁盘占用过高；
    - 日志命名为通用化名称，无客户端专属标识，适配多客户端日志排查。

3.  **响应工具（src/common/response_utils.py）**
    - 编写**4个通用化响应函数**，覆盖所有业务场景，返回格式完全统一，无客户端专属字段：
      - `success_response(data=None, msg=None)`：成功响应，默认使用配置中的成功码与提示语，支持自定义数据与提示；
      - `fail_response(msg=None, code=None, data=None)`：通用失败响应，支持自定义错误码、提示语、错误详情；
      - `auth_fail_response(msg=None)`：认证失败响应，固定使用配置中的认证失败码，适配后续接口认证扩展；
      - `data_none_response(msg=None)`：数据不存在响应，固定使用配置中的数据不存在码，适配知识库查询空结果场景；
    - 所有响应返回**标准JSON格式**：`{"code": 数字, "msg": 字符串, "data": 任意合法JSON数据}`，保证所有客户端均可直接解析，无需适配。

4.  **校验工具（src/common/validate_utils.py，辅助功能）**
    - 编写通用化校验函数，与业务、客户端无关，仅做数据格式/规则校验，返回**布尔值+错误信息**：
      - `validate_artifact_id(artifact_id)`：校验文物ID格式（如是否为数字/字母组合、长度是否符合规范）；
      - `validate_operation(operation, valid_operations)`：校验操作指令是否在合法列表中，适配配置中的动态合法操作；
      - `validate_scene_type(scene_type)`：校验场景类型是否为`study/leisure/public`，扩展公共场景适配多客户端；
    - 所有校验函数均为纯函数，无状态，可被任意模块调用，校验规则统一，保证多客户端请求的校验一致性。

### 步骤2：编写数据模型模块（数据规范，定义通用化请求/响应结构，无客户端专属字段，所有客户端均按此对接）
1.  **请求数据模型（src/models/request_models.py）**
    - 基于`pydantic.BaseModel`定义**通用化请求模型**`AgentParseRequest`，适配所有客户端的请求格式，字段均为通用项，无客户端专属内容：
      ```python
      from pydantic import BaseModel, Field
      from typing import Optional

      class AgentParseRequest(BaseModel):
          """博物馆智能体通用请求数据模型，所有客户端均按此格式发送请求"""
          user_input: str = Field(..., description="用户自然语言输入", min_length=1, max_length=2000)
          client_type: Optional[str] = Field(None, description="客户端类型（用于日志统计，非业务逻辑）", example="qiling/official/third")
          spirit_id: Optional[str] = Field(None, description="器灵ID（第三方客户端可传空，服务端不做业务处理）")
          scene_type: Optional[str] = Field("public", description="场景类型：study/leisure/public，默认公共场景", pattern="^(study|leisure|public)$")
      ```
    - 字段设计原则：**核心字段必填，客户端专属字段为可选且服务端不做业务处理**，仅做日志统计；扩展`user_input`长度至2000，适配多客户端的复杂需求输入；新增`public`公共场景，适配博物馆官网等通用客户端；
    - `pydantic`自动完成参数校验，非法参数直接返回异常，无需业务模块做额外校验，保证请求数据规范性。

2.  **响应数据模型（src/models/response_models.py）**
    - 基于`pydantic.BaseModel`定义**通用化标准化指令模型**`StandardCommand`，所有客户端均按此格式解析指令，字段为通用化操作参数，无客户端专属内容：
      ```python
      from pydantic import BaseModel
      from typing import Optional, Dict, List

      class StandardCommand(BaseModel):
          """博物馆智能体通用标准化指令模型，所有客户端均按此格式解析"""
          artifact_id: Optional[str] = None
          artifact_name: Optional[str] = None
          operation: Optional[str] = None
          operation_params: Optional[Dict] = None
          keywords: Optional[List] = None
          tips: Optional[str] = None
      ```
    - 基于`pydantic.BaseModel`定义**通用化响应模型**`AgentParseResponse`，包裹标准化指令，所有客户端均按此格式接收响应：
      ```python
      class AgentParseResponse(BaseModel):
          """博物馆智能体通用响应模型，所有客户端均按此格式接收响应"""
          code: int
          msg: str
          data: Optional[StandardCommand] = None
      ```
    - 模型设计原则：**字段可选但格式固定**，适配所有文物操作场景；新增`keywords`字段，返回LLM解析的关键词，便于多客户端做二次处理；`operation_params`为字典类型，支持动态传递不同操作的参数，适配多客户端的不同功能需求。

### 步骤3：编写核心业务模块（项目核心，调度各子模块，完成通用化业务逻辑闭环，与客户端完全解耦，仅处理数据与指令）
#### 子步骤3.1：LLM服务调用模块（src/core/llm_client.py）
- 定义通用化`LLMClient`类，与客户端无关，仅封装LLM服务商的调用逻辑，支持动态切换提供商；
- 初始化方法`__init__`：从全局配置中读取LLM所有参数（提供商、API Key、模型、请求参数、提示词模板），无需硬编码，便于配置修改；
- 编写`generate_prompt()`函数：传入用户输入、场景类型，填充通用化提示词模板，生成完整的LLM请求提示词，无客户端专属内容，提示词仅要求返回纯JSON格式，保证解析一致性；
- 编写**服务商通用调用函数**：`call_dashscope()`、`call_openai()`（预留）、`call_ernie()`（预留），每个函数封装对应服务商的API请求逻辑，包含：请求头设置、请求体构建、超时处理、异常捕获（API Key无效、额度不足、响应格式异常、网络超时），统一返回**LLM纯JSON响应字符串**，无多余处理；
- 编写核心`parse_user_input()`函数：根据配置中的LLM提供商，自动调用对应服务商的调用函数，返回LLM解析结果；捕获**不支持的提供商**异常，抛出清晰错误信息；
- 所有函数均为**通用化处理**，无客户端专属逻辑，仅做LLM请求与结果返回，保证多客户端调用的LLM解析一致性。

#### 子步骤3.2：文物知识库校验模块（src/core/knowledge_base.py）
- 定义通用化`ArtifactKnowledgeBase`类，与客户端无关，仅封装知识库的查询与校验逻辑，支持动态切换知识库类型（SQLite/MySQL）；
- 初始化方法`__init__`：从全局配置中读取知识库所有参数（类型、路径/连接信息、表名、合法操作列表），无需硬编码，便于配置修改；
- 编写**数据库通用连接函数**：`_connect_sqlite()`（私有）、`_connect_mysql()`（私有，预留），每个函数封装对应数据库的连接逻辑，包含：连接建立、异常捕获（文件不存在、连接失败、权限不足），设置行工厂为按列名查询，返回数据库连接对象；连接函数仅在查询时调用，查询完成后自动关闭，避免连接泄漏；
- 编写通用化`query_artifact_by_name()`函数：传入文物名称，执行**模糊查询**，适配用户自然语言输入的不准确性；查询结果转换为**通用化字典格式**，仅包含配置中定义的通用文物字段，无客户端专属内容；无结果返回`None`，捕获数据库查询异常（表不存在、字段错误），抛出清晰错误信息；
- 编写`validate_operation()`函数：传入操作指令，校验是否在配置中的合法操作列表中，返回布尔值，合法操作列表为动态配置，便于后续扩展，无客户端专属操作；
- 编写核心`get_standard_artifact_data()`函数：传入文物名称，调用查询函数，无结果抛出**数据不存在**异常；查询成功则返回**标准化文物字典数据**，包含文物ID、名称、3D资源路径、操作参数、简介等通用字段，无客户端专属内容；
- 所有函数均为**通用化处理**，无客户端专属逻辑，仅做知识库查询与合法性校验，避免LLM幻觉，保证多客户端调用的文物数据一致性。

#### 子步骤3.3：标准化指令生成模块（src/core/command_generator.py）
- 定义通用化`CommandGenerator`类，项目核心业务调度类，与客户端无关，仅做「LLM解析结果+知识库数据」的整合与标准化指令生成；
- 初始化方法`__init__`：实例化`LLMClient`与`ArtifactKnowledgeBase`，无需传参，直接使用全局配置，保证配置一致性；
- 编写`parse_llm_response()`函数：传入LLM纯JSON响应字符串，解析为**通用化字典格式**，捕获JSON格式错误异常，抛出清晰错误信息，保证解析一致性；
- 编写核心`generate_standard_command()`函数，**通用化业务逻辑闭环**，步骤如下，全程无客户端专属逻辑：
  1.  接收外部传入的**用户输入、场景类型**，为通用化参数，无客户端专属内容；
  2.  调用`LLMClient.parse_user_input()`，获取LLM纯JSON解析结果；
  3.  调用`parse_llm_response()`，解析LLM结果，提取**文物名称、操作指令、关键词**三个核心字段；
  4.  空值校验：文物名称/操作指令为空则抛出异常，关键词为空则赋值为空数组；
  5.  调用`ArtifactKnowledgeBase.validate_operation()`，校验操作指令合法性，不合法则抛出异常；
  6.  调用`ArtifactKnowledgeBase.get_standard_artifact_data()`，根据文物名称获取标准化文物数据；
  7.  **整合生成通用化标准化指令**：将文物数据（ID、名称、操作参数）、LLM解析结果（操作指令、关键词）、文物简介（tips）整合为`StandardCommand`模型要求的字典格式，无客户端专属字段；
  8.  返回标准化指令字典，完成业务逻辑闭环；
- 所有步骤均为**通用化处理**，异常均抛出清晰的业务错误信息，便于后续API网关模块做统一异常处理，保证多客户端调用的指令生成一致性。

### 步骤4：编写API网关模块（对外暴露标准化接口，承接所有客户端的请求，与业务逻辑完全解耦，仅做请求转发与响应封装）
1.  智能体核心API（src/api/agent_api.py）
    - 初始化FastAPI应用，设置**通用化标题、描述、版本**，自动生成标准化API文档，便于所有客户端对接开发；
    - 配置**跨域中间件**：从全局配置中读取允许的域名列表，设置允许所有请求方法、请求头、凭据，适配多客户端的跨域调用需求；
    - 实例化`CommandGenerator`类，全局唯一，所有请求共用一个实例，避免重复初始化；
    - 定义**通用化POST接口**`/api/agent/parse`，为服务端唯一对外暴露的核心接口，所有客户端均调用此接口，无客户端专属接口；
    - 接口装饰器配置：指定响应模型为`AgentParseResponse`，添加接口描述、参数说明，自动生成API文档，便于客户端对接；
    - 接口核心逻辑，**全程与客户端解耦**，仅做通用化请求处理与响应封装，步骤如下：
      1.  接收前端请求，`pydantic`自动将请求体映射为`AgentParseRequest`通用模型，完成参数校验；
      2.  记录**通用化访问日志**：包含请求时间、客户端类型、用户输入、场景类型，便于多客户端的调用统计与日志追溯；
      3.  调用`CommandGenerator.generate_standard_command()`，传入用户输入、场景类型，获取通用化标准化指令；
      4.  调用`success_response()`，将标准化指令作为`data`传入，返回通用化成功响应；
      5.  **统一异常处理**：捕获所有异常（参数校验异常、业务逻辑异常、LLM调用异常、知识库查询异常），根据异常类型调用对应的响应函数（`fail_response()`/`data_none_response()`），记录**错误日志**（包含异常信息、请求参数），便于问题排查；
    - 接口无任何客户端专属代码/逻辑，所有请求均按统一流程处理，所有响应均按统一格式返回，保证多客户端调用的接口一致性。

### 步骤5：编写项目入口文件（main.py，唯一启动入口，通用化启动，无业务逻辑，无客户端专属内容）
1.  导入核心依赖：`uvicorn`（FastAPI启动器）、`load_config`（配置读取）、`init_logger`（日志初始化）、`app`（FastAPI应用实例）；
2.  项目启动初始化：按顺序调用`load_config()`、`init_logger()`，完成全局配置与日志的初始化，初始化失败则直接退出程序，抛出清晰错误信息；
3.  读取服务端配置：从全局配置中读取`host`、`port`、`reload`参数，无需硬编码，便于配置修改；
4.  启动FastAPI服务：调用`uvicorn.run()`，设置启动入口为`main:app`，传入读取的配置参数，启动服务；
5.  入口文件**无任何业务逻辑，无任何客户端专属内容**，仅做服务启动初始化，通用化适配所有部署环境与多客户端调用。

### 步骤6：编写requirements.txt（依赖管理，通用化依赖，无客户端专属库，便于跨环境部署，逐行列出包名+固定版本号）
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.4.2
requests==2.31.0
dashscope==1.1.0
pymysql==1.1.0
python-dotenv==1.0.0
```
**依赖说明**：
1.  所有依赖均为**通用化库**，无客户端专属库，适配多客户端调用的服务端需求；
2.  所有库均指定**固定版本号**，避免部署时因版本更新导致的兼容性问题，保证跨环境部署的一致性；
3.  `dashscope`为阿里通义千问SDK，其他LLM服务商SDK（如`openai`/`erniebot`）可按需添加，无需修改代码，仅需配置即可切换；
4.  `pymysql`为MySQL扩展依赖，仅在使用远程MySQL知识库时需要，SQLite无需此依赖，可按需删除；
5.  `python-dotenv`为环境变量注入依赖，便于生产环境敏感配置（如API Key）的注入，提高服务安全性。

## 三、项目部署流程（阿里云Ubuntu服务器，纯文字步骤，可直接操作，通用化部署，适配多客户端调用，无客户端专属部署步骤）
### 部署核心原则
1.  服务端**独立部署**，与所有客户端解耦，部署完成后所有客户端均可通过网络调用，无需为单个客户端做部署修改；
2.  部署步骤**标准化、通用化**，适配阿里云Ubuntu服务器的基础环境，无特殊配置，便于博物馆运维人员操作；
3.  服务启动后**常驻运行**，异常自动重启，保障多客户端调用的高可用性。

### 步骤1：服务器环境配置（前置准备，确保服务器满足通用化运行条件，无客户端专属配置）
1.  登录阿里云Ubuntu服务器（通过SSH工具：Xshell/FinalShell/CMD，使用服务器账号密码/密钥）；
2.  更新系统软件包，保证基础环境最新：`sudo apt update && sudo apt upgrade -y`；
3.  安装Python基础依赖工具，保证Python环境正常：`sudo apt install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools`；
4.  安装进程守护工具，保证服务常驻运行：`sudo apt install -y supervisor`；
5.  安装git（可选），便于拉取项目代码：`sudo apt install -y git`；
6.  验证Python环境，确保版本≥3.8：`python3 --version`、`pip3 --version`，版本过低则手动升级Python；
7.  开放服务端口（阿里云安全组）：登录阿里云控制台→找到对应服务器→安全组配置→添加安全组规则，放行配置中的`port`（默认8000），**允许TCP协议，来源为0.0.0.0/0**（或指定博物馆内网IP，提高安全性），确保所有客户端均可通过网络访问。

### 步骤2：项目上传与初始化（部署项目代码，通用化配置，无客户端专属修改，可直接操作）
1.  创建通用化项目目录，便于运维管理：`mkdir -p /opt/MuseumAgent_Server && cd /opt/MuseumAgent_Server`；
2.  上传项目代码至服务器（二选一，通用化方式，无客户端专属）：
    - 方式1（git）：`git clone 你的项目仓库地址`（如GitHub/Gitee/GitLab），适用于开发阶段频繁迭代；
    - 方式2（scp）：本地执行`scp -r 本地项目根目录 root@服务器公网IP:/opt/`，适用于生产环境部署，避免代码仓库依赖；
3.  解压项目压缩包（若上传的是压缩包）：`unzip MuseumAgent_Server.zip`，确保项目目录结构与开发环境一致；
4.  安装项目第三方依赖，使用固定版本，保证环境一致性：`pip3 install -r requirements.txt`；
5.  创建通用化必要目录（若缺失），保证服务正常运行：`mkdir -p logs tmp data`；
6.  上传文物知识库文件：将`museum_artifact.db`（SQLite）通过scp上传至`/opt/MuseumAgent_Server/data`目录，若使用MySQL则无需上传，仅需配置数据库连接信息即可；
7.  修改配置文件（仅需修改敏感配置与服务器适配配置，无客户端专属修改）：
    - 编辑JSON主配置：`vim config/config.json`，更新`llm.api_key`（LLM服务商API Key）、`artifact_knowledge_base.path`（知识库路径，绝对路径/相对路径均可）；
    - 编辑INI辅助配置：`vim config/config.ini`，更新`database.mysql_password`（若使用MySQL）、其他运维配置按服务器环境调整；
    - 敏感配置（如API Key/数据库密码）建议通过**环境变量注入**：`export LLM_API_KEY=your-key`，代码中通过`os.getenv()`获取，避免配置文件明文存储，提高安全性；
8.  保存配置文件，退出编辑模式（vim：`ESC→:wq→回车`）。

### 步骤3：配置supervisor进程守护（确保服务常驻运行，异常自动重启，通用化配置，无客户端专属内容）
1.  创建supervisor通用化配置文件，唯一标识本服务：`sudo vim /etc/supervisor/conf.d/museum_agent_server.conf`；
2.  写入以下通用化配置内容，无客户端专属配置，仅需修改项目目录路径即可：
    ```ini
    [program:museum_agent_server]
    ; 服务启动命令，指定Python路径与项目入口文件路径，确保路径正确
    command=/usr/bin/python3 /opt/MuseumAgent_Server/main.py
    ; 项目工作目录，与创建的项目目录一致
    directory=/opt/MuseumAgent_Server
    ; 运行用户，默认root，可按需改为博物馆运维用户
    user=root
    ; 服务启动后自动开始运行
    autostart=true
    ; 服务异常退出后自动重启，保障高可用性
    autorestart=true
    ; 将标准错误输出重定向到标准输出，便于日志统一管理
    redirect_stderr=true
    ; 服务运行日志路径，与项目日志目录一致
    stdout_logfile=/opt/MuseumAgent_Server/logs/supervisor.log
    ; 服务错误日志路径，与项目日志目录一致
    stderr_logfile=/opt/MuseumAgent_Server/logs/supervisor_error.log
    ; 进程启动等待时间，避免频繁重启
    startsecs=5
    ; 最大重启次数，避免无限重启
    startretries=3
    ```
3.  保存配置文件，退出编辑模式；
4.  更新supervisor配置，让配置生效：`sudo supervisorctl update`；
5.  启动MuseumAgent_Server服务：`sudo supervisorctl start museum_agent_server`；
6.  验证服务状态，显示`RUNNING`即为启动成功：`sudo supervisorctl status museum_agent_server`；
    - 若显示`EXITED`，查看错误日志：`cat /opt/MuseumAgent_Server/logs/supervisor_error.log`，排查原因后重新启动；
    - 若需重启服务：`sudo supervisorctl restart museum_agent_server`；
    - 若需停止服务：`sudo supervisorctl stop museum_agent_server`。

### 步骤4：服务通用化验证（确保服务正常运行，接口可用，所有客户端均可调用，无客户端专属验证步骤）
1.  **访问API文档验证**：打开任意浏览器，输入`http://服务器公网IP:8000/docs`（替换为你的服务器IP与配置端口），若能正常打开FastAPI自动生成的**交互式API文档**，说明服务启动成功；
2.  **接口功能测试验证**：在API文档中找到`/api/agent/parse`接口→点击`Try it out`→输入通用化请求参数（示例：`user_input: 讲讲蟠龙盖罍`，`scene_type: public`）→点击`Execute`→查看响应结果；
3.  **响应格式验证**：响应结果需为标准格式，成功时`code=200`，`data`中包含标准化指令（artifact_id/artifact_name/operation等），无错误信息，说明接口功能正常；
4.  **日志验证**：进入服务器项目日志目录：`cd /opt/MuseumAgent_Server/logs`→查看普通运行日志：`cat museum_agent.log`，确认无ERROR级别日志，请求与处理流程正常记录；
5.  **多客户端网络调用验证**：在任意客户端（器灵/博物馆官网/第三方应用）中，通过HTTP/HTTPS协议调用`http://服务器公网IP:8000/api/agent/parse`接口，传入通用化请求参数，验证是否能正常获取标准化响应，确保多客户端均可正常调用。

## 四、项目运维与扩展（纯文字，保障服务稳定运行，便于后续功能扩展与多客户端适配，无客户端专属运维/扩展步骤）
### 核心原则
1.  **运维通用化**：所有运维操作均为服务端独立操作，与客户端解耦，无需为单个客户端做运维修改；
2.  **扩展无侵入**：所有功能扩展均基于现有模块开发，无需修改核心代码，仅需添加模块/配置即可，保证服务端的稳定性与多客户端调用的一致性；
3.  **兼容向前**：新增功能/配置后，原有客户端的调用方式与响应格式不变，无需做适配性修改，实现无缝升级。

### 1. 日常运维（保障服务稳定运行，快速排障，通用化操作，适配多客户端调用）
1.  **日志管理**：
    - 日志按类型存储在`logs/`目录，`museum_agent.log`为所有客户端的运行日志，`museum_agent_error.log`为错误日志，`supervisor.log`为进程日志；
    - 定期查看错误日志：`cat /opt/MuseumAgent_Server/logs/museum_agent_error.log`，快速定位问题，无错误则无需处理；
    - 日志自动按大小分割，保留7个备份，无需手动删除，若磁盘空间不足，可修改INI配置中的`log_max_size`/`log_backup_count`，重启服务即可生效；
2.  **服务状态监控**：
    - 实时查看服务状态：`sudo supervisorctl status museum_agent_server`，显示`RUNNING`即为正常，`EXITED`为异常；
    - 服务异常重启：`sudo supervisorctl restart museum_agent_server`，重启后查看日志排查异常原因；
    - 服务器资源监控：使用`top`/`htop`命令查看CPU/内存使用情况，若资源不足，可升级阿里云服务器配置，或优化服务性能；
3.  **配置更新**：
    - 修改配置文件后，无需重新部署，仅需重启服务即可生效：`sudo supervisorctl restart museum_agent_server`；
    - 敏感配置（API Key/数据库密码）建议通过**阿里云环境变量**注入，避免直接修改配置文件，提高安全性；
4.  **数据备份**：
    - SQLite知识库备份：`cp /opt/MuseumAgent_Server/data/museum_artifact.db /opt/MuseumAgent_Server/data/museum_artifact_backup_$(date +%Y%m%d).db`，按日期备份，避免数据丢失；
    - MySQL知识库备份：使用`mysqldump`命令备份，按博物馆数据库运维规范操作；
5.  **端口/IP管理**：
    - 若需修改服务端口，仅需修改JSON配置中的`server.port`，并在阿里云安全组中放行新端口，重启服务即可；
    - 生产环境建议将服务端部署在**博物馆内网**，仅开放内网IP访问，提高服务安全性，客户端通过内网调用。

### 2. 功能扩展（便于后续迭代，满足多客户端的新增需求，无侵入式扩展，兼容原有客户端）
1.  **新增LLM服务商**：
    - 步骤1：在`requirements.txt`中添加对应服务商SDK（如`openai`/`erniebot`），执行`pip3 install`安装；
    - 步骤2：在`src/core/llm_client.py`中添加对应服务商的调用函数（如`call_openai()`），封装API请求逻辑，统一返回纯JSON响应字符串；
    - 步骤3：在`LLMClient.parse_user_input()`中添加服务商判断，无需修改其他代码；
    - 步骤4：修改JSON配置中的`llm.provider`/`llm.model`/`llm.api_key`，重启服务即可切换，所有客户端无需做任何修改；
2.  **扩展知识库类型**：
    - 步骤1：若使用PostgreSQL/Oracle等数据库，在`src/core/knowledge_base.py`中添加对应数据库的连接/查询函数，封装通用化逻辑；
    - 步骤2：修改JSON配置中的`artifact_knowledge_base.type`与对应连接信息，重启服务即可切换，所有客户端无需做任何修改；
3.  **新增文物操作指令**：
    - 步骤1：修改JSON配置中的`llm.prompt_template`，添加新操作指令到可选值中；
    - 步骤2：修改JSON配置中的`artifact_knowledge_base.valid_operations`，添加新操作指令；
    - 步骤3：在知识库中添加新操作指令对应的`operation_params`参数；
    - 步骤4：重启服务即可支持新操作指令，所有客户端均可直接调用，无需修改代码；
4.  **添加接口认证**：
    - 步骤1：在`src/common/`中添加`auth_utils.py`，封装JWT/Token认证逻辑，生成通用化认证装饰器；
    - 步骤2：在`src/api/agent_api.py`的接口上添加认证装饰器，仅需一行代码；
    - 步骤3：修改JSON配置中的`response`，添加认证失败码与提示；
    - 步骤4：重启服务即可开启认证，客户端仅需在请求头中添加认证信息，无需修改其他调用逻辑；
5.  **添加缓存模块**：
    - 步骤1：安装Redis依赖：`pip3 install redis`，在服务器上安装并启动Redis服务；
    - 步骤2：在`src/common/`中添加`cache_utils.py`，封装Redis缓存逻辑，提供`set_cache()`/`get_cache()`函数；
    - 步骤3：在`src/core/knowledge_base.py`的`query_artifact_by_name()`中添加缓存逻辑，先查缓存再查数据库；
    - 步骤4：修改INI配置，添加Redis连接信息，重启服务即可，所有客户端无需做任何修改，调用响应速度大幅提升。

### 3. 性能优化（提高服务响应速度，支撑更高并发的多客户端调用，无客户端专属优化步骤）
1.  **异步化优化**：将`requests`（同步HTTP）替换为`aiohttp`（异步HTTP），修改`llm_client.py`中的LLM调用逻辑为异步，FastAPI自动支持异步接口，提高多客户端并发请求处理能力；
2.  **提示词优化**：简化LLM提示词模板，减少不必要的描述，降低LLM响应时间与令牌消耗，提高解析速度；
3.  **数据库优化**：对SQLite/MySQL的`artifact_name`字段建立**索引**，提高模糊查询速度；使用MySQL连接池，提升多客户端并发查询效率；
4.  **负载均衡优化**：部署多个MuseumAgent_Server服务实例，使用Nginx做负载均衡，将多客户端的请求分发至多个实例，支撑更高并发；
5.  **静态资源分离**：将文物3D资源、图片等静态资源分离至阿里云OSS/CDN，服务端仅返回资源路径，减少服务端带宽占用，提高响应速度；
6.  **请求限流优化**：在`src/api/agent_api.py`中添加请求限流逻辑（如基于IP/客户端类型限流），避免恶意请求导致服务崩溃，保障多客户端的正常调用。

## 四、项目核心价值与通用化对接说明
### 1. 服务端核心价值
- **完全解耦**：服务端与所有客户端完全解耦，仅提供标准化的「请求-响应」接口，无需为单个客户端做开发/部署/运维修改；
- **通用化适配**：支持器灵客户端、博物馆官方Web应用、第三方文物展示应用等多端调用，对接成本极低，仅需按标准化格式发送HTTP请求即可；
- **高可用**：服务端独立部署，异常自动重启，日志分级存储，问题快速排查，保障多客户端调用的稳定性；
- **易扩展**：模块化解耦的架构设计，支持LLM服务商、知识库类型、操作指令的无侵入式扩展，无需修改核心代码，仅需配置即可切换；
- **低成本**：基于Python+FastAPI开发，轻量化部署，无需高性能服务器，阿里云入门级Ubuntu服务器即可支撑多客户端调用，降低博物馆的技术投入成本。

### 2. 多客户端通用化对接说明
所有客户端对接MuseumAgent_Server均遵循**统一标准**，无需做适配性开发，对接步骤如下：
1.  **网络调用**：通过**HTTP/HTTPS POST**协议调用服务端接口：`http://服务端IP:端口/api/agent/parse`；
2.  **请求体格式**：标准JSON格式，按`AgentParseRequest`模型填充参数，核心字段`user_input`为必填，其他字段可选；
3.  **响应体解析**：按`AgentParseResponse`模型解析响应，根据`code`判断请求状态，`data`中为标准化指令，直接使用即可；
4.  **异常处理**：根据服务端返回的错误码（400/401/404）做差异化异常处理，提示语直接使用服务端返回的`msg`即可；

**通用对接示例（Python）**：
```python
import requests
import json

url = "http://你的服务端IP:8000/api/agent/parse"
headers = {"Content-Type": "application/json"}
data = {
    "user_input": "讲讲卷体夔纹蟠龙盖罍的纹样",
    "client_type": "qiling",
    "scene_type": "study"
}
response = requests.post(url, headers=headers, json=data, timeout=30)
result = response.json()
if result["code"] == 200:
    command = result["data"]
    # 客户端按标准化指令处理业务
    print(f"标准化指令：{command}")
else:
    print(f"请求失败：{result['msg']}")
```

**对接结论**：所有客户端的对接代码均类似上述示例，仅需修改请求参数与指令处理逻辑，无需关注服务端的内部实现，真正实现「一次开发，多端调用」。