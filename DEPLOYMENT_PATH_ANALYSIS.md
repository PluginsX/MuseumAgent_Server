# 部署环境 vs 本地测试环境访问路径对比分析

**分析时间**: 2026-03-09

---

## 📊 环境对比总览

| 环境 | 访问方式 | 后端端口 | 前端路径 | 状态 |
|------|---------|---------|---------|------|
| **生产环境** | `https://www.soulflaw.com/mas/` | 12301 | `/mas/` | ⚠️ 不一致 |
| **本地测试** | `http://localhost:12301/Control/` | 12301 | `/Control/` | ⚠️ 不一致 |

---

## 🔍 详细对比分析

### 1. 生产环境（Ubuntu + Nginx）

#### 访问路径
```
https://www.soulflaw.com/mas/
```

#### Nginx 配置
```nginx
# 控制面板静态文件
location /mas/ {
    alias /opt/MuseumAgent_Server/control-panel/dist/;
    index index.html;
    try_files $uri $uri/ /index.html;
}

# 控制面板 API 代理
location /mas/api/ {
    proxy_pass http://127.0.0.1:12301/api/;
}

# 旧路径兼容（重定向）
location /Control/ {
    return 301 /mas/;
}
```

#### 前端配置
- **Vite base**: `/mas/`
- **Router basename**: `/mas`
- **API baseURL**: `/mas`

#### 访问流程
```
用户访问: https://www.soulflaw.com/mas/
    ↓
Nginx 处理: location /mas/
    ↓
返回: /opt/MuseumAgent_Server/control-panel/dist/index.html
    ↓
前端路由: basename="/mas"
    ↓
API 请求: /mas/api/* → Nginx 代理 → http://127.0.0.1:12301/api/*
```

---

### 2. 本地测试环境（Windows + FastAPI）

#### 访问路径
```
http://localhost:12301/Control/
```

#### FastAPI 配置
```python
# agent_api.py
_spa_dir = Path(__file__).resolve().parent.parent.parent / "control-panel" / "dist"

# 挂载静态文件
app.mount("/Control/static", StaticFiles(directory=str(_spa_dir)), name="control-static")

# 处理SPA路由
@app.get("/Control/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = _spa_dir / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    else:
        return FileResponse(str(_spa_dir / "index.html"))

@app.get("/Control")
async def serve_control_root():
    return FileResponse(str(_spa_dir / "index.html"))
```

#### 前端配置
- **Vite base**: `/mas/`  ⚠️
- **Router basename**: `/mas`  ⚠️
- **API baseURL**: `/mas`  ⚠️

#### 访问流程
```
用户访问: http://localhost:12301/Control/
    ↓
FastAPI 处理: @app.get("/Control")
    ↓
返回: control-panel/dist/index.html
    ↓
前端路由: basename="/mas"  ⚠️ 路径不匹配！
    ↓
API 请求: /mas/api/* → FastAPI 路由 → /api/*  ⚠️ 404错误！
```

---

## ❌ 问题分析

### 问题1: 路径不一致

| 配置项 | 生产环境 | 本地环境 | 是否一致 |
|--------|---------|---------|---------|
| 静态文件路径 | `/mas/` | `/Control/` | ❌ 不一致 |
| API 路径 | `/mas/api/` | `/api/` | ❌ 不一致 |
| 前端 basename | `/mas` | `/mas` | ✅ 一致（但与本地路径不匹配） |
| 前端 API baseURL | `/mas` | `/mas` | ✅ 一致（但与本地路径不匹配） |

### 问题2: 本地测试访问失败

当访问 `http://localhost:12301/Control/` 时：

1. **静态文件加载失败**
   - 前端期望: `/mas/assets/xxx.js`
   - 实际路径: `/Control/assets/xxx.js`
   - 结果: 404 Not Found

2. **API 请求失败**
   - 前端请求: `/mas/api/auth/login`
   - FastAPI 路由: `/api/auth/login`
   - 结果: 404 Not Found

3. **前端路由失败**
   - 前端 basename: `/mas`
   - 实际访问: `/Control/`
   - 结果: 路由不匹配

---

## ✅ 解决方案

### 方案1: 统一使用 `/mas` 路径（推荐）

#### 修改本地 FastAPI 配置

```python
# agent_api.py

# 修改前
app.mount("/Control/static", StaticFiles(directory=str(_spa_dir)), name="control-static")

@app.get("/Control/{full_path:path}")
async def serve_spa(full_path: str):
    ...

@app.get("/Control")
async def serve_control_root():
    ...

# 修改后
app.mount("/mas/static", StaticFiles(directory=str(_spa_dir)), name="control-static")

@app.get("/mas/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = _spa_dir / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    else:
        return FileResponse(str(_spa_dir / "index.html"))

@app.get("/mas")
async def serve_control_root():
    return FileResponse(str(_spa_dir / "index.html"))

# 保留 /Control 兼容性（可选）
@app.get("/Control")
@app.get("/Control/{full_path:path}")
async def redirect_control(full_path: str = ""):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/mas/{full_path}", status_code=301)
```

#### 访问方式
- **本地测试**: `http://localhost:12301/mas/`
- **生产环境**: `https://www.soulflaw.com/mas/`

---

### 方案2: 使用环境变量切换（不推荐，已移除）

~~使用环境变量在开发和生产环境切换路径~~

**已废弃**: 根据之前的决定，我们已经移除了所有环境变量依赖。

---

## 📋 修改清单

### 需要修改的文件

1. **`src/api/agent_api.py`**
   - 修改静态文件挂载路径: `/Control/` → `/mas/`
   - 修改 SPA 路由处理: `/Control/{path}` → `/mas/{path}`
   - 添加 `/Control` 重定向（兼容性）

### 不需要修改的文件

1. **`control-panel/vite.config.ts`** - 已经是 `/mas/`
2. **`control-panel/src/App.tsx`** - 已经是 `/mas`
3. **`control-panel/src/utils/request.ts`** - 已经是 `/mas`
4. **Nginx 配置** - 已经是 `/mas/`

---

## 🎯 修改后的效果

### 统一的访问路径

| 环境 | 访问地址 | 状态 |
|------|---------|------|
| 本地测试 | `http://localhost:12301/mas/` | ✅ 正常 |
| 生产环境 | `https://www.soulflaw.com/mas/` | ✅ 正常 |
| 兼容路径 | `http://localhost:12301/Control/` | ✅ 重定向到 `/mas/` |

### 统一的 API 路径

| API 类型 | 路径 | 状态 |
|---------|------|------|
| 认证 API | `/mas/api/auth/*` | ✅ 正常 |
| 配置 API | `/mas/api/admin/config/*` | ✅ 正常 |
| 会话 API | `/mas/api/session/*` | ✅ 正常 |
| WebSocket | `/mas/ws/*` | ✅ 正常 |

---

## 🚀 部署步骤

### 1. 修改后端代码
```bash
# 修改 src/api/agent_api.py
# 将 /Control 改为 /mas
```

### 2. 重新构建前端（如果需要）
```bash
cd control-panel
npm run build
```

### 3. 重启服务
```bash
python main.py
```

### 4. 测试访问
```bash
# 本地测试
http://localhost:12301/mas/

# 生产环境
https://www.soulflaw.com/mas/
```

---

## 📝 总结

### 当前状态
- ❌ **不一致**: 生产环境使用 `/mas/`，本地测试使用 `/Control/`
- ❌ **本地测试失败**: 前端配置与后端路径不匹配

### 修改后状态
- ✅ **完全一致**: 两个环境都使用 `/mas/`
- ✅ **本地测试正常**: 前端配置与后端路径完全匹配
- ✅ **兼容性保留**: `/Control/` 自动重定向到 `/mas/`

### 优势
1. **开发测试一致**: 本地测试环境与生产环境完全一致
2. **减少错误**: 避免路径不匹配导致的 404 错误
3. **易于维护**: 统一的路径配置，减少配置复杂度
4. **向后兼容**: 保留 `/Control/` 重定向，不影响旧链接

---

**分析完成时间**: 2026-03-09  
**建议**: 立即修改 `agent_api.py`，统一使用 `/mas/` 路径

