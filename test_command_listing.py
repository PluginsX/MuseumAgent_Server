#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令列表查询功能测试
"""

import requests
import json

def test_command_listing():
    base_url = "https://localhost:8000"
    
    print("📋 指令列表查询功能测试")
    print("=" * 35)
    
    # 注册会话
    session_data = {
        'client_metadata': {
            'client_id': 'list-test',
            'client_type': 'spirit'
        },
        'operation_set': ['idle_mode', 'walk_action', 'run_action', 'sleep_mode']
    }
    
    try:
        session_id = requests.post(
            f"{base_url}/api/session/register",
            json=session_data,
            verify=False,
            timeout=10
        ).json()['session_id']
        
        print(f"✅ 会话注册成功: {session_id}")
        print(f"📋 注册指令: {session_data['operation_set']}")
        
        # 测试各种查询指令的方式
        query_inputs = [
            "请问我提供了哪些指令集",
            "列出所有可用指令",
            "显示指令列表",
            "有哪些指令可以使用",
            "查看当前指令集"
        ]
        
        print(f"\n🧪 查询测试:")
        print("-" * 20)
        
        for user_input in query_inputs:
            result = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": user_input,
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
                operation = data["operation"]
                response = data.get("response", "")
                
                status = "✅" if operation == "list_commands" else "❌"
                print(f"{status} \"{user_input}\"")
                if operation == "list_commands":
                    print(f"   回复: {response}")
                else:
                    print(f"   错误识别为: {operation}")
        
        # 对比测试：普通对话
        print(f"\n📊 对比测试:")
        print("-" * 20)
        
        normal_inputs = [
            "你好",
            "今天天气怎么样",
            "介绍一下博物馆"
        ]
        
        for user_input in normal_inputs:
            result = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": user_input,
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
                status = "✅" if operation == "general_chat" else "⚠️"
                print(f"{status} \"{user_input}\" -> {operation}")
        
        # 清理会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        print(f"\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    test_command_listing()