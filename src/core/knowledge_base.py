# -*- coding: utf-8 -*-
"""
文物知识库校验模块 - 封装数据库查询、操作合法性校验
"""
import sqlite3
import os
from typing import Any, Dict, List, Optional

from src.common.config_utils import get_global_config


class ArtifactKnowledgeBase:
    """通用化文物知识库，支持SQLite/MySQL"""
    
    def __init__(self) -> None:
        """从全局配置中读取知识库参数"""
        config = get_global_config()
        kb_config = config.get("artifact_knowledge_base", {})
        
        self.db_type = kb_config.get("type", "sqlite")
        self.db_path = kb_config.get("path", "./data/museum_artifact.db")
        self.table_name = kb_config.get("table_name", "museum_artifact_info")
        self.valid_operations = kb_config.get("valid_operations", [])
        
        # 解析路径为绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.normpath(os.path.join(base_dir, self.db_path))
    
    def _connect_sqlite(self) -> sqlite3.Connection:
        """
        建立SQLite数据库连接
        
        Returns:
            数据库连接对象
        
        Raises:
            RuntimeError: 连接失败
        """
        if not os.path.exists(self.db_path):
            raise RuntimeError(f"SQLite数据库文件不存在: {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 按列名查询
            return conn
        except sqlite3.Error as e:
            raise RuntimeError(f"SQLite连接失败: {str(e)}") from e
    
    def _connect_mysql(self):
        """
        建立MySQL数据库连接（预留）
        
        Raises:
            NotImplementedError: MySQL尚未实现
        """
        raise NotImplementedError("MySQL知识库尚未实现，请使用SQLite或配置type为sqlite")
    
    def _get_connection(self):
        """根据配置获取数据库连接"""
        if self.db_type == "sqlite":
            return self._connect_sqlite()
        elif self.db_type == "mysql":
            return self._connect_mysql()
        else:
            raise RuntimeError(f"不支持的数据库类型: {self.db_type}")
    
    def query_artifact_by_name(self, artifact_name: str) -> Optional[Dict[str, Any]]:
        """
        根据文物名称模糊查询
        
        Args:
            artifact_name: 文物名称（支持模糊匹配）
        
        Returns:
            文物数据字典，无结果返回None
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 模糊查询：LIKE %name%
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE artifact_name LIKE ?
                LIMIT 1
            """
            cursor.execute(query, (f"%{artifact_name}%",))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # 转换为字典（SQLite Row 支持 keys()）
            if hasattr(row, "keys"):
                return dict(row)
            return dict(zip([c[0] for c in cursor.description], row))
            
        except sqlite3.OperationalError as e:
            raise RuntimeError(f"数据库查询异常（表/字段可能不存在）: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"知识库查询失败: {str(e)}") from e
        finally:
            if conn:
                conn.close()
    
    def validate_operation(self, operation: str) -> bool:
        """
        校验操作指令是否在合法列表中
        
        Args:
            operation: 操作指令
        
        Returns:
            是否合法
        """
        return operation in self.valid_operations if operation else False
    
    def get_standard_artifact_data(self, artifact_name: str) -> Dict[str, Any]:
        """
        根据文物名称获取标准化文物数据
        
        Args:
            artifact_name: 文物名称
        
        Returns:
            标准化文物字典，包含 artifact_id, artifact_name, 3D资源路径, operation_params, 简介等
        
        Raises:
            RuntimeError: 未查询到相关文物数据
        """
        result = self.query_artifact_by_name(artifact_name)
        
        if result is None:
            raise RuntimeError("未查询到相关文物数据")
        
        # 标准化字段映射（适配不同数据库字段名）
        def _get_val(keys: tuple, default: Any = None):
            for k in keys:
                if k in result and result[k] is not None:
                    return result[k]
            return default
        
        standard_data = {
            "artifact_id": str(_get_val(("artifact_id", "id"), "")),
            "artifact_name": str(_get_val(("artifact_name", "name"), artifact_name)),
            "resource_path": str(_get_val(("resource_path", "model_path", "3d_path"), "")),
            "operation_params": _get_val(("operation_params", "params")) or {},
            "tips": str(_get_val(("tips", "intro", "description"), "")),
        }
        
        # operation_params 需为字典（数据库可能存JSON字符串）
        op_params = standard_data["operation_params"]
        if not isinstance(op_params, dict):
            try:
                import json
                standard_data["operation_params"] = json.loads(
                    str(op_params)
                ) if op_params else {}
            except Exception:
                standard_data["operation_params"] = {}
        
        return standard_data
