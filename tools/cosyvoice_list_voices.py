# cosyvoice_list_voices.py
import os
from dashscope.audio.tts_v2 import VoiceEnrollmentService

# 直接填写您的 API Key（生产环境建议使用环境变量）
DASHSCOPE_API_KEY = "sk-a7558f9302974d1891906107f6033939"

def list_cosy_voices(prefix: str):
    service = VoiceEnrollmentService(api_key=DASHSCOPE_API_KEY)
    # 确保 prefix 为小写、仅含字母/数字、长度 <10
    prefix = prefix.lower()
    if not prefix.isalnum() or len(prefix) >= 10:
        print("错误：前缀必须为小于10位的小写字母或数字")
        return

    voices = service.list_voices(prefix=prefix, page_index=0, page_size=10)
    if voices:
        print(f"找到 {len(voices)} 个音色：")
        for v in voices:
            # 注意：返回的是对象，用 .voice_id 而非 ['voice_id']
            print(f" - voice_id: {v.voice_id} (状态: {v.status})")
    else:
        print("未找到匹配的音色。")

if __name__ == '__main__':
    # 自动查询 hanli（因 CosyVoice 前缀不区分大小写，但要求小写格式）
    prefix = "hanli"
    print(f"正在查询音色前缀: {prefix}")
    list_cosy_voices(prefix)