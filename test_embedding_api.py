import requests
import json

# 测试向量化 API
url = "https://localhost:8000/api/admin/embedding/vectorize"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test-token"
}

data = {
    "text": "测试文本"
}

print("测试向量化 API...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, ensure_ascii=False)}")

# 禁用 SSL 证书验证（仅用于测试）
try:
    response = requests.post(
        url,
        headers=headers,
        json=data,
        verify=False
    )
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ 向量化 API 测试成功！")
    else:
        print(f"\n❌ 向量化 API 测试失败，状态码: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ 测试失败: {str(e)}")

print("\n测试完成。")
