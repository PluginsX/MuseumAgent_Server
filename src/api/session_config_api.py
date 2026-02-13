# -*- coding: utf-8 -*-
"""
会话管理配置API
提供动态配置会话管理参数的功能
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
import json
import os

from ..session.strict_session_manager import strict_session_manager
from ..common.enhanced_logger import get_enhanced_logger

router = APIRouter(prefix="/api/admin/session-config", tags=["会话配置管理"])

# 初始化日志记录器
logger = get_enhanced_logger()

@router.get("/current")
async def get_current_config():
    """
    获取当前会话管理配置
    """
    try:
        logger.sys.info('Getting current session configuration')
        
        config_info = {
            "current_config": strict_session_manager.config,
            "runtime_info": {
                "session_timeout": f"{strict_session_manager.session_timeout.total_seconds()/60}分钟",
                "inactivity_timeout": f"{strict_session_manager.inactivity_timeout.total_seconds()/60}分钟",
                "heartbeat_timeout": f"{strict_session_manager.heartbeat_timeout.total_seconds()/60}分钟",
                "cleanup_interval": f"{strict_session_manager.cleanup_interval}秒",
                "deep_validation_interval": f"{strict_session_manager.deep_validation_interval}秒",
                "auto_cleanup_enabled": strict_session_manager.enable_auto_cleanup,
                "heartbeat_monitoring_enabled": strict_session_manager.enable_heartbeat_monitoring
            },
            "session_stats": strict_session_manager.get_session_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.sys.info('Configuration retrieval successful')
        return config_info
        
    except Exception as e:
        logger.sys.error('Failed to get configuration', {'error': str(e)})
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.put("/update")
async def update_session_config(config_updates: Dict[str, Any]):
    """
    更新会话管理配置
    注意：部分配置需要重启服务才能生效
    """
    try:
        logger.sys.info('Updating session configuration', config_updates)
        
        # 验证配置参数
        valid_keys = {
            'session_timeout_minutes': (int, 1, 1440),
            'inactivity_timeout_minutes': (int, 1, 1440),
            'heartbeat_timeout_minutes': (int, 1, 60),
            'cleanup_interval_seconds': (int, 10, 300),
            'deep_validation_interval_seconds': (int, 60, 3600),
            'enable_auto_cleanup': (bool, None, None),
            'enable_heartbeat_monitoring': (bool, None, None),
            'log_level': (str, ['DEBUG', 'INFO', 'WARNING', 'ERROR'], None)
        }
        
        validated_config = {}
        
        for key, value in config_updates.items():
            if key not in valid_keys:
                raise HTTPException(status_code=400, detail=f"无效的配置项: {key}")
            
            expected_type, min_val, max_val = valid_keys[key]
            
            # 类型检查
            if not isinstance(value, expected_type):
                raise HTTPException(status_code=400, detail=f"配置项 {key} 类型错误，期望 {expected_type.__name__}")
            
            # 数值范围检查
            if expected_type == int and min_val is not None:
                if value < min_val or value > max_val:
                    raise HTTPException(status_code=400, detail=f"配置项 {key} 超出有效范围 {min_val}-{max_val}")
            
            # 字符串枚举检查
            if expected_type == str and min_val is not None:
                if value not in min_val:
                    raise HTTPException(status_code=400, detail=f"配置项 {key} 无效值，有效值: {min_val}")
            
            validated_config[key] = value
        
        # 应用配置更新
        changes_made = []
        restart_required = False
        
        for key, value in validated_config.items():
            old_value = strict_session_manager.config.get(key)
            if old_value != value:
                strict_session_manager.config[key] = value
                changes_made.append({
                    'key': key,
                    'old_value': old_value,
                    'new_value': value
                })
                
                # 检查是否需要重启
                restart_keys = ['session_timeout_minutes', 'inactivity_timeout_minutes']
                if key in restart_keys:
                    restart_required = True
        
        # 持久化配置到config.json文件
        try:
            config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json')
            config_file_path = os.path.abspath(config_file_path)
            
            # 读取现有配置文件
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
            else:
                full_config = {}
            
            # 更新会话管理配置
            if 'session_management' not in full_config:
                full_config['session_management'] = {}
            
            for key, value in validated_config.items():
                full_config['session_management'][key] = value
            
            # 写回配置文件
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2, ensure_ascii=False)
            
            logger.sys.info('Configuration persisted to file', 
                          {'file_path': config_file_path, 'updated_keys': list(validated_config.keys())})
            
        except Exception as e:
            logger.sys.error('Failed to persist configuration', {'error': str(e)})
            # 即使持久化失败，也不影响内存中的配置更新
        
        # 更新运行时参数（无需重启的配置）
        if 'cleanup_interval_seconds' in validated_config:
            strict_session_manager.cleanup_interval = validated_config['cleanup_interval_seconds']
        
        if 'deep_validation_interval_seconds' in validated_config:
            strict_session_manager.deep_validation_interval = validated_config['deep_validation_interval_seconds']
        
        if 'enable_auto_cleanup' in validated_config:
            strict_session_manager.enable_auto_cleanup = validated_config['enable_auto_cleanup']
            # 如果启用了自动清理但守护进程未运行，则启动它
            if validated_config['enable_auto_cleanup'] and not strict_session_manager._running:
                strict_session_manager._start_enhanced_cleanup_daemon()
        
        if 'enable_heartbeat_monitoring' in validated_config:
            strict_session_manager.enable_heartbeat_monitoring = validated_config['enable_heartbeat_monitoring']
        
        response_data = {
            "message": "配置更新成功",
            "changes_made": changes_made,
            "restart_required": restart_required,
            "updated_config": strict_session_manager.config,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.sys.info('Session configuration update completed', {
            'changes_count': len(changes_made),
            'restart_required': restart_required
        })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.sys.error('Failed to update configuration', {'error': str(e)})
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")

@router.post("/reset-defaults")
async def reset_to_defaults():
    """
    重置为默认配置
    """
    try:
        logger.sys.info('Resetting session configuration to default values')
        
        default_config = {
            'session_timeout_minutes': 15,
            'inactivity_timeout_minutes': 5,
            'heartbeat_timeout_minutes': 2,
            'cleanup_interval_seconds': 30,
            'deep_validation_interval_seconds': 300,
            'enable_auto_cleanup': True,
            'enable_heartbeat_monitoring': True,
            'log_level': 'INFO'
        }
        
        old_config = strict_session_manager.config.copy()
        strict_session_manager.config = default_config
        
        # 更新运行时参数
        strict_session_manager.session_timeout = timedelta(minutes=15)
        strict_session_manager.inactivity_timeout = timedelta(minutes=5)
        strict_session_manager.heartbeat_timeout = timedelta(minutes=2)
        strict_session_manager.cleanup_interval = 30
        strict_session_manager.deep_validation_interval = 300
        strict_session_manager.enable_auto_cleanup = True
        strict_session_manager.enable_heartbeat_monitoring = True
        strict_session_manager.log_level = 'INFO'
        
        # 持久化默认配置到文件
        try:
            config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json')
            config_file_path = os.path.abspath(config_file_path)
            
            # 读取现有配置文件
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
            else:
                full_config = {}
            
            # 更新会话管理配置为默认值
            full_config['session_management'] = default_config.copy()
            
            # 写回配置文件
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2, ensure_ascii=False)
            
            logger.sys.info('Default configuration persisted to file', 
                          {'file_path': config_file_path})
            
        except Exception as e:
            logger.sys.error('Failed to persist default configuration', {'error': str(e)})
        
        response_data = {
            "message": "配置已重置为默认值",
            "old_config": old_config,
            "new_config": default_config,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.sys.info('Session configuration reset completed')
        
        return response_data
        
    except Exception as e:
        logger.sys.error('Failed to reset configuration', {'error': str(e)})
        raise HTTPException(status_code=500, detail=f"配置重置失败: {str(e)}")

@router.get("/validate")
async def validate_config_format(config: Dict[str, Any]):
    """
    验证配置格式是否正确
    """
    try:
        logger.sys.info('Validating configuration format')
        
        # 使用相同的验证逻辑
        valid_keys = {
            'session_timeout_minutes': (int, 1, 1440),
            'inactivity_timeout_minutes': (int, 1, 1440),
            'heartbeat_timeout_minutes': (int, 1, 60),
            'cleanup_interval_seconds': (int, 10, 300),
            'deep_validation_interval_seconds': (int, 60, 3600),
            'enable_auto_cleanup': (bool, None, None),
            'enable_heartbeat_monitoring': (bool, None, None),
            'log_level': (str, ['DEBUG', 'INFO', 'WARNING', 'ERROR'], None)
        }
        
        validation_results = {}
        is_valid = True
        errors = []
        
        for key, value in config.items():
            if key not in valid_keys:
                validation_results[key] = {
                    "valid": False,
                    "error": "无效的配置项"
                }
                errors.append(f"无效的配置项: {key}")
                is_valid = False
                continue
            
            expected_type, min_val, max_val = valid_keys[key]
            
            # 类型检查
            if not isinstance(value, expected_type):
                validation_results[key] = {
                    "valid": False,
                    "error": f"类型错误，期望 {expected_type.__name__}"
                }
                errors.append(f"配置项 {key} 类型错误")
                is_valid = False
                continue
            
            # 数值范围检查
            if expected_type == int and min_val is not None:
                if value < min_val or value > max_val:
                    validation_results[key] = {
                        "valid": False,
                        "error": f"超出有效范围 {min_val}-{max_val}"
                    }
                    errors.append(f"配置项 {key} 超出有效范围")
                    is_valid = False
                    continue
            
            # 字符串枚举检查
            if expected_type == str and min_val is not None:
                if value not in min_val:
                    validation_results[key] = {
                        "valid": False,
                        "error": f"无效值，有效值: {min_val}"
                    }
                    errors.append(f"配置项 {key} 无效值")
                    is_valid = False
                    continue
            
            validation_results[key] = {"valid": True}
        
        response_data = {
            "is_valid": is_valid,
            "validation_results": validation_results,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
        if is_valid:
            logger.sys.info('Configuration validation passed')
        else:
            logger.sys.warn('Configuration validation failed', {'errors': errors})
        
        return response_data
        
    except Exception as e:
        logger.sys.error('Configuration validation exception', {'error': str(e)})
        raise HTTPException(status_code=500, detail=f"配置验证失败: {str(e)}")