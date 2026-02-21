/**
 * MuseumAgent SDK 常量定义
 * 集中管理所有常量，便于维护和 tree-shaking
 */

/**
 * 事件常量
 */
export const Events = {
    // 连接事件
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected',
    CONNECTION_ERROR: 'connection_error',
    SESSION_EXPIRED: 'session_expired',
    
    // 消息事件
    MESSAGE_SENT: 'message_sent',
    TEXT_CHUNK: 'text_chunk',
    VOICE_CHUNK: 'voice_chunk',
    MESSAGE_COMPLETE: 'message_complete',
    MESSAGE_ERROR: 'message_error',
    
    // 录音事件
    RECORDING_START: 'recording_start',
    RECORDING_STOP: 'recording_stop',
    RECORDING_ERROR: 'recording_error',
    RECORDING_COMPLETE: 'recording_complete',
    
    // VAD 事件
    SPEECH_START: 'speech_start',
    SPEECH_END: 'speech_end',
    
    // 函数调用事件
    FUNCTION_CALL: 'function_call',
    
    // 打断事件
    INTERRUPTED: 'interrupted'
};

/**
 * 默认配置
 */
export const DEFAULT_CONFIG = {
    serverUrl: 'ws://localhost:8001',
    platform: 'WEB',
    requireTTS: true,
    enableSRS: true,
    autoPlay: true,
    vadEnabled: true,
    vadParams: {
        silenceThreshold: 0.005,
        silenceDuration: 500,
        speechThreshold: 0.015,
        minSpeechDuration: 150,
        preSpeechPadding: 1000,
        postSpeechPadding: 100
    },
    roleDescription: '你叫韩立，辽宁省博物馆智能讲解员，男性。性格热情、阳光、开朗、健谈、耐心。你精通辽博的历史文物、展览背景、文化知识，擅长用通俗的语言讲解复杂的知识。只回答与辽宁省博物馆、文物、历史文化、参观导览相关的内容，保持专业又友好的讲解员形象。',
    responseRequirements: '基于当前所处的场景以及场景的内容，综合相关材料，回答用户的提问。同时你要分析用户的需求！在合适的时机选择合适函数，传入合适的参数返回函数调用响应，调用函数也必须要有语言回答内容！',
    sceneDescription: '当前所处的是"卷体夔纹蟠龙盖罍展示场景"，主要内容为该青铜器表面包含的各种纹样的图形和寓意展示，以及各部分组成结构的造型寓意。',
    functionCalling: []
};

/**
 * 存储键名
 */
export const STORAGE_KEYS = {
    SESSION: 'session',
    CONFIG: 'config',
    AUTH: 'auth'
};

/**
 * 错误类型
 */
export const ERROR_TYPES = {
    NETWORK_ERROR: 'NETWORK_ERROR',
    AUTH_ERROR: 'AUTH_ERROR',
    SESSION_EXPIRED: 'SESSION_EXPIRED',
    UNKNOWN_ERROR: 'UNKNOWN_ERROR'
};

/**
 * 日志级别
 */
export const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3,
    NONE: 4
};

