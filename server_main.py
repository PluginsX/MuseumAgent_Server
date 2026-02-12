# -*- coding: utf-8 -*-
"""
博物馆智能体服务器 - 主程序入口
基于优化架构设计的完整实现
"""
import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.common.log_utils import get_logger
from src.common.config_manager import load_config, get_global_config
from src.common.fault_tolerance import get_health_status


def main():
    """主函数"""
    print("=" * 60)
    print("博物馆智能体服务器 - 优化架构版")
    print("启动时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # 加载配置 - 必须在导入任何需要配置的模块之前
    print("\n1. 加载配置...")
    config_loaded = load_config("./config/config.json")
    if not config_loaded:
        print("警告: 配置文件加载失败，使用默认配置")
    
    config = get_global_config()
    server_config = config.get("server", {})
    
    # 现在可以安全地导入并初始化API网关
    print("2. 初始化API网关...")
    try:
        from src.gateway.api_gateway import APIGateway
        gateway = APIGateway(auto_init=False)  # 先不自动初始化
        gateway.initialize()  # 在配置加载完成后手动初始化
        print("   ✓ API网关初始化成功")
    except Exception as e:
        print(f"   ✗ API网关初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 检查系统健康状态
    print("3. 检查系统健康状态...")
    try:
        health_status = get_health_status()
        print(f"   ✓ 熔断器状态: {len(health_status['circuit_breakers'])} 个")
        print(f"   ✓ 错误统计: {health_status['error_stats']['total_errors']} 个错误")
    except Exception as e:
        print(f"   ✗ 健康状态检查失败: {e}")
    
    # 显示架构信息
    print("\n4. 系统架构信息:")
    print("   ┌─ 客户端请求")
    print("   ├─ API网关 (统一入口)")
    print("   ├─ 认证与授权")
    print("   ├─ 服务路由")
    print("   ├─ 业务服务层")
    print("   │  ├─ 文本处理服务")
    print("   │  ├─ 音频处理服务")
    print("   │  ├─ 语音通话服务")
    print("   │  ├─ LLM服务接口")
    print("   │  ├─ SRS服务接口")
    print("   │  └─ TTS/STT服务")
    print("   ├─ 数据处理与缓存")
    print("   └─ 外部服务集成")
    print("      ├─ 阿里云LLM服务 (OpenAI兼容API)")
    print("      ├─ 阿里云TTS/STT服务 (DashScope SDK)")
    print("      └─ SRS语义检索系统")
    
    # 显示配置信息
    print("\n5. 服务器配置:")
    print(f"   主机: {server_config.get('host', 'localhost')}")
    print(f"   端口: {server_config.get('port', 8000)}")
    print(f"   调试模式: {server_config.get('debug', False)}")
    print(f"   CORS允许源: {server_config.get('cors_allow_origins', ['*'])}")
    
    # 启动FastAPI应用
    try:
        import uvicorn
        
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8000)
        debug = server_config.get("debug", False)
        
        print(f"\n启动Web服务器... (host={host}, port={port})")
        print("服务器已启动，访问地址: http://{}:{}".format(host, port))
        print("按 Ctrl+C 停止服务器")
        
        uvicorn.run(
            gateway.app,
            host=host,
            port=port,
            reload=debug,
            log_level="info" if debug else "warning"
        )
        
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except Exception as e:
        print(f"\n启动服务器失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()