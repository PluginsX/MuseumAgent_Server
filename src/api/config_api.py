# -*- coding: utf-8 -*-
"""配置管理 API：LLM、Embedding、Server"""
import json
from typing import Any, Dict, Optional

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
    """更新 LLM 配置（写入 config.json，需重启生效）"""
    import os
    from src.common.config_utils import DEFAULT_JSON_CONFIG_PATH
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.normpath(os.path.join(base_dir, DEFAULT_JSON_CONFIG_PATH))
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    llm = data.setdefault("llm", {})
    if body.base_url is not None:
        llm["base_url"] = body.base_url
    if body.api_key is not None and body.api_key.strip():
        llm["api_key"] = body.api_key.strip()
    if body.model is not None:
        llm["model"] = body.model
    if body.parameters is not None:
        llm["parameters"] = {**(llm.get("parameters") or {}), **body.parameters}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    from src.common.config_utils import load_config
    load_config()
    llm = get_global_config().get("llm", {}).copy()
    if llm.get("api_key"):
        llm["api_key"] = _mask_api_key(llm["api_key"])
    return llm


# ---------- Server ----------
@router.get("/server")
def get_server_config(_: dict = Depends(get_current_user)):
    """获取服务器配置"""
    cfg = get_global_config()
    return cfg.get("server", {})


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



