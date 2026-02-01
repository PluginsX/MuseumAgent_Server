# -*- coding: utf-8 -*-
"""
MuseumAgent_Server 项目唯一入口
初始化配置、日志、启动FastAPI服务
"""
import os
import sys

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

        server_cfg = get_config_by_key("server")
        ssl_enabled = server_cfg.get("ssl_enabled", False)
        ssl_cert = server_cfg.get("ssl_cert_file", "")
        ssl_key = server_cfg.get("ssl_key_file", "")

        # 解析 SSL 证书路径为绝对路径
        if ssl_enabled and ssl_cert and ssl_key:
            ssl_cert = os.path.normpath(os.path.join(_project_root, ssl_cert))
            ssl_key = os.path.normpath(os.path.join(_project_root, ssl_key))
            if not os.path.exists(ssl_cert) or not os.path.exists(ssl_key):
                logger.warning("SSL 证书文件不存在，将使用 HTTP 启动")
                ssl_cert_file = None
                ssl_key_file = None
            else:
                ssl_cert_file = ssl_cert
                ssl_key_file = ssl_key
        else:
            ssl_cert_file = None
            ssl_key_file = None

        # 4. 启动 FastAPI 服务
        import uvicorn

        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload_mode,
            ssl_certfile=ssl_cert_file,
            ssl_keyfile=ssl_key_file,
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
