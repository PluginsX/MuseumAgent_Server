#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试打断逻辑
"""
import asyncio
import time

# 模拟 active_requests
active_requests = {}

def test_auto_interrupt():
    """测试自动打断逻辑"""
    
    # 模拟第一个请求
    session_id = "sess_test123"
    request_id_1 = "req_001"
    cancel_event_1 = asyncio.Event()
    
    active_requests[request_id_1] = {
        "session_id": session_id,
        "cancel_event": cancel_event_1,
        "start_time": time.time(),
        "type": "TEXT"
    }
    
    print(f"✅ 第一个请求已注册: {request_id_1}")
    print(f"   active_requests: {list(active_requests.keys())}")
    print(f"   cancel_event_1.is_set(): {cancel_event_1.is_set()}")
    print()
    
    # 模拟第二个请求到达（应该自动打断第一个）
    request_id_2 = "req_002"
    data_type = "TEXT"
    stream_flag = False
    stream_seq = 0
    
    # 自动打断逻辑
    should_interrupt_old = False
    if data_type == "TEXT":
        should_interrupt_old = True
    elif data_type == "VOICE":
        if stream_flag and stream_seq == 0:
            should_interrupt_old = True
        elif not stream_flag:
            should_interrupt_old = True
    
    print(f"📥 第二个请求到达: {request_id_2}")
    print(f"   should_interrupt_old: {should_interrupt_old}")
    
    if should_interrupt_old:
        interrupted_count = 0
        for old_req_id, req_info in list(active_requests.items()):
            if req_info["session_id"] == session_id and old_req_id != request_id_2:
                req_info["cancel_event"].set()
                interrupted_count += 1
                print(f"   ⚡ 自动打断旧请求: {old_req_id}")
        
        print(f"   ✅ 打断完成，共打断 {interrupted_count} 个请求")
    
    print()
    print(f"🔍 检查 cancel_event_1 状态:")
    print(f"   cancel_event_1.is_set(): {cancel_event_1.is_set()}")
    print()
    
    # 注册第二个请求
    cancel_event_2 = asyncio.Event()
    active_requests[request_id_2] = {
        "session_id": session_id,
        "cancel_event": cancel_event_2,
        "start_time": time.time(),
        "type": "TEXT"
    }
    
    print(f"✅ 第二个请求已注册: {request_id_2}")
    print(f"   active_requests: {list(active_requests.keys())}")
    print()
    
    # 验证结果
    if cancel_event_1.is_set():
        print("✅ 测试通过：第一个请求的 cancel_event 已被设置")
    else:
        print("❌ 测试失败：第一个请求的 cancel_event 未被设置")
    
    if not cancel_event_2.is_set():
        print("✅ 测试通过：第二个请求的 cancel_event 未被设置")
    else:
        print("❌ 测试失败：第二个请求的 cancel_event 被错误设置")

if __name__ == "__main__":
    print("=" * 60)
    print("测试自动打断逻辑")
    print("=" * 60)
    print()
    test_auto_interrupt()
    print()
    print("=" * 60)

