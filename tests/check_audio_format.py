
# -*- coding: utf-8 -*-
"""
检查AudioFormat枚举值
"""
from dashscope.audio.tts_v2.speech_synthesizer import AudioFormat
from dashscope.audio.tts_v2 import AudioFormat as AudioFormat2

print("="*50)
print("AudioFormat枚举值:")
print("="*50)

# 查看AudioFormat枚举
print("\nAudioFormat (speech_synthesizer):")
for attr in dir(AudioFormat):
    if not attr.startswith('_'):
        value = getattr(AudioFormat, attr)
        print(f"  {attr} = {value}")

print("\nAudioFormat (tts_v2):")
for attr in dir(AudioFormat2):
    if not attr.startswith('_'):
        value = getattr(AudioFormat2, attr)
        print(f"  {attr} = {value}")

print("\n" + "="*50)
print("可用值列表:")
print("="*50)

# 检查是否有PCM相关的枚举
print("\n检查是否有PCM格式:")
try:
    from dashscope.audio.tts_v2 import AudioFormat
    print("AudioFormat.MP3_22050HZ_MONO_128KBPS")
    print(dir(AudioFormat))
except Exception as e:
    print(f"错误: {e}")
