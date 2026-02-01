# -*- coding: utf-8 -*-
"""
管理员控制面板 API - /Control
"""
import io
import random
import string
import time
from typing import Tuple

import bcrypt
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from PIL import Image, ImageDraw, ImageFont

from src.common.config_utils import get_global_config, get_global_ini_config

router = APIRouter(prefix="/Control", tags=["管理员控制面板"])

# 依赖：检查是否已登录
def require_admin(request: Request) -> bool:
    return request.session.get("admin_logged_in", False)


def _get_admin_config():
    """获取管理员配置"""
    try:
        cfg = get_global_ini_config()
        if not cfg.has_section("admin"):
            return {"username": "admin", "password_hash": ""}
        return {
            "username": cfg.get("admin", "admin_username", fallback="admin"),
            "password_hash": cfg.get("admin", "admin_password_hash", fallback=""),
        }
    except Exception:
        return {"username": "admin", "password_hash": ""}


def _verify_captcha(request: Request, user_input: str) -> Tuple[bool, str]:
    """验证验证码"""
    stored = request.session.get("captcha_answer")
    expiry = request.session.get("captcha_expiry", 0)
    if not stored:
        return False, "验证码已过期，请刷新"
    if time.time() > expiry:
        return False, "验证码已过期，请刷新"
    if (user_input or "").strip().lower() != str(stored).lower():
        return False, "验证码错误"
    return True, ""


def _gen_captcha_image(text: str) -> bytes:
    """生成验证码图片"""
    w, h = 120, 40
    img = Image.new("RGB", (w, h), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    # 干扰线
    for _ in range(4):
        draw.line(
            (random.randint(0, w), random.randint(0, h), random.randint(0, w), random.randint(0, h)),
            fill=(180, 180, 180),
            width=1,
        )
    # 绘制文字（多平台字体回退）
    font = None
    for path in [
        "arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        try:
            font = ImageFont.truetype(path, 24)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    for i, c in enumerate(text):
        x = 20 + i * 24
        y = random.randint(5, 12)
        draw.text((x, y), c, fill=(50, 50, 50), font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


LOGIN_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理员登录 - MuseumAgent</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: "Segoe UI", system-ui, sans-serif; background: #1a1d24; min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .card {{ background: #252830; border-radius: 12px; padding: 36px; width: 100%; max-width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }}
        h1 {{ color: #e8eaed; font-size: 1.5rem; margin-bottom: 24px; text-align: center; }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; color: #9aa0a6; font-size: 0.875rem; margin-bottom: 6px; }}
        input[type="text"], input[type="password"] {{ width: 100%; padding: 12px; border: 1px solid #3c4043; border-radius: 8px; background: #202124; color: #e8eaed; font-size: 1rem; }}
        input:focus {{ outline: none; border-color: #8ab4f8; }}
        .captcha-row {{ display: flex; gap: 12px; align-items: center; }}
        .captcha-row input {{ flex: 1; }}
        .captcha-img {{ height: 40px; cursor: pointer; border-radius: 6px; }}
        .btn {{ width: 100%; padding: 12px; background: #8ab4f8; color: #1a1d24; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }}
        .btn:hover {{ background: #aecbfa; }}
        .error {{ color: #f28b82; font-size: 0.875rem; margin-top: 8px; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>管理员控制面板</h1>
        <form method="post" action="/Control/api/login">
            <div class="form-group">
                <label>用户名</label>
                <input type="text" name="username" required autocomplete="username">
            </div>
            <div class="form-group">
                <label>密码</label>
                <input type="password" name="password" required autocomplete="current-password">
            </div>
            <div class="form-group">
                <label>验证码</label>
                <div class="captcha-row">
                    <input type="text" name="captcha" placeholder="请输入验证码" required maxlength="6" autocomplete="off">
                    <img src="/Control/api/captcha?t={ts}" alt="验证码" class="captcha-img" title="点击刷新" onclick="this.src='/Control/api/captcha?t='+Date.now()">
                </div>
            </div>
            <div class="form-group">
                <button type="submit" class="btn">登 录</button>
            </div>
            {error_html}
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>控制面板 - MuseumAgent</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: "Segoe UI", system-ui, sans-serif; background: #1a1d24; color: #e8eaed; min-height: 100vh; }}
        .header {{ background: #252830; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 1.25rem; }}
        .header a {{ color: #8ab4f8; text-decoration: none; }}
        .header a:hover {{ text-decoration: underline; }}
        .main {{ padding: 24px; max-width: 900px; margin: 0 auto; }}
        .section {{ background: #252830; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
        .section h2 {{ font-size: 1rem; color: #9aa0a6; margin-bottom: 16px; }}
        .config-item {{ display: grid; grid-template-columns: 140px 1fr; gap: 12px; align-items: center; margin-bottom: 12px; font-size: 0.9rem; }}
        .config-item label {{ color: #9aa0a6; }}
        .config-item input, .config-item select {{ padding: 8px 12px; border: 1px solid #3c4043; border-radius: 6px; background: #202124; color: #e8eaed; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MuseumAgent 控制面板</h1>
        <a href="/Control/logout">退出登录</a>
    </div>
    <div class="main">
        <div class="section">
            <h2>LLM 配置</h2>
            <div class="config-item"><label>Base URL</label><input type="text" value="{llm_base_url}" readonly></div>
            <div class="config-item"><label>Model</label><input type="text" value="{llm_model}" readonly></div>
        </div>
        <div class="section">
            <h2>Embedding 配置</h2>
            <div class="config-item"><label>Base URL</label><input type="text" value="{emb_base_url}" readonly></div>
            <div class="config-item"><label>Model</label><input type="text" value="{emb_model}" readonly></div>
        </div>
        <p style="color:#9aa0a6;font-size:0.85rem;">配置修改请编辑 config/config.json 后重启服务</p>
    </div>
</body>
</html>
"""


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def control_index(request: Request):
    """控制面板入口：未登录显示登录页，已登录跳转仪表盘"""
    if request.session.get("admin_logged_in"):
        return RedirectResponse(url="/Control/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/Control/login", status_code=status.HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    if request.session.get("admin_logged_in"):
        return RedirectResponse(url="/Control/dashboard", status_code=status.HTTP_302_FOUND)
    return HTMLResponse(
        LOGIN_HTML.format(ts=int(time.time()), error_html="")
    )


@router.get("/api/captcha")
async def get_captcha(request: Request):
    """获取验证码图片"""
    chars = string.ascii_uppercase + string.digits
    text = "".join(random.choices(chars, k=4))
    request.session["captcha_answer"] = text
    cfg = get_global_config()
    admin_cfg = cfg.get("admin_panel", {})
    expire = admin_cfg.get("captcha_expire_seconds", 300)
    request.session["captcha_expiry"] = time.time() + expire
    img_bytes = _gen_captcha_image(text)
    return Response(content=img_bytes, media_type="image/png")


@router.post("/api/login")
async def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    captcha: str = Form(...),
):
    """处理登录"""
    ok, err = _verify_captcha(request, captcha)
    if not ok:
        html = LOGIN_HTML.format(
            ts=int(time.time()),
            error_html=f'<div class="error">{err}</div>'
        )
        return HTMLResponse(html, status_code=400)
    
    admin = _get_admin_config()
    if username != admin["username"]:
        html = LOGIN_HTML.format(
            ts=int(time.time()),
            error_html='<div class="error">用户名或密码错误</div>'
        )
        return HTMLResponse(html, status_code=401)
    
    ph = admin["password_hash"]
    if ph.startswith("$2") and len(ph) > 20:
        if not bcrypt.checkpw(password.encode("utf-8"), ph.encode("utf-8")):
            html = LOGIN_HTML.format(
                ts=int(time.time()),
                error_html='<div class="error">用户名或密码错误</div>'
            )
            return HTMLResponse(html, status_code=401)
    elif ph and password != ph:
        html = LOGIN_HTML.format(
            ts=int(time.time()),
            error_html='<div class="error">用户名或密码错误</div>'
        )
        return HTMLResponse(html, status_code=401)
    
    request.session["admin_logged_in"] = True
    return RedirectResponse(url="/Control/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/logout")
async def logout(request: Request):
    """退出登录"""
    request.session.clear()
    return RedirectResponse(url="/Control/login", status_code=status.HTTP_302_FOUND)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """仪表盘（需登录）"""
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/Control/login", status_code=status.HTTP_302_FOUND)
    try:
        cfg = get_global_config()
        llm = cfg.get("llm", {})
        emb = cfg.get("embedding", {})
    except Exception:
        llm = {}
        emb = {}
    return HTMLResponse(
        DASHBOARD_HTML.format(
            llm_base_url=llm.get("base_url", "-"),
            llm_model=llm.get("model", "-"),
            emb_base_url=emb.get("base_url", "-"),
            emb_model=emb.get("model", "-"),
        )
    )
