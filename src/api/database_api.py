# -*- coding: utf-8 -*-
"""数据库管理API"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text

import secrets
from src.common.auth_utils import get_current_user, hash_password
from src.db.database import get_db_session, get_engine
from src.common.enhanced_logger import get_enhanced_logger


# 数据库管理API路由器
database_router = APIRouter(prefix="/api/admin/database", tags=["database_management"])


@database_router.get("/tables")
def get_database_tables(current_user: dict = Depends(get_current_user)):
    """获取数据库表列表"""
    logger = get_enhanced_logger()
    
    try:
        logger.sys.info("Getting database tables", {
            "admin_user_id": current_user.get("user_id")
        })
        
        # 使用SQLAlchemy inspector获取表信息
        engine = get_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        table_info = []
        
        # 获取每个表的记录数
        with engine.connect() as connection:
            for table_name in tables:
                # 跳过系统表
                if table_name.startswith('__'):
                    continue
                
                try:
                    # 执行计数查询
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = result.scalar() or 0
                except Exception as e:
                    logger.sys.error(f"Error counting rows for table {table_name}: {str(e)}")
                    row_count = 0
                
                table_info.append({
                    "name": table_name,
                    "rowCount": row_count
                })
        
        logger.sys.info(f"Found {len(table_info)} database tables")
        
        return table_info
    except Exception as e:
        logger.sys.error(f"Error getting database tables: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据库表列表失败: {str(e)}")


@database_router.get("/tables/{table_name}")
def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """获取表数据"""
    logger = get_enhanced_logger()
    
    try:
        logger.sys.info(f"Getting table data for {table_name}", {
            "admin_user_id": current_user.get("user_id"),
            "page": page,
            "size": size
        })
        
        # 验证表是否存在
        engine = get_engine()
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
        
        # 计算偏移量
        offset = (page - 1) * size
        
        # 获取表数据
        with engine.connect() as connection:
            # 获取总记录数
            count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            total = count_result.scalar() or 0
            
            # 获取分页数据
            data_result = connection.execute(
                text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"),
                {"limit": size, "offset": offset}
            )
            
            # 构建结果
            rows = []
            for row in data_result:
                # 使用row._asdict()方法将结果行转换为字典
                row_dict = dict(row._asdict())
                rows.append(row_dict)
        
        logger.sys.info(f"Retrieved {len(rows)} rows from {table_name}")
        
        return {
            "rows": rows,
            "total": total
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.sys.error(f"Error getting table data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取表数据失败: {str(e)}")


@database_router.post("/tables/{table_name}")
def create_record(
    table_name: str,
    record_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """创建记录"""
    logger = get_enhanced_logger()
    
    try:
        logger.sys.info(f"Creating record in {table_name}", {
            "admin_user_id": current_user.get("user_id")
        })
        
        # 验证表是否存在
        engine = get_engine()
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
        
        # 处理用户表的特殊情况
        if table_name in ['admin_users', 'client_users']:
            # 处理密码哈希
            if 'password_hash' in record_data and record_data['password_hash']:
                # 如果前端传递了password_hash，检查是否已经是哈希值
                # 如果不是哈希值，进行哈希处理
                if len(record_data['password_hash']) < 60:  # 哈希值通常较长
                    record_data['password_hash'] = hash_password(record_data['password_hash'])
            
            # 为客户用户生成API-KEY
            if table_name == 'client_users' and 'api_key' not in record_data:
                record_data['api_key'] = f"museum_{secrets.token_urlsafe(32)}"
        
        # 构建插入语句
        columns = list(record_data.keys())
        values = list(record_data.values())
        
        if not columns:
            raise HTTPException(status_code=400, detail="记录数据不能为空")
        
        # 构建SQL语句
        column_names = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])
        
        sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        # 执行插入操作
        with engine.connect() as connection:
            connection.execute(text(sql), record_data)
            connection.commit()
        
        logger.sys.info(f"Record created successfully in {table_name}")
        
        return {"message": "记录创建成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.sys.error(f"Error creating record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建记录失败: {str(e)}")


@database_router.put("/tables/{table_name}/{record_id}")
def update_record(
    table_name: str,
    record_id: int,
    record_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """更新记录"""
    logger = get_enhanced_logger()
    
    try:
        logger.sys.info(f"Updating record {record_id} in {table_name}", {
            "admin_user_id": current_user.get("user_id")
        })
        
        # 验证表是否存在
        engine = get_engine()
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
        
        # 构建更新语句
        updates = []
        for key, value in record_data.items():
            updates.append(f"{key} = :{key}")
        
        if not updates:
            raise HTTPException(status_code=400, detail="更新数据不能为空")
        
        # 构建SQL语句
        update_clause = ", ".join(updates)
        sql = f"UPDATE {table_name} SET {update_clause} WHERE id = :record_id"
        
        # 添加record_id到参数
        record_data["record_id"] = record_id
        
        # 执行更新操作
        with engine.connect() as connection:
            result = connection.execute(text(sql), record_data)
            connection.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="记录不存在")
        
        logger.sys.info(f"Record {record_id} updated successfully in {table_name}")
        
        return {"message": "记录更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.sys.error(f"Error updating record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新记录失败: {str(e)}")


@database_router.delete("/tables/{table_name}/{record_id}")
def delete_record(
    table_name: str,
    record_id: int,
    current_user: dict = Depends(get_current_user)
):
    """删除记录"""
    logger = get_enhanced_logger()
    
    try:
        logger.sys.info(f"Deleting record {record_id} from {table_name}", {
            "admin_user_id": current_user.get("user_id")
        })
        
        # 验证表是否存在
        engine = get_engine()
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
        
        # 构建删除语句
        sql = f"DELETE FROM {table_name} WHERE id = :record_id"
        
        # 执行删除操作
        with engine.connect() as connection:
            result = connection.execute(text(sql), {"record_id": record_id})
            connection.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="记录不存在")
        
        logger.sys.info(f"Record {record_id} deleted successfully from {table_name}")
        
        return {"message": "记录删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.sys.error(f"Error deleting record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除记录失败: {str(e)}")


@database_router.post("/initialize")
def initialize_database(current_user: dict = Depends(get_current_user)):
    """初始化数据库"""
    logger = get_enhanced_logger()
    
    try:
        logger.sys.info("Initializing database", {
            "admin_user_id": current_user.get("user_id")
        })
        
        # 导入数据库初始化函数
        from src.db.database import init_db
        
        # 执行数据库初始化
        init_db()
        
        logger.sys.info("Database initialized successfully")
        
        return {"message": "数据库初始化成功"}
    except Exception as e:
        logger.sys.error(f"Error initializing database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据库初始化失败: {str(e)}")


@database_router.post("/clear")
def clear_database(current_user: dict = Depends(get_current_user)):
    """清空数据库"""
    logger = get_enhanced_logger()
    
    try:
        logger.sys.info("Clearing database", {
            "admin_user_id": current_user.get("user_id")
        })
        
        # 使用SQLAlchemy inspector获取表信息
        engine = get_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # 清空每个表
        with engine.connect() as connection:
            for table_name in tables:
                # 跳过系统表
                if table_name.startswith('__'):
                    continue
                
                try:
                    # 执行清空操作
                    connection.execute(text(f"DELETE FROM {table_name}"))
                    logger.sys.info(f"Cleared table {table_name}")
                except Exception as e:
                    logger.sys.error(f"Error clearing table {table_name}: {str(e)}")
            
            # 提交事务
            connection.commit()
        
        logger.sys.info("Database cleared successfully")
        
        return {"message": "数据库清空成功"}
    except Exception as e:
        logger.sys.error(f"Error clearing database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据库清空失败: {str(e)}")


@database_router.post("/tables/{table_name}/clear")
def clear_table(
    table_name: str,
    current_user: dict = Depends(get_current_user)
):
    """清空表记录"""
    logger = get_enhanced_logger()
    
    try:
        logger.sys.info(f"Clearing table {table_name}", {
            "admin_user_id": current_user.get("user_id")
        })
        
        # 验证表是否存在
        engine = get_engine()
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
        
        # 执行清空操作
        with engine.connect() as connection:
            connection.execute(text(f"DELETE FROM {table_name}"))
            connection.commit()
        
        logger.sys.info(f"Table {table_name} cleared successfully")
        
        return {"message": "表记录清空成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.sys.error(f"Error clearing table {table_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清空表记录失败: {str(e)}")
