# VAD (Voice Activity Detection) 集成文档

## 概述

已为 Web Demo 客户端集成轻量级 VAD（语音活动检测）模块，使用 Silero VAD 实现。VAD 可以自动检测用户是否在说话，仅在检测到语音时采集音频，从而节省流量和性能开销。

## 技术方案

### 核心技术栈

- **VAD 引擎**: Silero VAD (WebAssembly 版本)
- **库大小**: ~1.5MB (首次加载，之后缓存)
- **加载方式**: CDN 动态加载 (`@ricky0123/vad-web@0.0.7`)
- **集成方式**: 模块化设计，与现有录音模块无缝集成

### 工作原理

```
用户开始录音
  ↓
[VAD 初始化] → 加载 Silero VAD 模型
  ↓
[实时检测] → 分析音频帧（每 96ms）
  ↓
检测到语音？
  ├─ 是 → [开始采集] → 发送 PCM 数据到服务器
  └─ 否 → [跳过采集] → 节省流量
  ↓
静音超过阈值？
  ├─ 是 → [停止采集] → 等待下次语音
  └─ 否 → [继续采集]
```

## 文件结构

```
client/web/Demo/
├── js/
│   ├── modules/
│   │   ├── vad.js          # VAD 模块（新增）
│   │   ├── recorder.js     # 录音模块（已修改，集成 VAD）
│   │   └── ...
│   └── app.js              # 主应用（已修改，初始化 VAD）
├── css/
│   └── style.css           # 样式文件（已修改，添加 VAD 样式）
└── index.html              # HTML 文件（已修改，添加 VAD 配置 UI）
```

## 配置参数说明

### UI 配置项

所有 VAD 配置参数都暴露在 Web UI 的"1. 客户端配置"面板中：

| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| **启用 VAD** | ✅ 启用 | - | 是否启用语音活动检测 |
| **静音超时** | 1000ms | 500-5000ms | 静音多久后停止采集 |
| **语音检测阈值** | 0.5 | 0-1 | 越高越严格，减少误触发 |
| **静音检测阈值** | 0.35 | 0-1 | 越低越严格，更快检测静音 |
| **语音前保留帧数** | 1 | 0-10 | 避免语音开头被截断 |
| **容错帧数** | 8 | 0-20 | 避免短暂静音误判 |
| **最小语音帧数** | 3 | 1-10 | 避免误触发（如咳嗽、噪音） |

### 参数调优建议

**场景 1：安静环境（办公室、家庭）**
```javascript
{
  positiveSpeechThreshold: 0.5,  // 标准阈值
  negativeSpeechThreshold: 0.35, // 标准阈值
  silenceDuration: 1000,          // 1秒静音超时
  minSpeechFrames: 3              // 标准容错
}
```

**场景 2：嘈杂环境（展厅、公共场所）**
```javascript
{
  positiveSpeechThreshold: 0.7,  // 提高阈值，减少误触发
  negativeSpeechThreshold: 0.5,  // 提高阈值
  silenceDuration: 800,           // 缩短超时，更快响应
  minSpeechFrames: 5              // 增加容错，过滤噪音
}
```

**场景 3：低延迟要求（实时对话）**
```javascript
{
  positiveSpeechThreshold: 0.4,  // 降低阈值，更快检测
  negativeSpeechThreshold: 0.3,  // 降低阈值
  silenceDuration: 600,           // 缩短超时
  preSpeechPadFrames: 2           // 增加前置帧，避免截断
}
```

## 使用方法

### 1. 启用/禁用 VAD

在 Web UI 的"客户端配置"面板中：
- 勾选"启用 VAD"复选框 → 启用
- 取消勾选 → 禁用（使用传统连续采集）

### 2. 调整参数

直接在 UI 中修改参数，实时生效（下次录音时应用）。

### 3. 查看状态

录音时，"VAD 状态"会实时显示：
- 🔇 **静音中** - 灰色背景，未检测到语音
- 🎤 **检测到语音** - 绿色背景，正在采集

### 4. 查看统计

停止录音后，控制台会输出 VAD 统计信息：
```javascript
{
  totalFrames: 1000,      // 总帧数
  voiceFrames: 650,       // 语音帧数
  silenceFrames: 350,     // 静音帧数
  voiceRatio: "65.00%",   // 语音占比
  activations: 5          // 激活次数
}
```

## 性能优化

### 流量节省

假设用户说话占比 60%，静音占比 40%：

| 场景 | 无 VAD | 有 VAD | 节省 |
|------|--------|--------|------|
| 1分钟录音 | 1.92MB | 1.15MB | **40%** |
| 10分钟录音 | 19.2MB | 11.5MB | **40%** |

*基于 PCM 16kHz/16bit/单声道，32KB/s*

### CPU 开销

- **VAD 检测**: ~2-5% CPU（单核）
- **音频采集**: ~3-8% CPU（单核）
- **总开销**: 与传统方式相当，但流量大幅降低

### 内存占用

- **VAD 模型**: ~2MB（首次加载后缓存）
- **运行时内存**: ~5-10MB
- **总增加**: < 15MB

## API 参考

### VADModule 类

```javascript
import { VADModule } from './modules/vad.js';

const vad = new VADModule();

// 初始化
await vad.init(audioStream, {
  enabled: true,
  silenceDuration: 1000,
  positiveSpeechThreshold: 0.5,
  // ... 其他配置
});

// 设置回调
vad.onVoiceStart = () => {
  console.log('语音开始');
};

vad.onVoiceEnd = () => {
  console.log('语音结束');
};

// 启动检测
vad.start();

// 暂停检测
vad.pause();

// 获取统计
const stats = vad.getStats();

// 销毁
vad.destroy();
```

### RecorderModule 集成

```javascript
import { recorderModule } from './modules/recorder.js';
import { VADModule } from './modules/vad.js';

const vad = new VADModule();

// 初始化录音模块（传入 VAD 实例）
recorderModule.init(client, vad);

// 设置 VAD 配置
recorderModule.setVADConfig({
  enabled: true,
  silenceDuration: 1000,
  // ... 其他配置
});

// 开始录音（自动使用 VAD）
await recorderModule.startRecording();
```

## 故障排查

### 问题 1：VAD 库加载失败

**症状**: 控制台显示"VAD库加载失败"

**解决方案**:
1. 检查网络连接
2. 确认 CDN 可访问：`https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.7/dist/bundle.min.js`
3. 如果 CDN 被墙，可下载到本地并修改 `vad.js` 中的路径

### 问题 2：VAD 误触发（噪音被识别为语音）

**解决方案**:
1. 提高"语音检测阈值"（如 0.7）
2. 增加"最小语音帧数"（如 5）
3. 启用浏览器的噪声抑制：
   ```javascript
   audio: {
     noiseSuppression: true,
     echoCancellation: true
   }
   ```

### 问题 3：语音开头被截断

**解决方案**:
1. 增加"语音前保留帧数"（如 2-3）
2. 降低"语音检测阈值"（如 0.4）

### 问题 4：短暂停顿导致采集中断

**解决方案**:
1. 增加"容错帧数"（如 10-15）
2. 延长"静音超时"（如 1500ms）

## 浏览器兼容性

| 浏览器 | 最低版本 | 支持状态 |
|--------|----------|----------|
| Chrome | 57+ | ✅ 完全支持 |
| Edge | 79+ | ✅ 完全支持 |
| Firefox | 52+ | ✅ 完全支持 |
| Safari | 14.1+ | ✅ 完全支持 |
| Opera | 44+ | ✅ 完全支持 |

**注意**: 需要 WebAssembly 和 Web Audio API 支持。

## 最佳实践

1. **首次使用提示**: 告知用户 VAD 正在加载（~1.5MB）
2. **参数预设**: 为不同场景提供预设配置
3. **实时反馈**: 显示 VAD 状态，让用户知道系统在工作
4. **降级方案**: VAD 加载失败时自动切换到传统模式
5. **统计展示**: 录音结束后显示流量节省情况

## 未来优化

- [ ] 支持自定义 VAD 模型
- [ ] 添加音量可视化
- [ ] 支持多语言优化
- [ ] 离线模式（本地加载模型）
- [ ] 自适应阈值调整

---

**集成完成时间**: 2026-02-15  
**版本**: v1.0  
**维护者**: MuseumAgent Team

