#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令命名策略测试
测试不同命名方式对LLM识别的影响
"""

import requests
import json

def test_naming_strategies():
    base_url = "https://localhost:8000"
    
    print("🧪 指令命名策略测试")
    print("=" * 40)
    
    # 测试不同的指令命名方式
    naming_tests = [
        {
            "name": "动作类命名",
            "operations": ["idle_action", "walk_action", "run_action", "sleep_action"],
            "test_inputs": ["sleep_action", "执行 sleep_action", "我要睡觉"]
        },
        {
            "name": "功能类命名", 
            "operations": ["set_idle", "do_walk", "do_run", "do_sleep"],
            "test_inputs": ["do_sleep", "执行睡眠", "进入睡眠状态"]
        },
        {
            "name": "状态类命名",
            "operations": ["idle_state", "walking", "running", "sleeping"],
            "test_inputs": ["sleeping", "进入睡眠", "开始睡觉"]
        }
    ]
    
    try:
        for test_case in naming_tests:
            print(f"\n📋 {test_case['name']}测试:")
            print("-" * 30)
            
            # 注册会话
            session_data = {
                'client_metadata': {
                    'client_id': f"naming-test-{test_case['name']}",
                    'client_type': 'spirit'
                },
                'operation_set': test_case['operations']
            }
            
            session_id = requests.post(
                f"{base_url}/api/session/register",
                json=session_data,
                verify=False,
                timeout=10
            ).json()['session_id']
            
            print(f"注册指令: {test_case['operations']}")
            
            # 测试识别效果
            success_count = 0
            total_count = len(test_case['test_inputs'])
            
            for test_input in test_case['test_inputs']:
                result = requests.post(
                    f"{base_url}/api/agent/parse",
                    json={
                        "user_input": test_input,
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
                    if operation in test_case['operations']:
                        status = "✅"
                        success_count += 1
                    else:
                        status = "❌"
                    print(f"{status} \"{test_input}\" -> {operation}")
            
            success_rate = (success_count / total_count) * 100
            print(f"成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
            
            # 清理会话
            requests.delete(
                f"{base_url}/api/session/unregister",
                headers={"session-id": session_id},
                verify=False
            )
        
        print(f"\n🎯 建议:")
        print("如果某种命名方式识别率较高，建议采用该命名策略")
        print("通常带有'action'、'do_'、'_state'等后缀的命名更容易被识别")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    test_naming_strategies()