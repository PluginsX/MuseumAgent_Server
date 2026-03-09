# 控制面板环境变量清理报告

**清理时间**: 2026-03-09

---

## 🎯 目标

移除控制面板构建中的所有环境变量依赖，直接使用生产环境配置。

---

## 🔍 检查结果

### 原有环境变量使用情况

#### 1. `src/utils/request.ts`
```typescript
// 修改前
baseURL: import.meta.env.VITE_API_BASE_URL || '/mas'
timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000
const base = import.meta.env.BASE_URL || '';
```

#### 2. `src/App.tsx`
```typescript
// 已经是硬编码，无需修改
<BrowserRouter basename="/mas">
```

#### 3. `vite.config.ts`
```typescript
// 已经是硬编码，无需修改
base: '/mas/'
```

---

## ✅ 修改内容

### 文件: `src/utils/request.ts`

#### 修改1: 移除 baseURL 环境变量
```typescript
// 修改前
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/mas',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 修改后
const request = axios.create({
  baseURL: '/mas', // 生产环境固定路径
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

#### 修改2: 移除登录跳转的环境变量
```typescript
// 修改前
case 401:
  localStorage.removeItem('token');
  const base = import.meta.env.BASE_URL || '';
  window.location.href = `${base}login`;
  message.error('登录已过期，请重新登录');
  break;

// 修改后
case 401:
  localStorage.removeItem('token');
  window.location.href = '/mas/login';
  message.error('登录已过期，请重新登录');
  break;
```

---

## 📋 配置总结

### 生产环境固定配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Base URL | `/mas` | API 基础路径 |
| Timeout | `30000` | 请求超时时间（30秒） |
| Router Base | `/mas` | 前端路由基础路径 |
| Build Base | `/mas/` | 构建输出基础路径 |

---

## 🚀 构建说明

### 构建命令
```bash
cd control-panel
npm run build
```

### 构建输出
- 输出目录: `control-panel/dist/`
- 所有资源路径前缀: `/mas/`
- 无需任何环境变量配置

### 部署说明
1. 构建完成后，`dist` 目录包含所有静态资源
2. 后端服务会自动挂载 `dist` 目录到 `/Control` 路径
3. 访问地址: `http://your-domain/Control` 或 `http://your-domain/mas/`

---

## ✅ 验证清单

- [x] 移除 `VITE_API_BASE_URL` 环境变量
- [x] 移除 `VITE_API_TIMEOUT` 环境变量
- [x] 移除 `BASE_URL` 环境变量
- [x] 确认 `App.tsx` 使用硬编码 basename
- [x] 确认 `vite.config.ts` 使用硬编码 base
- [x] 确认无 `.env` 文件依赖

---

## 📊 影响范围

### 修改的文件
1. `control-panel/src/utils/request.ts` - 移除环境变量

### 未修改的文件（已经是硬编码）
1. `control-panel/src/App.tsx` - basename 已硬编码
2. `control-panel/vite.config.ts` - base 已硬编码

---

## 🎉 结果

现在控制面板构建完全不依赖环境变量，直接按照生产环境配置构建：
- ✅ 无需配置 `.env` 文件
- ✅ 无需区分开发/生产环境
- ✅ 构建命令统一: `npm run build`
- ✅ 配置简单明确，减少出错可能

---

## 📝 注意事项

1. **开发环境**: 使用 `npm run dev` 时，Vite 会使用 `vite.config.ts` 中的 proxy 配置代理到后端
2. **生产环境**: 构建后的静态文件直接使用 `/mas` 作为 API 基础路径
3. **路由**: 所有前端路由都基于 `/mas` 路径
4. **后端配置**: 确保后端正确挂载静态文件到 `/Control` 或 `/mas` 路径

---

**清理完成时间**: 2026-03-09  
**状态**: ✅ 完成

