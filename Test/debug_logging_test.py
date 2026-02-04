#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的调试日志输出
"""

import sys
import os
import json
import requests
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def test_debug_logging():
    """测试调试日志输出"""
    print("=" * 80)
    print("🧪 调试日志输出测试")
    print("=" * 80)
    
    base_url = "https://localhost:8000"
    session = requests.Session()
    session.verify = False
    
    try:
        # 1. 注册会话
        print("\n1. 注册测试会话")
        print("-" * 40)
        
        response = session.post(
            f"{base_url}/api/session/register",
            json={
                "client_metadata": {
                    "client_id": "debug_logging_test",
                    "client_type": "test",
                    "client_version": "1.0.0"
                },
                "functions": []  # 普通对话模式
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 会话注册失败")
            return
            
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✅ 会话注册成功: {session_id[:8]}...")
        
        # 2. 发送测试请求
        print("\n2. 发送测试请求")
        print("-" * 40)
        print("请查看服务器控制台输出，您将看到详细的调试信息：")
        print("• LLM请求负载")
        print("• LLM原始响应") 
        print("• CommandGenerator处理过程")
        print("• API层数据流转")
        print("• StandardCommand序列化过程")
        print("-" * 40)
        
        test_message = "你好"
        
        response = session.post(
            f"{base_url}/api/agent/parse",
            headers={"session-id": session_id},
            json={
                "user_input": test_message,
                "client_type": "test",
                "scene_type": "public"
            },
            timeout=15
        )
        
        print(f"\n📤 客户端发送: {test_message}")
        print(f"📥 客户端接收 HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200 and result.get('data'):
                data = result['data']
                print(f"📊 客户端收到的最终数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 统计字段
                llm_fields = ["choices", "created", "id", "model", "object", "usage"]
                found_llm_fields = [field for field in llm_fields if field in data]
                total_fields = len(data)
                
                print(f"\n📈 数据统计:")
                print(f"  LLM原始字段: {len(found_llm_fields)}/{len(llm_fields)}")
                print(f"  总字段数: {total_fields}")
                print(f"  多余字段: {total_fields - len(found_llm_fields)}")
                
            else:
                print(f"❌ API响应异常: {result}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🚀 调试日志输出验证测试")
    print("请同时查看服务器控制台的详细输出")
    print()
    
    test_debug_logging()
    
    print(f"\n🏁 测试完成")
    print("💡 提示：服务器控制台现在会显示每个步骤的详细数据流转信息")