# -*- coding: utf-8 -*-
"""
音频处理API路由
处理TTS和STT相关的HTTP请求
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any
import json
from datetime import datetime

from src.common.enhanced_logger import get_enhanced_logger
from src.common.auth_utils import get_current_user
from src.services.registry import service_registry

router = APIRouter(prefix="/api/audio", tags=["音频处理"])

@router.post("/stt")
async def audio_to_text(audio: UploadFile = File(...), token: str = Depends(get_current_user)):
    """
    音频转文本API - 上传音频文件
    """
    try:
        logger.api.info("Audio-to-text request received", 
                       {'filename': audio.filename, 'size': audio.size, 
                        'user': token.get('sub', 'unknown')})
        
        # 读取音频数据
        audio_data = await audio.read()
        
        # 构建请求对象
        request = {
            "audio_data": audio_data
        }
        
        # 获取音频处理服务
        service = service_registry.get_service("audio_processing")
        if not service:
            raise HTTPException(status_code=500, detail="音频处理服务不可用")
        
        result = await service.stt_convert(request, token)
        
        logger.api.info("Audio-to-text response sent", result)
        return result
    except Exception as e:
        logger.api.error("Audio-to-text conversion failed", {'error': str(e)})
        raise HTTPException(status_code=500, detail=f"音频转文本失败: {str(e)}")


@router.post("/tts")
async def text_to_audio(request: Dict[str, Any], token: str = Depends(get_current_user)):
    """
    文本转音频API
    """
    try:
        logger.api.info("Text-to-audio request received", 
                       {'request_preview': str(request)[:100], 
                        'user': token.get('sub', 'unknown')})
        
        # 获取音频处理服务
        service = service_registry.get_service("audio_processing")
        if not service:
            raise HTTPException(status_code=500, detail="音频处理服务不可用")
        
        result = await service.tts_convert(request, token)
        
        logger.api.info("Text-to-audio response sent", result)
        return result
    except Exception as e:
        logger.api.error("Text-to-audio conversion failed", {'error': str(e)})
        raise HTTPException(status_code=500, detail=f"文本转音频失败: {str(e)}")