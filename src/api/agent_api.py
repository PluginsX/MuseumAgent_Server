# -*- coding: utf-8 -*-
"""
智能体核心API - 定义/api/agent/parse标准化接口
"""
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.config_utils import get_config_by_key
from src.common.log_utils import get_logger
from src.common.response_utils import (
    data_none_response,
    fail_response,
    success_response,
)
from src.core.command_generator import CommandGenerator
from src.models.request_models import AgentParseRequest
from src.models.response_models import AgentParseResponse, StandardCommand

# 初始化FastAPI应用
app = FastAPI(
    title="MuseumAgent 博物馆智能体服务",
    description="博物馆文物智能解析服务，支持多客户端标准化对接",
    version="1.0.0",
)

# 配置CORS（必须在应用创建后、启动前添加）
try:
    from src.common.config_utils import load_config, get_global_config
    load_config()
    allow_origins = get_config_by_key("server", "cors_allow_origins")
except Exception:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局CommandGenerator实例（延迟初始化）
_command_generator: CommandGenerator | None = None


def _get_command_generator() -> CommandGenerator:
    """获取CommandGenerator单例"""
    global _command_generator
    if _command_generator is None:
        _command_generator = CommandGenerator()
    return _command_generator


@app.get("/", tags=["健康检查"])
async def root():
    """服务健康检查"""
    return {"status": "ok", "service": "MuseumAgent", "version": "1.0.0"}


@app.post(
    "/api/agent/parse",
    response_model=AgentParseResponse,
    summary="智能体解析接口",
    description="接收用户自然语言输入，返回标准化文物操作指令",
)
async def parse_agent(request: AgentParseRequest):
    """
    博物馆智能体核心解析接口
    
    - **user_input**: 用户自然语言输入（必填）
    - **client_type**: 客户端类型，用于日志统计（可选）
    - **spirit_id**: 器灵ID（可选）
    - **scene_type**: 场景类型 study/leisure/public（可选，默认public）
    """
    logger = get_logger()
    
    try:
        # 记录访问日志
        ui_preview = request.user_input[:50] + ("..." if len(request.user_input) > 50 else "")
        logger.info(
            f"请求时间={datetime.now().isoformat()} "
            f"client_type={request.client_type or 'unknown'} "
            f"user_input={ui_preview} "
            f"scene_type={request.scene_type}"
        )
        
        # 调用指令生成器
        generator = _get_command_generator()
        command_dict = generator.generate_standard_command(
            user_input=request.user_input,
            scene_type=request.scene_type or "public"
        )
        
        # 构造StandardCommand
        command = StandardCommand(**command_dict)
        
        # 返回成功响应
        return success_response(data=command.model_dump())
        
    except ValueError as e:
        logger.warning(f"参数/解析异常: {str(e)}, 请求: user_input={request.user_input}")
        return fail_response(msg=str(e))
        
    except RuntimeError as e:
        err_msg = str(e)
        if "未查询到相关文物" in err_msg or "数据不存在" in err_msg:
            logger.info(f"知识库无匹配: {err_msg}")
            return data_none_response(msg=err_msg)
        logger.error(f"业务异常: {err_msg}, 请求: {request.model_dump()}")
        return fail_response(msg=err_msg)
        
    except Exception as e:
        logger.exception(f"未知异常: {str(e)}, 请求: {request.model_dump()}")
        return fail_response(msg=f"请求处理失败: {str(e)}")
