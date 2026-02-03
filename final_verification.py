#!/usr/bin/env python3
"""
会话管理修复验证脚本
验证之前修复的会话管理问题是否完全解决
"""

import requests
import json
import time
from datetime import datetime

def main():
    print("=" * 60)
    print("🏛️ 博物馆智能体服务器 - 会话管理修复验证")
    print("=" * 60)
    
    base_url = "https://localhost:8000"
    admin_headers = {"Authorization": "Bearer admin_token"}
    
    try:
        # 1. 测试会话注册
        print("\n📋 测试1: 会话注册功能")
        print("-" * 40)
        
        register_data = {
            "client_metadata": {
                "client_type": "verification_test",
                "client_id": "test_client_001",
                "platform": "test_script"
            },
            "operation_set": ["general_chat", "artifact_query", "exhibition_info"]
        }
        
        response = requests.post(
            f"{base_url}/api/session/register",
            json=register_data,
            headers={"Content-Type": "application/json"},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            session_info = response.json()
            session_id = session_info['session_id']
            print(f"✅ 会话注册成功!")
            print(f"   Session ID: {session_id}")
            print(f"   Expires at: {session_info['expires_at']}")
            print(f"   Supported features: {session_info['supported_features']}")
        else:
            print(f"❌ 会话注册失败: {response.status_code} - {response.text}")
            return False
        
        # 2. 测试客户端列表查询
        print("\n📋 测试2: 客户端列表查询")
        print("-" * 40)
        
        response = requests.get(
            f"{base_url}/api/admin/clients/connected",
            headers=admin_headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            clients = response.json()
            print(f"✅ 客户端列表查询成功!")
            print(f"   当前连接客户端数: {len(clients)}")
            for i, client in enumerate(clients, 1):
                print(f"   {i}. Session: {client.get('session_id', 'N/A')[:12]}...")
                print(f"      Client Type: {client.get('client_type', 'Unknown')}")
                print(f"      Operations: {len(client.get('operation_set', []))} 项")
                print(f"      Status: {'Active' if client.get('is_active', False) else 'Inactive'}")
        else:
            print(f"❌ 客户端列表查询失败: {response.status_code} - {response.text}")
            return False
        
        # 3. 测试会话统计
        print("\n📋 测试3: 会话统计信息")
        print("-" * 40)
        
        response = requests.get(
            f"{base_url}/api/admin/session/stats",
            headers=admin_headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 会话统计查询成功!")
            print(f"   总会话数: {stats['total_sessions']}")
            print(f"   活跃会话数: {stats['active_sessions']}")
            print(f"   过期会话数: {stats['expired_sessions']}")
            print(f"   断开会话数: {stats['disconnected_sessions']}")
            print(f"   不活跃会话数: {stats['inactive_sessions']}")
            print(f"   待清理会话数: {stats['cleanup_pending']}")
        else:
            print(f"❌ 会话统计查询失败: {response.status_code} - {response.text}")
            return False
        
        # 4. 测试心跳功能
        print("\n📋 测试4: 心跳更新功能")
        print("-" * 40)
        
        response = requests.post(
            f"{base_url}/api/session/heartbeat",
            headers={"session-id": session_id},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ 心跳更新成功!")
        else:
            print(f"❌ 心跳更新失败: {response.status_code} - {response.text}")
            return False
        
        # 5. 测试配置查询
        print("\n📋 测试5: 会话配置查询")
        print("-" * 40)
        
        response = requests.get(
            f"{base_url}/api/admin/session-config/current",
            headers=admin_headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            config_data = response.json()
            config = config_data['current_config']
            runtime = config_data['runtime_info']
            print(f"✅ 会话配置查询成功!")
            print(f"   会话超时: {config['session_timeout_minutes']} 分钟")
            print(f"   不活跃超时: {config['inactivity_timeout_minutes']} 分钟")
            print(f"   心跳超时: {config['heartbeat_timeout_minutes']} 分钟")
            print(f"   清理间隔: {config['cleanup_interval_seconds']} 秒")
            print(f"   自动清理: {'启用' if config['enable_auto_cleanup'] else '禁用'}")
            print(f"   心跳监控: {'启用' if config['enable_heartbeat_monitoring'] else '禁用'}")
        else:
            print(f"❌ 会话配置查询失败: {response.status_code} - {response.text}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过! 会话管理修复验证成功!")
        print("=" * 60)
        print("\n📊 修复总结:")
        print("   • 解决了 EnhancedClientSession 缺少 heartbeat_timeout 属性的问题")
        print("   • 修正了 is_disconnected 方法的参数传递")
        print("   • 修复了会话统计和状态检查中的属性访问错误")
        print("   • 确保了会话管理器的稳定运行")
        print("   • 验证了所有相关API接口的正常工作")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)