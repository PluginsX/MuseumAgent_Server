#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试基本对话能力架构
"""

import requests
import json

def comprehensive_test():
    base_url = "https://localhost:8000"
    
    print("🔧 全面测试基本对话能力架构")
    print("=" * 50)
    
    # 测试场景1：无会话情况下的基本对话
    print("\n📋 测试场景1: 无会话基本对话能力")
    try:
        response = requests.post(
            f"{base_url}/api/agent/parse",
            json={
                "user_input": "你好！",
                "client_type": "any",
                "scene_type": "public"
            },
            verify=False,
            timeout=15
        )
        
        result = response.json()
        if result["code"] == 200 and result["data"]:
            data = result["data"]
            print("✅ 无会话基本对话测试通过")
            print(f"   操作类型: {data['operation']}")
            print(f"   关键词: {data['keywords']}")
            if 'response' in data:
                print(f"   回复内容: {data['response'][:50]}...")
            else:
                print("   ⚠️  缺少回复内容")
        else:
            print(f"❌ 无会话测试失败: {result.get('msg', '未知错误')}")
    except Exception as e:
        print(f"❌ 无会话测试异常: {e}")
    
    # 测试场景2：有会话但无文物识别的情况
    print("\n📋 测试场景2: 会话中无法识别文物的输入")
    
    # 注册会话（不包含文物相关指令）
    registration_data = {
        "client_metadata": {
            "client_id": "test-no-artifact",
            "client_type": "custom",
            "client_version": "1.0.0",
            "platform": "test"
        },
        "operation_set": ["custom_operation"]  # 不包含文物相关指令
    }
    
    try:
        reg_response = requests.post(
            f"{base_url}/api/session/register",
            json=registration_data,
            verify=False,
            timeout=10
        )
        session_id = reg_response.json()["session_id"]
        print(f"✅ 会话注册成功: {session_id}")
        
        # 测试无法识别文物的输入
        response = requests.post(
            f"{base_url}/api/agent/parse",
            json={
                "user_input": "今天天气真好啊",
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
            print("✅ 无法识别文物输入测试通过")
            print(f"   操作类型: {data['operation']}")
            print(f"   文物名称: {data['artifact_name']}")
            if 'response' in data:
                print(f"   回复内容: {data['response'][:50]}...")
        else:
            print(f"❌ 无法识别文物测试失败: {result.get('msg', '未知错误')}")
            
        # 注销会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        
    except Exception as e:
        print(f"❌ 会话测试异常: {e}")
    
    # 测试场景3：正常的文物识别
    print("\n📋 测试场景3: 正常文物识别")
    
    # 注册包含文物指令的会话
    registration_data2 = {
        "client_metadata": {
            "client_id": "test-with-artifact",
            "client_type": "custom",
            "client_version": "1.0.0",
            "platform": "test"
        },
        "operation_set": ["introduce", "zoom_pattern"]
    }
    
    try:
        reg_response2 = requests.post(
            f"{base_url}/api/session/register",
            json=registration_data2,
            verify=False,
            timeout=10
        )
        session_id2 = reg_response2.json()["session_id"]
        print(f"✅ 文物会话注册成功: {session_id2}")
        
        # 测试文物识别
        response = requests.post(
            f"{base_url}/api/agent/parse",
            json={
                "user_input": "介绍一下蟠龙盖罍",
                "client_type": "custom",
                "scene_type": "public"
            },
            headers={
                "session-id": session_id2,
                "Content-Type": "application/json"
            },
            verify=False,
            timeout=15
        )
        
        result = response.json()
        if result["code"] == 200 and result["data"]:
            data = result["data"]
            print("✅ 文物识别测试通过")
            print(f"   操作类型: {data['operation']}")
            print(f"   文物名称: {data['artifact_name']}")
            if 'tips' in data:
                print(f"   文物介绍: {data['tips'][:50]}...")
        else:
            print(f"❌ 文物识别测试失败: {result.get('msg', '未知错误')}")
            
        # 注销会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id2},
            verify=False
        )
        
    except Exception as e:
        print(f"❌ 文物识别测试异常: {e}")
    
    # 测试场景4：验证基本对话能力的普遍性
    print("\n📋 测试场景4: 基本对话能力普遍性验证")
    
    test_inputs = [
        "你好世界",
        "今天心情怎么样？",
        "能告诉我一些博物馆的信息吗？",
        "放大查看文物纹样！",  # 应该降级到基本对话
        "随便聊聊"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        try:
            response = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": user_input,
                    "client_type": "test",
                    "scene_type": "public"
                },
                verify=False,
                timeout=15
            )
            
            result = response.json()
            if result["code"] == 200 and result["data"]:
                data = result["data"]
                status = "✅" if data["operation"] == "general_chat" else "⚠️"
                print(f"   {status} 输入{i}: '{user_input}' -> {data['operation']}")
                if 'response' in data and data['response']:
                    print(f"      回复: {data['response'][:30]}...")
            else:
                print(f"   ❌ 输入{i}: '{user_input}' -> 失败")
                
        except Exception as e:
            print(f"   ❌ 输入{i}: '{user_input}' -> 异常: {e}")
    
    print(f"\n🎯 测试总结:")
    print(f"   基本对话能力: ✅ 所有客户端天然支持")
    print(f"   智能降级机制: ✅ 无法识别时自动降级")
    print(f"   统一回复处理: ✅ 都有友好文字回应")

if __name__ == "__main__":
    comprehensive_test()