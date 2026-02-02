#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令识别修复验证测试
"""

import requests
import json

def test_instruction_fix():
    base_url = "https://localhost:8000"
    
    print("🔧 指令识别修复验证")
    print("=" * 40)
    
    # 注册会话
    session_data = {
        'client_metadata': {
            'client_id': 'fix-validation',
            'client_type': 'custom'
        },
        'operation_set': ['Crying', 'Happy', 'Walk', 'Run']
    }
    
    try:
        session_response = requests.post(
            f"{base_url}/api/session/register",
            json=session_data,
            verify=False,
            timeout=10
        )
        session_id = session_response.json()['session_id']
        print(f"✅ 会话注册成功: {session_id}")
        print(f"📋 可用指令: {session_data['operation_set']}")
        
        # 测试用例
        test_cases = [
            ("执行 Crying", "指令识别测试1"),
            ("跑步", "指令识别测试2"), 
            ("开心一下", "指令识别测试3"),
            ("介绍一下蟠龙盖罍", "文物查询对比")
        ]
        
        print(f"\n🧪 测试结果:")
        print("-" * 30)
        
        for user_input, description in test_cases:
            response = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": user_input,
                    "client_type": "custom", 
                    "scene_type": "study"
                },
                headers={
                    "session-id": session_id,
                    "Content-Type": "application/json"
                },
                verify=False,
                timeout=30
            )
            
            result = response.json()
            if result["code"] == 200 and result["data"]:
                data = result["data"]
                operation = data["operation"]
                artifact_name = data.get("artifact_name", "None")
                
                # 判断是否成功识别
                if operation in session_data['operation_set']:
                    status = "✅"
                    result_desc = f"正确识别为指令: {operation}"
                elif operation != "general_chat" and artifact_name != "None":
                    status = "✅" 
                    result_desc = f"正确识别为文物操作: {operation}"
                else:
                    status = "❌"
                    result_desc = f"错误识别为: {operation}"
                
                print(f"{status} {description}")
                print(f"   输入: {user_input}")
                print(f"   结果: {result_desc}")
                print()
        
        # 清理会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        print("✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    test_instruction_fix()