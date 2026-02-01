# -*- coding: utf-8 -*-
"""
MuseumAgent_Server 项目唯一入口
初始化配置、日志、启动FastAPI服务
"""
import sys
import os

# 确保项目根目录在 Python 路径中
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.config_utils import load_config, get_config_by_key
from src.common.log_utils import init_logger, get_logger
from src.api.agent_api import app


def main() -> None:
    """项目启动入口"""
    try:
        # 1. 加载配置
        load_config()
        
        # 2. 初始化日志
        init_logger()
        
        logger = get_logger()
        logger.info("MuseumAgent_Server 启动中...")
        
        # 3. 读取服务配置
        host = get_config_by_key("server", "host")
        port = get_config_by_key("server", "port")
        reload_mode = get_config_by_key("server", "reload")
        
        # 4. 启动 FastAPI 服务
        import uvicorn
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload_mode,
        )
        
    except FileNotFoundError as e:
        print(f"[ERROR] 配置文件不存在: {e}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, ValueError) as e:
        print(f"[ERROR] 配置错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 启动失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
