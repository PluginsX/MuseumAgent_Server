# -*- coding: utf-8 -*-
"""配置管理 API：LLM、Embedding、Server"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.common.auth_utils import get_current_user
from src.common.config_utils import get_global_config

router = APIRouter(prefix="/api/admin/config", tags=["配置管理"])


def _mask_api_key(key: Optional[str]) -> str:
    if not key or len(key) < 8:
        return ""
    return key[:4] + "****" + key[-4:] if len(key) > 8 else "****"


# ---------- LLM ----------
class LLMConfigUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


@router.get("/llm")
def get_llm_config(_: dict = Depends(get_current_user)):
    """获取 LLM 配置（API Key 脱敏）"""
    cfg = get_global_config()
    llm = cfg.get("llm", {}).copy()
    if "api_key" in llm and llm["api_key"]:
        llm["api_key"] = _mask_api_key(llm["api_key"])
    llm["version"] = 1
    return llm


@router.get("/llm/raw")
def get_llm_config_raw(_: dict = Depends(get_current_user)):
    """获取 LLM 配置（完整API Key，仅限管理员配置页面使用）"""
    cfg = get_global_config()
    llm = cfg.get("llm", {}).copy()
    llm["version"] = 1
    return llm


@router.put("/llm")
def update_llm_config(
    body: LLMConfigUpdate,
    _: dict = Depends(get_current_user),
):
    """更新 LLM 配置（写入 config.json，无需重启生效）"""
    from src.common.config_utils import update_config_section
    
    # 准备更新的配置
    update_data = {}
    if body.base_url is not None:
        update_data["base_url"] = body.base_url
    if body.api_key is not None and body.api_key.strip():
        update_data["api_key"] = body.api_key.strip()
    if body.model is not None:
        update_data["model"] = body.model
    if body.parameters is not None:
        update_data["parameters"] = body.parameters
    
    # 更新配置并通知监听器
    update_config_section("llm", update_data)
    
    # 返回更新后的配置（API Key 脱敏）
    llm = get_global_config().get("llm", {}).copy()
    if llm.get("api_key"):
        llm["api_key"] = _mask_api_key(llm["api_key"])
    return llm


# ---------- Server ----------
class ServerConfigUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    reload: Optional[bool] = None
    cors_allow_origins: Optional[List[str]] = None
    request_limit: Optional[int] = None
    request_timeout: Optional[int] = None
    ssl_enabled: Optional[bool] = None
    ssl_cert_file: Optional[str] = None
    ssl_key_file: Optional[str] = None
    debug: Optional[bool] = None

@router.get("/server")
def get_server_config(_: dict = Depends(get_current_user)):
    """获取服务器配置"""
    cfg = get_global_config()
    return cfg.get("server", {})

@router.put("/server")
def update_server_config(
    body: ServerConfigUpdate,
    _: dict = Depends(get_current_user),
):
    """更新服务器配置（写入 config.json，需重启生效）"""
    from src.common.config_utils import update_config_section
    
    # 准备更新的配置
    update_data = {}
    if body.host is not None:
        update_data["host"] = body.host
    if body.port is not None:
        update_data["port"] = body.port
    if body.reload is not None:
        update_data["reload"] = body.reload
    if body.cors_allow_origins is not None:
        update_data["cors_allow_origins"] = body.cors_allow_origins
    if body.request_limit is not None:
        update_data["request_limit"] = body.request_limit
    if body.request_timeout is not None:
        update_data["request_timeout"] = body.request_timeout
    if body.ssl_enabled is not None:
        update_data["ssl_enabled"] = body.ssl_enabled
    if body.ssl_cert_file is not None:
        update_data["ssl_cert_file"] = body.ssl_cert_file
    if body.ssl_key_file is not None:
        update_data["ssl_key_file"] = body.ssl_key_file
    if body.debug is not None:
        update_data["debug"] = body.debug
    
    # 更新配置并通知监听器
    update_config_section("server", update_data)
    
    # 返回更新后的配置
    server_config = get_global_config().get("server", {})
    return server_config


# ---------- SRS (SemanticRetrievalSystem) ----------
class SRSConfigUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    timeout: Optional[int] = None
    search_params: Optional[Dict[str, Any]] = None


class STTConfigUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class TTSConfigUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


@router.get("/srs")
def get_srs_config(_: dict = Depends(get_current_user)):
    """获取 SRS 配置（API Key 脱敏）"""
    cfg = get_global_config()
    srs = cfg.get("semantic_retrieval", {}).copy()
    if "api_key" in srs and srs["api_key"]:
        srs["api_key"] = _mask_api_key(srs["api_key"])
    srs["version"] = 1
    return srs


@router.get("/srs/raw")
def get_srs_config_raw(_: dict = Depends(get_current_user)):
    """获取 SRS 配置（完整API Key，仅限管理员配置页面使用）"""
    cfg = get_global_config()
    srs = cfg.get("semantic_retrieval", {}).copy()
    srs["version"] = 1
    return srs


@router.put("/srs")
def update_srs_config(
    body: SRSConfigUpdate,
    _: dict = Depends(get_current_user),
):
    """更新 SRS 配置（写入 config.json，无需重启生效）"""
    from src.common.config_utils import update_config_section
    
    # 准备更新的配置
    update_data = {}
    if body.base_url is not None:
        update_data["base_url"] = body.base_url
    if body.api_key is not None:
        update_data["api_key"] = body.api_key
    if body.timeout is not None:
        update_data["timeout"] = body.timeout
    if body.search_params is not None:
        update_data["search_params"] = body.search_params
    
    # 更新配置并通知监听器
    update_config_section("semantic_retrieval", update_data)
    
    # 尝试重新加载语义检索处理器的配置
    try:
        from src.core.modules.semantic_retrieval_processor import SemanticRetrievalProcessor
        processor = SemanticRetrievalProcessor()
        processor.reload_config()
    except:
        pass
    
    srs = get_global_config().get("semantic_retrieval", {}).copy()
    if "api_key" in srs and srs["api_key"]:
        srs["api_key"] = _mask_api_key(srs["api_key"])
    return srs


# ---------- STT (Speech to Text) ----------
@router.get("/stt")
def get_stt_config(_: dict = Depends(get_current_user)):
    """获取 STT 配置（API Key 脱敏）"""
    cfg = get_global_config()
    stt = cfg.get("stt", {}).copy()
    if "api_key" in stt and stt["api_key"]:
        stt["api_key"] = _mask_api_key(stt["api_key"])
    stt["version"] = 1
    return stt


@router.get("/stt/raw")
def get_stt_config_raw(_: dict = Depends(get_current_user)):
    """获取 STT 配置（完整API Key，仅限管理员配置页面使用）"""
    cfg = get_global_config()
    stt = cfg.get("stt", {}).copy()
    stt["version"] = 1
    return stt


@router.put("/stt")
def update_stt_config(
    body: STTConfigUpdate,
    _: dict = Depends(get_current_user),
):
    """更新 STT 配置（写入 config.json，无需重启生效）"""
    from src.common.config_utils import update_config_section
    
    # 准备更新的配置
    update_data = {}
    if body.base_url is not None:
        update_data["base_url"] = body.base_url
    if body.api_key is not None:
        update_data["api_key"] = body.api_key
    if body.model is not None:
        update_data["model"] = body.model
    if body.parameters is not None:
        update_data["parameters"] = body.parameters
    
    # 更新配置并通知监听器
    update_config_section("stt", update_data)
    
    stt = get_global_config().get("stt", {}).copy()
    if "api_key" in stt and stt["api_key"]:
        stt["api_key"] = _mask_api_key(stt["api_key"])
    return stt


# ---------- TTS (Text to Speech) ----------
@router.get("/tts")
def get_tts_config(_: dict = Depends(get_current_user)):
    """获取 TTS 配置（API Key 脱敏）"""
    cfg = get_global_config()
    tts = cfg.get("tts", {}).copy()
    if "api_key" in tts and tts["api_key"]:
        tts["api_key"] = _mask_api_key(tts["api_key"])
    tts["version"] = 1
    return tts


@router.get("/tts/raw")
def get_tts_config_raw(_: dict = Depends(get_current_user)):
    """获取 TTS 配置（完整API Key，仅限管理员配置页面使用）"""
    cfg = get_global_config()
    tts = cfg.get("tts", {}).copy()
    tts["version"] = 1
    return tts


@router.put("/tts")
def update_tts_config(
    body: TTSConfigUpdate,
    _: dict = Depends(get_current_user),
):
    """更新 TTS 配置（写入 config.json，无需重启生效）"""
    from src.common.config_utils import update_config_section
    
    # 准备更新的配置
    update_data = {}
    if body.base_url is not None:
        update_data["base_url"] = body.base_url
    if body.api_key is not None:
        update_data["api_key"] = body.api_key
    if body.model is not None:
        update_data["model"] = body.model
    if body.parameters is not None:
        update_data["parameters"] = body.parameters
    
    # 更新配置并通知监听器
    update_config_section("tts", update_data)
    
    tts = get_global_config().get("tts", {}).copy()
    if "api_key" in tts and tts["api_key"]:
        tts["api_key"] = _mask_api_key(tts["api_key"])
    return tts


# ---------- Validate / Test ----------
class ValidateLLMRequest(BaseModel):
    base_url: str
    api_key: str
    model: str


@router.post("/llm/validate")
def validate_llm_config(
    body: ValidateLLMRequest,
    _: dict = Depends(get_current_user),
):
    """验证 LLM 配置是否可用"""
    import requests
    url = (body.base_url or "").rstrip("/") + "/chat/completions"
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {body.api_key}", "Content-Type": "application/json"},
            json={"model": body.model, "messages": [{"role": "user", "content": "hi"}]},
            timeout=10,
        )
        if r.status_code == 200:
            return {"valid": True, "message": "连接成功"}
        return {"valid": False, "message": r.text or f"HTTP {r.status_code}"}
    except Exception as e:
        return {"valid": False, "message": str(e)}


class ValidateSRSRequest(BaseModel):
    base_url: str
    api_key: str


@router.post("/srs/validate")
def validate_srs_config(
    body: ValidateSRSRequest,
    _: dict = Depends(get_current_user),
):
    """验证 SRS 配置是否可用"""
    import requests
    url = (body.base_url or "").rstrip("/") + "/health"
    try:
        headers = {"Content-Type": "application/json"}
        if body.api_key:
            headers["Authorization"] = f"Bearer {body.api_key}"
        r = requests.get(
            url,
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            return {"valid": True, "message": "连接成功"}
        return {"valid": False, "message": r.text or f"HTTP {r.status_code}"}
    except Exception as e:
        return {"valid": False, "message": str(e)}


class ValidateSTTRequest(BaseModel):
    base_url: str
    api_key: str
    model: str


@router.post("/stt/validate")
def validate_stt_config(
    body: ValidateSTTRequest,
    _: dict = Depends(get_current_user),
):
    """验证 STT 配置是否可用"""
    # 由于STT是WebSocket API，这里只验证URL格式和API Key是否存在
    try:
        if not body.base_url.startswith("wss://"):
            return {"valid": False, "message": "STT Base URL 必须以 wss:// 开头"}
        if not body.api_key:
            return {"valid": False, "message": "API Key 不能为空"}
        if not body.model:
            return {"valid": False, "message": "Model 不能为空"}
        return {"valid": True, "message": "配置格式正确"}
    except Exception as e:
        return {"valid": False, "message": str(e)}


class ValidateTTSRequest(BaseModel):
    base_url: str
    api_key: str
    model: str


@router.post("/tts/validate")
def validate_tts_config(
    body: ValidateTTSRequest,
    _: dict = Depends(get_current_user),
):
    """验证 TTS 配置是否可用"""
    # 由于TTS是WebSocket API，这里只验证URL格式和API Key是否存在
    try:
        if not body.base_url.startswith("wss://"):
            return {"valid": False, "message": "TTS Base URL 必须以 wss:// 开头"}
        if not body.api_key:
            return {"valid": False, "message": "API Key 不能为空"}
        if not body.model:
            return {"valid": False, "message": "Model 不能为空"}
        return {"valid": True, "message": "配置格式正确"}
    except Exception as e:
        return {"valid": False, "message": str(e)}


# ---------- MySQL Database ----------
class MySQLConfigUpdate(BaseModel):
    db_type: Optional[str] = None
    mysql_host: Optional[str] = None
    mysql_port: Optional[int] = None
    mysql_user: Optional[str] = None
    mysql_password: Optional[str] = None
    mysql_db: Optional[str] = None
    mysql_charset: Optional[str] = None
    mysql_pool_size: Optional[int] = None
    mysql_pool_recycle: Optional[int] = None


@router.get("/mysql")
def get_mysql_config(_: dict = Depends(get_current_user)):
    """获取 MySQL 配置（密码脱敏）"""
    from src.common.config_utils import get_global_ini_config
    ini_config = get_global_ini_config()
    
    mysql_config = {
        "db_type": ini_config.get('database', 'db_type', fallback='sqlite'),
        "mysql_host": ini_config.get('database', 'mysql_host', fallback='127.0.0.1'),
        "mysql_port": ini_config.getint('database', 'mysql_port', fallback=3306),
        "mysql_user": ini_config.get('database', 'mysql_user', fallback='root'),
        "mysql_password": _mask_api_key(ini_config.get('database', 'mysql_password', fallback='')),
        "mysql_db": ini_config.get('database', 'mysql_db', fallback='museum_artifact'),
        "mysql_charset": ini_config.get('database', 'mysql_charset', fallback='utf8mb4'),
        "mysql_pool_size": ini_config.getint('database', 'mysql_pool_size', fallback=10),
        "mysql_pool_recycle": ini_config.getint('database', 'mysql_pool_recycle', fallback=3600),
    }
    return mysql_config


@router.get("/mysql/raw")
def get_mysql_config_raw(_: dict = Depends(get_current_user)):
    """获取 MySQL 配置（完整密码，仅限管理员配置页面使用）"""
    from src.common.config_utils import get_global_ini_config
    ini_config = get_global_ini_config()
    
    mysql_config = {
        "db_type": ini_config.get('database', 'db_type', fallback='sqlite'),
        "mysql_host": ini_config.get('database', 'mysql_host', fallback='127.0.0.1'),
        "mysql_port": ini_config.getint('database', 'mysql_port', fallback=3306),
        "mysql_user": ini_config.get('database', 'mysql_user', fallback='root'),
        "mysql_password": ini_config.get('database', 'mysql_password', fallback=''),
        "mysql_db": ini_config.get('database', 'mysql_db', fallback='museum_artifact'),
        "mysql_charset": ini_config.get('database', 'mysql_charset', fallback='utf8mb4'),
        "mysql_pool_size": ini_config.getint('database', 'mysql_pool_size', fallback=10),
        "mysql_pool_recycle": ini_config.getint('database', 'mysql_pool_recycle', fallback=3600),
    }
    return mysql_config


@router.put("/mysql")
def update_mysql_config(
    body: MySQLConfigUpdate,
    _: dict = Depends(get_current_user),
):
    """更新 MySQL 配置（写入 config.ini，需重启生效）"""
    from src.common.config_utils import get_global_ini_config, save_ini_config
    import os
    
    ini_config = get_global_ini_config()
    
    # 更新配置
    if body.db_type is not None:
        ini_config.set('database', 'db_type', body.db_type)
    if body.mysql_host is not None:
        ini_config.set('database', 'mysql_host', body.mysql_host)
    if body.mysql_port is not None:
        ini_config.set('database', 'mysql_port', str(body.mysql_port))
    if body.mysql_user is not None:
        ini_config.set('database', 'mysql_user', body.mysql_user)
    if body.mysql_password is not None:
        ini_config.set('database', 'mysql_password', body.mysql_password)
    if body.mysql_db is not None:
        ini_config.set('database', 'mysql_db', body.mysql_db)
    if body.mysql_charset is not None:
        ini_config.set('database', 'mysql_charset', body.mysql_charset)
    if body.mysql_pool_size is not None:
        ini_config.set('database', 'mysql_pool_size', str(body.mysql_pool_size))
    if body.mysql_pool_recycle is not None:
        ini_config.set('database', 'mysql_pool_recycle', str(body.mysql_pool_recycle))
    
    # 保存配置
    save_ini_config(ini_config)
    
    # 返回更新后的配置（密码脱敏）
    mysql_config = {
        "db_type": ini_config.get('database', 'db_type', fallback='sqlite'),
        "mysql_host": ini_config.get('database', 'mysql_host', fallback='127.0.0.1'),
        "mysql_port": ini_config.getint('database', 'mysql_port', fallback=3306),
        "mysql_user": ini_config.get('database', 'mysql_user', fallback='root'),
        "mysql_password": _mask_api_key(ini_config.get('database', 'mysql_password', fallback='')),
        "mysql_db": ini_config.get('database', 'mysql_db', fallback='museum_artifact'),
        "mysql_charset": ini_config.get('database', 'mysql_charset', fallback='utf8mb4'),
        "mysql_pool_size": ini_config.getint('database', 'mysql_pool_size', fallback=10),
        "mysql_pool_recycle": ini_config.getint('database', 'mysql_pool_recycle', fallback=3600),
    }
    return mysql_config


class ValidateMySQLRequest(BaseModel):
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_db: str


@router.post("/mysql/validate")
def validate_mysql_config(
    body: ValidateMySQLRequest,
    _: dict = Depends(get_current_user),
):
    """验证 MySQL 配置是否可用"""
    try:
        from sqlalchemy import create_engine, text
        
        # 构建连接URL
        url = f"mysql+pymysql://{body.mysql_user}:{body.mysql_password}@{body.mysql_host}:{body.mysql_port}/{body.mysql_db}?charset=utf8mb4"
        
        # 尝试连接
        engine = create_engine(url, pool_pre_ping=True, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        return {"valid": True, "message": "MySQL连接成功"}
    except Exception as e:
        return {"valid": False, "message": f"MySQL连接失败: {str(e)}"}



