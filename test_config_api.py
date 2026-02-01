import requests
import urllib3
import json

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_config_api():
    print("测试配置API...")
    
    # 先登录获取token
    try:
        login_response = requests.post(
            "https://localhost:8000/api/auth/login",
            json={"username": "admin", "password": "Admin@123"},
            verify=False,
            timeout=10
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('access_token')
            print(f"获取到token: {token[:20]}...")
            
            # 测试LLM配置API（脱敏版本）
            headers = {"Authorization": f"Bearer {token}"}
            llm_response = requests.get(
                "https://localhost:8000/api/admin/config/llm",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            print(f"\nLLM配置API状态码: {llm_response.status_code}")
            if llm_response.status_code == 200:
                llm_data = llm_response.json()
                print("LLM配置数据:")
                print(json.dumps(llm_data, indent=2, ensure_ascii=False))
                
                # 检查是否有api_key字段
                if 'data' in llm_data and 'api_key' in llm_data['data']:
                    print(f"\nAPI Key: {llm_data['data']['api_key']}")
                else:
                    print("未找到api_key字段")
            else:
                print(f"LLM配置API错误: {llm_response.text}")
                
            # 测试Embedding配置API（脱敏版本）
            embedding_response = requests.get(
                "https://localhost:8000/api/admin/config/embedding",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            # 测试LLM配置API（原始版本）
            llm_raw_response = requests.get(
                "https://localhost:8000/api/admin/config/llm/raw",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            print(f"\nLLM配置API（原始）状态码: {llm_raw_response.status_code}")
            if llm_raw_response.status_code == 200:
                llm_raw_data = llm_raw_response.json()
                print("LLM原始配置数据:")
                print(json.dumps(llm_raw_data, indent=2, ensure_ascii=False))
                
                # 检查是否有完整的api_key字段
                if 'api_key' in llm_raw_data:
                    print(f"\n完整API Key: {llm_raw_data['api_key']}")
                else:
                    print("未找到api_key字段")
            else:
                print(f"LLM原始配置API错误: {llm_raw_response.text}")
                
            # 测试Embedding配置API（原始版本）
            embedding_raw_response = requests.get(
                "https://localhost:8000/api/admin/config/embedding/raw",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            print(f"\nEmbedding配置API（原始）状态码: {embedding_raw_response.status_code}")
            if embedding_raw_response.status_code == 200:
                embedding_raw_data = embedding_raw_response.json()
                print("Embedding原始配置数据:")
                print(json.dumps(embedding_raw_data, indent=2, ensure_ascii=False))
                
                # 检查是否有完整的api_key字段
                if 'api_key' in embedding_raw_data:
                    print(f"\n完整API Key: {embedding_raw_data['api_key']}")
                else:
                    print("未找到api_key字段")
            else:
                print(f"Embedding原始配置API错误: {embedding_raw_response.text}")
                
            print("\n=== 测试完成 ===")
            
            print(f"\nEmbedding配置API状态码: {embedding_response.status_code}")
            if embedding_response.status_code == 200:
                embedding_data = embedding_response.json()
                print("Embedding配置数据:")
                print(json.dumps(embedding_data, indent=2, ensure_ascii=False))
            else:
                print(f"Embedding配置API错误: {embedding_response.text}")
                
        else:
            print(f"登录失败: {login_response.status_code}")
            print(login_response.text)
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    test_config_api()