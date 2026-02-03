#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
严格会话管理测试脚本
验证会话注册、验证、清理等核心功能
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 初始化配置
from src.common.config_utils import load_config
load_config()

from src.session.strict_session_manager import strict_session_manager
from src.common.log_formatter import log_step, log_communication

def test_session_lifecycle():
    """测试会话完整生命周期"""
    print("=" * 80)
    print("🧪 严格会话管理测试")
    print("=" * 80)
    
    # 1. 测试会话注册
    print("\n📝 步骤1: 会话注册测试")
    session_id = "test-session-123"
    client_metadata = {
        "client_type": "test_client",
        "client_id": "test-client-001",
        "platform": "python-test",
        "version": "1.0.0"
    }
    operation_set = ["test_op1", "test_op2", "general_chat"]
    
    session = strict_session_manager.register_session(
        session_id=session_id,
        client_metadata=client_metadata,
        operation_set=operation_set
    )
    
    print(f"  ✅ 会话注册成功")
    print(f"  会话ID: {session.session_id}")
    print(f"  操作集: {session.operation_set}")
    print(f"  过期时间: {session.expires_at}")
    
    # 2. 测试会话验证
    print("\n🔍 步骤2: 会话验证测试")
    validated_session = strict_session_manager.validate_session(session_id)
    if validated_session:
        print(f"  ✅ 会话验证通过")
        print(f"  会话活跃: {validated_session.is_active()}")
    else:
        print(f"  ❌ 会话验证失败")
        return False
    
    # 3. 测试心跳更新
    print("\n💓 步骤3: 心跳更新测试")
    heartbeat_success = strict_session_manager.heartbeat(session_id)
    if heartbeat_success:
        print(f"  ✅ 心跳更新成功")
    else:
        print(f"  ❌ 心跳更新失败")
        return False
    
    # 4. 测试获取操作集
    print("\n⚙️  步骤4: 操作集获取测试")
    operations = strict_session_manager.get_operations_for_session(session_id)
    print(f"  ✅ 获取到操作集: {operations}")
    
    # 5. 测试会话统计
    print("\n📊 步骤5: 会话统计测试")
    stats = strict_session_manager.get_session_stats()
    print(f"  ✅ 会话统计:")
    for key, value in stats.items():
        print(f"    {key}: {value}")
    
    return True

def test_session_cleanup():
    """测试会话清理机制"""
    print("\n🧹 步骤6: 会话清理测试")
    
    # 创建即将过期的会话
    expiring_session_id = "expiring-session-456"
    expiring_session = strict_session_manager.register_session(
        session_id=expiring_session_id,
        client_metadata={"client_type": "expiring_client"},
        operation_set=["expiring_op"]
    )
    
    # 手动设置会话过期
    expiring_session.expires_at = datetime.now() - timedelta(minutes=1)
    print(f"  创建过期会话: {expiring_session_id}")
    
    # 执行清理
    print(f"  执行严格清理...")
    strict_session_manager._perform_strict_cleanup()
    
    # 验证清理结果
    remaining_session = strict_session_manager.validate_session(expiring_session_id)
    if remaining_session is None:
        print(f"  ✅ 过期会话已成功清理")
        return True
    else:
        print(f"  ❌ 过期会话清理失败")
        return False

def test_concurrent_sessions():
    """测试并发会话处理"""
    print("\n🔄 步骤7: 并发会话测试")
    
    session_ids = []
    
    # 创建多个会话
    for i in range(5):
        session_id = f"concurrent-session-{i}"
        session_ids.append(session_id)
        strict_session_manager.register_session(
            session_id=session_id,
            client_metadata={"client_type": f"concurrent_client_{i}"},
            operation_set=[f"op_{i}_1", f"op_{i}_2"]
        )
    
    print(f"  ✅ 创建了 {len(session_ids)} 个并发会话")
    
    # 验证所有会话
    valid_count = 0
    for session_id in session_ids:
        if strict_session_manager.validate_session(session_id):
            valid_count += 1
    
    print(f"  ✅ 成功验证 {valid_count}/{len(session_ids)} 个会话")
    
    # 清理所有会话
    for session_id in session_ids:
        strict_session_manager.unregister_session(session_id)
    
    final_stats = strict_session_manager.get_session_stats()
    if final_stats['total_sessions'] == 0:
        print(f"  ✅ 所有会话已成功清理")
        return True
    else:
        print(f"  ❌ 仍有 {final_stats['total_sessions']} 个会话未清理")
        return False

def main():
    """主测试函数"""
    print("🚀 开始严格会话管理功能测试")
    
    tests = [
        ("会话生命周期", test_session_lifecycle),
        ("会话清理机制", test_session_cleanup),
        ("并发会话处理", test_concurrent_sessions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} 测试通过")
            else:
                print(f"\n❌ {test_name} 测试失败")
        except Exception as e:
            print(f"\n💥 {test_name} 测试异常: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"🏁 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！严格会话管理功能工作正常")
    else:
        print("⚠️  部分测试失败，请检查实现")
    
    print("=" * 80)

if __name__ == "__main__":
    main()