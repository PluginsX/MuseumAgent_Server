#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
会话管理配置测试脚本
验证配置加载、更新、重置等功能
"""

import sys
import os
import json
import requests
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 初始化配置
from src.common.config_utils import load_config
load_config()

from src.session.strict_session_manager import strict_session_manager

def test_config_loading():
    """测试配置加载功能"""
    print("📋 测试配置加载功能")
    print("-" * 50)
    
    try:
        # 检查配置是否正确加载
        config = strict_session_manager.config
        print(f"✅ 配置加载成功")
        print(f"   会话超时: {config['session_timeout_minutes']} 分钟")
        print(f"   不活跃超时: {config['inactivity_timeout_minutes']} 分钟")
        print(f"   心跳超时: {config['heartbeat_timeout_minutes']} 分钟")
        print(f"   清理间隔: {config['cleanup_interval_seconds']} 秒")
        print(f"   自动清理: {'启用' if config['enable_auto_cleanup'] else '禁用'}")
        
        # 检查运行时参数
        print(f"\n🔧 运行时参数:")
        print(f"   Session Timeout: {strict_session_manager.session_timeout}")
        print(f"   Inactivity Timeout: {strict_session_manager.inactivity_timeout}")
        print(f"   Heartbeat Timeout: {strict_session_manager.heartbeat_timeout}")
        print(f"   Cleanup Interval: {strict_session_manager.cleanup_interval}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载测试失败: {str(e)}")
        return False

def test_config_api():
    """测试配置API功能"""
    print("\n🌐 测试配置API功能")
    print("-" * 50)
    
    base_url = "https://localhost:8000"
    
    try:
        # 1. 获取当前配置
        print("1. 获取当前配置...")
        response = requests.get(f"{base_url}/api/admin/session-config/current", verify=False)
        if response.status_code == 200:
            config_data = response.json()
            print(f"✅ 获取配置成功")
            print(f"   当前配置项数: {len(config_data.get('current_config', {}))}")
            print(f"   运行时参数: {len(config_data.get('runtime_info', {}))}")
        else:
            print(f"❌ 获取配置失败: {response.status_code}")
            return False
        
        # 2. 验证配置格式
        print("\n2. 验证配置格式...")
        test_config = {
            "session_timeout_minutes": 10,
            "inactivity_timeout_minutes": 3,
            "heartbeat_timeout_minutes": 1,
            "cleanup_interval_seconds": 15,
            "enable_auto_cleanup": True
        }
        
        response = requests.post(f"{base_url}/api/admin/session-config/validate", 
                               json=test_config, verify=False)
        if response.status_code == 200:
            validation_result = response.json()
            if validation_result.get('is_valid'):
                print(f"✅ 配置格式验证通过")
            else:
                print(f"❌ 配置格式验证失败: {validation_result.get('errors')}")
                return False
        else:
            print(f"❌ 验证请求失败: {response.status_code}")
            return False
        
        # 3. 更新配置
        print("\n3. 更新配置...")
        update_config = {
            "session_timeout_minutes": 20,
            "cleanup_interval_seconds": 20,
            "log_level": "DEBUG"
        }
        
        response = requests.put(f"{base_url}/api/admin/session-config/update", 
                              json=update_config, verify=False)
        if response.status_code == 200:
            update_result = response.json()
            print(f"✅ 配置更新成功")
            print(f"   变更项数: {len(update_result.get('changes_made', []))}")
            print(f"   需要重启: {'是' if update_result.get('restart_required') else '否'}")
        else:
            print(f"❌ 配置更新失败: {response.status_code}")
            return False
        
        # 4. 验证更新结果
        print("\n4. 验证更新结果...")
        response = requests.get(f"{base_url}/api/admin/session-config/current", verify=False)
        if response.status_code == 200:
            current_config = response.json()['current_config']
            if (current_config.get('session_timeout_minutes') == 20 and 
                current_config.get('cleanup_interval_seconds') == 20):
                print(f"✅ 配置更新验证通过")
            else:
                print(f"❌ 配置更新验证失败")
                return False
        else:
            print(f"❌ 验证请求失败: {response.status_code}")
            return False
        
        # 5. 重置为默认配置
        print("\n5. 重置为默认配置...")
        response = requests.post(f"{base_url}/api/admin/session-config/reset-defaults", verify=False)
        if response.status_code == 200:
            reset_result = response.json()
            print(f"✅ 配置重置成功")
            print(f"   旧配置项数: {len(reset_result.get('old_config', {}))}")
            print(f"   新配置项数: {len(reset_result.get('new_config', {}))}")
        else:
            print(f"❌ 配置重置失败: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务已启动")
        return False
    except Exception as e:
        print(f"❌ API测试异常: {str(e)}")
        return False

def test_runtime_behavior():
    """测试运行时行为变化"""
    print("\n⚡ 测试运行时行为")
    print("-" * 50)
    
    try:
        # 修改清理间隔进行测试
        original_interval = strict_session_manager.cleanup_interval
        test_interval = 10  # 10秒
        
        print(f"原清理间隔: {original_interval}秒")
        print(f"设置测试间隔: {test_interval}秒")
        
        # 更新配置
        strict_session_manager.cleanup_interval = test_interval
        strict_session_manager.config['cleanup_interval_seconds'] = test_interval
        
        print(f"✅ 配置更新完成")
        print(f"新清理间隔: {strict_session_manager.cleanup_interval}秒")
        
        # 恢复原配置
        strict_session_manager.cleanup_interval = original_interval
        strict_session_manager.config['cleanup_interval_seconds'] = original_interval
        
        print(f"✅ 配置恢复完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 运行时行为测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🔧 会话管理配置功能测试")
    print("=" * 60)
    
    tests = [
        ("配置加载", test_config_loading),
        ("配置API", test_config_api),
        ("运行时行为", test_runtime_behavior)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} 测试通过")
            else:
                print(f"\n❌ {test_name} 测试失败")
        except Exception as e:
            print(f"\n💥 {test_name} 测试异常: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"🏁 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有配置功能测试通过！")
    else:
        print("⚠️  部分测试失败，请检查实现")
    
    print("=" * 60)

if __name__ == "__main__":
    main()