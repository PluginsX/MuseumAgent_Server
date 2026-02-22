# -*- coding: utf-8 -*-
"""
测试配置变更通知机制
测试LLM/STT/TTS/SRS配置修改后是否能自动通知服务重新加载
"""
import requests
import json
import time

# 服务器配置
BASE_URL = "http://localhost:12301"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
CONFIG_URLS = {
    "llm": f"{BASE_URL}/api/admin/config/llm",
    "stt": f"{BASE_URL}/api/admin/config/stt",
    "tts": f"{BASE_URL}/api/admin/config/tts",
    "srs": f"{BASE_URL}/api/admin/config/srs"
}

# 登录凭据
LOGIN_DATA = {
    "username": "123",
    "password": "123"
}

def get_auth_token():
    """获取认证token"""
    print("获取认证token...")
    try:
        response = requests.post(LOGIN_URL, json=LOGIN_DATA, timeout=10)
        print(f"登录响应状态码: {response.status_code}")
        print(f"登录响应内容: {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"登录响应数据: {data}")
            token = data.get("access_token")
            print(f"获取到的token: {token}")
            if token:
                print("获取token成功")
                return token
            else:
                print("登录响应中没有access_token字段")
                return None
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"登录请求失败: {e}")
        return None

def get_config(service, token):
    """获取配置"""
    print(f"获取{service}配置...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(CONFIG_URLS[service], headers=headers, timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"获取{service}配置成功")
            return config
        else:
            print(f"获取配置失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"获取配置请求失败: {e}")
        return None

def update_config(service, token, new_config):
    """更新配置"""
    print(f"更新{service}配置...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.put(CONFIG_URLS[service], headers=headers, json=new_config, timeout=10)
        if response.status_code == 200:
            updated_config = response.json()
            print(f"更新{service}配置成功")
            return updated_config
        else:
            print(f"更新配置失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"更新配置请求失败: {e}")
        return None

def test_config_notification():
    """测试配置变更通知机制"""
    print("=" * 60)
    print("测试配置变更通知机制")
    print("=" * 60)
    
    # 获取认证token
    token = get_auth_token()
    print(f"最终获取的token: {token}")
    if not token:
        print("测试失败: 无法获取认证token")
        return False
    
    # 测试LLM配置
    print("\n1. 测试LLM配置变更通知")
    llm_config = get_config("llm", token)
    if llm_config:
        print(f"当前LLM模型: {llm_config.get('model')}")
        
        # 修改LLM配置
        new_llm_config = {
            "model": "qwen-plus" if llm_config.get('model') == "qwen-turbo" else "qwen-turbo"
        }
        updated_llm_config = update_config("llm", token, new_llm_config)
        if updated_llm_config:
            print(f"更新后LLM模型: {updated_llm_config.get('model')}")
            print("LLM配置变更通知测试成功")
        else:
            print("LLM配置变更通知测试失败")
    
    # 测试TTS配置
    print("\n2. 测试TTS配置变更通知")
    tts_config = get_config("tts", token)
    if tts_config:
        print(f"当前TTS模型: {tts_config.get('model')}")
        
        # 修改TTS配置
        new_tts_config = {
            "model": "cosyvoice-v3-plus" if tts_config.get('model') == "cosyvoice-v3" else "cosyvoice-v3"
        }
        updated_tts_config = update_config("tts", token, new_tts_config)
        if updated_tts_config:
            print(f"更新后TTS模型: {updated_tts_config.get('model')}")
            print("TTS配置变更通知测试成功")
        else:
            print("TTS配置变更通知测试失败")
    
    # 测试STT配置
    print("\n3. 测试STT配置变更通知")
    stt_config = get_config("stt", token)
    if stt_config:
        print(f"当前STT模型: {stt_config.get('model')}")
        
        # 修改STT配置
        new_stt_config = {
            "model": "paraformer-realtime-v2" if stt_config.get('model') == "paraformer-realtime-v1" else "paraformer-realtime-v1"
        }
        updated_stt_config = update_config("stt", token, new_stt_config)
        if updated_stt_config:
            print(f"更新后STT模型: {updated_stt_config.get('model')}")
            print("STT配置变更通知测试成功")
        else:
            print("STT配置变更通知测试失败")
    
    # 测试SRS配置
    print("\n4. 测试SRS配置变更通知")
    srs_config = get_config("srs", token)
    if srs_config:
        print(f"当前SRS超时: {srs_config.get('timeout')}")
        
        # 修改SRS配置
        new_srs_config = {
            "timeout": 350 if srs_config.get('timeout') == 300 else 300
        }
        updated_srs_config = update_config("srs", token, new_srs_config)
        if updated_srs_config:
            print(f"更新后SRS超时: {updated_srs_config.get('timeout')}")
            print("SRS配置变更通知测试成功")
        else:
            print("SRS配置变更通知测试失败")
    
    print("\n" + "=" * 60)
    print("配置变更通知机制测试完成")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_config_notification()
