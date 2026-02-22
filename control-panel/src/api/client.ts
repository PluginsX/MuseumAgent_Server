import { http } from '../utils/request';
import type { 
  User, 
  ClientInfo, 
  ClientStats, 
  AuditLog, 
  LLMConfig, 
  STTConfig, 
  TTSConfig, 
  SRSConfig,
  SessionConfig,
  MonitorStatus,
  LogsResponse,
  PaginationParams 
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

// 系统监控API
export const monitorApi = {
  status: () => http.get<MonitorStatus>('/api/admin/monitor/status'),
  logs: (params?: PaginationParams) => http.get<LogsResponse>('/api/admin/monitor/logs', { params }),
  clearLogs: () => http.delete('/api/admin/monitor/logs'),
};

// 用户管理API
export const usersApi = {
  list: (params?: PaginationParams & { search?: string }) => 
    http.get<User[]>('/api/admin/users/admins', { params }),
  create: (data: { username: string; password: string; email?: string; role?: string }) =>
    http.post<User>('/api/admin/users/admins', data),
  update: (id: number, data: { email?: string; role?: string; is_active?: boolean; password?: string }) =>
    http.put<User>(`/api/admin/users/admins/${id}`, data),
  delete: (id: number) => http.delete(`/api/admin/users/admins/${id}`),
};

// 客户管理API
export const clientsApiExtended = {
  // 创建客户账户
  createClient: (data: { username: string; password: string; email?: string; role?: string; remark?: string }) =>
    http.post<User>('/api/admin/users/clients', data),
  // 删除客户账户
  deleteClient: (clientId: number) => http.delete(`/api/admin/users/clients/${clientId}`),
  // 重置客户API密钥
  resetApiKey: (clientId: number) => 
    http.post<{ api_key: string }>('/api/internal/client/api_key/reset', { client_id: clientId }),
  // 查询审计日志
  getAuditLogs: (params?: { 
    start_time?: string; 
    end_time?: string; 
    action?: string; 
    user_id?: number; 
    page?: number; 
    size?: number;
  }) => http.get<{ logs: AuditLog[]; pagination: any }>('/api/internal/audit/logs', { params }),
  // 获取客户列表
  listClients: (params?: PaginationParams) => 
    http.get<User[]>('/api/admin/users/clients', { params }),
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

// 数据库管理API
export const databaseApi = {
  // 获取数据库表列表
  getTables: () => http.get<{ name: string; rowCount: number }[]>('/api/admin/database/tables'),
  // 获取表数据
  getTableData: (tableName: string, params?: PaginationParams) => 
    http.get<any[]>(`/api/admin/database/tables/${tableName}`, { params }),
  // 创建记录
  createRecord: (tableName: string, data: any) => 
    http.post<any>(`/api/admin/database/tables/${tableName}`, data),
  // 更新记录
  updateRecord: (tableName: string, id: number, data: any) => 
    http.put<any>(`/api/admin/database/tables/${tableName}/${id}`, data),
  // 删除记录
  deleteRecord: (tableName: string, id: number) => 
    http.delete(`/api/admin/database/tables/${tableName}/${id}`),
  // 初始化数据库
  initializeDatabase: () => http.post('/api/admin/database/initialize'),
  // 清空数据库
  clearDatabase: () => http.post('/api/admin/database/clear'),
};