#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态指令集系统测试脚本
验证会话管理和动态LLM功能
"""

import requests
import json
import time
import uuid
from datetime import datetime


class DynamicCommandSetTester:
    """动态指令集系统测试器"""
    
    def __init__(self, base_url="https://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def test_health_check(self):
        """测试服务健康检查"""
        print("=== 测试1: 服务健康检查 ===")
        try:
            response = requests.get(f"{self.base_url}/", verify=False, timeout=10)
            if response.status_code == 200:
                print("✅ 服务健康检查通过")
                print(f"响应: {response.json()}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def test_session_registration(self):
        """测试会话注册"""
        print("\n=== 测试2: 会话注册 ===")
        
        registration_data = {
            "client_metadata": {
                "client_id": f"test-client-{uuid.uuid4()}",
                "client_type": "web3d",
                "client_version": "1.0.0",
                "platform": "test-environment",
                "capabilities": {
                    "max_concurrent_requests": 3,
                    "supported_scenes": ["study", "public"],
                    "preferred_response_format": "json"
                }
            },
            "operation_set": ["zoom_pattern", "restore_scene", "introduce"]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/session/register",
                json=registration_data,
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.session_id = result["session_id"]
                print("✅ 会话注册成功")
                print(f"会话ID: {self.session_id}")
                print(f"过期时间: {result['expires_at']}")
                print(f"支持功能: {result['supported_features']}")
                return True
            else:
                print(f"❌ 会话注册失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 注册请求失败: {e}")
            return False
    
    def test_session_operations(self):
        """测试获取会话操作集"""
        print("\n=== 测试3: 获取会话操作集 ===")
        
        if not self.session_id:
            print("❌ 没有有效的会话ID")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/session/operations",
                headers={"session-id": self.session_id},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 获取操作集成功")
                print(f"操作指令: {result['operations']}")
                print(f"客户端类型: {result['client_type']}")
                return True
            else:
                print(f"❌ 获取操作集失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 获取操作集请求失败: {e}")
            return False
    
    def test_heartbeat(self):
        """测试心跳功能"""
        print("\n=== 测试4: 心跳功能 ===")
        
        if not self.session_id:
            print("❌ 没有有效的会话ID")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/session/heartbeat",
                headers={"session-id": self.session_id},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 心跳成功")
                print(f"状态: {result['status']}")
                print(f"时间戳: {result['timestamp']}")
                return True
            else:
                print(f"❌ 心跳失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 心跳请求失败: {e}")
            return False
    
    def test_agent_parse_with_session(self):
        """测试带会话的智能体解析"""
        print("\n=== 测试5: 带会话的智能体解析 ===")
        
        test_cases = [
            {
                "input": "放大查看蟠龙盖罍的纹样",
                "expected_ops": ["zoom_pattern"]
            },
            {
                "input": "还原卷体夔纹蟠龙盖罍的历史场景",
                "expected_ops": ["restore_scene"]
            },
            {
                "input": "介绍一下这件青铜器",
                "expected_ops": ["introduce"]
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i} ---")
            print(f"输入: {test_case['input']}")
            
            try:
                request_data = {
                    "user_input": test_case['input'],
                    "client_type": "web3d",
                    "scene_type": "study"
                }
                
                headers = {"Content-Type": "application/json"}
                if self.session_id:
                    headers["session-id"] = self.session_id
                
                response = requests.post(
                    f"{self.base_url}/api/agent/parse",
                    json=request_data,
                    headers=headers,
                    verify=False,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["code"] == 200 and result["data"]:
                        command = result["data"]
                        operation = command["operation"]
                        print(f"✅ 解析成功")
                        print(f"操作指令: {operation}")
                        print(f"文物名称: {command['artifact_name']}")
                        
                        # 检查是否在期望的操作集中
                        if operation in test_case['expected_ops']:
                            print("✅ 操作指令符合预期")
                            success_count += 1
                        else:
                            print(f"⚠️  操作指令不在预期范围内: {test_case['expected_ops']}")
                    else:
                        print(f"❌ 解析失败: {result.get('msg', '未知错误')}")
                else:
                    print(f"❌ HTTP错误: {response.status_code}")
                    print(f"响应内容: {response.text}")
                    
            except Exception as e:
                print(f"❌ 测试用例执行失败: {e}")
        
        print(f"\n📊 测试结果: {success_count}/{len(test_cases)} 成功")
        return success_count == len(test_cases)
    
    def test_session_stats(self):
        """测试会话统计"""
        print("\n=== 测试6: 会话统计 ===")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/session/stats",
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                print("✅ 获取统计信息成功")
                print(f"活跃会话数: {stats['active_sessions']}")
                print(f"总会话数: {stats['total_sessions']}")
                print(f"服务器时间: {stats['server_time']}")
                return True
            else:
                print(f"❌ 获取统计信息失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 统计请求失败: {e}")
            return False
    
    def test_unregistration(self):
        """测试会话注销"""
        print("\n=== 测试7: 会话注销 ===")
        
        if not self.session_id:
            print("❌ 没有有效的会话ID")
            return False
        
        try:
            response = requests.delete(
                f"{self.base_url}/api/session/unregister",
                headers={"session-id": self.session_id},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 会话注销成功")
                print(f"消息: {result['message']}")
                self.session_id = None
                return True
            else:
                print(f"❌ 会话注销失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 注销请求失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始动态指令集系统测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"服务地址: {self.base_url}")
        print("=" * 50)
        
        test_results = []
        
        # 按顺序执行测试
        test_results.append(("健康检查", self.test_health_check()))
        test_results.append(("会话注册", self.test_session_registration()))
        test_results.append(("获取操作集", self.test_session_operations()))
        test_results.append(("心跳功能", self.test_heartbeat()))
        test_results.append(("智能体解析", self.test_agent_parse_with_session()))
        test_results.append(("会话统计", self.test_session_stats()))
        test_results.append(("会话注销", self.test_unregistration()))
        
        # 输出测试总结
        print("\n" + "=" * 50)
        print("📊 测试总结")
        print("=" * 50)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
        
        print(f"\n总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！动态指令集系统工作正常")
            return True
        else:
            print("⚠️  部分测试失败，请检查相关功能")
            return False


if __name__ == "__main__":
    # 创建测试器实例
    tester = DynamicCommandSetTester("https://localhost:8000")
    
    # 运行所有测试
    success = tester.run_all_tests()
    
    # 退出码表示测试结果
    exit(0 if success else 1)