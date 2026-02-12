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
from starlette.middleware.sessions import SessionMiddleware

from src.common.config_utils import get_config_by_key, get_global_config
from src.common.log_utils import get_logger
from src.common.auth_utils import decode_access_token
from src.api.auth_api import get_current_user
from src.services.registry import service_registry
from src.api.websocket_api import router as websocket_router


class APIGateway:
    """API网关核心类"""
    
    def __init__(self, auto_init: bool = True):
        """初始化API网关"""
        self.logger = get_logger()
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

        # 会话中间件
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=session_secret,
            max_age=session_max_age,
            same_site="lax",
            https_only=False,
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
        
        self.logger.info("所有服务已注册到网关")
    
    def _setup_routes(self):
        """设置路由"""
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "gateway": "api_gateway", "timestamp": "now"}
        
        # 文本处理路由
        @self.app.post("/api/text/process")
        async def process_text(request: Dict[str, Any], token: str = Depends(get_current_user)):
            """处理文本请求"""
            try:
                service = service_registry.get_service("text_processing")
                result = await service.process_text(request, token)
                return result
            except Exception as e:
                self.logger.error(f"文本处理失败: {str(e)}")
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
                self.logger.error(f"音频转文本失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"音频转文本失败: {str(e)}")
        
        @self.app.post("/api/audio/tts")
        async def text_to_audio(request: Dict[str, Any], token: str = Depends(get_current_user)):
            """文本转音频"""
            try:
                service = service_registry.get_service("audio_processing")
                result = await service.tts_convert(request, token)
                return result
            except Exception as e:
                self.logger.error(f"文本转音频失败: {str(e)}")
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
                self.logger.error(f"启动语音通话失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"启动语音通话失败: {str(e)}")
        
        @self.app.post("/api/voice/end")
        async def end_voice_call(call_id: str, token: str = Depends(get_current_user)):
            """结束语音通话"""
            try:
                service = service_registry.get_service("voice_call")
                result = await service.end_call(call_id, token)
                return result
            except Exception as e:
                self.logger.error(f"结束语音通话失败: {str(e)}")
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
                self.logger.error(f"登录失败: {str(e)}")
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
                self.logger.error(f"登录失败: {str(e)}")
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
                self.logger.error(f"获取用户信息失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")
        
        # 智能体解析路由
        from src.models.request_models import AgentParseRequest
        from src.core.command_generator import CommandGenerator
        
        @self.app.post("/api/agent/parse")
        async def parse_agent(request: AgentParseRequest, session_id: str = Header(None)):
            """智能体解析接口 - 接收用户自然语言输入，返回标准化文物操作指令"""
            try:
                logger = get_logger()
                
                # 记录客户端消息接收
                ui_preview = request.user_input[:50] + ("..." if len(request.user_input) > 50 else "")
                from src.common.log_formatter import log_communication, log_step
                print(log_communication('CLIENT', 'RECEIVE', 'User Message', 
                                       request.dict(), 
                                       {'session_id': session_id, 'preview': ui_preview}))
                
                # 记录处理开始
                print(log_step('API', 'START', '开始处理用户请求', 
                              {'client_type': request.client_type, 'scene_type': request.scene_type}))
                
                # 调用指令生成器
                generator = CommandGenerator()
                
                command_dict = generator.generate_standard_command(
                    user_input=request.user_input,
                    scene_type=request.scene_type or "public",
                    session_id=session_id  # 传递会话ID
                )
                
                # 记录处理完成
                print(log_step('API', 'SUCCESS', '请求处理完成', 
                              {'operation': command_dict.get('operation'), 
                               'artifact_name': command_dict.get('artifact_name')}))
                
                # 记录响应发送
                print(log_communication('CLIENT', 'SEND', 'Agent Response', command_dict))
                
                return command_dict
            except Exception as e:
                self.logger.error(f"智能体解析失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"智能体解析失败: {str(e)}")
        
        # 包含WebSocket API路由
        self.app.include_router(websocket_router)
    
    def get_app(self):
        """获取FastAPI应用实例"""
        return self.app


# 服务注册表
class ServiceRegistry:
    """服务注册表"""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
    
    def register_service(self, name: str, service: Any):
        """注册服务"""
        self.services[name] = service
    
    def get_service(self, name: str) -> Optional[Any]:
        """获取服务"""
        return self.services.get(name)
    
    def unregister_service(self, name: str):
        """注销服务"""
        if name in self.services:
            del self.services[name]


# 全局服务注册表实例
service_registry = ServiceRegistry()

# API网关将在main.py中初始化，此处不创建实例
# app将通过get_app()方法在main.py中获取