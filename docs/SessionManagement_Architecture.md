# 会话管理系统架构文档

## 一、设计理念

本会话管理系统采用**主流 WebSocket 最佳实践**，核心设计理念：

1. **活动即延续**：任何业务请求或心跳都会自动延长会话有效期
2. **简化验证**：只检查会话是否存在和是否过期，避免复杂的多重判断
3. **宽松超时**：采用较长的超时时间（2小时），适合实际业务场景
4. **对称设计**：客户端和服务器端的会话管理逻辑完全对称

## 二、核心机制

### 2.1 会话生命周期

```
注册 → 活跃使用 → 自动延续 → 超时清理
  ↓        ↓           ↓           ↓
创建会话  业务请求    延长有效期   删除会话
         心跳回复
```

### 2.2 时间戳管理

每个会话维护三个关键时间戳：

| 时间戳 | 说明 | 更新时机 |
|--------|------|----------|
| `created_at` | 创建时间 | 会话注册时 |
| `last_heartbeat` | 最后心跳时间 | 收到心跳回复时 |
| `last_activity` | 最后活动时间 | 任何业务请求或心跳时 |
| `expires_at` | 过期时间 | 任何业务请求或心跳时（延长2小时） |

### 2.3 会话验证逻辑

```python
def validate_session(session_id):
    session = get_session(session_id)
    
    # 简化验证：只检查两个条件
    if not session:
        return None  # 会话不存在
    
    if not session.is_registered or session.is_expired():
        return None  # 未注册或已过期
    
    # 更新活动时间（自动延长会话）
    session.update_activity()
    
    return session
```

**关键优化：**
- ❌ 不再检查 `is_disconnected()`（避免误判正在使用的会话）
- ❌ 不再检查 `is_inactive()`（避免误判长时间操作）
- ✅ 只检查 `is_expired()`（基于 `expires_at`）

### 2.4 会话清理逻辑

```python
def cleanup():
    for session in all_sessions:
        # 只清理真正过期的会话
        if session.is_expired():
            delete_session(session)
```

**关键优化：**
- ❌ 不再使用心跳超时判断（`is_disconnected`）
- ❌ 不再使用无活动超时判断（`is_inactive`）
- ✅ 只使用过期时间判断（`is_expired`）

## 三、心跳机制

### 3.1 心跳流程

```
服务器 ----[HEARTBEAT]----> 客户端
         (每60秒发送)
         
客户端 <---[HEARTBEAT_REPLY]--- 服务器
         (立即回复)
         
服务器更新 last_heartbeat 和 last_activity
服务器延长 expires_at = now + 120分钟
```

### 3.2 心跳参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 服务器发送间隔 | 60秒 | 减少网络负担 |
| 客户端超时 | 120秒 | 容忍网络延迟 |
| 服务器延长时间 | 120分钟 | 每次心跳延长2小时 |

### 3.3 心跳与业务请求的关系

**重要：业务请求优先于心跳**

```python
# 业务请求时
def handle_request(session_id):
    session = validate_session(session_id)  # 自动延长会话
    process_request()

# 心跳回复时
def handle_heartbeat_reply(session_id):
    session.update_heartbeat()  # 也会延长会话
```

**结论：**
- 用户正在使用时，业务请求会不断延长会话
- 即使错过几次心跳，会话也不会过期
- 只有真正超过2小时无任何活动，会话才会过期

## 四、配置参数

### 4.1 推荐配置（生产环境）

```yaml
session_management:
  session_timeout_minutes: 120      # 2小时总超时
  cleanup_interval_seconds: 120     # 2分钟清理一次
  deep_validation_interval_seconds: 600  # 10分钟深度验证
```

### 4.2 配置说明

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `session_timeout_minutes` | 120 | 会话总超时时间，任何活动都会重置 |
| `cleanup_interval_seconds` | 120 | 清理间隔，不宜过短 |
| `deep_validation_interval_seconds` | 600 | 深度验证间隔 |

**废弃参数：**
- `inactivity_timeout_minutes`：已不再使用
- `heartbeat_timeout_minutes`：已不再使用

## 五、问题修复总结

### 5.1 修复前的问题

1. **误判断开连接**：清理线程使用 `is_disconnected()` 检查心跳超时，导致正在使用的会话被清理
2. **心跳与活动分离**：`last_heartbeat` 和 `last_activity` 独立更新，清理时只看心跳
3. **验证逻辑复杂**：`validate_session()` 检查多个条件，容易误判
4. **超时时间过短**：5分钟心跳超时，无法容忍长时间操作

### 5.2 修复后的改进

1. **统一活动判断**：`is_disconnected()` 改为检查 `last_activity` 而非 `last_heartbeat`
2. **心跳更新活动**：`update_heartbeat()` 同时更新 `last_activity`
3. **简化验证逻辑**：只检查 `is_registered` 和 `is_expired()`
4. **延长超时时间**：会话总超时 120 分钟，清理间隔 120 秒
5. **活动即延续**：任何业务请求或心跳都会延长会话到 120 分钟

### 5.3 架构对比

| 项目 | 修复前 | 修复后 |
|------|--------|--------|
| 会话超时 | 15分钟 | 120分钟 |
| 心跳超时 | 2分钟 | 不再使用 |
| 无活动超时 | 5分钟 | 不再使用 |
| 清理判断 | 3个条件 | 1个条件（过期） |
| 验证判断 | 5个条件 | 2个条件（注册+过期） |
| 活动延续 | 只延长15分钟 | 延长120分钟 |

## 六、最佳实践

### 6.1 客户端实现

```javascript
// 1. 注册会话
await wsClient.register(authData, platform, requireTTS, enableSRS, functions);

// 2. 发送业务请求（自动延长会话）
await wsClient.sendTextRequest(text, options);

// 3. 接收心跳并回复（自动延长会话）
wsClient.onHeartbeat = (data) => {
    wsClient.sendHeartbeatReply();
};

// 4. 处理会话过期
wsClient.onSessionExpired = () => {
    // 提示用户重新登录
    showNotification('会话已过期，请重新登录');
};
```

### 6.2 服务器实现

```python
# 1. 注册会话
session = strict_session_manager.register_session_with_functions(
    session_id, client_metadata, functions
)

# 2. 验证会话（自动延长）
session = strict_session_manager.validate_session(session_id)
if not session:
    return error("SESSION_INVALID")

# 3. 处理心跳回复（自动延长）
success = strict_session_manager.heartbeat(session_id)

# 4. 清理过期会话（自动执行）
# 清理线程每2分钟自动清理过期会话
```

## 七、监控与调试

### 7.1 关键日志

```python
# 会话注册
logger.sess.info('New session registered', {
    'session_id': session_id[:8],
    'expires_in': 120
})

# 会话验证
logger.sess.debug('Session validation passed', {
    'session_id': session_id[:8],
    'remaining_seconds': remaining
})

# 会话清理
logger.sess.info('Session cleaned up', {
    'session_id': session_id[:8],
    'cleanup_reason': 'expired'
})
```

### 7.2 监控指标

```python
stats = strict_session_manager.get_session_stats()
# {
#     'total_sessions': 10,
#     'active_sessions': 10,
#     'expired_sessions': 0,
#     'disconnected_sessions': 0,
#     'inactive_sessions': 0
# }
```

## 八、总结

本次重构采用**简化、宽松、对称**的设计理念：

1. **简化**：只用一个条件判断会话是否有效（`is_expired`）
2. **宽松**：超时时间足够长（120分钟），容忍各种场景
3. **对称**：客户端和服务器端逻辑完全一致

**核心原则：活动即延续，过期即清理**

任何业务请求或心跳都会自动延长会话到120分钟，只有真正超过120分钟无任何活动，会话才会被清理。这样既保证了用户体验，又避免了资源浪费。

