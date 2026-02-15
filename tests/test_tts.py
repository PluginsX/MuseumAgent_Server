#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单独测试TTS输出脚本
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.tts_service import UnifiedTTSService
from src.common.config_utils import load_config


async def test_tts():
    """测试TTS服务"""
    print("=" * 60)
    print("TTS测试脚本")
    print("=" * 60)
    
    # 加载配置
    load_config()
    
    # 读取配置
    config_path = project_root / "config" / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    tts_config = config["tts"]
    print(f"\nTTS配置:")
    print(f"  模型: {tts_config['model']}")
    print(f"  音色: {tts_config['voice']}")
    print(f"  格式: {tts_config['format']}")
    
    # 创建输出目录
    output_dir = project_root / "tests" / "tts_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 测试文本
    test_text = "你好，很高兴见到你！我是辽宁省博物馆的智能助手，有什么可以帮你的吗？"
    print(f"\n测试文本: {test_text}")
    
    # 创建TTS服务
    tts_service = UnifiedTTSService()
    
    # 测试非流式TTS
    print("\n" + "=" * 60)
    print("测试1: 非流式TTS")
    print("=" * 60)
    
    try:
        audio_data = await tts_service.synthesize_text(test_text)
        
        if audio_data:
            # 保存音频文件
            output_file = output_dir / "tts_test_non_streaming.pcm"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            print(f"✓ 非流式TTS成功!")
            print(f"✓ 音频文件已保存: {output_file}")
            print(f"✓ 音频大小: {len(audio_data)} 字节")
        else:
            print("✗ 非流式TTS返回空数据")
        
    except Exception as e:
        print(f"✗ 非流式TTS失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试流式TTS
    print("\n" + "=" * 60)
    print("测试2: 流式TTS")
    print("=" * 60)
    
    try:
        all_audio_chunks = []
        
        async for chunk in tts_service.stream_synthesize(test_text):
            all_audio_chunks.append(chunk)
            print(f"✓ 收到音频块: {len(chunk)} 字节")
        
        # 合并所有音频块
        combined_audio = b"".join(all_audio_chunks)
        
        # 保存音频文件
        output_file = output_dir / "tts_test_streaming.pcm"
        with open(output_file, "wb") as f:
            f.write(combined_audio)
        
        print(f"\n✓ 流式TTS成功!")
        print(f"✓ 音频文件已保存: {output_file}")
        print(f"✓ 总音频大小: {len(combined_audio)} 字节")
        print(f"✓ 音频块数量: {len(all_audio_chunks)}")
        
    except Exception as e:
        print(f"✗ 流式TTS失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print(f"\n音频文件保存在: {output_dir}")
    print("\n您可以使用以下工具播放PCM文件:")
    print("  - Audacity: 导入为原始数据，设置采样率16000Hz，单声道，16位PCM")
    print("  - ffplay: ffplay -f s16le -ar 16000 -ac 1 tts_test.pcm")
    print("  - Python: 使用sounddevice库播放")


if __name__ == "__main__":
    asyncio.run(test_tts())
