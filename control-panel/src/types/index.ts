// API响应类型定义
export interface ApiResponse<T = any> {
  code?: number;
  msg?: string;
  message?: string;
  data?: T;
}

// 用户相关类型
export interface User {
  id: number;
  username: string;
  email?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  api_key?: string;
}

// 客户端信息类型
export interface ClientInfo {
  session_id: string;
  client_type: string;
  client_id: string;
  platform: string;
  client_version: string;
  ip_address: string;
  created_at: string;
  expires_at: string;
  is_active: boolean;
  function_names: string[];
  function_count: number;
  last_heartbeat: string;
  time_since_heartbeat: number;
}

// 客户端统计类型
export interface ClientStats {
  total_clients: number;
  active_sessions: number;
  inactive_sessions: number;
  client_types: Record<string, number>;
  timestamp: string;
}

// 审计日志类型
export interface AuditLog {
  id: number;
  user_id?: number;
  action: string;
  ip_address?: string;
  details: string;
  created_at: string;
}

// 分页参数
export interface PaginationParams {
  page?: number;
  size?: number;
}

// 分页响应
export interface PaginationResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// LLM配置类型
export interface LLMConfig {
  base_url: string;
  api_key: string;
  model: string;
  parameters: {
    temperature: number;
    max_tokens: number;
    top_p: number;
    stream: boolean;
    seed?: number;
    presence_penalty: number;
    frequency_penalty: number;
    n: number;
  };
}

// STT配置类型
export interface STTConfig {
  base_url: string;
  api_key: string;
  model: string;
  parameters: {
    sample_rate: number;
    format: string;
    language: string;
    enable_punctuation: boolean;
    enable_itn: boolean;
    enable_vad: boolean;
    vad_silence_timeout: number;
    max_sentence_length: number;
  };
}

// TTS配置类型
export interface TTSConfig {
  base_url: string;
  api_key: string;
  model: string;
  parameters: {
    voice: string;
    speech_rate: number;
    pitch: number;
    volume: number;
    format: string;
    sample_rate: number;
    enable_subtitle: boolean;
  };
}

// SRS配置类型
export interface SRSConfig {
  base_url: string;
  api_key?: string;
  timeout: number;
  search_params: {
    top_k: number;
    threshold: number;
  };
}

// 会话配置类型
export interface SessionConfig {
  session_timeout_minutes: number;
  inactivity_timeout_minutes: number;
  heartbeat_timeout_minutes: number;
  cleanup_interval_seconds: number;
  deep_validation_interval_seconds: number;
  log_level: string;
  enable_auto_cleanup: boolean;
  enable_heartbeat_monitoring: boolean;
}

// 系统监控状态
export interface MonitorStatus {
  service_status: string;
  version: string;
  uptime: string;
}

// 日志响应
export interface LogsResponse {
  lines: string[];
  total: number;
}

