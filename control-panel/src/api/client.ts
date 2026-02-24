import { http } from '../utils/request';
import type { 
  User, 
  ClientInfo, 
  ClientStats, 
  LLMConfig, 
  STTConfig, 
  TTSConfig, 
  SRSConfig,
  SessionConfig
} from '../types';

// 导出http实例供其他地方使用
export const api = http;

// 认证相关API
export const auth = {
  login: (username: string, password: string) =>
    http.post<{ access_token: string; token_type: string; expires_in: number }>('/api/auth/login', { username, password }),
  me: () => http.get<User>('/api/auth/me'),
};

// 配置管理API
export const configApi = {
  // LLM配置
  getLLM: () => http.get<LLMConfig>('/api/admin/config/llm/raw'),
  updateLLM: (data: Partial<LLMConfig>) => http.put('/api/admin/config/llm', data),
  validateLLM: (data: { base_url: string; api_key: string; model: string }) =>
    http.post<{ valid: boolean; message: string }>('/api/admin/config/llm/validate', data),
  
  // STT配置
  getSTT: () => http.get<STTConfig>('/api/admin/config/stt/raw'),
  updateSTT: (data: Partial<STTConfig>) => http.put('/api/admin/config/stt', data),
  validateSTT: (data: { base_url: string; api_key: string; model: string }) =>
    http.post<{ valid: boolean; message: string }>('/api/admin/config/stt/validate', data),
  
  // TTS配置
  getTTS: () => http.get<TTSConfig>('/api/admin/config/tts/raw'),
  updateTTS: (data: Partial<TTSConfig>) => http.put('/api/admin/config/tts', data),
  validateTTS: (data: { base_url: string; api_key: string; model: string }) =>
    http.post<{ valid: boolean; message: string }>('/api/admin/config/tts/validate', data),
  
  // SRS配置
  getSRS: () => http.get<SRSConfig>('/api/admin/config/srs/raw'),
  updateSRS: (data: Partial<SRSConfig>) => http.put('/api/admin/config/srs', data),
  validateSRS: (data: { base_url: string; api_key?: string }) =>
    http.post<{ valid: boolean; message: string }>('/api/admin/config/srs/validate', data),
  
  // 服务器配置
  getServer: () => http.get('/api/admin/config/server'),
  updateServer: (data: any) => http.put('/api/admin/config/server', data),
};





// 客户端连接管理API
export const clientsApi = {
  list: () => http.get<ClientInfo[]>('/api/admin/clients/connected'),
  stats: () => http.get<ClientStats>('/api/admin/clients/stats'),
  getDetails: (sessionId: string) => http.get<ClientInfo>(`/api/admin/clients/session/${sessionId}`),
  disconnect: (sessionId: string) => http.delete(`/api/admin/clients/session/${sessionId}`),
};

// 会话配置管理API
export const sessionConfigApi = {
  getCurrent: () => http.get<{
    current_config: SessionConfig;
    runtime_info: any;
    session_stats: any;
  }>('/api/admin/session-config/current'),
  update: (configData: Partial<SessionConfig>) => 
    http.put<{ restart_required: boolean }>('/api/admin/session-config/update', configData),
  resetDefaults: () => http.post('/api/admin/session-config/reset-defaults'),
  validate: (configData: Partial<SessionConfig>) => 
    http.post<{ is_valid: boolean; errors: string[] }>('/api/admin/session-config/validate', configData),
};

// 用户管理API
export const usersApi = {
  // 管理员用户
  listAdmins: (page: number = 1, size: number = 10) =>
    http.get<any[]>('/api/admin/users/admins', { params: { page, size } }),
  createAdmin: (data: { username: string; email: string; password: string; role?: string }) =>
    http.post('/api/admin/users/admins', data),
  updateAdmin: (userId: number, data: { username?: string; email?: string; password?: string; role?: string; is_active?: boolean }) =>
    http.put(`/api/admin/users/admins/${userId}`, data),
  deleteAdmin: (userId: number) =>
    http.delete(`/api/admin/users/admins/${userId}`),
  
  // 客户用户
  listClients: (page: number = 1, size: number = 10) =>
    http.get<any[]>('/api/admin/users/clients', { params: { page, size } }),
  createClient: (data: { username: string; email?: string; password: string; role?: string }) =>
    http.post('/api/admin/users/clients', data),
  updateClient: (userId: number, data: { username?: string; email?: string; password?: string; role?: string; is_active?: boolean }) =>
    http.put(`/api/admin/users/clients/${userId}`, data),
  deleteClient: (userId: number) =>
    http.delete(`/api/admin/users/clients/${userId}`),
};