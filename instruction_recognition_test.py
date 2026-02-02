#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令识别问题诊断和修复测试
"""

import requests
import json

def test_instruction_recognition():
    base_url = "https://localhost:8000"
    
    print("🔍 指令识别问题诊断")
    print("=" * 50)
    
    # 1. 注册包含具体指令的会话
    session_data = {
        'client_metadata': {
            'client_id': 'instruction-diagnosis',
            'client_type': 'custom',
            'client_version': '1.0.0',
            'platform': 'test'
        },
        'operation_set': ['Crying', 'Happy', 'Sleeping', 'Walk', 'Run', 'Sprint', 'Speaking']
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
        
        # 2. 测试各种指令输入格式
        test_cases = [
            {
                "input": "执行 Crying",
                "description": "标准指令格式1"
            },
            {
                "input": "Crying",
                "description": "纯指令名称"
            },
            {
                "input": "请执行哭泣动作",
                "description": "中文描述"
            },
            {
                "input": "运行跑步指令",
                "description": "动作+指令组合"
            },
            {
                "input": "让我看看你跑步",
                "description": "自然语言请求"
            },
            {
                "input": "表演一个开心的表情",
                "description": "情感表达请求"
            }
        ]
        
        print(f"\n🧪 指令识别测试:")
        print("-" * 40)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试 {i}: {test_case['description']}")
            print(f"输入: {test_case['input']}")
            
            response = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": test_case['input'],
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
                
                status = "✅" if operation in session_data['operation_set'] else "❌"
                print(f"   {status} 识别结果: {operation}")
                print(f"   文物名称: {artifact_name}")
                if operation == "general_chat":
                    print(f"   回复内容: {data.get('response', '')[:50]}...")
                    
            else:
                print(f"   ❌ 处理失败: {result.get('msg', '未知错误')}")
        
        # 3. 测试文物相关指令对比
        print(f"\n📊 文物相关指令对比测试:")
        print("-" * 40)
        
        artifact_test_cases = [
            "介绍一下蟠龙盖罍",
            "放大查看蟠龙纹样",
            "还原蟠龙的历史场景"
        ]
        
        for test_input in artifact_test_cases:
            response = requests.post(
                f"{base_url}/api/agent/parse",
                json={
                    "user_input": test_input,
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
                
                status = "✅" if artifact_name != "None" else "❌"
                print(f"输入: {test_input}")
                print(f"   {status} 操作: {operation}, 文物: {artifact_name}")
        
        # 注销会话
        requests.delete(
            f"{base_url}/api/session/unregister",
            headers={"session-id": session_id},
            verify=False
        )
        print(f"\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def analyze_prompt_issue():
    """分析提示词问题"""
    print(f"\n📝 提示词分析:")
    print("-" * 40)
    
    # 读取当前提示词
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    current_prompt = config['llm']['prompt_template']
    print(f"当前提示词: {current_prompt}")
    
    # 分析问题
    issues = []
    
    if "指令或general_chat" in current_prompt:
        issues.append("❌ 提示词没有明确说明可用的具体指令")
    
    if "文物名或null" in current_prompt:
        issues.append("❌ 对于非文物指令，'文物名'概念会造成混淆")
        
    if len(current_prompt) < 200:
        issues.append("❌ 提示词过于简短，缺乏足够的上下文指导")
    
    print(f"\n发现问题:")
    for issue in issues:
        print(f"   {issue}")
    
    if not issues:
        print("   暂未发现明显问题")

if __name__ == "__main__":
    test_instruction_recognition()
    analyze_prompt_issue()