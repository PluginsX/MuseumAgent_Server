import requests
import urllib3
import sys

print("Starting API test...")

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 先获取认证token
try:
    print("Getting authentication token...")
    login_response = requests.post(
        "https://localhost:8000/api/auth/login",
        json={"username": "admin", "password": "Admin@123"},
        verify=False,
        timeout=10
    )
    print("Login Status Code:", login_response.status_code)
    if login_response.status_code == 200:
        token_data = login_response.json()
        token = token_data.get('access_token')
        print("Token obtained successfully")
        
        # 使用token测试stats API
        print("\nTesting stats API with authentication...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://localhost:8000/api/admin/embedding/stats",
            headers=headers,
            verify=False,
            timeout=10
        )
        print("Stats Status Code:", response.status_code)
        print("Stats Response:", response.json())
    else:
        print("Login failed:", login_response.text)
except Exception as e:
    print("Authentication Error:", e)
    print("Exception type:", type(e).__name__)

# 测试其他API
try:
    print("\nTesting health check API...")
    response = requests.get(
        "https://localhost:8000/",
        verify=False,
        timeout=10
    )
    print("Health Check Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Health Check Error:", e)
    print("Exception type:", type(e).__name__)

print("API test completed.")