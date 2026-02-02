#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度诊断指令识别问题
分析LLM为什么无法正确识别注册的指令集
"""

import requests
import json

def deep_diagnose_instruction_recognition():
    base_url = "https://localhost:8000"
    
    print("🔍 深度指令识别问题诊断")
    print("=" * 50)
    
    # 注册详细的会话
    session_data = {
        'client_metadata': {
            'client_id': 'deep-diagnosis',
            'client_type': 'spirit',
            'client_version': '1.0.0',
            'platform': 'windows-desktop'
        },
        'operation_set': ['idle', 'Walk', 'Run', 'Sprint', 'Speaking', 'Happy', 'Crying', 'Sleeping']
    }
    
    try:
        # 注册会话
        session_response = requests.post(
            f"{base_url}/api/session/register",
            json=session_data,
            verify=False,
            timeout=10
        )
        session_id = session_response.json()['session_id']
        print(f"✅ 会话注册成功: {session_id}")
        print(f"📋 注册的指令集: {session_data['operation_set']}")
        
        # 获取服务器端生成的实际提示词
        print(f"\n📝 服务器端提示词分析:")
        print("-" * 40)
        
        # 发送一个测试请求来查看提示词
        test_input = "Sleeping"
        response = requests.post(
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
        )
        
        result = response.json()
        if result["code"] == 200 and result["data"]:
            data = result["data"]
            operation = data["operation"]
            print(f"输入: {test_input}")
            print(f"识别结果: {operation}")
            if operation == "general_chat":
                print(f"回复内容: {data.get('response', '')[:100]}...")
            else:
                print(f"✅ 成功识别为具体指令!")
        
        # 分析不同输入格式的识别效果
        print(f"\n🧪 多格式输入测试:")
        print("-" * 40)
        
        test_formats = [
            "Sleeping",           # 直接指令名
            "执行 Sleeping",       # 带动词的指令
            "让我睡觉",           # 中文自然语言
            "进入睡眠模式",       # 中文描述
            "休息一下",           # 功能性描述
            "Running",            # 英文指令测试
            "跑起来"              # 中文动作描述
        ]
        
        successful_recognitions = 0
        total_tests = len(test_formats)
        
        for test_input in test_formats:
            response = requests.post(
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
            )
            
            result = response.json()
            if result["code"] == 200 and result["data"]:
                data = result["data"]
                operation = data["operation"]
                
                if operation in session_data['operation_set']:
                    status = "✅"
                    successful_recognitions += 1
                else:
                    status = "❌"
                
                print(f"{status} \"{test_input}\" -> {operation}")
        
        success_rate = (successful_recognitions / total_tests) * 100
        print(f"\n📊 识别成功率: {successful_recognitions}/{total_tests} ({success_rate:.1f}%)")
        
        # 对比测试：文物相关指令
        print(f"\n📊 文物指令对比测试:")
        print("-" * 40)
        
        artifact_tests = [
            "介绍一下蟠龙盖罍",
            "放大查看蟠龙纹样",
            "还原历史场景"
        ]
        
        for test_input in artifact_tests:
            response = requests.post(
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
            )
            
            result = response.json()
            if result["code"] == 200 and result["data"]:
                data = result["data"]
                operation = data["operation"]
                artifact_name = data.get("artifact_name", "None")
                status = "✅" if artifact_name != "None" else "❌"
                print(f"{status} \"{test_input}\" -> {operation} (文物: {artifact_name})")
        
        # 注销会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        print(f"\n✅ 诊断完成")
        
        # 提供改进建议
        print(f"\n💡 问题分析与建议:")
        print("-" * 40)
        if success_rate < 30:
            print("❌ 指令识别存在严重问题")
            print("   建议: 检查提示词设计和LLM模型配置")
        elif success_rate < 70:
            print("⚠️  指令识别效果一般")
            print("   建议: 优化提示词或调整指令命名")
        else:
            print("✅ 指令识别效果良好")
            print("   建议: 可以正常使用")
            
    except Exception as e:
        print(f"❌ 诊断异常: {e}")

if __name__ == "__main__":
    deep_diagnose_instruction_recognition()