# -*- coding: utf-8 -*-
"""
系统监控API - 提供服务状态、日志等监控信息
"""
import os
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.common.log_utils import get_logger
from src.common.response_utils import success_response

router = APIRouter()

# 获取日志路径（从配置中读取，如果没有则使用默认路径）
def get_log_path():
    from src.common.config_utils import get_global_config
    try:
        cfg = get_global_config()
        log_cfg = cfg.get("log", {})
        log_path = log_cfg.get("log_path", "./logs/")
        if not os.path.isabs(log_path):
            import os
            _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            log_path = os.path.normpath(os.path.join(_project_root, log_path))
        return log_path
    except:
        return "./logs/"


class StatusResponse(BaseModel):
    service_status: str
    version: str
    uptime: str
    timestamp: datetime


class LogsResponse(BaseModel):
    lines: List[str]
    total: int


@router.get("/api/admin/monitor/status", summary="获取系统状态")
async def get_status():
    """获取系统运行状态"""
    # 使用固定的版本号，因为src.__init__.py中没有__version__
    app_version = "1.0.0"
    return success_response(data={
        "service_status": "running",
        "version": app_version,
        "uptime": "N/A",  # 这里可以实现真正的运行时间计算
        "timestamp": datetime.now()
    })


@router.get("/api/admin/monitor/logs", summary="获取日志")
async def get_logs(page: int = 1, size: int = 50):
    """获取系统日志"""
    log_dir = get_log_path()
    log_file = os.path.join(log_dir, "museum_agent.log")
    
    if not os.path.exists(log_file):
        return success_response(data={"lines": [], "total": 0})
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 翻转顺序，显示最新的日志在前面
        lines.reverse()
        
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        
        return success_response(data={
            "lines": [line.rstrip('\n') for line in lines[start_idx:end_idx]],
            "total": len(lines)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志文件失败: {str(e)}")


@router.delete("/api/admin/monitor/logs", summary="清空日志")
async def clear_logs():
    """清空系统日志"""
    log_dir = get_log_path()
    log_file = os.path.join(log_dir, "museum_agent.log")
    
    try:
        # 检查文件是否存在
        if os.path.exists(log_file):
            # 清空文件内容
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('')
            get_logger().info("日志文件已清空")
            return success_response(msg="日志已清空")
        else:
            return success_response(msg="日志文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空日志文件失败: {str(e)}")


@router.get("/api/admin/monitor/logs/download", summary="下载日志文件")
async def download_logs():
    """下载日志文件"""
    log_dir = get_log_path()
    log_file = os.path.join(log_dir, "museum_agent.log")
    
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="日志文件不存在")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=log_file,
        filename=f"museum_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        media_type='text/plain'
    )