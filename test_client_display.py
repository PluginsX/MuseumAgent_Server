#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试客户端显示修复效果
"""

import requests
import json

def test_client_display_fix():
    base_url = "https://localhost:8000"
    
    print("🔧 测试客户端显示修复效果")
    print("=" * 40)
    
    # 注册会话
    registration_data = {
        "client_metadata": {
            "client_id": "display-test",
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
        
        # 测试普通对话
        print("\n📝 测试普通对话显示...")
        user_input = "你好！今天过得怎么样？"
        
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
            print("✅ 服务器响应:")
            print(f"   操作类型: {data['operation']}")
            print(f"   关键词: {data['keywords']}")
            if 'response' in data and data['response']:
                print(f"   回复内容: {data['response'][:100]}...")
            else:
                print("   ❌ 缺少回复内容字段")
            
            # 检查是否包含必要的字段用于客户端显示
            required_fields = ['operation', 'keywords']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ 缺少必要字段: {missing_fields}")
            else:
                print("✅ 包含所有必要字段用于客户端显示")
                
        else:
            print(f"❌ 请求失败: {result.get('msg', '未知错误')}")
        
        # 测试文物查询对比
        print("\n📝 测试文物查询显示...")
        user_input2 = "介绍一下蟠龙盖罍"
        
        response2 = requests.post(
            f"{base_url}/api/agent/parse",
            json={
                "user_input": user_input2,
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
        
        result2 = response2.json()
        if result2["code"] == 200 and result2["data"]:
            data2 = result2["data"]
            print("✅ 文物查询响应:")
            print(f"   操作类型: {data2['operation']}")
            print(f"   文物名称: {data2['artifact_name']}")
            print(f"   关键词: {data2['keywords']}")
            if 'tips' in data2 and data2['tips']:
                print(f"   文物介绍: {data2['tips'][:100]}...")
        
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
    test_client_display_fix()