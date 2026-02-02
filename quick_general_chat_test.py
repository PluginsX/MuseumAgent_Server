#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证通用对话模式
"""

import requests
import json

def quick_test():
    base_url = "https://localhost:8000"
    
    print("🚀 快速验证通用对话模式")
    print("=" * 40)
    
    # 注册会话
    registration_data = {
        "client_metadata": {
            "client_id": "quick-test",
            "client_type": "custom",
            "client_version": "1.0.0",
            "platform": "test"
        },
        "operation_set": ["general_chat", "introduce"]
    }
    
    try:
        # 注册会话
        reg_response = requests.post(
            f"{base_url}/api/session/register",
            json=registration_data,
            verify=False,
            timeout=10
        )
        session_id = reg_response.json()["session_id"]
        print(f"✅ 会话注册成功: {session_id}")
        
        # 测试用例
        test_cases = [
            ("你好！", "普通问候"),
            ("介绍一下蟠龙盖罍", "文物查询"),
            ("今天天气如何？", "日常对话")
        ]
        
        for user_input, description in test_cases:
            print(f"\n📝 测试: {description}")
            print(f"输入: {user_input}")
            
            response = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": user_input,
                    "client_type": "custom",
                    "scene_type": "public"
                },
                headers={
                    "session-id": session_id,
                    "Content-Type": "application/json"
                },
                verify=False,
                timeout=15
            )
            
            result = response.json()
            if result["code"] == 200 and result["data"]:
                data = result["data"]
                print(f"✅ 成功!")
                print(f"   操作类型: {data['operation']}")
                if data['artifact_name']:
                    print(f"   文物名称: {data['artifact_name']}")
                if 'response' in data:
                    print(f"   回复内容: {data['response'][:50]}...")
                print(f"   关键词: {data['keywords']}")
            else:
                print(f"❌ 失败: {result.get('msg', '未知错误')}")
        
        # 注销会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    quick_test()