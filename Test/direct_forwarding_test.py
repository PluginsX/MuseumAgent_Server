import requests
import json

print("🚀 LLM原始数据直通转发测试")
print("=" * 50)

# 1. 注册会话
print("\n1. 注册测试会话")
register_url = "https://localhost:8000/api/session/register"
register_data = {
    "client_type": "test_direct",
    "client_version": "1.0.0",
    "platform": "windows"
}

try:
    register_response = requests.post(
        register_url,
        json=register_data,
        headers={"Content-Type": "application/json"},
        verify=False
    )
    
    if register_response.status_code == 200:
        session_data = register_response.json()
        session_id = session_data.get('data', {}).get('session_id')
        print(f"✅ 会话注册成功: {session_id[:8]}...")
    else:
        print(f"❌ 会话注册失败: {register_response.text}")
        exit(1)
        
except Exception as e:
    print(f"❌ 会话注册异常: {e}")
    exit(1)

# 2. 直接测试LLM调用（绕过RAG）
print("\n2. 测试LLM原始数据直通转发")

# 创建一个简化的测试，直接调用不依赖RAG的端点
# 或者我们可以临时禁用RAG来测试直通转发

test_cases = [
    {
        "name": "简单问候",
        "input": "你好"
    },
    {
        "name": "询问能力",
        "input": "你能做什么？"
    }
]

for i, test_case in enumerate(test_cases, 1):
    print(f"\n--- 测试 {i}: {test_case['name']} ---")
    
    parse_url = "https://localhost:8000/api/agent/parse"
    parse_data = {
        "user_input": test_case['input'],
        "client_type": "test_direct",
        "scene_type": "public"
    }
    
    try:
        parse_response = requests.post(
            parse_url,
            json=parse_data,
            headers={
                "Content-Type": "application/json",
                "session-id": session_id
            },
            verify=False
        )
        
        print(f"📤 客户端发送: {test_case['input']}")
        print(f"📥 客户端接收 HTTP {parse_response.status_code}")
        
        if parse_response.status_code == 200:
            response_data = parse_response.json()
            print("📊 客户端收到的最终数据:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # 检查是否为原始LLM响应格式
            if isinstance(response_data, dict) and 'choices' in response_data:
                print("✅ 接收到原始LLM响应格式")
                if response_data.get('choices'):
                    message = response_data['choices'][0].get('message', {})
                    content = message.get('content', '')
                    print(f"💬 LLM回复: {content}")
            else:
                print("⚠️  非原始LLM响应格式")
                
        else:
            print(f"❌ API响应错误: {parse_response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

print("\n🏁 直通转发测试完成")