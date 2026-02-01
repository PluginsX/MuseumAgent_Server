# -*- coding: utf-8 -*-
"""
校验工具 - 辅助pydantic完成复杂请求参数校验
"""
import re
from typing import List, Tuple

# 文物ID格式：数字/字母组合，长度1-50
ARTIFACT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")

# 场景类型合法值
VALID_SCENE_TYPES = ("study", "leisure", "public")


def validate_artifact_id(artifact_id: str) -> Tuple[bool, str]:
    """
    校验文物ID格式
    
    Args:
        artifact_id: 文物ID字符串
    
    Returns:
        (是否合法, 错误信息)，合法时错误信息为空字符串
    """
    if not artifact_id or not isinstance(artifact_id, str):
        return False, "文物ID不能为空"
    
    if not ARTIFACT_ID_PATTERN.match(artifact_id):
        return False, "文物ID格式不合法，应为字母、数字、下划线或连字符组合，长度1-50"
    
    return True, ""


def validate_operation(
    operation: str,
    valid_operations: List[str]
) -> Tuple[bool, str]:
    """
    校验操作指令是否在合法列表中
    
    Args:
        operation: 操作指令
        valid_operations: 合法操作列表
    
    Returns:
        (是否合法, 错误信息)
    """
    if not operation or not isinstance(operation, str):
        return False, "操作指令不能为空"
    
    if operation not in valid_operations:
        return False, f"操作指令不合法，有效值为: {', '.join(valid_operations)}"
    
    return True, ""


def validate_scene_type(scene_type: str) -> Tuple[bool, str]:
    """
    校验场景类型是否为 study/leisure/public
    
    Args:
        scene_type: 场景类型
    
    Returns:
        (是否合法, 错误信息)
    """
    if not scene_type or not isinstance(scene_type, str):
        return False, "场景类型不能为空"
    
    if scene_type not in VALID_SCENE_TYPES:
        return False, f"场景类型不合法，有效值为: {', '.join(VALID_SCENE_TYPES)}"
    
    return True, ""
