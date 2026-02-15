#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 音频质量测试脚本
用于诊断 TTS 输出的 PCM 数据是否包含静音间隔
"""
import asyncio
import struct
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.tts_service import UnifiedTTSService
from src.common.config_utils import load_config


def analyze_pcm_data(pcm_data: bytes, sample_rate: int = 16000) -> dict:
    """
    分析 PCM 数据，检测静音片段
    
    Args:
        pcm_data: PCM 原始数据（16-bit, 单声道）
        sample_rate: 采样率
    
    Returns:
        分析结果字典
    """
    # 解析 PCM 数据为样本
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    total_samples = len(samples)
    
    # 统计非零样本
    non_zero_samples = sum(1 for s in samples if s != 0)
    
    # 计算最大振幅
    max_amplitude = max(abs(s) for s in samples) if samples else 0
    
    # 检测静音片段（振幅 < 100 的连续样本）
    silence_threshold = 100
    silent_segments = []
    current_silent_start = -1
    
    for i, sample in enumerate(samples):
        if abs(sample) < silence_threshold:
            if current_silent_start == -1:
                current_silent_start = i
        else:
            if current_silent_start != -1:
                silent_duration = (i - current_silent_start) / sample_rate
                if silent_duration > 0.1:  # 只记录超过 100ms 的静音
                    silent_segments.append({
                        'start': current_silent_start / sample_rate,
                        'end': i / sample_rate,
                        'duration': silent_duration
                    })
                current_silent_start = -1
    
    # 处理末尾的静音
    if current_silent_start != -1:
        silent_duration = (total_samples - current_silent_start) / sample_rate
        if silent_duration > 0.1:
            silent_segments.append({
                'start': current_silent_start / sample_rate,
                'end': total_samples / sample_rate,
                'duration': silent_duration
            })
    
    return {
        'total_samples': total_samples,
        'non_zero_samples': non_zero_samples,
        'max_amplitude': max_amplitude,
        'duration': total_samples / sample_rate,
        'silent_segments': silent_segments,
        'data_size': len(pcm_data)
    }


async def test_tts_streaming():
    """测试流式 TTS 输出质量"""
    print("=" * 80)
    print("TTS 音频质量测试")
    print("=" * 80)
    
    # 加载配置
    load_config()
    
    # 创建 TTS 服务实例
    tts_service = UnifiedTTSService()
    
    # 测试文本（包含多个句子）
    test_text = "你好，欢迎来到辽宁省博物馆。今天我将为您介绍馆藏的珍贵文物。"
    
    print(f"\n测试文本: {test_text}")
    print(f"文本长度: {len(test_text)} 字符\n")
    
    # 收集所有音频片段
    audio_chunks = []
    chunk_count = 0
    
    print("开始流式合成...\n")
    
    try:
        async for chunk in tts_service.stream_synthesize(test_text):
            chunk_count += 1
            audio_chunks.append(chunk)
            
            # 分析当前片段
            analysis = analyze_pcm_data(chunk)
            
            print(f"片段 #{chunk_count}:")
            print(f"  大小: {analysis['data_size']} bytes")
            print(f"  时长: {analysis['duration']:.3f} s")
            print(f"  样本数: {analysis['total_samples']}")
            print(f"  非零样本: {analysis['non_zero_samples']} ({analysis['non_zero_samples']/analysis['total_samples']*100:.1f}%)")
            print(f"  最大振幅: {analysis['max_amplitude']}")
            
            if analysis['silent_segments']:
                print(f"  [警告] 检测到 {len(analysis['silent_segments'])} 个静音片段:")
                for idx, seg in enumerate(analysis['silent_segments']):
                    print(f"    [{idx+1}] {seg['start']:.3f}s - {seg['end']:.3f}s (时长: {seg['duration']:.3f}s)")
            else:
                print(f"  [正常] 无明显静音片段")
            print()
        
        print(f"流式合成完成，共收到 {chunk_count} 个片段\n")
        
        # 合并所有片段并分析
        if audio_chunks:
            combined_pcm = b''.join(audio_chunks)
            print("=" * 80)
            print("完整音频分析")
            print("=" * 80)
            
            full_analysis = analyze_pcm_data(combined_pcm)
            
            print(f"总大小: {full_analysis['data_size']} bytes")
            print(f"总时长: {full_analysis['duration']:.3f} s")
            print(f"总样本数: {full_analysis['total_samples']}")
            print(f"非零样本: {full_analysis['non_zero_samples']} ({full_analysis['non_zero_samples']/full_analysis['total_samples']*100:.1f}%)")
            print(f"最大振幅: {full_analysis['max_amplitude']}")
            
            if full_analysis['silent_segments']:
                print(f"\n[警告] 完整音频中检测到 {len(full_analysis['silent_segments'])} 个静音片段 (>100ms):")
                for idx, seg in enumerate(full_analysis['silent_segments']):
                    print(f"  [{idx+1}] {seg['start']:.3f}s - {seg['end']:.3f}s (时长: {seg['duration']:.3f}s)")
                print("\n结论: TTS 输出的音频本身包含静音间隔！")
            else:
                print(f"\n[正常] 完整音频无明显静音片段")
                print("\n结论: TTS 输出质量良好，静音问题可能在客户端处理环节")
            
            # 保存完整音频用于进一步分析
            output_file = "test_tts_output.pcm"
            with open(output_file, 'wb') as f:
                f.write(combined_pcm)
            print(f"\n完整音频已保存到: {output_file}")
            print(f"可使用以下命令播放:")
            print(f"  ffplay -f s16le -ar 16000 -ac 1 {output_file}")
            
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tts_streaming())

