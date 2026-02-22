# -*- coding: utf-8 -*-
"""
API网关层实现
根据优化架构设计实现统一的API网关
负责请求路由、认证授权、协议转换等功能
"""
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware

from src.common.config_utils import get_config_by_key, get_global_config
from src.common.enhanced_logger import get_enhanced_logger
from src.common.auth_utils import decode_access_token
from src.api.auth_api import get_current_user
from src.services.registry import service_registry
from src.ws import agent_stream_router


class APIGateway:
    """API网关核心类"""
    
    def __init__(self, auto_init: bool = True):
        """初始化API网关"""
        self.logger = get_enhanced_logger()
        self.app = FastAPI(
            title="MuseumAgent API Gateway",
            description="博物馆智能体服务API网关",
            version="1.0.0"
        )
        if auto_init:
            self._setup_middleware()
            self._register_services()
            self._setup_routes()
    
    def initialize(self):
        """手动初始化网关组件"""
        self._setup_middleware()
        self._register_services()
        self._setup_routes()
    
    def _setup_middleware(self):
        """设置中间件"""
        # 加载CORS配置
        try:
            allow_origins = get_config_by_key("server", "cors_allow_origins")
            admin_cfg = get_global_config().get("admin_panel", {})
            session_secret = admin_cfg.get("session_secret", "change-me-in-production")
            session_max_age = admin_cfg.get("session_max_age", 86400)
        except Exception:
            allow_origins = ["*"]
            session_secret = "change-me-in-production"
            session_max_age = 86400

        # 检查是否启用了SSL
        try:
            ssl_enabled = get_config_by_key("server", "ssl_enabled")
        except Exception:
            ssl_enabled = False
        
        # 会话中间件
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=session_secret,
            max_age=session_max_age,
            same_site="lax",
            https_only=ssl_enabled,
        )
        
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _register_services(self):
        """注册内部服务"""
        # 注册文本处理服务
        from src.services.text_processing_service import TextProcessingService
        service_registry.register_service("text_processing", TextProcessingService())
        
        # 注册音频处理服务
        from src.services.audio_processing_service import AudioProcessingService
        service_registry.register_service("audio_processing", AudioProcessingService())
        
        # 注册语音通话服务
        from src.services.voice_call_service import VoiceCallService
        service_registry.register_service("voice_call", VoiceCallService())
        
        # 注册会话管理服务
        from src.services.session_service import SessionService
        service_registry.register_service("session", SessionService())
        
        self.logger.sys.info("All services registered to gateway")
    
    def _setup_routes(self):
        """设置路由"""
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "gateway": "api_gateway", "timestamp": "now"}
        
        # Favicon图标（避免404错误）
        @self.app.get("/favicon.ico")
        async def favicon():
            from fastapi.responses import Response
            return Response(content="", media_type="image/x-icon")
        
        # 文本处理路由
        @self.app.post("/api/text/process")
        async def process_text(request: Dict[str, Any], token: str = Depends(get_current_user)):
            """处理文本请求"""
            try:
                service = service_registry.get_service("text_processing")
                result = await service.process_text(request, token)
                return result
            except Exception as e:
                self.logger.api.error('Text processing failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"文本处理失败: {str(e)}")
        
        # 音频处理路由
        @self.app.post("/api/audio/stt")
        async def audio_to_text(request: Dict[str, Any], token: str = Depends(get_current_user)):
            """音频转文本"""
            try:
                service = service_registry.get_service("audio_processing")
                result = await service.stt_convert(request, token)
                return result
            except Exception as e:
                self.logger.api.error('Audio to text failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"音频转文本失败: {str(e)}")
        
        @self.app.post("/api/audio/tts")
        async def text_to_audio(request: Dict[str, Any], token: str = Depends(get_current_user)):
            """文本转音频"""
            try:
                service = service_registry.get_service("audio_processing")
                result = await service.tts_convert(request, token)
                return result
            except Exception as e:
                self.logger.api.error('Text to audio failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"文本转音频失败: {str(e)}")
        
        # 语音通话路由
        @self.app.post("/api/voice/start")
        async def start_voice_call(request: Dict[str, Any], token: str = Depends(get_current_user)):
            """启动语音通话"""
            try:
                service = service_registry.get_service("voice_call")
                result = await service.start_call(request, token)
                return result
            except Exception as e:
                self.logger.api.error('Start voice call failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"启动语音通话失败: {str(e)}")
        
        @self.app.post("/api/voice/end")
        async def end_voice_call(call_id: str, token: str = Depends(get_current_user)):
            """结束语音通话"""
            try:
                service = service_registry.get_service("voice_call")
                result = await service.end_call(call_id, token)
                return result
            except Exception as e:
                self.logger.api.error('End voice call failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"结束语音通话失败: {str(e)}")
        
        # 会话管理路由
        @self.app.post("/api/auth/login")
        async def login(credentials: Dict[str, str]):
            """用户登录"""
            try:
                service = service_registry.get_service("session")
                result = await service.login(credentials)
                return result
            except Exception as e:
                self.logger.api.error('Login failed', {'error': str(e)})
                raise HTTPException(status_code=401, detail=f"登录失败: {str(e)}")

        # 兼容性登录路由 - 为旧版前端提供兼容的返回格式
        @self.app.post("/api/auth/login_legacy")
        async def login_legacy(credentials: Dict[str, str]):
            """用户登录 - 兼容旧版前端格式"""
            try:
                service = service_registry.get_service("session")
                result = await service.login(credentials)
                
                # 如果登录成功，转换为兼容旧版前端的格式
                if result.get("code") == 200 and result.get("data"):
                    data = result["data"]
                    # 返回扁平化的结构，兼容旧版前端
                    legacy_result = {
                        "access_token": data.get("access_token", ""),
                        "token_type": data.get("token_type", "bearer"),
                        "session_id": data.get("session_id", ""),
                        "expires_in": data.get("expires_in", 3600),
                        "success": True
                    }
                    return legacy_result
                else:
                    # 如果登录失败，也保持兼容格式
                    return {
                        "success": False,
                        "error": result.get("msg", "登录失败"),
                        "error_code": result.get("code", 500)
                    }
            except Exception as e:
                self.logger.api.error('Login failed', {'error': str(e)})
                return {
                    "success": False,
                    "error": str(e),
                    "error_code": 401
                }
        
        @self.app.get("/api/auth/me")
        async def get_user_info(token: str = Depends(get_current_user)):
            """获取用户信息"""
            try:
                service = service_registry.get_service("session")
                result = await service.get_user_info(token)
                return result
            except Exception as e:
                self.logger.api.error('Get user info failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")
        
        # 会话管理路由
        @self.app.post("/api/session/register")
        async def register_session(request: Dict[str, Any], credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
            """注册会话"""
            try:
                self.logger.sess.debug('Session registration request', {'request': request})
                
                if not credentials:
                    raise HTTPException(status_code=401, detail="未提供认证信息")
                
                # 直接使用原始token
                token = credentials.credentials
                
                service = service_registry.get_service("session")
                self.logger.api.debug('Session service retrieved', {'service': service is not None})
                
                # 提取用户信息
                user_info = await service.get_user_info(token)
                self.logger.api.debug('User information retrieved', {'user_info': user_info})
                
                if user_info.get("code") != 200:
                    raise HTTPException(status_code=401, detail="无效的令牌")
                
                username = user_info["data"]["username"]
                
                # 从请求中提取函数定义
                client_metadata = request.get("client_metadata", {})
                functions = request.get("functions", [])
                
                # 生成会话ID
                import secrets
                session_id = f"sess_{secrets.token_hex(16)}"
                
                # 使用strict_session_manager注册会话（包含函数定义）
                from src.session.strict_session_manager import strict_session_manager
                session = strict_session_manager.register_session_with_functions(
                    session_id=session_id,
                    client_metadata=client_metadata,
                    functions=functions
                )
                
                self.logger.api.debug('Session registered with strict manager', 
                                 {'session_id': session_id, 'function_count': len(functions)})
                
                # 返回会话信息
                result = {
                    "code": 200,
                    "msg": "会话注册成功",
                    "data": {
                        "session_id": session_id,
                        "username": username,
                        "registered_at": "now"
                    },
                    "timestamp": "now"
                }
                
                self.logger.api.debug('Session registration response', {'result': result})
                return result
            except HTTPException:
                raise
            except Exception as e:
                self.logger.api.error('Session register failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"会话注册失败: {str(e)}")
        
        @self.app.post("/api/session/validate")
        async def validate_session(request: Dict[str, Any], session_id: str = Header(None, alias="session_id"), credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
            """验证会话"""
            try:
                # 优先从header获取session_id，如果没有则从请求体中获取
                effective_session_id = session_id or request.get("session_id")
                if not effective_session_id:
                    raise HTTPException(status_code=400, detail="缺少会话ID")
                
                service = service_registry.get_service("session")
                is_valid = await service.validate_session(effective_session_id)
                
                if not is_valid:
                    raise HTTPException(status_code=401, detail="会话无效或已过期")
                
                result = {
                    "code": 200,
                    "msg": "会话验证成功",
                    "data": {
                        "session_id": effective_session_id,
                        "valid": True
                    },
                    "timestamp": "now"
                }
                
                return result
            except HTTPException:
                raise
            except Exception as e:
                self.logger.api.error('Session validate failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"会话验证失败: {str(e)}")
        
        @self.app.post("/api/session/disconnect")
        async def disconnect_session(request: Dict[str, Any], session_id: str = Header(None, alias="session_id"), credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
            """断开会话"""
            try:
                # 优先从header获取session_id，如果没有则从请求体中获取
                effective_session_id = session_id or request.get("session_id")
                if not effective_session_id:
                    raise HTTPException(status_code=400, detail="缺少会话ID")
                
                # 在实际应用中，可能会在这里清理会话数据
                # 目前只是返回成功响应
                result = {
                    "code": 200,
                    "msg": "会话断开成功",
                    "data": {
                        "session_id": effective_session_id
                    },
                    "timestamp": "now"
                }
                
                return result
            except HTTPException:
                raise
            except Exception as e:
                self.logger.api.error('Disconnect session failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"断开会话失败: {str(e)}")
        
        # 智能体解析路由
        from src.models.request_models import AgentParseRequest
        from src.core.command_generator import CommandGenerator
        
        @self.app.post("/api/agent/parse")
        async def parse_agent(request: AgentParseRequest, session_id: str = Header(None)):
            """智能体解析接口 - 接收用户自然语言输入，返回标准化文物操作指令"""
            try:
                logger = get_logger()
                
                # 验证会话是否已注册
                if session_id:
                    service = service_registry.get_service("session")
                    is_valid = await service.validate_session(session_id)
                    if not is_valid:
                        raise HTTPException(status_code=401, detail="会话无效或未注册")
                
                # 记录客户端消息接收
                ui_preview = request.user_input[:50] + ("..." if len(request.user_input) > 50 else "")
                self.logger.api.info("User message received", 
                                   {'session_id': session_id, 'preview': ui_preview})
                
                # 记录处理开始
                self.logger.api.info('Starting to process user request', 
                              {'client_type': request.client_type, 'scene_type': request.scene_type})
                
                # 调用指令生成器
                generator = CommandGenerator()
                
                command_dict = generator.generate_standard_command(
                    user_input=request.user_input,
                    scene_type=request.scene_type or "public",
                    session_id=session_id  # 传递会话ID
                )
                
                # 记录处理完成
                self.logger.api.info('Request processing completed', 
                              {'operation': command_dict.get('operation'), 
                               'artifact_name': command_dict.get('artifact_name')})
                
                # 记录响应发送
                self.logger.api.info('Sending agent response to client', command_dict)
                
                return command_dict
            except HTTPException:
                raise
            except Exception as e:
                self.logger.api.error('Agent parse failed', {'error': str(e)})
                raise HTTPException(status_code=500, detail=f"智能体解析失败: {str(e)}")
        
        # 包含 WebSocket 通信路由（协议：docs/CommunicationProtocol_CS.md）
        self.app.include_router(agent_stream_router)
        
        # 包含会话管理API路由
        from src.api.session_api import router as session_router
        self.app.include_router(session_router)
        
        # 包含管理员API路由
        from src.api.auth_api import router as auth_router
        from src.api.config_api import router as config_router
        from src.api.monitor_api import router as monitor_router
        from src.api.users_api import router as users_router
        from src.api.client_api import router as client_router
        from src.api.session_config_api import router as session_config_router
        from src.api.database_api import database_router
        
        self.app.include_router(auth_router)
        self.app.include_router(config_router)
        self.app.include_router(monitor_router)
        self.app.include_router(users_router)
        self.app.include_router(client_router)
        self.app.include_router(session_config_router)
        self.app.include_router(database_router)
        
        # 包含内部管理员API路由（仅内部使用）
        from src.api.internal_admin_api import internal_router
        self.app.include_router(internal_router)
        
        # 挂载管理员控制面板：优先提供新版 SPA 静态资源，不存在则使用旧版 HTML
        import os
        from pathlib import Path
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        
        _spa_dir = Path(__file__).resolve().parent.parent.parent / "control-panel" / "dist"
        if _spa_dir.exists():
            # 挂载静态文件
            self.app.mount("/Control/static", StaticFiles(directory=str(_spa_dir)), name="control-static")
            
            # 处理SPA路由 - 对于所有Control下的路径，如果文件不存在则返回index.html
            @self.app.get("/Control/{full_path:path}")
            async def serve_spa(full_path: str):
                file_path = _spa_dir / full_path
                if file_path.exists() and file_path.is_file():
                    return FileResponse(str(file_path))
                else:
                    # 对于不存在的路径，返回index.html让前端路由处理
                    return FileResponse(str(_spa_dir / "index.html"))
            
            # 根路径特殊处理
            @self.app.get("/Control")
            async def serve_control_root():
                return FileResponse(str(_spa_dir / "index.html"))
        else:
            from src.api.admin_api import router as admin_router
            self.app.include_router(admin_router)
    
    def get_app(self):
        """获取FastAPI应用实例"""
        return self.app
# app将通过get_app()方法在main.py中获取