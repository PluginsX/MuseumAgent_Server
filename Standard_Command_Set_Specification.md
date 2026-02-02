# 博物馆智能体标准指令集数据结构规范

## 🎯 设计目标

为博物馆智能体系统定义统一的指令集标准格式，支持客户端动态注册和服务器解析。

## 📋 标准数据结构定义

### 1. 指令集基本信息结构

```json
{
  "spec_version": "1.0.0",
  "client_metadata": {
    "client_id": "string",           // 客户端唯一标识
    "client_type": "enum",           // 客户端类型枚举
    "client_version": "string",      // 客户端版本号
    "platform": "string",            // 运行平台
    "capabilities": {
      "max_concurrent_requests": 5,  // 最大并发请求数
      "supported_scenes": ["study", "leisure", "public"], // 支持的场景类型
      "preferred_response_format": "json" // 响应格式偏好
    }
  },
  "operation_set": {
    "version": "1.0.0",              // 指令集版本
    "timestamp": "ISO8601_datetime", // 注册时间戳
    "operations": []                 // 指令列表
  }
}
```

### 2. 单个指令的标准定义

```json
{
  "operation_id": "unique_operation_identifier",
  "name": "human_readable_name",
  "category": "operation_category",
  "description": "detailed_description",
  "parameters": {
    "required": [
      {
        "name": "param_name",
        "type": "string|number|boolean|object|array",
        "description": "parameter description",
        "validation": {
          "min_value": 0,
          "max_value": 100,
          "pattern": "regex_pattern",
          "enum": ["option1", "option2"]
        }
      }
    ],
    "optional": [
      {
        "name": "optional_param",
        "type": "string",
        "default": "default_value",
        "description": "optional parameter description"
      }
    ]
  },
  "response_schema": {
    "success": {
      "type": "object",
      "properties": {
        "result_data": { "type": "any" },
        "execution_time": { "type": "number" }
      }
    },
    "error": {
      "type": "object", 
      "properties": {
        "error_code": { "type": "string" },
        "error_message": { "type": "string" }
      }
    }
  },
  "compatibility": {
    "min_server_version": "1.0.0",
    "deprecated_since": null,
    "removal_planned": null
  }
}
```

### 3. 完整的指令集示例

```json
{
  "spec_version": "1.0.0",
  "client_metadata": {
    "client_id": "web3d-explorer-v1.2",
    "client_type": "web3d",
    "client_version": "1.2.3",
    "platform": "web-browser",
    "capabilities": {
      "max_concurrent_requests": 3,
      "supported_scenes": ["study", "public"],
      "preferred_response_format": "json"
    }
  },
  "operation_set": {
    "version": "2024.02.02",
    "timestamp": "2024-02-02T19:00:00Z",
    "operations": [
      {
        "operation_id": "zoom_pattern",
        "name": "纹样放大",
        "category": "visualization",
        "description": "对文物特定区域进行放大显示和高亮标注",
        "parameters": {
          "required": [
            {
              "name": "zoom_area",
              "type": "string",
              "description": "需要放大的区域标识",
              "validation": {
                "pattern": "^[a-zA-Z0-9_-]+$"
              }
            }
          ],
          "optional": [
            {
              "name": "zoom_level",
              "type": "number",
              "default": 2.0,
              "description": "放大倍数",
              "validation": {
                "min_value": 1.0,
                "max_value": 10.0
              }
            },
            {
              "name": "highlight_color",
              "type": "string", 
              "default": "#FF0000",
              "description": "高亮颜色HEX值",
              "validation": {
                "pattern": "^#[0-9A-Fa-f]{6}$"
              }
            },
            {
              "name": "animation_duration",
              "type": "number",
              "default": 1000,
              "description": "动画持续时间(毫秒)",
              "validation": {
                "min_value": 100,
                "max_value": 5000
              }
            }
          ]
        },
        "response_schema": {
          "success": {
            "type": "object",
            "properties": {
              "zoom_coordinates": {
                "type": "object",
                "properties": {
                  "x": { "type": "number" },
                  "y": { "type": "number" },
                  "width": { "type": "number" },
                  "height": { "type": "number" }
                }
              },
              "applied_effects": {
                "type": "array",
                "items": { "type": "string" }
              }
            }
          }
        },
        "compatibility": {
          "min_server_version": "1.0.0"
        }
      },
      {
        "operation_id": "restore_scene",
        "name": "场景复原",
        "category": "visualization", 
        "description": "还原文物的历史场景或展示环境",
        "parameters": {
          "required": [
            {
              "name": "scene_type",
              "type": "string",
              "description": "场景类型",
              "validation": {
                "enum": ["excavation", "museum_display", "historical_period"]
              }
            }
          ],
          "optional": [
            {
              "name": "lighting_preset",
              "type": "string",
              "default": "natural",
              "description": "光照预设",
              "validation": {
                "enum": ["natural", "museum", "dramatic"]
              }
            }
          ]
        },
        "response_schema": {
          "success": {
            "type": "object", 
            "properties": {
              "scene_loaded": { "type": "boolean" },
              "environment_details": { "type": "object" }
            }
          }
        },
        "compatibility": {
          "min_server_version": "1.0.0"
        }
      },
      {
        "operation_id": "introduce", 
        "name": "文物介绍",
        "category": "information",
        "description": "提供文物的基本介绍和背景信息",
        "parameters": {
          "required": [],
          "optional": [
            {
              "name": "detail_level",
              "type": "string", 
              "default": "medium",
              "description": "介绍详细程度",
              "validation": {
                "enum": ["brief", "medium", "detailed"]
              }
            },
            {
              "name": "include_multimedia",
              "type": "boolean",
              "default": true,
              "description": "是否包含多媒体内容"
            }
          ]
        },
        "response_schema": {
          "success": {
            "type": "object",
            "properties": {
              "introduction_text": { "type": "string" },
              "multimedia_urls": {
                "type": "array",
                "items": { "type": "string" }
              },
              "estimated_reading_time": { "type": "number" }
            }
          }
        },
        "compatibility": {
          "min_server_version": "1.0.0"
        }
      }
    ]
  }
}
```

### 4. 客户端类型枚举定义

```json
{
  "client_types": {
    "web3d": {
      "description": "Web3D文物展示客户端",
      "typical_operations": ["zoom_pattern", "restore_scene", "introduce"],
      "platform_constraints": ["web_browser", "webgl_support_required"]
    },
    "spirit": {
      "description": "器灵桌面宠物客户端", 
      "typical_operations": ["spirit_interact", "introduce"],
      "platform_constraints": ["desktop_application", "3d_acceleration_required"]
    },
    "mobile": {
      "description": "移动端文物浏览客户端",
      "typical_operations": ["introduce", "query_param"],
      "platform_constraints": ["mobile_device", "touch_interface"]
    },
    "api": {
      "description": "第三方API调用客户端",
      "typical_operations": ["all_operations"],
      "platform_constraints": ["any_platform", "api_access_key_required"]
    }
  }
}
```

### 5. 验证和解析工具

```python
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
import json

class ClientTypeEnum(str, Enum):
    WEB3D = "web3d"
    SPIRIT = "spirit" 
    MOBILE = "mobile"
    API = "api"

class ParameterValidation(BaseModel):
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    enum: Optional[List[str]] = None

class ParameterDefinition(BaseModel):
    name: str
    type: str
    description: str
    validation: Optional[ParameterValidation] = None
    default: Optional[Any] = None

class ResponseSchema(BaseModel):
    success: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None

class OperationDefinition(BaseModel):
    operation_id: str
    name: str
    category: str
    description: str
    parameters: Dict[str, List[ParameterDefinition]]
    response_schema: ResponseSchema
    compatibility: Dict[str, Any]

class ClientCapabilities(BaseModel):
    max_concurrent_requests: int = 5
    supported_scenes: List[str] = ["public"]
    preferred_response_format: str = "json"

class ClientMetadata(BaseModel):
    client_id: str
    client_type: ClientTypeEnum
    client_version: str
    platform: str
    capabilities: ClientCapabilities

class OperationSet(BaseModel):
    version: str
    timestamp: str
    operations: List[OperationDefinition]

class StandardCommandSet(BaseModel):
    spec_version: str = "1.0.0"
    client_metadata: ClientMetadata
    operation_set: OperationSet

    @validator('spec_version')
    def validate_spec_version(cls, v):
        if not v.startswith(('1.', '2.')):
            raise ValueError('Unsupported specification version')
        return v

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return json.loads(self.json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardCommandSet':
        """从字典创建实例"""
        return cls(**data)

# 使用示例
def validate_client_command_set(command_set_data: Dict[str, Any]) -> bool:
    """验证客户端指令集数据的有效性"""
    try:
        command_set = StandardCommandSet.from_dict(command_set_data)
        # 额外的业务逻辑验证
        return True
    except Exception as e:
        print(f"Command set validation failed: {e}")
        return False
```

### 6. 兼容性处理机制

```json
{
  "backward_compatibility": {
    "version_mapping": {
      "1.0": ["zoom_pattern", "introduce"],
      "1.1": ["zoom_pattern", "restore_scene", "introduce"], 
      "2.0": ["all_current_operations"]
    },
    "deprecation_policy": {
      "warning_period_days": 90,
      "removal_notice_required": true
    }
  },
  "forward_compatibility": {
    "unknown_operation_handling": "graceful_degradation",
    "extension_fields_allowed": true
  }
}
```

这个标准数据结构为后续的动态注册机制奠定了坚实基础，既保证了规范性又具备良好的扩展性。