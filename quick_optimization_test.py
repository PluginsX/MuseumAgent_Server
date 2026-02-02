#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证优化后的指令识别
"""

import requests
import json

def quick_verification():
    base_url = "https://localhost:8000"
    
    print("⚡ 快速验证优化效果")
    print("=" * 30)
    
    # 使用优化后的指令命名
    optimized_operations = [
        'idle_mode', 'walk_action', 'run_action', 'sprint_action', 
        'speak_action', 'happy_emotion', 'cry_action', 'sleep_mode'
    ]
    
    try:
        # 注册优化后的会话
        session_data = {
            'client_metadata': {
                'client_id': 'optimization-test',
                'client_type': 'spirit'
            },
            'operation_set': optimized_operations
        }
        
        session_id = requests.post(
            f"{base_url}/api/session/register",
            json=session_data,
            verify=False,
            timeout=10
        ).json()['session_id']
        
        print(f"✅ 会话注册成功")
        print(f"📋 优化后指令: {optimized_operations}")
        
        # 测试用例
        test_cases = [
            ("sleep_mode", "直接指令名"),
            ("执行 sleep_mode", "带动词指令"),
            ("我要睡觉", "自然语言"),
            ("进入睡眠状态", "状态描述"),
            ("跑步", "中文动作"),
            ("开心一下", "情感表达")
        ]
        
        print(f"\n🧪 测试结果:")
        print("-" * 20)
        
        success_count = 0
        for user_input, description in test_cases:
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
                if operation in optimized_operations:
                    status = "✅"
                    success_count += 1
                else:
                    status = "❌"
                print(f"{status} {description}: \"{user_input}\" -> {operation}")
        
        success_rate = (success_count / len(test_cases)) * 100
        print(f"\n📊 成功率: {success_count}/{len(test_cases)} ({success_rate:.1f}%)")
        
        if success_rate >= 70:
            print("🎉 优化效果良好！")
            print("建议采用这种命名策略")
        elif success_rate >= 40:
            print("⚠️  效果一般，可继续优化")
        else:
            print("❌ 仍需进一步优化")
        
        # 清理会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        
    except Exception as e:
        print(f"❌ 验证异常: {e}")

if __name__ == "__main__":
    quick_verification()