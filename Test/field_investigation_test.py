import requests
import json
import time

print("🔍 字段来源调查测试")
print("=" * 50)

# 1. 注册会话
print("\n1. 注册测试会话")
register_url = "https://localhost:8000/api/session/register"
register_data = {
    "client_metadata": {
        "client_id": "field_investigation_" + str(int(time.time())),
        "client_type": "field_investigation",
        "client_version": "1.0.0",
        "platform": "test"
    },
    "functions": []
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
        session_id = session_data.get('session_id')  # 修正：直接从根级别获取
        print(f"✅ 会话注册成功: {session_id[:8]}...")
    else:
        print(f"❌ 会话注册失败: {register_response.text}")
        exit(1)
        
except Exception as e:
    print(f"❌ 会话注册异常: {e}")
    exit(1)

# 2. 发送测试请求
print("\n2. 发送测试请求")
parse_url = "https://localhost:8000/api/agent/parse"
parse_data = {
    "user_input": "你好",
    "client_type": "field_investigation",
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
    
    print(f"📤 客户端发送: 你好")
    print(f"📥 客户端接收 HTTP {parse_response.status_code}")
    
    if parse_response.status_code == 200:
        response_data = parse_response.json()
        print("📊 客户端收到的完整数据:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        # 分析字段来源
        if 'data' in response_data and response_data['data']:
            data = response_data['data']
            print("\n🔍 字段分析:")
            
            # LLM原始字段
            llm_fields = ['choices', 'created', 'id', 'model', 'object', 'usage']
            print("🟢 LLM原始字段:")
            for field in llm_fields:
                if field in data:
                    print(f"  ✅ {field}: 存在")
                else:
                    print(f"  ❌ {field}: 缺失")
            
            # 旧的传统字段
            old_fields = ['artifact_id', 'artifact_name', 'operation', 'operation_params', 
                         'keywords', 'tips', 'response', 'command', 'parameters', 'type', 
                         'format', 'timestamp', 'session_id', 'processing_mode']
            print("\n🔴 传统/旧字段:")
            found_old_fields = []
            for field in old_fields:
                if field in data and data[field] is not None:
                    print(f"  ⚠️  {field}: {data[field]}")
                    found_old_fields.append(field)
                elif field in data and data[field] is None:
                    print(f"  🔘 {field}: null")
                    found_old_fields.append(field)
            
            if found_old_fields:
                print(f"\n🚨 发现 {len(found_old_fields)} 个旧字段!")
                print("这些字段可能来源于StandardCommand模型的默认字段定义")
            else:
                print("\n✅ 未发现旧字段，数据很干净!")
                
        else:
            print("❌ 响应数据格式异常")
            
    else:
        print(f"❌ API响应错误: {parse_response.text}")
        
except Exception as e:
    print(f"❌ 请求异常: {e}")

print("\n🏁 字段调查完成")