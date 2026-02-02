# 博物馆智能体控制面板增强文档

## 概述
本次更新扩展了LLM和Embedding配置面板的功能，增加了更多专业参数配置选项，并设置了符合博物馆项目特性的默认值。

## 新增功能

### 1. LLM配置面板增强

#### 🟢 用户可配置参数（扩展版）
| 参数名 | 类型 | 默认值 | 说明 | 适用场景 |
|--------|------|--------|------|----------|
| **base_url** | string | - | LLM API基础URL | 模型服务地址配置 |
| **api_key** | string | - | API密钥 | 访问认证 |
| **model** | string | qwen-turbo | 模型名称 | 选择不同能力模型 |
| **temperature** | number | 0.2 | 控制生成随机性（0-2） | 博物馆场景需要准确稳定 |
| **top_p** | number | 0.9 | 核采样阈值（0-1） | 平衡创造性和准确性 |
| **max_tokens** | integer | 1024 | 限制输出长度 | 控制响应长度和成本 |
| **stream** | boolean | false | 流式响应开关 | 实时交互体验 |
| **seed** | integer | null | 随机种子 | 确保结果可复现性 |
| **presence_penalty** | number | 0.0 | 存在惩罚(-2到2) | 鼓励新话题讨论 |
| **frequency_penalty** | number | 0.0 | 频率惩罚(-2到2) | 减少重复内容 |
| **n** | integer | 1 | 生成选项数量(1-5) | 多候选方案选择 |

#### 📋 博物馆项目参数配置建议
- **temperature = 0.2**: 博物馆文物解析需要高度准确性，低温度确保稳定输出
- **presence_penalty = 0.0**: 保持文物相关信息的连贯性
- **frequency_penalty = 0.0**: 允许必要的术语重复（如文物名称）
- **max_tokens = 1024**: 足够容纳完整的JSON格式响应

### 2. Embedding配置面板增强

#### 🟢 用户可配置参数（扩展版）
| 参数名 | 类型 | 默认值 | 说明 | 适用场景 |
|--------|------|--------|------|----------|
| **base_url** | string | - | Embedding API基础URL | 向量服务地址配置 |
| **api_key** | string | - | API密钥 | 访问认证 |
| **model** | string | text-embedding-v4 | 模型名称 | 选择向量模型 |
| **dimensions** | integer | 1024 | 向量维度(256/512/1024/1536/2048) | 平衡精度和存储 |
| **encoding_format** | string | float | 编码格式(float/base64) | 数据格式选择 |

#### 📋 博物馆项目参数配置建议
- **dimensions = 1024**: 平衡文物描述的语义丰富度和存储效率
- **encoding_format = float**: 便于后续向量计算和相似度比较

## 技术实现细节

### 前端改进
1. **ConfigLLM.tsx**: 
   - 添加了Switch组件用于流式响应控制
   - 增加了InputNumber组件支持数值参数调节
   - 使用Divider组件组织基础参数和高级参数区域
   - 实现了参数默认值自动填充逻辑

2. **ConfigEmbedding.tsx**:
   - 添加了Select组件支持维度选择（预设博物馆常用维度）
   - 增加了编码格式选择功能
   - 优化了用户体验，提供清晰的选项说明

### 后端改进
1. **config_api.py**: 
   - 保持现有API接口兼容性
   - 支持新的parameters字段结构

2. **llm_client.py**:
   - 增加了对stream、seed、presence_penalty、frequency_penalty、n参数的支持
   - 采用条件添加方式，保持向后兼容

3. **embedding_client.py**:
   - 增加了对encoding_format参数的支持
   - 优化了参数传递逻辑

### 配置文件更新
**config.json**中预设了博物馆项目的最优参数组合：
```json
{
  "llm": {
    "parameters": {
      "temperature": 0.2,
      "max_tokens": 1024,
      "top_p": 0.9,
      "stream": false,
      "presence_penalty": 0.0,
      "frequency_penalty": 0.0,
      "n": 1
    }
  },
  "embedding": {
    "parameters": {
      "dimensions": 1024,
      "encoding_format": "float"
    }
  }
}
```

## 使用指南

### LLM配置最佳实践
1. **稳定性优先**: 博物馆场景建议保持temperature在0.1-0.3范围内
2. **成本控制**: 根据实际需求调整max_tokens，避免不必要的token消耗
3. **一致性保证**: 需要可复现结果时设置固定seed值
4. **内容质量**: 适度调整penalty参数避免过度创新影响准确性

### Embedding配置最佳实践
1. **维度选择**: 
   - 256: 轻量级应用，存储优先
   - 512: 标准配置，平衡性能
   - 1024: 推荐配置，文物描述丰富度佳
   - 1536+: 高精度需求场景
2. **格式选择**: float格式便于后续向量运算和相似度计算

## 测试验证
- ✅ 前端编译通过
- ✅ 服务器正常启动
- ✅ API接口响应正常
- ✅ 配置参数可正常保存和读取

## 后续优化方向
1. 添加参数预设模板（如"文物保护模式"、"展览解说模式"等）
2. 实现参数效果可视化对比
3. 增加配置版本管理和回滚功能
4. 添加参数调优建议和最佳实践指导