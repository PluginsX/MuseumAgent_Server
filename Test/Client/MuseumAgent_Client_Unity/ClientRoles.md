在该文件夹下创建帮我开发适用于Unity 2022.3的本服务的客户端组件
MuseumAgent_Client.cs

要求
实现完整的通过API访问本智能体服务端的业务需求

可挂载到任意GameObject的方式创建客户端示例
独立的Inspector界面脚本
MuseumAgent_Client_Editor.cs

Inspector中支持函数客户端所有参数的定义
1.包括但不限于
2.服务器API配置
3.客户端基本信息
4.客户端支持的函数定义，即为用于注册会话时声明的本客户端支持的Function Calling
提供OpenAI兼容的function calling 标准函数定义
以列表的方式新增函数定义
每项都支持完整的OpenAI兼容的函数信息字段定义
例如
{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "获取指定城市的当前天气",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，例如：北京"
                },
                "unit": {
                    "type": "string", 
                    "enum": ["celsius", "fahrenheit"]
                }
            },
            "required": ["location"]
        }
    }
}