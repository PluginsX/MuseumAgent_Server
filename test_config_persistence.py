import requests
import json

def test_config_persistence():
    """测试配置持久化功能"""
    base_url = "https://localhost:8000"
    headers = {"Authorization": "Bearer admin_token", "Content-Type": "application/json"}
    
    print("🧪 测试配置持久化功能...")
    
    # 1. 先获取当前配置
    print("\n1. 获取当前配置...")
    try:
        response = requests.get(f"{base_url}/api/admin/session-config/current", 
                              headers=headers, verify=False, timeout=10)
        if response.status_code == 200:
            current_config = response.json()['current_config']
            print(f"✅ 当前配置获取成功")
            print(f"   会话超时: {current_config['session_timeout_minutes']} 分钟")
            print(f"   不活跃超时: {current_config['inactivity_timeout_minutes']} 分钟")
        else:
            print(f"❌ 获取配置失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取配置异常: {e}")
        return False
    
    # 2. 更新配置
    print("\n2. 更新配置...")
    update_data = {
        "session_timeout_minutes": 12,
        "inactivity_timeout_minutes": 3
    }
    
    try:
        response = requests.put(f"{base_url}/api/admin/session-config/update",
                              headers=headers, json=update_data, verify=False, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 配置更新成功")
            print(f"   更改项数: {result['changes_made']}")
            print(f"   是否需要重启: {result['restart_required']}")
            if 'timestamp' in result:
                print(f"   更新时间: {result['timestamp']}")
        else:
            print(f"❌ 配置更新失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 配置更新异常: {e}")
        return False
    
    # 3. 验证配置是否持久化到文件
    print("\n3. 验证配置持久化...")
    try:
        with open('./config/config.json', 'r', encoding='utf-8') as f:
            config_file = json.load(f)
        
        session_config = config_file.get('session_management', {})
        if (session_config.get('session_timeout_minutes') == 12 and 
            session_config.get('inactivity_timeout_minutes') == 3):
            print(f"✅ 配置已成功持久化到 config.json")
            print(f"   文件中的会话超时: {session_config['session_timeout_minutes']} 分钟")
            print(f"   文件中的不活跃超时: {session_config['inactivity_timeout_minutes']} 分钟")
        else:
            print(f"❌ 配置未正确持久化到文件")
            print(f"   期望: 12分钟和3分钟")
            print(f"   实际: {session_config.get('session_timeout_minutes')}分钟和{session_config.get('inactivity_timeout_minutes')}分钟")
            return False
            
    except Exception as e:
        print(f"❌ 验证配置文件异常: {e}")
        return False
    
    print("\n🎉 配置持久化测试通过!")
    return True

if __name__ == "__main__":
    test_config_persistence()