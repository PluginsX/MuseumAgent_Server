#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器端直接测试指令集查询
通过API端点进行测试，避免进程隔离问题
"""

import requests
import json

def server_side_test():
    base_url = "https://localhost:8000"
    
    print("🚀 服务器端指令集查询测试")
    print("=" * 35)
    
    # 用户提供的实际指令集
    actual_operations = ['idle', 'Walk', 'Run', 'Sprint', 'Speaking', 'Happy', 'Crying', 'Sleeping']
    
    try:
        # 1. 注册会话
        session_data = {
            'client_metadata': {
                'client_id': 'server-test',
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
        session_result = session_response.json()
        session_id = session_result['session_id']
        
        print(f"✅ 会话注册成功: {session_id}")
        print(f"📋 注册指令: {actual_operations}")
        print(f"📋 API返回的指令: {session_result.get('operations', [])}")
        
        # 2. 立即查询指令集（在同一会话中）
        query_result = requests.post(
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
        
        if query_result["code"] == 200 and query_result["data"]:
            data = query_result["data"]
            print(f"🤖 操作类型: {data['operation']}")
            print(f"💬 回复内容: {data['response']}")
            
            # 3. 验证回复内容
            print(f"\n🔍 验证结果:")
            if all(op in data['response'] for op in ['idle', 'Walk', 'Run']):
                print("✅ 系统正确返回了完整的会话指令集")
            elif "基础指令集" in data['response']:
                print("❌ 系统返回了基础指令集（有问题）")
            else:
                print("⚠️  回复内容不完整")
        
        # 4. 测试其他查询方式
        print(f"\n🧪 多方式查询测试:")
        test_queries = [
            "列出所有可用指令",
            "显示指令列表",
            "有哪些指令可以使用"
        ]
        
        for query in test_queries:
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
                status = "✅" if operation == "list_commands" else "❌"
                print(f"{status} \"{query}\" -> {operation}")
                if operation == "list_commands":
                    print(f"   指令内容: {response}")
        
        # 5. 清理会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        print(f"\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    server_side_test()