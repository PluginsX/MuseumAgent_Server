#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通用对话模式功能
"""

import requests
import json

def test_general_chat_mode():
    base_url = "https://localhost:8000"
    
    print("💬 测试通用对话模式")
    print("=" * 50)
    
    # 测试用例：混合文物相关和普通对话
    test_cases = [
        {
            "input": "你好！",
            "type": "普通问候",
            "expect_general_chat": True
        },
        {
            "input": "今天天气怎么样？",
            "type": "日常对话", 
            "expect_general_chat": True
        },
        {
            "input": "介绍一下蟠龙盖罍",
            "type": "文物查询",
            "expect_general_chat": False
        },
        {
            "input": "博物馆几点开门？",
            "type": "场馆咨询",
            "expect_general_chat": True
        },
        {
            "input": "放大查看卷体夔纹蟠龙盖罍的纹样",
            "type": "文物操作",
            "expect_general_chat": False
        }
    ]
    
    # 先注册一个简单的会话
    registration_data = {
        "client_metadata": {
            "client_id": "test-general-chat",
            "client_type": "custom",
            "client_version": "1.0.0",
            "platform": "test"
        },
        "operation_set": ["zoom_pattern", "introduce", "general_chat"]  # 包含通用对话指令
    }
    
    try:
        # 注册会话
        reg_response = requests.post(
            f"{base_url}/api/session/register",
            json=registration_data,
            verify=False,
            timeout=10
        )
        
        if reg_response.status_code != 200:
            print("❌ 会话注册失败")
            return
            
        session_id = reg_response.json()["session_id"]
        print(f"✅ 会话注册成功: {session_id}")
        
        # 测试各个用例
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 测试 {i}: {test_case['type']} ---")
            print(f"输入: {test_case['input']}")
            
            try:
                response = requests.post(
                    f"{base_url}/api/agent/parse",
                    json={
                        "user_input": test_case['input'],
                        "client_type": "web",
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
                    operation = data["operation"]
                    artifact_name = data["artifact_name"]
                    
                    is_general_chat = (operation == "general_chat")
                    status = "✅" if is_general_chat == test_case["expect_general_chat"] else "❌"
                    
                    print(f"{status} 操作类型: {operation}")
                    if artifact_name:
                        print(f"   文物名称: {artifact_name}")
                    if "response" in data:
                        print(f"   回复内容: {data['response'][:50]}...")
                    print(f"   关键词: {data.get('keywords', [])}")
                    
                else:
                    print(f"❌ 处理失败: {result.get('msg', '未知错误')}")
                    
            except Exception as e:
                print(f"❌ 测试异常: {e}")
        
        # 注销会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        print("\n✅ 会话注销完成")
        
    except Exception as e:
        print(f"❌ 测试过程异常: {e}")

def test_current_behavior():
    """测试当前行为（应该会报错）"""
    print("\n🔍 测试当前行为（预期会报错）")
    print("=" * 50)
    
    try:
        response = requests.post(
            "https://localhost:8000/api/agent/parse",
            json={
                "user_input": "你好世界！",
                "client_type": "web",
                "scene_type": "public"
            },
            verify=False,
            timeout=15
        )
        
        result = response.json()
        if result["code"] != 200:
            print("✅ 当前行为正确：普通对话被拦截")
            print(f"   错误信息: {result.get('msg', '未知错误')}")
        else:
            print("❌ 当前行为异常：普通对话被接受了")
            
    except Exception as e:
        print(f"测试异常: {e}")

if __name__ == "__main__":
    print("🚀 开始测试通用对话模式")
    
    # 先测试当前行为
    test_current_behavior()
    
    # 再测试新功能
    test_general_chat_mode()
    
    print("\n🎯 测试完成")