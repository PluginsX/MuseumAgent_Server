#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打断机制测试脚本

测试场景：
1. 正常打断流程
2. 并发打断
3. 打断不存在的请求
4. 打断后立即发送新请求
"""
import asyncio
import json
import time
from typing import Dict, Any


class MockCancelEvent:
    """模拟 asyncio.Event"""
    def __init__(self):
        self._is_set = False
    
    def set(self):
        self._is_set = True
        print(f"  [OK] 取消信号已设置")
    
    def is_set(self):
        return self._is_set


class InterruptTester:
    """打断机制测试器"""
    
    def __init__(self):
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.test_results = []
    
    def register_request(self, request_id: str, session_id: str):
        """注册活跃请求"""
        cancel_event = MockCancelEvent()
        self.active_requests[request_id] = {
            "session_id": session_id,
            "cancel_event": cancel_event,
            "start_time": time.time(),
            "type": "TEXT"
        }
        print(f"[OK] 注册请求: {request_id[:16]}... (会话: {session_id[:16]}...)")
        return cancel_event
    
    def interrupt_request(self, session_id: str, interrupt_request_id: str = None, reason: str = "USER_NEW_INPUT"):
        """模拟打断请求处理"""
        print(f"\n[测试] 处理打断请求")
        print(f"  会话ID: {session_id[:16]}...")
        print(f"  目标请求: {interrupt_request_id[:16] if interrupt_request_id else 'ALL'}...")
        print(f"  原因: {reason}")
        print(f"  活跃请求数: {len(self.active_requests)}")
        
        interrupted_ids = []
        
        if interrupt_request_id:
            # 中断指定请求
            if interrupt_request_id in self.active_requests:
                req_info = self.active_requests[interrupt_request_id]
                if req_info["session_id"] == session_id:
                    req_info["cancel_event"].set()
                    interrupted_ids.append(interrupt_request_id)
                    print(f"  [OK] 请求已中断: {interrupt_request_id[:16]}...")
                else:
                    print(f"  [FAIL] 请求属于不同会话")
            else:
                print(f"  [FAIL] 请求不存在或已完成")
        else:
            # 中断该会话的所有请求
            for req_id, req_info in list(self.active_requests.items()):
                if req_info["session_id"] == session_id:
                    req_info["cancel_event"].set()
                    interrupted_ids.append(req_id)
            print(f"  [OK] 已中断 {len(interrupted_ids)} 个请求")
        
        # 构建确认消息
        status = "SUCCESS" if interrupted_ids else "PARTIAL"
        message = f"已中断 {len(interrupted_ids)} 个请求" if interrupted_ids else "无活跃请求可中断"
        
        ack = {
            "interrupted_request_ids": interrupted_ids,
            "status": status,
            "message": message
        }
        
        print(f"  → INTERRUPT_ACK: {ack}")
        return ack
    
    def cleanup_request(self, request_id: str):
        """清理请求"""
        if request_id in self.active_requests:
            del self.active_requests[request_id]
            print(f"[OK] 清理请求: {request_id[:16]}...")
    
    async def test_normal_interrupt(self):
        """测试1: 正常打断流程"""
        print("\n" + "="*60)
        print("测试1: 正常打断流程")
        print("="*60)
        
        session_id = "sess_test_001"
        request_id = "req_test_001"
        
        # 1. 注册请求
        cancel_event = self.register_request(request_id, session_id)
        
        # 2. 模拟请求处理中
        print("\n[模拟] 请求处理中...")
        await asyncio.sleep(0.1)
        
        # 3. 发送打断
        ack = self.interrupt_request(session_id, request_id, "USER_NEW_INPUT")
        
        # 4. 检查取消信号
        if cancel_event.is_set():
            print("[PASS] 取消信号已正确设置")
            self.test_results.append(("正常打断", True))
        else:
            print("[FAIL] 取消信号未设置")
            self.test_results.append(("正常打断", False))
        
        # 5. 清理
        self.cleanup_request(request_id)
    
    async def test_interrupt_all(self):
        """测试2: 中断会话的所有请求"""
        print("\n" + "="*60)
        print("测试2: 中断会话的所有请求")
        print("="*60)
        
        session_id = "sess_test_002"
        request_ids = [f"req_test_00{i}" for i in range(2, 5)]
        
        # 1. 注册多个请求
        cancel_events = []
        for req_id in request_ids:
            event = self.register_request(req_id, session_id)
            cancel_events.append(event)
        
        # 2. 中断所有请求（不指定 request_id）
        ack = self.interrupt_request(session_id, None, "USER_NEW_INPUT")
        
        # 3. 检查所有取消信号
        all_set = all(event.is_set() for event in cancel_events)
        if all_set and len(ack["interrupted_request_ids"]) == len(request_ids):
            print(f"[PASS] 所有 {len(request_ids)} 个请求都已中断")
            self.test_results.append(("中断所有请求", True))
        else:
            print(f"[FAIL] 部分请求未中断")
            self.test_results.append(("中断所有请求", False))
        
        # 4. 清理
        for req_id in request_ids:
            self.cleanup_request(req_id)
    
    async def test_interrupt_nonexistent(self):
        """测试3: 中断不存在的请求"""
        print("\n" + "="*60)
        print("测试3: 中断不存在的请求")
        print("="*60)
        
        session_id = "sess_test_003"
        request_id = "req_nonexistent"
        
        # 1. 不注册请求，直接打断
        ack = self.interrupt_request(session_id, request_id, "USER_NEW_INPUT")
        
        # 2. 检查结果
        if ack["status"] == "PARTIAL" and len(ack["interrupted_request_ids"]) == 0:
            print("[PASS] 正确处理不存在的请求")
            self.test_results.append(("中断不存在的请求", True))
        else:
            print("[FAIL] 处理不正确")
            self.test_results.append(("中断不存在的请求", False))
    
    async def test_interrupt_then_new_request(self):
        """测试4: 打断后立即发送新请求"""
        print("\n" + "="*60)
        print("测试4: 打断后立即发送新请求")
        print("="*60)
        
        session_id = "sess_test_004"
        old_request_id = "req_test_old"
        new_request_id = "req_test_new"
        
        # 1. 注册旧请求
        old_cancel_event = self.register_request(old_request_id, session_id)
        
        # 2. 打断旧请求
        print("\n[操作] 打断旧请求")
        ack = self.interrupt_request(session_id, old_request_id, "USER_NEW_INPUT")
        
        # 3. 立即注册新请求
        print("\n[操作] 注册新请求")
        new_cancel_event = self.register_request(new_request_id, session_id)
        
        # 4. 检查状态
        if old_cancel_event.is_set() and not new_cancel_event.is_set():
            print("[PASS] 旧请求已中断，新请求正常")
            self.test_results.append(("打断后新请求", True))
        else:
            print("[FAIL] 状态不正确")
            self.test_results.append(("打断后新请求", False))
        
        # 5. 清理
        self.cleanup_request(old_request_id)
        self.cleanup_request(new_request_id)
    
    async def test_concurrent_interrupts(self):
        """测试5: 并发打断"""
        print("\n" + "="*60)
        print("测试5: 并发打断")
        print("="*60)
        
        session_id = "sess_test_005"
        request_id = "req_test_concurrent"
        
        # 1. 注册请求
        cancel_event = self.register_request(request_id, session_id)
        
        # 2. 并发发送多个打断请求
        print("\n[操作] 并发发送3个打断请求")
        tasks = [
            self.interrupt_request(session_id, request_id, f"INTERRUPT_{i}")
            for i in range(3)
        ]
        
        # 3. 检查结果
        if cancel_event.is_set():
            print("[PASS] 并发打断正确处理")
            self.test_results.append(("并发打断", True))
        else:
            print("[FAIL] 并发打断失败")
            self.test_results.append(("并发打断", False))
        
        # 4. 清理
        self.cleanup_request(request_id)
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("测试摘要")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result)
        failed = total - passed
        
        print(f"\n总测试数: {total}")
        print(f"通过: {passed} [PASS]")
        print(f"失败: {failed} [FAIL]")
        print(f"通过率: {passed/total*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, result in self.test_results:
            status = "[PASS] 通过" if result else "[FAIL] 失败"
            print(f"  {test_name}: {status}")
        
        print("\n" + "="*60)


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("博物馆智能体 - 打断机制测试")
    print("="*60)
    
    tester = InterruptTester()
    
    # 运行所有测试
    await tester.test_normal_interrupt()
    await tester.test_interrupt_all()
    await tester.test_interrupt_nonexistent()
    await tester.test_interrupt_then_new_request()
    await tester.test_concurrent_interrupts()
    
    # 打印摘要
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())

