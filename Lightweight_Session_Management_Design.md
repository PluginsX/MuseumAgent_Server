# 轻量级会话管理与指令集动态注册方案

## 🎯 设计原则

基于您的要求，设计一个**无外部依赖**的轻量级会话管理系统：

- ❌ 不使用Redis等外部数据库
- ✅ 纯内存管理，自动清理
- ✅ 简单的心跳机制
- ✅ 短生命周期会话（适合教育场景）

## 🏗️ 核心架构设计

### 1. 内存会话管理器

```python
# src/session/session_manager.py
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class ClientSession:
    """客户端会话数据结构"""
    session_id: str
    client_metadata: Dict[str, Any]
    operation_set: List[str]
    created_at: datetime
    last_heartbeat: datetime
    expires_at: datetime
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now() > self.expires_at
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
        # 延长会话有效期
        self.expires_at = datetime.now() + timedelta(minutes=15)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换datetime为字符串
        data['created_at'] = self.created_at.isoformat()
        data['last_heartbeat'] = self.last_heartbeat.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return data

class LightweightSessionManager:
    """轻量级会话管理器"""
    
    def __init__(self, session_timeout_minutes: int = 15):
        self.sessions: Dict[str, ClientSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._lock = threading.RLock()
        self._cleanup_thread = None
        self._running = False
        self._start_cleanup_daemon()
    
    def _start_cleanup_daemon(self):
        """启动清理守护线程"""
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_loop(self):
        """定期清理过期会话"""
        while self._running:
            time.sleep(60)  # 每分钟检查一次
            self._cleanup_expired_sessions()
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        with self._lock:
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if session.is_expired()
            ]
            for session_id in expired_sessions:
                del self.sessions[session_id]
                print(f"Cleaned up expired session: {session_id}")
    
    def register_session(self, session_id: str, client_metadata: Dict[str, Any], 
                        operation_set: List[str]) -> ClientSession:
        """注册新会话"""
        with self._lock:
            session = ClientSession(
                session_id=session_id,
                client_metadata=client_metadata,
                operation_set=operation_set,
                created_at=datetime.now(),
                last_heartbeat=datetime.now(),
                expires_at=datetime.now() + self.session_timeout
            )
            self.sessions[session_id] = session
            return session
    
    def get_session(self, session_id: str) -> Optional[ClientSession]:
        """获取会话信息"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and not session.is_expired():
                return session
            elif session:
                # 会话已过期，清理它
                del self.sessions[session_id]
            return None
    
    def heartbeat(self, session_id: str) -> bool:
        """心跳更新"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and not session.is_expired():
                session.update_heartbeat()
                return True
            return False
    
    def get_operations_for_session(self, session_id: str) -> List[str]:
        """获取会话支持的操作指令集"""
        session = self.get_session(session_id)
        if session:
            return session.operation_set
        return []  # 返回空列表或默认指令集
    
    def unregister_session(self, session_id: str) -> bool:
        """主动注销会话"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
    
    def get_active_session_count(self) -> int:
        """获取活跃会话数量"""
        with self._lock:
            return len([s for s in self.sessions.values() if not s.is_expired()])
    
    def shutdown(self):
        """关闭会话管理器"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

# 全局会话管理器实例
session_manager = LightweightSessionManager()
```

### 2. 客户端注册API

```python
# src/api/session_api.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from ..session.session_manager import session_manager
from ..models.command_set_models import StandardCommandSet

router = APIRouter(prefix="/api/session", tags=["会话管理"])

class ClientRegistrationRequest(BaseModel):
    client_metadata: Dict[str, Any]
    operation_set: List[str]
    client_signature: Optional[str] = None  # 可选的客户端签名

class ClientRegistrationResponse(BaseModel):
    session_id: str
    expires_at: str
    server_timestamp: str
    supported_features: List[str]

@router.post("/register", response_model=ClientRegistrationResponse)
async def register_client_session(registration: ClientRegistrationRequest):
    """
    客户端注册接口
    客户端首次连接时调用此接口注册自己的能力集
    """
    try:
        # 生成唯一会话ID
        session_id = str(uuid.uuid4())
        
        # 注册会话
        session = session_manager.register_session(
            session_id=session_id,
            client_metadata=registration.client_metadata,
            operation_set=registration.operation_set
        )
        
        # 返回注册成功响应
        return ClientRegistrationResponse(
            session_id=session_id,
            expires_at=session.expires_at.isoformat(),
            server_timestamp=datetime.now().isoformat(),
            supported_features=["dynamic_operations", "session_management"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"会话注册失败: {str(e)}")

@router.post("/heartbeat")
async def session_heartbeat(session_id: str = Header(...)):
    """
    会话心跳接口
    客户端定期调用以维持会话活跃
    """
    if session_manager.heartbeat(session_id):
        return {"status": "alive", "timestamp": datetime.now().isoformat()}
    else:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

@router.delete("/unregister")
async def unregister_session(session_id: str = Header(...)):
    """
    注销会话接口
    客户端主动断开连接时调用
    """
    if session_manager.unregister_session(session_id):
        return {"status": "unregistered", "timestamp": datetime.now().isoformat()}
    else:
        raise HTTPException(status_code=404, detail="会话不存在")

@router.get("/operations")
async def get_session_operations(session_id: str = Header(...)):
    """
    获取会话支持的操作指令集
    """
    operations = session_manager.get_operations_for_session(session_id)
    if operations:
        return {"operations": operations, "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
```

### 3. 动态LLM客户端改造

```python
# src/core/dynamic_llm_client.py
from typing import List, Dict, Any
import json
from datetime import datetime

from .llm_client import LLMClient
from ..session.session_manager import session_manager

class DynamicLLMClient(LLMClient):
    """支持动态指令集的LLM客户端"""
    
    def __init__(self):
        super().__init__()
        # 缓存基础指令集（用于无会话情况下的fallback）
        self.base_operations = ["introduce", "query_param"]
    
    def generate_dynamic_prompt(self, session_id: str, user_input: str, 
                              scene_type: str = "public") -> str:
        """
        根据会话动态生成提示词
        """
        # 获取会话特定的操作指令集
        session_operations = session_manager.get_operations_for_session(session_id)
        
        # 如果没有有效会话，使用基础指令集
        if not session_operations:
            operations = self.base_operations
            context_note = "（使用基础指令集，建议重新注册会话）"
        else:
            operations = session_operations
            context_note = ""
        
        # 构造动态提示词
        dynamic_prompt = self.prompt_template.format(
            scene_type=scene_type,
            user_input=user_input,
            valid_operations=", ".join(operations),
            context_note=context_note
        )
        
        return dynamic_prompt
    
    def parse_user_input_with_session(self, session_id: str, user_input: str, 
                                    scene_type: str = "public") -> str:
        """
        带会话支持的用户输入解析
        """
        # 生成动态提示词
        prompt = self.generate_dynamic_prompt(session_id, user_input, scene_type)
        
        # 调用LLM
        return self._chat_completions(prompt)
    
    def get_available_operations(self, session_id: str = None) -> List[str]:
        """
        获取可用操作指令集
        """
        if session_id:
            session_ops = session_manager.get_operations_for_session(session_id)
            if session_ops:
                return session_ops
        
        # fallback到基础指令集
        return self.base_operations.copy()

# 使用示例
def demonstrate_dynamic_client():
    """演示动态客户端的使用"""
    client = DynamicLLMClient()
    
    # 模拟会话ID
    test_session_id = "test-session-123"
    
    # 获取当前可用指令
    available_ops = client.get_available_operations(test_session_id)
    print(f"Available operations: {available_ops}")
    
    # 生成动态提示词示例
    sample_prompt = client.generate_dynamic_prompt(
        session_id=test_session_id,
        user_input="我想了解这件文物的历史",
        scene_type="study"
    )
    print(f"Generated prompt: {sample_prompt}")

if __name__ == "__main__":
    demonstrate_dynamic_client()
```

### 4. 客户端实现示例

```javascript
// client_example.js - 客户端注册和使用示例

class MuseumAgentClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.sessionId = null;
        this.heartbeatInterval = null;
    }
    
    async registerSession() {
        // 定义客户端能力集
        const clientCapabilities = {
            client_metadata: {
                client_id: "web3d-explorer-" + Date.now(),
                client_type: "web3d",
                client_version: "1.0.0",
                platform: "web-browser",
                capabilities: {
                    max_concurrent_requests: 3,
                    supported_scenes: ["study", "public"],
                    preferred_response_format: "json"
                }
            },
            operation_set: ["zoom_pattern", "restore_scene", "introduce"]
        };
        
        try {
            const response = await fetch(`${this.serverUrl}/api/session/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(clientCapabilities)
            });
            
            const result = await response.json();
            this.sessionId = result.session_id;
            
            console.log('Session registered:', this.sessionId);
            
            // 启动心跳机制
            this.startHeartbeat();
            
            return result;
        } catch (error) {
            console.error('Session registration failed:', error);
            throw error;
        }
    }
    
    startHeartbeat() {
        // 每5分钟发送一次心跳
        this.heartbeatInterval = setInterval(async () => {
            try {
                await fetch(`${this.serverUrl}/api/session/heartbeat`, {
                    method: 'POST',
                    headers: {
                        'session_id': this.sessionId
                    }
                });
                console.log('Heartbeat sent');
            } catch (error) {
                console.error('Heartbeat failed:', error);
                this.stopHeartbeat();
            }
        }, 5 * 60 * 1000);
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    async unregisterSession() {
        if (this.sessionId) {
            try {
                await fetch(`${this.serverUrl}/api/session/unregister`, {
                    method: 'DELETE',
                    headers: {
                        'session_id': this.sessionId
                    }
                });
                console.log('Session unregistered');
            } catch (error) {
                console.error('Session unregistration failed:', error);
            }
            this.sessionId = null;
        }
        this.stopHeartbeat();
    }
    
    async parseUserInput(userInput, sceneType = "public") {
        if (!this.sessionId) {
            throw new Error('No active session. Please register first.');
        }
        
        const response = await fetch(`${this.serverUrl}/api/agent/parse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'session_id': this.sessionId
            },
            body: JSON.stringify({
                user_input: userInput,
                scene_type: sceneType
            })
        });
        
        return await response.json();
    }
    
    // 页面卸载时清理会话
    cleanup() {
        this.unregisterSession();
    }
}

// 使用示例
const client = new MuseumAgentClient('https://localhost:8000');

// 页面加载时注册会话
window.addEventListener('load', async () => {
    try {
        await client.registerSession();
        console.log('Client ready for use');
    } catch (error) {
        console.error('Failed to initialize client:', error);
    }
});

// 页面关闭前清理会话
window.addEventListener('beforeunload', () => {
    client.cleanup();
});
```

## 🎯 系统特点

### 优势：
1. **零外部依赖** - 纯内存管理，无需Redis等外部服务
2. **自动清理** - 过期会话自动回收，防止内存泄漏
3. **轻量级** - 适合教育资源场景的短会话模式
4. **简单可靠** - 心跳机制简单有效

### 适用场景：
- 教育展示应用
- 短时交互场景  
- 轻量级Web应用
- 临时性演示环境

这个方案完美契合您的需求：简单、轻量、无外部依赖，同时实现了真正的动态指令集发现机制！