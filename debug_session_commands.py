#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试会话指令集查询问题
"""

import requests
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_session_commands():
    base_url = "https://localhost:8000"
    
    print("🐛 会话指令集查询调试")
    print("=" * 30)
    
    # 用户提供的实际指令集
    actual_operations = ['idle', 'Walk', 'Run', 'Sprint', 'Speaking', 'Happy', 'Crying', 'Sleeping']
    
    try:
        # 1. 注册会话
        session_data = {
            'client_metadata': {
                'client_id': 'debug-test',
                'client_type': 'spirit'
            },
            'operation_set': actual_operations
        }
        
        session_response = requests.post(
            f"{base_url}/api/session/register",
            json=session_data,
            verify=False,
            timeout=10
        )
        session_id = session_response.json()['session_id']
        
        print(f"✅ 会话注册成功: {session_id}")
        print(f"📋 实际注册指令: {actual_operations}")
        
        # 2. 直接检查会话管理器
        from src.session.session_manager import session_manager
        session_ops = session_manager.get_operations_for_session(session_id)
        print(f"🔧 会话管理器返回的完整指令: {session_ops}")
        
        # 也检查原始会话对象
        raw_session = session_manager.get_session(session_id)
        if raw_session:
            print(f"🔧 原始会话注册的指令: {raw_session.operation_set}")
        else:
            print("❌ 无法获取原始会话对象")
        
        # 3. 测试指令查询
        result = requests.post(
            f"{base_url}/api/agent/parse",
            json={
                "user_input": "请问我提供了哪些指令集",
                "client_type": "spirit",
                "scene_type": "study"
            },
            headers={
                "session-id": session_id,
                "Content-Type": "application/json"
            },
            verify=False,
            timeout=30
        ).json()
        
        if result["code"] == 200 and result["data"]:
            data = result["data"]
            print(f"🤖 操作类型: {data['operation']}")
            print(f"💬 回复内容: {data['response']}")
            
            # 4. 分析问题原因
            print(f"\n🔍 问题分析:")
            if "基础指令集" in data['response']:
                print("❌ 系统返回了基础指令集而非会话指令集")
                print("可能原因:")
                print("  1. 会话ID传递问题")
                print("  2. 会话管理器查询问题") 
                print("  3. 命令生成器逻辑问题")
            elif "idle" in data['response'] and "Walk" in data['response']:
                print("✅ 系统正确返回了会话指令集")
            else:
                print("⚠️  返回内容异常")
        
        # 5. 测试其他查询方式
        print(f"\n🧪 其他查询测试:")
        other_queries = ["列出可用指令", "显示指令列表"]
        
        for query in other_queries:
            result = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": query,
                    "client_type": "spirit",
                    "scene_type": "study"
                },
                headers={
                    "session-id": session_id,
                    "Content-Type": "application/json"
                },
                verify=False,
                timeout=30
            ).json()
            
            if result["code"] == 200 and result["data"]:
                operation = result["data"]["operation"]
                response = result["data"]["response"]
                print(f"\"{query}\" -> {operation}: {response[:50]}...")
        
        # 清理会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        print(f"\n✅ 调试完成")
        
    except Exception as e:
        print(f"❌ 调试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_session_commands()