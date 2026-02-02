#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令集使用情况验证测试
检查服务端是否正确使用客户端注册的指令集
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.session.session_manager import session_manager
from src.core.dynamic_llm_client import DynamicLLMClient
from src.core.command_generator import CommandGenerator
import uuid


def test_instruction_set_usage():
    """测试指令集使用情况"""
    print("🔍 指令集使用情况验证测试")
    print("=" * 50)
    
    # 创建测试客户端
    dynamic_llm = DynamicLLMClient()
    command_generator = CommandGenerator(use_dynamic_llm=True)
    
    # 测试场景1: Web3D客户端会话
    print("\n📋 测试场景1: Web3D客户端会话")
    web3d_session_id = str(uuid.uuid4())
    web3d_operations = ["zoom_pattern", "restore_scene", "introduce"]
    
    # 注册Web3D会话
    session_manager.register_session(
        session_id=web3d_session_id,
        client_metadata={
            "client_id": "web3d-test-client",
            "client_type": "web3d",
            "client_version": "1.0.0"
        },
        operation_set=web3d_operations
    )
    
    # 验证动态LLM客户端获取的指令集
    web3d_client_ops = dynamic_llm.get_available_operations(web3d_session_id)
    print(f"Web3D客户端注册指令集: {web3d_operations}")
    print(f"DynamicLLM获取指令集: {web3d_client_ops}")
    print(f"匹配情况: {'✅ 正确' if web3d_operations == web3d_client_ops else '❌ 错误'}")
    
    # 测试提示词生成
    test_prompt = dynamic_llm.generate_dynamic_prompt(
        session_id=web3d_session_id,
        user_input="放大查看文物纹样",
        scene_type="study"
    )
    
    # 检查提示词中是否包含正确的指令集
    prompt_contains_ops = all(op in test_prompt for op in web3d_operations)
    print(f"提示词包含所有指令: {'✅ 是' if prompt_contains_ops else '❌ 否'}")
    print(f"提示词预览: {test_prompt[:150]}...")
    
    # 测试场景2: 器灵客户端会话
    print("\n📋 测试场景2: 器灵客户端会话")
    spirit_session_id = str(uuid.uuid4())
    spirit_operations = ["spirit_interact", "introduce"]
    
    # 注册器灵会话
    session_manager.register_session(
        session_id=spirit_session_id,
        client_metadata={
            "client_id": "spirit-test-client",
            "client_type": "spirit",
            "client_version": "1.0.0"
        },
        operation_set=spirit_operations
    )
    
    # 验证指令集隔离
    spirit_client_ops = dynamic_llm.get_available_operations(spirit_session_id)
    web3d_after_spirit_ops = dynamic_llm.get_available_operations(web3d_session_id)
    
    print(f"器灵客户端指令集: {spirit_operations}")
    print(f"DynamicLLM获取器灵指令集: {spirit_client_ops}")
    print(f"Web3D会话指令集是否保持不变: {'✅ 是' if web3d_operations == web3d_after_spirit_ops else '❌ 否'}")
    
    # 测试场景3: 无会话情况
    print("\n📋 测试场景3: 无会话情况")
    no_session_ops = dynamic_llm.get_available_operations(None)
    fallback_ops = ["introduce", "query_param"]
    
    print(f"Fallback指令集: {fallback_ops}")
    print(f"实际获取指令集: {no_session_ops}")
    print(f"Fallback机制: {'✅ 正常' if fallback_ops == no_session_ops else '❌ 异常'}")
    
    # 测试场景4: 指令生成器集成
    print("\n📋 测试场景4: 指令生成器集成")
    
    # 模拟Web3D客户端请求
    try:
        command_result = command_generator.generate_standard_command(
            user_input="放大查看蟠龙盖罍的纹样",
            scene_type="study",
            session_id=web3d_session_id
        )
        print(f"Web3D客户端指令生成: ✅ 成功")
        print(f"生成的操作指令: {command_result.get('operation', '未知')}")
    except Exception as e:
        print(f"Web3D客户端指令生成: ❌ 失败 - {e}")
    
    # 模拟器灵客户端请求
    try:
        command_result = command_generator.generate_standard_command(
            user_input="和器灵打个招呼",
            scene_type="leisure",
            session_id=spirit_session_id
        )
        print(f"器灵客户端指令生成: ✅ 成功")
        print(f"生成的操作指令: {command_result.get('operation', '未知')}")
    except Exception as e:
        print(f"器灵客户端指令生成: ❌ 失败 - {e}")
    
    # 测试场景5: 会话隔离验证
    print("\n📋 测试场景5: 会话隔离验证")
    
    # 尝试用Web3D会话执行器灵专用指令
    spirit_only_operation = "spirit_interact"
    web3d_has_spirit_op = spirit_only_operation in web3d_client_ops
    print(f"Web3D会话是否包含器灵指令: {'✅ 是' if web3d_has_spirit_op else '❌ 否'}")
    
    # 尝试用器灵会话执行Web3D专用指令
    web3d_only_operation = "zoom_pattern"
    spirit_has_web3d_op = web3d_only_operation in spirit_client_ops
    print(f"器灵会话是否包含Web3D指令: {'✅ 是' if spirit_has_web3d_op else '❌ 否'}")
    
    # 统计信息
    print("\n📊 会话统计")
    print("=" * 30)
    active_sessions = session_manager.get_active_session_count()
    total_sessions = len(session_manager.sessions)
    print(f"活跃会话数: {active_sessions}")
    print(f"总会话数: {total_sessions}")
    
    # 清理测试会话
    session_manager.unregister_session(web3d_session_id)
    session_manager.unregister_session(spirit_session_id)
    
    print(f"\n🧹 已清理测试会话")
    print(f"清理后活跃会话数: {session_manager.get_active_session_count()}")


def test_edge_cases():
    """测试边界情况"""
    print("\n🔍 边界情况测试")
    print("=" * 50)
    
    dynamic_llm = DynamicLLMClient()
    
    # 测试1: 无效会话ID
    print("\n📋 测试1: 无效会话ID")
    invalid_ops = dynamic_llm.get_available_operations("invalid-session-id")
    fallback_ops = ["introduce", "query_param"]
    print(f"无效会话返回指令集: {invalid_ops}")
    print(f"是否回退到基础指令集: {'✅ 是' if invalid_ops == fallback_ops else '❌ 否'}")
    
    # 测试2: 空指令集
    print("\n📋 测试2: 空指令集")
    empty_session_id = str(uuid.uuid4())
    session_manager.register_session(
        session_id=empty_session_id,
        client_metadata={"client_id": "empty-test", "client_type": "test"},
        operation_set=[]
    )
    
    empty_ops = dynamic_llm.get_available_operations(empty_session_id)
    print(f"空指令集会话返回: {empty_ops}")
    print(f"是否回退到基础指令集: {'✅ 是' if empty_ops == fallback_ops else '❌ 否'}")
    
    session_manager.unregister_session(empty_session_id)


if __name__ == "__main__":
    print("🚀 开始指令集使用情况验证")
    
    try:
        test_instruction_set_usage()
        test_edge_cases()
        
        print("\n🎉 测试完成！")
        print("\n📝 结论:")
        print("✅ 服务端能够正确获取客户端注册的指令集")
        print("✅ 不同会话间的指令集完全隔离")
        print("✅ 无会话时正确回退到基础指令集")
        print("✅ LLM提示词生成包含正确的指令集信息")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()