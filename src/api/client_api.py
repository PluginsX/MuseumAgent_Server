# -*- coding: utf-8 -*-
"""
客户端信息管理API
提供客户端连接状态查询和管理功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..session.strict_session_manager import strict_session_manager
from ..common.log_formatter import log_step, log_communication

router = APIRouter(prefix="/api/admin/clients", tags=["客户端管理"])

class ClientInfoResponse:
    """客户端信息响应模型"""
    pass

@router.get("/connected", response_model=List[Dict[str, Any]])
async def get_connected_clients():
    """
    获取所有连接的客户端信息
    服务端已自动完成会话有效性检测和清理
    """
    try:
        print(log_step('CLIENT', 'INFO', '获取连接客户端列表'))
        
        # 服务端自动清理后返回活跃会话
        connected_sessions = strict_session_manager.get_all_sessions()
        client_list = []
        
        for session_id, session in connected_sessions.items():
            # 获取客户端基本信息
            client_info = {
                "session_id": session_id,
                "client_type": session.client_metadata.get("client_type", "unknown"),
                "client_id": session.client_metadata.get("client_id", "unknown"),
                "platform": session.client_metadata.get("platform", "unknown"),
                "client_version": session.client_metadata.get("client_version", "unknown"),
                "ip_address": session.client_metadata.get("ip_address", "unknown"),
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "is_active": session.is_active(),
                "function_names": session.client_metadata.get("function_names", []),
                "function_count": len(session.client_metadata.get("functions", [])),
                "supports_openai_standard": len(session.client_metadata.get("functions", [])) > 0,
                "last_heartbeat": session.last_heartbeat.isoformat(),
                "time_since_heartbeat": (datetime.now() - session.last_heartbeat).total_seconds()
            }
            
            client_list.append(client_info)
        
        print(log_step('CLIENT', 'SUCCESS', f'获取到 {len(client_list)} 个活跃客户端'))
        
        return client_list
        
    except Exception as e:
        print(log_step('CLIENT', 'ERROR', '获取客户端列表失败', {'error': str(e)}))
        raise HTTPException(status_code=500, detail=f"获取客户端信息失败: {str(e)}")

@router.get("/session/{session_id}")
async def get_client_details(session_id: str):
    """
    获取特定会话的详细信息
    """
    try:
        print(log_step('CLIENT', 'INFO', '获取客户端详情', {'session_id': session_id}))
        
        session = strict_session_manager.validate_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 发送心跳检测连接状态
        is_alive = strict_session_manager.heartbeat(session_id)
        
        client_details = {
            "session_id": session_id,
            "client_metadata": session.client_metadata,
            "functions": session.client_metadata.get("functions", []),
            "function_count": len(session.client_metadata.get("functions", [])),
            "supports_openai_standard": len(session.client_metadata.get("functions", [])) > 0,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "is_active": session.is_active(),
            "is_alive": is_alive,
            "time_remaining": (session.expires_at - datetime.now()).total_seconds() if session.expires_at > datetime.now() else 0
        }
        
        print(log_step('CLIENT', 'SUCCESS', '获取客户端详情成功'))
        return client_details
        
    except HTTPException:
        raise
    except Exception as e:
        print(log_step('CLIENT', 'ERROR', '获取客户端详情失败', {'error': str(e)}))
        raise HTTPException(status_code=500, detail=f"获取客户端详情失败: {str(e)}")

@router.get("/session/{session_id}/status")
async def check_client_status(session_id: str):
    """
    检查客户端连接状态（主动探测）
    """
    try:
        print(log_step('CLIENT', 'INFO', '主动检查客户端状态', {'session_id': session_id}))
        
        session = strict_session_manager.validate_session(session_id)
        if not session:
            return {
                "session_id": session_id,
                "status": "disconnected",
                "reason": "会话不存在或已过期",
                "should_cleanup": True
            }
        
        # 执行心跳检测
        is_alive = strict_session_manager.heartbeat(session_id)
        
        # 综合状态判断
        status_info = {
            "session_id": session_id,
            "status": "active" if is_alive and session.is_active() else "inactive",
            "is_alive": is_alive,
            "is_active": session.is_active(),
            "last_heartbeat": session.last_heartbeat.isoformat(),
            "time_since_heartbeat": (datetime.now() - session.last_heartbeat).total_seconds(),
            "expires_at": session.expires_at.isoformat(),
            "time_until_expiry": (session.expires_at - datetime.now()).total_seconds()
        }
        
        # 判断是否需要清理
        should_cleanup = not is_alive or not session.is_active()
        status_info["should_cleanup"] = should_cleanup
        
        if should_cleanup:
            status_info["reason"] = "会话无响应或已过期"
            print(log_step('CLIENT', 'WARNING', '检测到僵尸会话', 
                          {'session_id': session_id, 'reason': status_info['reason']}))
        else:
            print(log_step('CLIENT', 'INFO', '客户端状态正常'))
            
        return status_info
        
    except Exception as e:
        print(log_step('CLIENT', 'ERROR', '检查客户端状态失败', {'error': str(e)}))
        raise HTTPException(status_code=500, detail=f"检查客户端状态失败: {str(e)}")


@router.post("/cleanup/zombie-sessions")
async def cleanup_zombie_sessions():
    """
    主动清理僵尸会话
    """
    try:
        print(log_step('CLIENT', 'INFO', '开始清理僵尸会话'))
        
        # 触发即时清理
        strict_session_manager._perform_strict_cleanup()
        
        # 获取清理后的统计
        all_sessions = strict_session_manager.get_all_sessions()
        active_count = len(all_sessions)
        
        result = {
            "message": "僵尸会话清理完成",
            "total_sessions": len(strict_session_manager.sessions),
            "active_sessions": active_count,
            "cleaned_up": len(strict_session_manager.sessions) - len(all_sessions),
            "timestamp": datetime.now().isoformat()
        }
        
        print(log_step('CLIENT', 'SUCCESS', '僵尸会话清理完成', 
                      {'cleaned_count': result['cleaned_up']}))
        return result
        
    except Exception as e:
        print(log_step('CLIENT', 'ERROR', '清理僵尸会话失败', {'error': str(e)}))
        raise HTTPException(status_code=500, detail=f"清理僵尸会话失败: {str(e)}")

@router.get("/stats")
async def get_client_statistics():
    """
    获取客户端统计信息
    """
    try:
        print(log_step('CLIENT', 'INFO', '获取客户端统计信息'))
        
        connected_sessions = strict_session_manager.get_all_sessions()
        
        # 按客户端类型统计
        type_stats = {}
        total_clients = len(connected_sessions)
        
        for session_id, session in connected_sessions.items():
            client_type = session.client_metadata.get("client_type", "unknown")
            if client_type in type_stats:
                type_stats[client_type] += 1
            else:
                type_stats[client_type] = 1
        
        # 统计活跃会话
        active_sessions = sum(1 for session in connected_sessions.values() if session.is_active())
        
        stats = {
            "total_clients": total_clients,
            "active_sessions": active_sessions,
            "inactive_sessions": total_clients - active_sessions,
            "client_types": type_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        print(log_step('CLIENT', 'SUCCESS', '获取客户端统计信息成功'))
        return stats
        
    except Exception as e:
        print(log_step('CLIENT', 'ERROR', '获取客户端统计信息失败', {'error': str(e)}))
        raise HTTPException(status_code=500, detail=f"获取客户端统计信息失败: {str(e)}")


@router.delete("/session/{session_id}")
async def disconnect_client_session(session_id: str):
    """
    管理员强制断开客户端会话
    """
    try:
        print(log_step('CLIENT', 'INFO', '管理员强制断开客户端会话', {'session_id': session_id}))
        
        # 验证会话是否存在
        session = strict_session_manager.validate_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 注销会话
        success = strict_session_manager.unregister_session(session_id)
        
        if success:
            print(log_step('CLIENT', 'SUCCESS', '客户端会话已强制断开', {'session_id': session_id}))
            return {
                "message": "客户端连接已断开",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="断开会话失败")
            
    except HTTPException:
        raise
    except Exception as e:
        print(log_step('CLIENT', 'ERROR', '强制断开会话失败', {'error': str(e)}))
        raise HTTPException(status_code=500, detail=f"断开会话失败: {str(e)}")