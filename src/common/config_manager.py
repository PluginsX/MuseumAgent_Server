# -*- coding: utf-8 -*-
"""
配置管理系统
实现配置的加载、管理、验证和动态更新
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import threading
import asyncio

from src.common.enhanced_logger import get_enhanced_logger


class ConfigurationManager:
    """配置管理系统"""
    
    def __init__(self, config_path: str = "./config/config.json"):
        """初始化配置管理器"""
        self.logger = get_enhanced_logger()
        self.config_path = Path(config_path)
        self.config_data = {}
        self.lock = threading.RLock()  # 线程安全锁
        self.last_modified = None
        
        # 加载初始配置
        self.load_config()
    
    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            是否加载成功
        """
        try:
            with self.lock:
                if not self.config_path.exists():
                    self.logger.sys.error('Config file not found', {'path': self.config_path})
                    return False
                
                # 检查文件修改时间
                stat = self.config_path.stat()
                current_modified = stat.st_mtime
                
                if self.last_modified and current_modified <= self.last_modified:
                    # 文件未修改，无需重新加载
                    return True
                
                # 读取配置文件
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                
                self.last_modified = current_modified
                
                self.logger.sys.info('Configuration file loaded successfully', 
                              {'file': str(self.config_path), 'size': len(self.config_data)})
                
                return True
                
        except json.JSONDecodeError as e:
            self.logger.sys.error('Config file JSON format error', {'error': str(e)})
            return False
        except Exception as e:
            self.logger.sys.error('Load config file failed', {'error': str(e)})
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取完整配置
        
        Returns:
            配置数据
        """
        with self.lock:
            return self.config_data.copy()
    
    def get_config_by_key(self, *keys) -> Any:
        """
        根据键路径获取配置值
        
        Args:
            *keys: 键路径，例如 get_config_by_key("server", "port")
            
        Returns:
            配置值
        """
        with self.lock:
            current = self.config_data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
    
    def set_config_value(self, *keys_and_value) -> bool:
        """
        设置配置值
        
        Args:
            *keys_and_value: 键路径和值，例如 set_config_value("server", "port", 8080)
            
        Returns:
            是否设置成功
        """
        if len(keys_and_value) < 2:
            return False
        
        with self.lock:
            current = self.config_data
            # 获取到倒数第二个键
            for key in keys_and_value[:-2]:
                if not isinstance(current, dict):
                    current[key] = {}
                current = current.setdefault(key, {})
            
            # 设置最后一个键的值
            last_key = keys_and_value[-2]
            value = keys_and_value[-1]
            current[last_key] = value
            
            # 保存到文件
            return self.save_config()
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            是否保存成功
        """
        try:
            with self.lock:
                # 确保目录存在
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 写入配置文件
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config_data, f, ensure_ascii=False, indent=2)
                
                self.logger.sys.info('Configuration file saved successfully', 
                              {'file': str(self.config_path)})
                
                return True
                
        except Exception as e:
            self.logger.sys.error(f"保存配置文件失败: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置的有效性
        
        Returns:
            验证结果
        """
        with self.lock:
            errors = []
            warnings = []
            
            # 验证服务器配置
            server_config = self.config_data.get("server", {})
            if not server_config:
                warnings.append("服务器配置缺失")
            else:
                if "host" not in server_config:
                    errors.append("服务器配置缺少 host")
                if "port" not in server_config:
                    errors.append("服务器配置缺少 port")
                elif not isinstance(server_config["port"], int) or server_config["port"] < 1 or server_config["port"] > 65535:
                    errors.append("服务器端口配置无效")
            
            # 验证LLM配置
            llm_config = self.config_data.get("llm", {})
            if not llm_config:
                warnings.append("LLM配置缺失")
            else:
                if not llm_config.get("base_url"):
                    errors.append("LLM配置缺少 base_url")
                if not llm_config.get("api_key"):
                    warnings.append("LLM配置缺少 api_key（某些服务可能不需要）")
                if not llm_config.get("model"):
                    errors.append("LLM配置缺少 model")
            
            # 验证TTS配置
            tts_config = self.config_data.get("tts", {})
            if not tts_config:
                warnings.append("TTS配置缺失")
            else:
                if not tts_config.get("api_key"):
                    warnings.append("TTS配置缺少 api_key（某些服务可能不需要）")
            
            # 验证STT配置
            stt_config = self.config_data.get("stt", {})
            if not stt_config:
                warnings.append("STT配置缺失")
            else:
                if not stt_config.get("api_key"):
                    warnings.append("STT配置缺少 api_key（某些服务可能不需要）")
            
            # 验证SRS配置
            srs_config = self.config_data.get("semantic_retrieval", {})
            if not srs_config:
                warnings.append("SRS配置缺失")
            else:
                if not srs_config.get("base_url"):
                    errors.append("SRS配置缺少 base_url")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        获取特定服务的配置
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务配置
        """
        with self.lock:
            return self.config_data.get(service_name, {})
    
    def update_service_config(self, service_name: str, config: Dict[str, Any]) -> bool:
        """
        更新特定服务的配置
        
        Args:
            service_name: 服务名称
            config: 服务配置
            
        Returns:
            是否更新成功
        """
        with self.lock:
            self.config_data[service_name] = config
            return self.save_config()
    
    def get_runtime_config(self) -> Dict[str, Any]:
        """
        获取运行时配置
        
        Returns:
            运行时配置
        """
        with self.lock:
            return {
                "config_loaded": self.last_modified is not None,
                "last_modified": datetime.fromtimestamp(self.last_modified).isoformat() if self.last_modified else None,
                "config_path": str(self.config_path),
                "config_keys": list(self.config_data.keys()) if self.config_data else []
            }
    
    async def reload_if_changed(self) -> bool:
        """
        如果配置文件发生变化则重新加载
        
        Returns:
            是否重新加载
        """
        try:
            stat = self.config_path.stat()
            current_modified = stat.st_mtime
            
            if self.last_modified is None or current_modified > self.last_modified:
                self.load_config()
                return True
            return False
        except Exception as e:
            self.logger.sys.error(f"检查配置文件变更失败: {e}")
            return False


# 全局配置管理器实例
_config_manager = None
_config_manager_lock = threading.Lock()


def get_config_manager() -> ConfigurationManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        with _config_manager_lock:
            if _config_manager is None:
                _config_manager = ConfigurationManager()
    return _config_manager


def get_global_config() -> Dict[str, Any]:
    """获取全局配置"""
    return get_config_manager().get_config()


def get_config_by_key(*keys) -> Any:
    """根据键路径获取配置值"""
    return get_config_manager().get_config_by_key(*keys)


def validate_config() -> Dict[str, Any]:
    """验证配置"""
    return get_config_manager().validate_config()


def load_config(config_path: str = "./config/config.json") -> bool:
    """加载配置"""
    global _config_manager
    with _config_manager_lock:
        _config_manager = ConfigurationManager(config_path)
    return _config_manager.load_config()