# -*- coding: utf-8 -*-
"""
服务注册模块
用于管理微服务的注册和发现
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from src.common.enhanced_logger import get_enhanced_logger


class ServiceInterface(ABC):
    """服务接口基类"""
    
    @abstractmethod
    async def process(self, request: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """处理请求"""
        pass


class ServiceRegistry:
    """服务注册表"""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
    
    def register_service(self, name: str, service: Any):
        """注册服务"""
        self.services[name] = service
        logger = get_enhanced_logger()
        logger.sys.info(f"Service {name} registered")
    
    def get_service(self, name: str) -> Optional[Any]:
        """获取服务"""
        return self.services.get(name)
    
    def unregister_service(self, name: str):
        """注销服务"""
        if name in self.services:
            del self.services[name]
            logger = get_enhanced_logger()
            logger.sys.info(f"Service {name} unregistered")


# 全局服务注册表实例
service_registry = ServiceRegistry()