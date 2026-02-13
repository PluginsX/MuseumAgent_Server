#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试TTS配置是否生效
"""
import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.common.config_utils import load_config
from src.services.tts_service import UnifiedTTSService

# 加载配置
load_config()

async def test_tts_config():
    """测试TTS配置是否正确加载"""
    print("测试TTS配置加载...")
    
    tts_service = UnifiedTTSService()
    
    # 手动触发配置加载
    tts_service._ensure_config_loaded()
    
    print(f"TTS模型: {tts_service.tts_model}")
    print(f"TTS音色: {tts_service.tts_voice}")
    print(f"TTS格式: {tts_service.tts_format}")
    print(f"TTS API密钥: {'已配置' if tts_service.tts_api_key else '未配置'}")
    
    # 测试TTS功能
    print("\n测试TTS合成...")
    try:
        audio_data = await tts_service.synthesize_text("这是一段测试语音。")
        if audio_data:
            print("TTS合成成功！")
            print(f"音频数据大小: {len(audio_data)} 字节")
        else:
            print("TTS合成返回空数据")
    except Exception as e:
        print(f"TTS合成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tts_config())