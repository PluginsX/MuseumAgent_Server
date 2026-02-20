# 手动配置更新机制升级文档

## 升级概述

将原先的**自动检测配置修改**机制升级为**手动标记 + 差异更新**机制。

### 核心改进

1. **手动标记**：用户通过 UI 开关手动标记需要更新的配置项
2. **差异更新**：只携带标记为"开启"的配置项，减少报文流量
3. **自动关闭**：配置更新发送后，自动关闭所有更新开关
4. **语音消息修复**：修复语音消息结束时未携带配置更新的 BUG

---

## 一、UI 改进

### 1.1 配置面板标题栏新增开关

每个配置分类的标题栏右侧新增 Switch 开关：

```
┌─────────────────────────────────────────────┐
│ ▼ 智能体角色配置              [更新] ○─   │  ← 开关默认关闭
├─────────────────────────────────────────────┤
│   角色描述: [文本框]                        │
│   响应要求: [文本框]                        │
└─────────────────────────────────────────────┘
```

用户修改配置后，手动将开关切换到"开"状态：

```
┌─────────────────────────────────────────────┐
│ ▼ 智能体角色配置              [更新] ─●   │  ← 开关打开
├─────────────────────────────────────────────┤
│   角色描述: [已修改的内容]                  │
│   响应要求: [已修改的内容]                  │
└─────────────────────────────────────────────┘
```

### 1.2 开关样式

- **默认状态**：灰色背景，滑块在左侧
- **开启状态**：绿色背景，滑块在右侧
- **文字标签**："更新"
- **位置**：标题栏右侧，不影响折叠/展开功能

---

## 二、配置分类与开关映射

| 配置分类 ID | 标题 | 是否有开关 | 包含字段 |
|------------|------|-----------|---------|
| `basic` | 客户端基本信息 | ✅ | `requireTTS`, `enableSRS` |
| `role` | 智能体角色配置 | ✅ | `roleDescription`, `responseRequirements` |
| `scene` | 上下文配置 | ✅ | `sceneDescription` |
| `functions` | 函数定义 | ✅ | `functionCalling` |
| `vad` | VAD配置 | ❌ | 客户端本地配置，不发送到服务器 |

---

## 三、差异更新机制

### 3.1 更新策略

**客户端**：
- 只携带开关为"开"的配置项
- 发送成功后自动关闭所有开关

**服务器**：
- 只要收到某个字段，就直接覆盖会话缓存中的对应数据
- 不需要完整配置，支持部分更新

### 3.2 更新数据结构

#### 示例 1：只更新角色配置

```json
{
  "update_session": {
    "system_prompt": {
      "role_description": "你是博物馆智能助手",
      "response_requirements": "请用友好的语言回答"
    }
  }
}
```

#### 示例 2：只更新场景配置

```json
{
  "update_session": {
    "scene_context": {
      "scene_description": "纹样展示场景"
    }
  }
}
```

#### 示例 3：同时更新多个配置

```json
{
  "update_session": {
    "require_tts": true,
    "enable_srs": true,
    "system_prompt": {
      "role_description": "你是博物馆智能助手",
      "response_requirements": "请用友好的语言回答"
    },
    "scene_context": {
      "scene_description": "纹样展示场景"
    }
  }
}
```

#### 示例 4：无需更新（所有开关都关闭）

```json
{
  "update_session": {}
}
```

---

## 四、代码实现

### 4.1 SettingsPanel.js 改动

#### 新增状态管理

```javascript
// 配置更新开关状态（手动标记哪些配置需要更新）
this.updateSwitches = {
    basic: false,      // 基本配置
    role: false,       // 角色配置
    scene: false,      // 场景配置
    functions: false   // 函数定义
};
```

#### 新增方法：获取待更新配置

```javascript
getPendingUpdates() {
    const updates = {};

    // 基本配置
    if (this.updateSwitches.basic) {
        updates.require_tts = this.config.requireTTS;
        updates.enable_srs = this.config.enableSRS;
    }

    // 角色配置
    if (this.updateSwitches.role) {
        updates.system_prompt = {
            role_description: this.config.roleDescription || '',
            response_requirements: this.config.responseRequirements || ''
        };
    }

    // 场景配置
    if (this.updateSwitches.scene) {
        updates.scene_context = {
            scene_description: this.config.sceneDescription || ''
        };
    }

    // 函数定义
    if (this.updateSwitches.functions) {
        updates.function_calling = this.config.functionCalling;
    }

    return updates;
}
```

#### 新增方法：清除更新开关

```javascript
clearUpdateSwitches() {
    for (const key in this.updateSwitches) {
        this.updateSwitches[key] = false;
    }
    
    // 更新 UI 中的开关状态
    if (this.element) {
        const switches = this.element.querySelectorAll('.update-switch');
        switches.forEach(sw => {
            sw.checked = false;
        });
    }
    
    console.log('[SettingsPanel] 所有更新开关已清除');
}
```

### 4.2 SendManager.js 改动

#### 构造函数新增参数

```javascript
constructor(wsClient, sessionId, clientConfig, settingsPanel = null) {
    this.wsClient = wsClient;
    this.sessionId = sessionId;
    this.clientConfig = clientConfig;
    this.settingsPanel = settingsPanel;  // ✅ 保存设置面板引用
    this.currentVoiceStream = null;
}
```

#### 重构配置更新方法

```javascript
_buildUpdateSession() {
    // 如果没有设置面板引用，返回空对象
    if (!this.settingsPanel) {
        return {};
    }
    
    // 获取需要更新的配置（差异更新）
    const updates = this.settingsPanel.getPendingUpdates();
    
    // 如果有更新，发送后自动关闭开关
    if (Object.keys(updates).length > 0) {
        console.log('[SendManager] 携带配置更新:', updates);
        
        // ✅ 发送成功后自动关闭所有更新开关
        setTimeout(() => {
            this.settingsPanel.clearUpdateSwitches();
        }, 100);
    }
    
    return updates;
}
```

#### 修复语音消息结束时的配置更新

```javascript
endVoiceStream() {
    // ... 省略其他代码 ...
    
    // ✅ 添加配置更新（语音流结束时也携带配置更新）
    const updateSession = this._buildUpdateSession();
    if (Object.keys(updateSession).length > 0) {
        endMessage.payload.update_session = updateSession;
    }
    
    this.wsClient.send(endMessage);
}
```

### 4.3 MuseumAgentSDK.js 改动

#### 新增方法：设置设置面板引用

```javascript
setSettingsPanel(settingsPanel) {
    if (this.sendManager) {
        this.sendManager.settingsPanel = settingsPanel;
    }
}
```

### 4.4 app.js 改动

#### 设置面板创建时建立引用

```javascript
settingsButton.addEventListener('click', () => {
    if (window.settingsPanel) {
        window.settingsPanel.toggle();
    } else {
        import('./components/SettingsPanel.js').then(({ SettingsPanel }) => {
            window.settingsPanel = new SettingsPanel(this.client);
            // ✅ 将设置面板引用传递给客户端
            this.client.setSettingsPanel(window.settingsPanel);
            window.settingsPanel.toggle();
        });
    }
});
```

---

## 五、使用流程

### 5.1 用户操作流程

1. **打开配置面板**：点击右上角设置按钮 ⚙️
2. **修改配置**：展开某个配置分类，修改配置内容
3. **标记更新**：将该分类标题栏右侧的开关切换到"开"
4. **发送消息**：发送文本或语音消息
5. **自动关闭**：配置更新随消息发送，开关自动关闭

### 5.2 示例场景

#### 场景 1：切换场景描述

```
1. 用户打开配置面板
2. 展开"上下文配置"
3. 修改场景描述为"铸造工艺展示场景"
4. 打开"上下文配置"的更新开关
5. 关闭配置面板
6. 发送消息："介绍一下这个场景"
7. 系统携带场景描述更新，发送到服务器
8. 更新开关自动关闭
```

#### 场景 2：同时更新多个配置

```
1. 用户打开配置面板
2. 修改"角色描述"，打开"智能体角色配置"开关
3. 修改"场景描述"，打开"上下文配置"开关
4. 修改"函数定义"，打开"函数定义"开关
5. 发送消息
6. 系统携带三个配置的更新数据
7. 所有开关自动关闭
```

---

## 六、BUG 修复

### 6.1 问题描述

**原问题**：
- 文本消息：✅ 配置更新正常携带
- 语音消息：❌ 开始消息携带配置，但结束消息（stream_seq: -1）未携带配置

**影响**：
- 语音消息发送时，如果有配置修改，可能无法完整更新到服务器

### 6.2 修复方案

在 `endVoiceStream()` 方法中添加配置更新：

```javascript
// 发送结束消息
const endMessage = {
    version: '1.0',
    msg_type: 'REQUEST',
    session_id: this.sessionId,
    payload: {
        request_id: requestId,
        data_type: 'VOICE',
        stream_flag: true,
        stream_seq: -1,
        require_tts: requireTTS,
        content: { 
            voice_mode: 'BINARY',
            audio_format: 'pcm'
        }
    },
    timestamp: Date.now()
};

// ✅ 添加配置更新
const updateSession = this._buildUpdateSession();
if (Object.keys(updateSession).length > 0) {
    endMessage.payload.update_session = updateSession;
}

this.wsClient.send(endMessage);
```

### 6.3 修复验证

**文本消息**：
```
REQUEST → payload.update_session: { ... }
```

**语音消息**：
```
REQUEST (stream_seq: 0) → payload.update_session: { ... }
BINARY DATA (音频块)
REQUEST (stream_seq: -1) → payload.update_session: { ... }  ✅ 已修复
```

---

## 七、优势总结

### 7.1 用户体验

- ✅ **明确控制**：用户清楚知道哪些配置会被更新
- ✅ **减少误操作**：不会因为误修改配置而意外更新
- ✅ **视觉反馈**：开关状态清晰，更新后自动关闭

### 7.2 性能优化

- ✅ **减少流量**：只传输需要更新的配置项
- ✅ **降低开销**：避免每次都携带完整配置
- ✅ **按需更新**：用户决定何时更新哪些配置

### 7.3 技术优势

- ✅ **差异更新**：支持部分配置更新
- ✅ **服务器兼容**：服务器只需覆盖收到的字段
- ✅ **扩展性强**：新增配置项只需添加开关映射

---

## 八、测试建议

### 8.1 功能测试

1. **开关交互**：
   - 点击开关，状态正确切换
   - 开关不影响折叠/展开功能

2. **差异更新**：
   - 只打开一个开关，验证只携带对应配置
   - 打开多个开关，验证携带多个配置
   - 所有开关关闭，验证不携带任何配置

3. **自动关闭**：
   - 发送文本消息后，开关自动关闭
   - 发送语音消息后，开关自动关闭

4. **语音消息修复**：
   - 打开配置开关
   - 发送语音消息
   - 检查服务器日志，确认配置更新被接收

### 8.2 边界测试

1. **无设置面板引用**：
   - 未打开过设置面板时发送消息
   - 应返回空的 update_session

2. **快速切换**：
   - 快速打开/关闭开关
   - 快速发送多条消息

3. **配置验证**：
   - 修改配置但不打开开关
   - 验证配置不会被发送

---

## 九、注意事项

1. **VAD 配置不需要开关**：VAD 是客户端本地配置，不发送到服务器
2. **开关状态持久化**：当前实现不持久化开关状态，刷新页面后所有开关重置为关闭
3. **服务器兼容性**：确保服务器支持部分配置更新（只覆盖收到的字段）
4. **错误处理**：如果发送失败，开关不会自动关闭（需要用户手动重试）

---

## 十、后续优化建议

1. **开关状态提示**：在发送按钮旁显示"有 N 个配置待更新"
2. **批量操作**：添加"全部打开"/"全部关闭"按钮
3. **配置预览**：发送前预览将要更新的配置内容
4. **更新历史**：记录配置更新历史，方便回溯
5. **失败重试**：发送失败时保持开关状态，允许重试

---

**升级完成时间**：2026-02-20  
**文档版本**：v1.0

