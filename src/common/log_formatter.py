# -*- coding: utf-8 -*-
"""
统一日志格式工具
提供标准化的日志输出格式
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import json


class LogFormatter:
    """日志格式化器"""
    
    # 模块标识符
    MODULES = {
        'COORDINATOR': '[COORD]',
        'RAG': '[RAG]',
        'PROMPT': '[PROMPT]',
        'LLM': '[LLM]',
        'PARSER': '[PARSER]',
        'SESSION': '[SESSION]',
        'CLIENT': '[CLIENT]',
        'API': '[API]'
    }
    
    # 操作类型
    OPERATIONS = {
        'START': '▶',
        'END': '■',
        'SEND': '📤',
        'RECEIVE': '📥',
        'PROCESS': '⚙',
        'SUCCESS': '✅',
        'ERROR': '❌',
        'WARNING': '⚠',
        'INFO': 'ℹ',
        'REGISTER': '📝',
        'HEARTBEAT': '💓',
        'UNREGISTER': '🗑',
        'VALIDATE': '🔍'
    }
    
    @staticmethod
    def format_step(module: str, operation: str, message: str, 
                   data: Any = None, step_num: Optional[int] = None) -> str:
        """
        格式化步骤日志
        
        Args:
            module: 模块标识
            operation: 操作类型
            message: 消息内容
            data: 附加数据
            step_num: 步骤编号
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        module_tag = LogFormatter.MODULES.get(module, f'[{module}]')
        op_icon = LogFormatter.OPERATIONS.get(operation, operation)
        
        # 构建基础日志行
        step_info = f"Step {step_num}" if step_num else ""
        log_line = f"[{timestamp}] {module_tag} {op_icon} {step_info} {message}"
        
        # 添加数据（如果提供）
        if data is not None:
            if isinstance(data, (dict, list)):
                formatted_data = json.dumps(data, ensure_ascii=False, indent=2)
                log_line += f"\n{module_tag} 📊 Data:\n{formatted_data}"
            else:
                log_line += f" | Data: {data}"
        
        return log_line
    
    @staticmethod
    def format_external_communication(module: str, direction: str, 
                                    service: str, data: Any, 
                                    metadata: Optional[Dict] = None) -> str:
        """
        格式化外部服务通信日志
        
        Args:
            module: 模块标识
            direction: 通信方向 ('SEND' or 'RECEIVE')
            service: 服务名称
            data: 通信数据
            metadata: 元数据
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        module_tag = LogFormatter.MODULES.get(module, f'[{module}]')
        direction_icon = '📤' if direction == 'SEND' else '📥'
        
        log_lines = [
            f"[{timestamp}] {module_tag} {direction_icon} {service} COMMUNICATION",
            f"{module_tag} 📡 Service: {service}",
            f"{module_tag} 📡 Direction: {direction}"
        ]
        
        # 添加元数据
        if metadata:
            log_lines.append(f"{module_tag} 📡 Metadata: {json.dumps(metadata, ensure_ascii=False)}")
        
        # 添加完整数据
        if isinstance(data, str):
            # 字符串数据截断显示
            preview = data[:200] + "..." if len(data) > 200 else data
            log_lines.append(f"{module_tag} 📡 Content Preview: {preview}")
            if len(data) > 200:
                log_lines.append(f"{module_tag} 📡 Full Content Length: {len(data)} chars")
        else:
            # 结构化数据完整显示
            formatted_data = json.dumps(data, ensure_ascii=False, indent=2)
            log_lines.append(f"{module_tag} 📡 Full Content:\n{formatted_data}")
        
        return "\n".join(log_lines)
    
    @staticmethod
    def format_process_flow(steps: List[Dict[str, Any]]) -> str:
        """
        格式化完整的处理流程
        
        Args:
            steps: 步骤列表，每个步骤包含module, operation, message等
        """
        lines = ["=" * 80, "PROCESS FLOW SUMMARY", "=" * 80]
        
        for i, step in enumerate(steps, 1):
            module = step.get('module', 'UNKNOWN')
            operation = step.get('operation', 'INFO')
            message = step.get('message', '')
            module_tag = LogFormatter.MODULES.get(module, f'[{module}]')
            op_icon = LogFormatter.OPERATIONS.get(operation, operation)
            
            lines.append(f"{i:2d}. {module_tag} {op_icon} {message}")
        
        lines.extend(["=" * 80, ""])
        return "\n".join(lines)


# 便捷函数
def log_step(module: str, operation: str, message: str, 
             data: Any = None, step_num: Optional[int] = None):
    """记录步骤日志"""
    return LogFormatter.format_step(module, operation, message, data, step_num)

def log_communication(module: str, direction: str, service: str, 
                     data: Any, metadata: Optional[Dict] = None):
    """记录通信日志"""
    return LogFormatter.format_external_communication(module, direction, service, data, metadata)

def log_flow_summary(steps: List[Dict[str, Any]]):
    """记录流程摘要"""
    return LogFormatter.format_process_flow(steps)