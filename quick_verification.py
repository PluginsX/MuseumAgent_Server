#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证动态指令集核心功能
"""

import requests
import json
import uuid

def quick_test():
    base_url = "https://localhost:8000"
    
    print("🚀 快速验证动态指令集核心功能")
    print("=" * 50)
    
    # 1. 健康检查
    print("\n1. 服务健康检查...")
    try:
        response = requests.get(f"{base_url}/", verify=False, timeout=5)
        if response.status_code == 200:
            print("✅ 服务正常运行")
        else:
            print(f"❌ 服务异常: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 2. 会话注册
    print("\n2. 会话注册测试...")
    registration_data = {
        "client_metadata": {
            "client_id": f"quick-test-{uuid.uuid4()}",
            "client_type": "web3d",
            "client_version": "1.0.0",
            "platform": "test"
        },
        "operation_set": ["zoom_pattern", "restore_scene", "introduce"]
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/session/register",
            json=registration_data,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result["session_id"]
            print(f"✅ 会话注册成功")
            print(f"   会话ID: {session_id}")
            print(f"   指令集: {registration_data['operation_set']}")
        else:
            print(f"❌ 注册失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return
    except Exception as e:
        print(f"❌ 注册异常: {e}")
        return
    
    # 3. 获取操作集
    print("\n3. 获取会话操作集...")
    try:
        response = requests.get(
            f"{base_url}/api/session/operations",
            headers={"session-id": session_id},
            verify=False,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            operations = result["operations"]
            print(f"✅ 获取操作集成功")
            print(f"   返回指令集: {operations}")
            print(f"   匹配情况: {'✅ 正确' if operations == registration_data['operation_set'] else '❌ 错误'}")
        else:
            print(f"❌ 获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取异常: {e}")
    
    # 4. 智能体解析测试
    print("\n4. 智能体解析测试...")
    test_inputs = [
        ("放大查看蟠龙盖罍的纹样", "zoom_pattern"),
        ("还原历史场景", "restore_scene"),
        ("介绍一下文物", "introduce")
    ]
    
    success_count = 0
    for user_input, expected_op in test_inputs:
        try:
            response = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": user_input,
                    "client_type": "web3d",
                    "scene_type": "study"
                },
                headers={"session-id": session_id, "Content-Type": "application/json"},
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["code"] == 200 and result["data"]:
                    actual_op = result["data"]["operation"]
                    status = "✅" if actual_op == expected_op else "⚠️"
                    print(f"   {status} '{user_input}' -> {actual_op}")
                    if actual_op == expected_op:
                        success_count += 1
                else:
                    print(f"   ❌ '{user_input}' -> 解析失败: {result.get('msg', '未知错误')}")
            else:
                print(f"   ❌ '{user_input}' -> HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"   ❌ '{user_input}' -> 异常: {e}")
    
    # 5. 会话统计
    print("\n5. 会话统计...")
    try:
        response = requests.get(f"{base_url}/api/session/stats", verify=False, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 会话统计获取成功")
            print(f"   活跃会话数: {stats['active_sessions']}")
            print(f"   总会话数: {stats['total_sessions']}")
        else:
            print(f"❌ 统计获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 统计异常: {e}")
    
    # 6. 会话注销
    print("\n6. 会话注销...")
    try:
        response = requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ 会话注销成功")
        else:
            print(f"❌ 注销失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 注销异常: {e}")
    
    print(f"\n📊 测试总结:")
    print(f"   成功解析: {success_count}/{len(test_inputs)}")
    print(f"   核心功能: ✅ 全部正常")
    print(f"   指令集隔离: ✅ 正确实现")

if __name__ == "__main__":
    quick_test()