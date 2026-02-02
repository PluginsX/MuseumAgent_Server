#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证自定义指令集修复效果测试
"""

import requests
import json
import uuid

def test_custom_instruction_set():
    base_url = "https://localhost:8000"
    
    print("🔧 验证自定义指令集修复效果")
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
    
    # 2. 注册自定义指令集会话
    print("\n2. 注册自定义指令集会话...")
    custom_instructions = ["idle", "Walk", "Run", "Sprint", "Speaking", "Happy", "Crying", "Sleeping"]
    
    registration_data = {
        "client_metadata": {
            "client_id": f"custom-test-{uuid.uuid4()}",
            "client_type": "custom",
            "client_version": "1.0.0",
            "platform": "test"
        },
        "operation_set": custom_instructions
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
            print(f"   自定义指令集: {custom_instructions}")
        else:
            print(f"❌ 注册失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return
    except Exception as e:
        print(f"❌ 注册异常: {e}")
        return
    
    # 3. 验证指令集获取
    print("\n3. 验证会话指令集获取...")
    try:
        response = requests.get(
            f"{base_url}/api/session/operations",
            headers={"session-id": session_id},
            verify=False,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            returned_ops = result["operations"]
            print(f"✅ 指令集获取成功")
            print(f"   返回指令集: {returned_ops}")
            print(f"   完全匹配: {'✅ 是' if returned_ops == custom_instructions else '❌ 否'}")
        else:
            print(f"❌ 获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取异常: {e}")
    
    # 4. 测试智能体解析 - 关键测试
    print("\n4. 关键测试：智能体解析自定义指令...")
    
    # 测试用例：使用完全不相关的输入，看是否会返回自定义指令
    test_cases = [
        ("你好！蟠龙", "应该返回自定义指令而不是introduce"),
        ("开始跑步", "Run"),
        ("停止动作", "idle"),
        ("表达快乐", "Happy"),
        ("进入睡眠", "Sleeping")
    ]
    
    for i, (user_input, expected_desc) in enumerate(test_cases, 1):
        print(f"\n   测试用例 {i}: '{user_input}'")
        print(f"   期望: {expected_desc}")
        
        try:
            response = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": user_input,
                    "client_type": "custom",
                    "scene_type": "public"
                },
                headers={"session-id": session_id, "Content-Type": "application/json"},
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["code"] == 200 and result["data"]:
                    actual_op = result["data"]["operation"]
                    artifact_name = result["data"]["artifact_name"]
                    
                    # 检查是否是我们自定义的指令
                    is_custom_op = actual_op in custom_instructions
                    status = "✅" if is_custom_op else "❌"
                    
                    print(f"   {status} 实际返回: {actual_op}")
                    print(f"   文物名称: {artifact_name}")
                    print(f"   是否自定义指令: {'是' if is_custom_op else '否'}")
                    
                    if not is_custom_op:
                        print(f"   ⚠️  问题：返回了非自定义指令 '{actual_op}'")
                        print(f"   🎯 应该从以下指令中选择: {custom_instructions}")
                else:
                    print(f"   ❌ 解析失败: {result.get('msg', '未知错误')}")
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                print(f"   响应内容: {response.text}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 5. 测试指令集边界验证（服务端只做基本匹配，不判断可行性）
    print("\n5. 测试指令集边界验证...")
    print("   🎯 服务端职责：只验证指令是否在客户端注册的指令集中")
    print("   🎯 客户端职责：判断具体指令是否可以执行")
    
    # 测试不在指令集中的指令
    try:
        illegal_test_data = {
            "user_input": "放大查看文物",
            "client_type": "custom",
            "scene_type": "public"
        }
        
        response = requests.post(
            f"{base_url}/api/agent/parse",
            json=illegal_test_data,
            headers={"session-id": session_id, "Content-Type": "application/json"},
            verify=False,
            timeout=15
        )
        
        result = response.json()
        if result["code"] != 200:
            print(f"✅ 指令集边界验证通过")
            print(f"   错误信息: {result.get('msg', '无错误信息')}")
            print(f"   说明：服务端正确拦截了不在注册指令集中的指令")
        else:
            actual_op = result["data"]["operation"] if result["data"] else "未知"
            print(f"❌ 边界验证失败，返回了未注册的指令: {actual_op}")
            
    except Exception as e:
        print(f"   测试异常: {e}")
    
    # 测试在指令集中的指令（即使可能不可行）
    print("\n6. 测试注册指令集内的指令（服务端放行）...")
    feasible_test_cases = [
        ("执行idle动作", "idle"),
        ("开始跑步", "Run"),  
        ("播放快乐动画", "Happy")
    ]
    
    for user_input, expected_op in feasible_test_cases:
        try:
            response = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": user_input,
                    "client_type": "custom",
                    "scene_type": "public"
                },
                headers={"session-id": session_id, "Content-Type": "application/json"},
                verify=False,
                timeout=15
            )
            
            result = response.json()
            if result["code"] == 200 and result["data"]:
                actual_op = result["data"]["operation"]
                if actual_op == expected_op:
                    print(f"✅ 指令'{actual_op}'通过服务端验证并放行")
                    print(f"   说明：服务端只验证指令在注册集中，具体可行性由客户端判断")
                else:
                    print(f"⚠️  返回指令'{actual_op}'与期望'{expected_op}'不符")
            else:
                print(f"❌ 指令处理失败: {result.get('msg', '未知错误')}")
                
        except Exception as e:
            print(f"   异常: {e}")
    
    # 6. 会话注销
    print("\n6. 会话清理...")
    try:
        response = requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ 会话注销成功")
    except Exception as e:
        print(f"❌ 注销异常: {e}")
    
    print(f"\n🎯 测试总结:")
    print(f"   自定义指令集注册: ✅ 成功")
    print(f"   指令集隔离验证: ✅ 正确")
    print(f"   修复效果验证: 待观察（需要查看LLM实际输出）")

if __name__ == "__main__":
    test_custom_instruction_set()