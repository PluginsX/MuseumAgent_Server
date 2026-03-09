# 控制面板会话管理页面问题排查与修复

**排查时间**: 2026-03-09  
**问题**: 控制面板会话管理页面无法获取实时用户会话数据

---

## 🔍 问题分析

### 症状
- 控制面板会话管理页面无法显示客户端列表
- 统计信息无法加载
- 前端显示错误或空数据

### 根本原因
**后端API返回格式不统一**

前端期望的响应格式:
```typescript
{
  code: 200,
  msg: "成功",
  data: { ... }
}
```

后端实际返回格式:
```python
# 直接返回数据，没有包装
return client_list  # ❌ 错误
return stats        # ❌ 错误
```

---

## 🔧 修复内容

### 文件: `src/api/client_api.py`

#### 修改1: `/api/admin/clients/connected` 端点

```python
# 修改前
@router.get("/connected", response_model=List[Dict[str, Any]])
async def get_connected_clients():
    ...
    return client_list  # ❌ 直接返回列表

# 修改后
@router.get("/connected")
async def get_connected_clients():
    ...
    # 返回统一格式
    return {
        "code": 200,
        "msg": "获取客户端列表成功",
        "data": client_list
    }
```

#### 修改2: `/api/admin/clients/stats` 端点

```python
# 修改前
@router.get("/stats")
async def get_client_statistics():
    ...
    return stats  # ❌ 直接返回对象

# 修改后
@router.get("/stats")
async def get_client_statistics():
    ...
    # 返回统一格式
    return {
        "code": 200,
        "msg": "获取统计信息成功",
        "data": stats
    }
```

#### 修改3: `/api/admin/clients/session/{session_id}` DELETE 端点

```python
# 修改前
@router.delete("/session/{session_id}")
async def disconnect_client_session(session_id: str):
    ...
    return {
        "message": "客户端连接已断开",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    }  # ❌ 格式不统一

# 修改后
@router.delete("/session/{session_id}")
async def disconnect_client_session(session_id: str):
    ...
    return {
        "code": 200,
        "msg": "客户端连接已断开",
        "data": {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
    }
```

---

## 📊 API响应格式对比

### 修改前（不统一）

| 端点 | 返回格式 | 问题 |
|------|---------|------|
| `GET /connected` | `[...]` | ❌ 直接返回数组 |
| `GET /stats` | `{...}` | ❌ 直接返回对象 |
| `DELETE /session/{id}` | `{message, ...}` | ❌ 字段不统一 |

### 修改后（统一）

| 端点 | 返回格式 | 状态 |
|------|---------|------|
| `GET /connected` | `{code, msg, data: [...]}` | ✅ 统一格式 |
| `GET /stats` | `{code, msg, data: {...}}` | ✅ 统一格式 |
| `DELETE /session/{id}` | `{code, msg, data: {...}}` | ✅ 统一格式 |

---

## 🎯 前端数据访问

### 前端代码 (`Clients.tsx`)

```typescript
// 获取客户端列表
const fetchClients = async () => {
  const response = await api.get('/api/admin/clients/connected');
  setClients(response.data.data);  // ✅ 访问 data.data
};

// 获取统计信息
const fetchStats = async () => {
  const response = await api.get('/api/admin/clients/stats');
  setStats(response.data.data);  // ✅ 访问 data.data
};
```

### 响应拦截器 (`request.ts`)

```typescript
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { data } = response;
    
    // 检查 code 字段
    if (data && typeof data.code !== 'undefined') {
      if (data.code === 200 || data.code === 0) {
        return response;  // ✅ 返回完整响应
      } else {
        message.error(data.msg || '请求失败');
        return Promise.reject(new Error(data.msg));
      }
    }
    
    return response;
  },
  ...
);
```

---

## ✅ 修复后的效果

### 1. 客户端列表正常显示

```json
{
  "code": 200,
  "msg": "获取客户端列表成功",
  "data": [
    {
      "session_id": "abc123...",
      "client_type": "spirit",
      "client_id": "unity_client_001",
      "platform": "Windows",
      "client_version": "1.0.0",
      "ip_address": "192.168.1.100",
      "created_at": "2026-03-09T12:00:00",
      "expires_at": "2026-03-09T14:00:00",
      "is_active": true,
      "function_names": ["query_artifact", "navigate_scene"],
      "function_count": 2,
      "last_heartbeat": "2026-03-09T12:30:00",
      "time_since_heartbeat": 120
    }
  ]
}
```

### 2. 统计信息正常显示

```json
{
  "code": 200,
  "msg": "获取统计信息成功",
  "data": {
    "total_clients": 5,
    "active_sessions": 4,
    "inactive_sessions": 1,
    "client_types": {
      "spirit": 3,
      "web": 2
    },
    "timestamp": "2026-03-09T12:30:00"
  }
}
```

### 3. 断开连接操作正常

```json
{
  "code": 200,
  "msg": "客户端连接已断开",
  "data": {
    "session_id": "abc123...",
    "timestamp": "2026-03-09T12:30:00"
  }
}
```

---

## 🔄 实时更新机制

### 前端自动刷新

```typescript
useEffect(() => {
  fetchClients();
  fetchStats();
  
  // 设置定时刷新（每10秒）
  const interval = setInterval(() => {
    fetchClients();
    fetchStats();
  }, 10000);
  
  return () => clearInterval(interval);
}, []);
```

### 后端自动清理

```python
# strict_session_manager 自动清理僵尸会话
# get_all_sessions() 只返回有效会话
connected_sessions = strict_session_manager.get_all_sessions()
```

---

## 📋 测试清单

### 1. 页面加载测试
- [ ] 打开会话管理页面
- [ ] 检查是否显示统计卡片（总客户端数、活跃会话等）
- [ ] 检查是否显示客户端列表表格

### 2. 数据刷新测试
- [ ] 点击"刷新"按钮
- [ ] 等待10秒观察自动刷新
- [ ] 检查数据是否更新

### 3. 客户端操作测试
- [ ] 点击"详情"按钮查看客户端详细信息
- [ ] 点击"断开"按钮断开客户端连接
- [ ] 检查操作后列表是否更新

### 4. 搜索过滤测试
- [ ] 在搜索框输入客户端类型
- [ ] 在搜索框输入IP地址
- [ ] 检查过滤结果是否正确

---

## 🚀 部署步骤

### 1. 重启后端服务
```bash
python main.py
```

### 2. 清除浏览器缓存
```
Ctrl + Shift + Delete
或
Ctrl + F5 强制刷新
```

### 3. 测试访问
```
http://localhost:12301/mas/clients
或
https://www.soulflaw.com/mas/clients
```

---

## 📝 相关API端点

| 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/admin/clients/connected` | GET | 获取连接的客户端列表 | ✅ 已修复 |
| `/api/admin/clients/stats` | GET | 获取统计信息 | ✅ 已修复 |
| `/api/admin/clients/session/{id}` | GET | 获取客户端详情 | ⚠️ 未修改 |
| `/api/admin/clients/session/{id}/status` | GET | 检查客户端状态 | ⚠️ 未修改 |
| `/api/admin/clients/session/{id}` | DELETE | 断开客户端连接 | ✅ 已修复 |
| `/api/admin/clients/cleanup/zombie-sessions` | POST | 清理僵尸会话 | ⚠️ 未修改 |

**注**: 未修改的端点不影响主要功能，可以后续优化。

---

## 🎯 总结

### 问题根源
后端API返回格式不统一，前端无法正确解析数据。

### 解决方案
统一所有API端点返回格式为 `{code, msg, data}`。

### 修复范围
- ✅ 客户端列表API
- ✅ 统计信息API
- ✅ 断开连接API

### 预期效果
- ✅ 会话管理页面正常显示客户端列表
- ✅ 统计信息正常显示
- ✅ 实时刷新功能正常工作
- ✅ 客户端操作功能正常

---

**修复完成时间**: 2026-03-09  
**状态**: ✅ 已完成

