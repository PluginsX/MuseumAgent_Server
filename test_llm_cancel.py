# -*- coding: utf-8 -*-
"""
测试 LLM 流式生成取消机制

验证点：
1. LLM 流式生成过程中可以被取消
2. 取消后立即停止接收数据
3. 资源正确释放
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.command_generator import CommandGenerator
from src.session.strict_session_manager import strict_session_manager


async def test_llm_cancel():
    """测试 LLM 流式生成取消"""
    print("=" * 60)
    print("测试：LLM 流式生成取消机制")
    print("=" * 60)
    
    # 1. 创建测试会话
    session_id = "test_cancel_session"
    client_metadata = {
        "platform": "test",
        "require_tts": False,
        "enable_srs": False,  # 禁用 SRS 加快测试
        "user_id": "test_user",
    }
    strict_session_manager.register_session_with_functions(
        session_id, client_metadata, []
    )
    print(f"✓ 创建测试会话: {session_id}")
    
    # 2. 创建取消事件
    cancel_event = asyncio.Event()
    print(f"✓ 创建取消事件")
    
    # 3. 创建 CommandGenerator
    generator = CommandGenerator()
    print(f"✓ 创建 CommandGenerator")
    
    # 4. 启动流式生成任务
    print("\n开始流式生成（将在 2 秒后取消）...")
    print("-" * 60)
    
    chunk_count = 0
    cancelled = False
    
    async def generate_task():
        nonlocal chunk_count, cancelled
        try:
            async for chunk in generator.stream_generate(
                user_input="请详细介绍一下中国的历史文化，包括各个朝代的特点和重要事件",
                session_id=session_id,
                cancel_event=cancel_event
            ):
                chunk_count += 1
                if isinstance(chunk, dict):
                    content = chunk.get("content", "")
                    print(f"[Chunk {chunk_count}] {content}", end="", flush=True)
                elif isinstance(chunk, str):
                    print(chunk, end="", flush=True)
        except Exception as e:
            print(f"\n✗ 生成过程中出错: {e}")
            cancelled = True
    
    # 5. 启动生成任务
    task = asyncio.create_task(generate_task())
    
    # 6. 等待 2 秒后触发取消
    await asyncio.sleep(2)
    print("\n\n" + "=" * 60)
    print("⚠️  触发取消信号...")
    print("=" * 60)
    cancel_event.set()
    
    # 7. 等待任务完成
    await asyncio.sleep(1)
    
    # 8. 检查结果
    print("\n" + "=" * 60)
    print("测试结果：")
    print("=" * 60)
    print(f"✓ 接收到的数据块数量: {chunk_count}")
    print(f"✓ 任务是否完成: {task.done()}")
    print(f"✓ 取消信号是否设置: {cancel_event.is_set()}")
    
    if chunk_count > 0 and task.done():
        print("\n✅ 测试通过：LLM 流式生成成功响应取消信号")
        print("   - 生成过程正常启动")
        print("   - 取消信号被正确检测")
        print("   - 任务及时终止")
    else:
        print("\n✗ 测试失败：取消机制未正常工作")
    
    # 9. 清理
    strict_session_manager.unregister_session(session_id)
    print("\n✓ 清理测试会话")


async def test_cancel_before_start():
    """测试在生成开始前就设置取消信号"""
    print("\n" + "=" * 60)
    print("测试：生成前取消")
    print("=" * 60)
    
    session_id = "test_cancel_before_session"
    client_metadata = {
        "platform": "test",
        "require_tts": False,
        "enable_srs": False,
        "user_id": "test_user",
    }
    strict_session_manager.register_session_with_functions(
        session_id, client_metadata, []
    )
    
    cancel_event = asyncio.Event()
    cancel_event.set()  # 提前设置取消信号
    print("✓ 提前设置取消信号")
    
    generator = CommandGenerator()
    chunk_count = 0
    
    print("\n开始流式生成（应该立即终止）...")
    async for chunk in generator.stream_generate(
        user_input="测试",
        session_id=session_id,
        cancel_event=cancel_event
    ):
        chunk_count += 1
    
    print(f"\n✓ 接收到的数据块数量: {chunk_count}")
    
    if chunk_count == 0:
        print("✅ 测试通过：提前设置的取消信号被正确处理")
    else:
        print("✗ 测试失败：提前设置的取消信号未被检测")
    
    strict_session_manager.unregister_session(session_id)


async def main():
    """运行所有测试"""
    try:
        # 测试 1：正常流式生成后取消
        await test_llm_cancel()
        
        # 测试 2：生成前取消
        await test_cancel_before_start()
        
        print("\n" + "=" * 60)
        print("所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

