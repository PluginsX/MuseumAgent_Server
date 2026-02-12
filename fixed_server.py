# -*- coding: utf-8 -*-
"""
博物馆智能体服务器 - 修复版启动脚本
解决配置加载顺序问题
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    print("=" * 60)
    print("博物馆智能体服务器 - 修复版启动")
    print("启动时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # 第一步：加载配置
    print("\n1. 加载配置...")
    try:
        # 首先从config_utils导入并加载配置
        from src.common.config_utils import load_config as utils_load_config
        config_loaded = utils_load_config("./config/config.json")
        if not config_loaded:
            print("警告: 配置文件加载失败，使用默认配置")
        
        # 同时确保config_manager也加载配置
        from src.common.config_manager import load_config as manager_load_config
        manager_loaded = manager_load_config("./config/config.json")
        print(f"   配置管理器加载结果: {'成功' if manager_loaded else '失败'}")
        
        # 验证配置是否已加载
        from src.common.config_utils import get_global_config
        config = get_global_config()
        print("   ✓ 配置加载验证成功")
    except Exception as e:
        print(f"   ✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    server_config = config.get("server", {})
    
    # 第二步：初始化日志
    print("2. 初始化日志系统...")
    try:
        from src.common.log_utils import get_logger
        logger = get_logger()
        logger.info("博物馆智能体服务器启动 - 配置已加载")
        print("   ✓ 日志系统初始化成功")
    except Exception as e:
        print(f"   ✗ 日志系统初始化失败: {e}")
        return
    
    # 第三步：初始化API网关
    print("3. 初始化API网关...")
    try:
        # 导入API网关类
        from src.gateway.api_gateway import APIGateway
        gateway = APIGateway(auto_init=False)  # 先不自动初始化
        gateway.initialize()  # 在配置加载完成后手动初始化
        print("   ✓ API网关初始化成功")
    except Exception as e:
        print(f"   ✗ API网关初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 第四步：启动FastAPI应用
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