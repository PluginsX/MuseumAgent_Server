#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理系统测试脚本
用于验证会话管理系统的正确性
"""
import time
from datetime import datetime, timedelta
from src.session.strict_session_manager import strict_session_manager

def print_section(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_session_lifecycle():
    """测试会话生命周期"""
    print_section("测试1: 会话生命周期")
    
    # 1. 注册会话
    session_id = "test_session_001"
    client_metadata = {
        "platform": "WEB",
        "require_tts": True,
        "enable_srs": True,
        "user_id": "test_user"
    }
    
    print("1.1 注册会话...")
    session = strict_session_manager.register_session_with_functions(
        session_id, client_metadata, []
    )
    print(f"✓ 会话已注册: {session_id}")
    print(f"  - 创建时间: {session.created_at}")
    print(f"  - 过期时间: {session.expires_at}")
    print(f"  - 有效期: {(session.expires_at - session.created_at).total_seconds() / 60:.1f} 分钟")
    
    # 2. 验证会话
    print("\n1.2 验证会话...")
    validated = strict_session_manager.validate_session(session_id)
    if validated:
        print(f"✓ 会话验证通过")
        print(f"  - 新过期时间: {validated.expires_at}")
    else:
        print("✗ 会话验证失败")
    
    # 3. 心跳更新
    print("\n1.3 心跳更新...")
    time.sleep(2)
    success = strict_session_manager.heartbeat(session_id)
    if success:
        session = strict_session_manager.get_session(session_id)
        print(f"✓ 心跳更新成功")
        print(f"  - 新过期时间: {session.expires_at}")
    else:
        print("✗ 心跳更新失败")
    
    # 4. 注销会话
    print("\n1.4 注销会话...")
    success = strict_session_manager.unregister_session(session_id)
    if success:
        print(f"✓ 会话已注销")
    else:
        print("✗ 会话注销失败")
    
    # 5. 验证已注销的会话
    print("\n1.5 验证已注销的会话...")
    validated = strict_session_manager.validate_session(session_id)
    if not validated:
        print(f"✓ 已注销的会话无法验证（符合预期）")
    else:
        print("✗ 已注销的会话仍可验证（异常）")

def test_session_expiration():
    """测试会话过期机制"""
    print_section("测试2: 会话过期机制")
    
    # 创建一个短期会话（用于测试）
    session_id = "test_session_002"
    client_metadata = {"platform": "WEB"}
    
    print("2.1 注册会话...")
    session = strict_session_manager.register_session_with_functions(
        session_id, client_metadata, []
    )
    
    # 手动设置过期时间为5秒后
    session.expires_at = datetime.now() + timedelta(seconds=5)
    print(f"✓ 会话已注册，5秒后过期")
    
    # 立即验证
    print("\n2.2 立即验证会话...")
    validated = strict_session_manager.validate_session(session_id)
    if validated:
        print(f"✓ 会话有效")
    else:
        print("✗ 会话无效（异常）")
    
    # 等待过期
    print("\n2.3 等待会话过期...")
    time.sleep(6)
    
    # 再次验证
    print("2.4 验证过期会话...")
    validated = strict_session_manager.validate_session(session_id)
    if not validated:
        print(f"✓ 过期会话无法验证（符合预期）")
    else:
        print("✗ 过期会话仍可验证（异常）")
    
    # 清理
    strict_session_manager.unregister_session(session_id)

def test_activity_extension():
    """测试活动延长机制"""
    print_section("测试3: 活动延长机制")
    
    session_id = "test_session_003"
    client_metadata = {"platform": "WEB"}
    
    print("3.1 注册会话...")
    session = strict_session_manager.register_session_with_functions(
        session_id, client_metadata, []
    )
    initial_expires = session.expires_at
    print(f"✓ 初始过期时间: {initial_expires}")
    
    # 等待2秒
    time.sleep(2)
    
    # 业务请求（通过 validate_session）
    print("\n3.2 模拟业务请求...")
    validated = strict_session_manager.validate_session(session_id)
    new_expires = validated.expires_at
    print(f"✓ 新过期时间: {new_expires}")
    
    # 检查是否延长
    if new_expires > initial_expires:
        extension = (new_expires - initial_expires).total_seconds() / 60
        print(f"✓ 会话已延长 {extension:.1f} 分钟")
    else:
        print("✗ 会话未延长（异常）")
    
    # 清理
    strict_session_manager.unregister_session(session_id)

def test_multiple_sessions():
    """测试多会话管理"""
    print_section("测试4: 多会话管理")
    
    print("4.1 注册多个会话...")
    session_ids = []
    for i in range(5):
        session_id = f"test_session_00{i+4}"
        client_metadata = {"platform": "WEB", "user_id": f"user_{i}"}
        strict_session_manager.register_session_with_functions(
            session_id, client_metadata, []
        )
        session_ids.append(session_id)
        print(f"  ✓ 会话 {i+1} 已注册: {session_id}")
    
    # 获取统计信息
    print("\n4.2 获取会话统计...")
    stats = strict_session_manager.get_session_stats()
    print(f"  - 总会话数: {stats['total_sessions']}")
    print(f"  - 活跃会话: {stats['active_sessions']}")
    print(f"  - 过期会话: {stats['expired_sessions']}")
    
    # 清理所有会话
    print("\n4.3 清理所有会话...")
    for session_id in session_ids:
        strict_session_manager.unregister_session(session_id)
    print(f"✓ 已清理 {len(session_ids)} 个会话")

def test_session_attributes():
    """测试会话属性更新"""
    print_section("测试5: 会话属性更新")
    
    session_id = "test_session_009"
    client_metadata = {
        "platform": "WEB",
        "require_tts": False,
        "enable_srs": True
    }
    
    print("5.1 注册会话...")
    session = strict_session_manager.register_session_with_functions(
        session_id, client_metadata, []
    )
    print(f"✓ 初始配置:")
    print(f"  - RequireTTS: {session.client_metadata.get('require_tts')}")
    print(f"  - EnableSRS: {session.client_metadata.get('enable_srs')}")
    
    # 更新属性
    print("\n5.2 更新会话属性...")
    success = strict_session_manager.update_session_attributes(
        session_id,
        require_tts=True,
        enable_srs=False
    )
    
    if success:
        session = strict_session_manager.get_session(session_id)
        print(f"✓ 更新后配置:")
        print(f"  - RequireTTS: {session.client_metadata.get('require_tts')}")
        print(f"  - EnableSRS: {session.client_metadata.get('enable_srs')}")
    else:
        print("✗ 属性更新失败")
    
    # 清理
    strict_session_manager.unregister_session(session_id)

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  会话管理系统测试")
    print("="*60)
    
    try:
        # 运行所有测试
        test_session_lifecycle()
        test_session_expiration()
        test_activity_extension()
        test_multiple_sessions()
        test_session_attributes()
        
        # 最终统计
        print_section("测试完成")
        stats = strict_session_manager.get_session_stats()
        print(f"最终会话统计:")
        print(f"  - 总会话数: {stats['total_sessions']}")
        print(f"  - 活跃会话: {stats['active_sessions']}")
        print(f"  - 过期会话: {stats['expired_sessions']}")
        
        print("\n✓ 所有测试完成！")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

