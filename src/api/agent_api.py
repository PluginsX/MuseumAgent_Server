# -*- coding: utf-8 -*-
"""
智能体核心API - 定义/api/agent/parse标准化接口
"""
import json
from datetime import datetime

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.common.config_utils import get_config_by_key
from src.common.log_utils import get_logger
from src.common.log_formatter import log_step, log_communication
from src.common.response_utils import (
    data_none_response,
    fail_response,
    success_response,
)
from src.core.command_generator import CommandGenerator
from src.models.request_models import AgentParseRequest

# 初始化FastAPI应用
app = FastAPI(
    title="MuseumAgent 博物馆智能体服务",
    description="博物馆文物智能解析服务，支持多客户端标准化对接",
    version="1.0.0",
)

# 配置（必须在应用创建后、启动前添加）
try:
    from src.common.config_utils import load_config, get_global_config
    load_config()
    allow_origins = get_config_by_key("server", "cors_allow_origins")
    admin_cfg = get_global_config().get("admin_panel", {})
    session_secret = admin_cfg.get("session_secret", "change-me-in-production")
    session_max_age = admin_cfg.get("session_max_age", 86400)
except Exception:
    allow_origins = ["*"]
    session_secret = "change-me-in-production"
    session_max_age = 86400

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    max_age=session_max_age,
    same_site="lax",
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载管理员控制面板：优先提供新版 SPA 静态资源，不存在则使用旧版 HTML
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_spa_dir = Path(__file__).resolve().parent.parent.parent / "control-panel" / "dist"
if _spa_dir.exists():
    # 挂载静态文件
    app.mount("/Control/static", StaticFiles(directory=str(_spa_dir)), name="control-static")
    
    # 处理SPA路由 - 对于所有Control下的路径，如果文件不存在则返回index.html
    @app.get("/Control/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = _spa_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        else:
            # 对于不存在的路径，返回index.html让前端路由处理
            return FileResponse(str(_spa_dir / "index.html"))
    
    # 根路径特殊处理
    @app.get("/Control")
    async def serve_control_root():
        return FileResponse(str(_spa_dir / "index.html"))
else:
    from src.api.admin_api import router as admin_router
    app.include_router(admin_router)

# 挂载新版 API（JWT 认证）
from src.api.auth_api import router as auth_router
from src.api.config_api import router as config_router
from src.api.monitor_api import router as monitor_router
from src.api.users_api import router as users_router
from src.api.session_api import router as session_router
from src.api.client_api import router as client_router
from src.api.session_config_api import router as session_config_router
from src.api.function_api import router as function_router  # OpenAI标准函数API

app.include_router(auth_router)
app.include_router(config_router)
app.include_router(monitor_router)
app.include_router(users_router)
app.include_router(session_router)
app.include_router(client_router)
app.include_router(session_config_router)
app.include_router(function_router)  # 添加OpenAI标准函数API路由


@app.on_event("startup")
def startup_event():
    """启动时初始化数据库并创建默认管理员"""
    try:
        from src.db.seed import seed_admin
        seed_admin()
    except Exception:
        pass

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
    # 移除response_model以避免FastAPI自动转换StandardCommand模型
    # response_model=AgentParseResponse,
    summary="智能体解析接口",
    description="接收用户自然语言输入，返回标准化文物操作指令",
)
async def parse_agent(request: AgentParseRequest, session_id: str = Header(None)):
    """
    博物馆智能体核心解析接口
    
    - **user_input**: 用户自然语言输入（必填）
    - **client_type**: 客户端类型，用于日志统计（可选）
    - **spirit_id**: 器灵ID（可选）
    - **scene_type**: 场景类型 study/leisure/public（可选，默认public）
    """
    logger = get_logger()
    
    try:
        # 记录客户端消息接收
        ui_preview = request.user_input[:50] + ("..." if len(request.user_input) > 50 else "")
        print(log_communication('CLIENT', 'RECEIVE', 'User Message', 
                               request.dict(), 
                               {'session_id': session_id, 'preview': ui_preview}))
        
        # 记录处理开始
        print(log_step('API', 'START', '开始处理用户请求', 
                      {'client_type': request.client_type, 'scene_type': request.scene_type}))
        
        # 调用指令生成器（使用严格会话管理）
        from src.session.strict_session_manager import strict_session_manager
        generator = _get_command_generator()
        
        # 严格验证会话
        if session_id:
            session = strict_session_manager.validate_session(session_id)
            if not session:
                print(log_step('SESSION', 'DENY', '会话验证失败，拒绝请求', 
                              {'session_id': session_id}))
                return fail_response(msg="会话不存在或已过期，请重新注册")
            print(log_step('SESSION', 'ALLOW', '会话验证通过', 
                          {'session_id': session_id[:8]}))
        
        command_dict = generator.generate_standard_command(
            user_input=request.user_input,
            scene_type=request.scene_type or "public",
            session_id=session_id  # 传递会话ID
        )
        
        # 输出CommandGenerator返回的数据
        print(f"[DEBUG] API层接收到CommandGenerator返回的数据:")
        print(json.dumps(command_dict, indent=2, ensure_ascii=False))
        
        # 记录处理完成
        print(log_step('API', 'SUCCESS', '请求处理完成', 
                      {'operation': command_dict.get('operation'), 
                       'artifact_name': command_dict.get('artifact_name')}))
        
        # 记录响应发送
        print(log_communication('CLIENT', 'SEND', 'Agent Response', command_dict))
        
        # 输出LLM原始响应（直通转发前）
        print(f"[DEBUG] LLM原始响应准备直通转发:")
        print(json.dumps(command_dict, indent=2, ensure_ascii=False))
        
        # 构造最小化的API响应格式，保持LLM原始数据完整性
        print(f"[DIRECT] 构造直通转发响应")
        
        direct_response = {
            "code": 200,
            "msg": "请求处理成功",
            "data": command_dict
        }
        
        print(f"[DIRECT] 直接转发LLM原始数据给客户端")
        return direct_response
        
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
