import requests
import json
import time

def test_session_fix():
    """测试会话管理修复"""
    base_url = "https://localhost:8000"
    
    print("🔍 测试会话管理修复...")
    
    # 1. 测试会话注册
    print("\n1. 测试会话注册...")
    try:
        register_data = {
            "client_type": "test_client",
            "supported_operations": ["general_chat", "artifact_query"]
        }
        
        response = requests.post(
            f"{base_url}/api/session/register",
            json=register_data,
            verify=False,
            timeout=10
        )
        
        print(f"注册响应状态码: {response.status_code}")
        if response.status_code == 200:
            register_result = response.json()
            session_id = register_result.get('session_id')
            print(f"✅ 会话注册成功!")
            print(f"   Session ID: {session_id}")
            print(f"   Expires at: {register_result.get('expires_at')}")
        else:
            print(f"❌ 会话注册失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 会话注册异常: {e}")
        return False
    
    # 2. 测试客户端列表查询
    print("\n2. 测试客户端列表查询...")
    try:
        headers = {"Authorization": "Bearer admin_token"}
        response = requests.get(
            f"{base_url}/api/admin/clients/connected",
            headers=headers,
            verify=False,
            timeout=10
        )
        
        print(f"客户端列表响应状态码: {response.status_code}")
        if response.status_code == 200:
            clients = response.json()
            print(f"✅ 客户端列表查询成功!")
            print(f"   连接客户端数: {len(clients)}")
            for client in clients:
                print(f"   - {client.get('session_id', 'N/A')[:8]}... - {client.get('client_type', 'Unknown')}")
        else:
            print(f"❌ 客户端列表查询失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 客户端列表查询异常: {e}")
        return False
    
    # 3. 测试会话统计信息
    print("\n3. 测试会话统计信息...")
    try:
        response = requests.get(
            f"{base_url}/api/admin/session/stats",
            headers=headers,
            verify=False,
            timeout=10
        )
        
        print(f"会话统计响应状态码: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 会话统计查询成功!")
            print(f"   总会话数: {stats.get('total_sessions', 0)}")
            print(f"   活跃会话数: {stats.get('active_sessions', 0)}")
            print(f"   过期会话数: {stats.get('expired_sessions', 0)}")
            print(f"   断开会话数: {stats.get('disconnected_sessions', 0)}")
        else:
            print(f"❌ 会话统计查询失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 会话统计查询异常: {e}")
        return False
    
    # 4. 测试心跳功能
    print("\n4. 测试心跳功能...")
    try:
        response = requests.post(
            f"{base_url}/api/session/heartbeat",
            headers={"session-id": session_id},
            verify=False,
            timeout=10
        )
        
        print(f"心跳响应状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 心跳更新成功!")
        else:
            print(f"❌ 心跳更新失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 心跳更新异常: {e}")
    
    print("\n🎉 所有测试完成!")
    return True

if __name__ == "__main__":
    test_session_fix()