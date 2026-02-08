import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      const base = import.meta.env.BASE_URL || '';
      window.location.href = `${base}login`;
    }
    // 对于其他错误，保留完整的错误对象以便前端处理
    return Promise.reject(err);
  }
);

export const auth = {
  login: (username: string, password: string) =>
    api.post<{ access_token: string; token_type: string; expires_in: number }>('/api/auth/login', { username, password }),
  me: () => api.get('/api/auth/me'),
};

export const configApi = {
  getLLM: () => api.get('/api/admin/config/llm/raw'),
  updateLLM: (data: Record<string, unknown>) => api.put('/api/admin/config/llm', data),
  getServer: () => api.get('/api/admin/config/server'),
  validateLLM: (data: { base_url: string; api_key: string; model: string }) =>
    api.post('/api/admin/config/llm/validate', data),
  getSRS: () => api.get('/api/admin/config/srs/raw'),
  updateSRS: (data: Record<string, unknown>) => api.put('/api/admin/config/srs', data),
  validateSRS: (data: { base_url: string; api_key: string }) =>
    api.post('/api/admin/config/srs/validate', data),
};

export const monitorApi = {
  status: () => api.get('/api/admin/monitor/status'),
  logs: (params?: { page?: number; size?: number }) => api.get('/api/admin/monitor/logs', { params }),
  clearLogs: () => api.delete('/api/admin/monitor/logs'), // 添加清空日志方法
};

export const usersApi = {
  list: (params?: { page?: number; size?: number; search?: string }) => api.get('/api/admin/users', { params }),
  create: (data: { username: string; password: string; email?: string; role?: string }) =>
    api.post('/api/admin/users', data),
  update: (id: number, data: { email?: string; role?: string; is_active?: boolean }) =>
    api.put(`/api/admin/users/${id}`, data),
  delete: (id: number) => api.delete(`/api/admin/users/${id}`),
};

export const clientsApi = {
  list: () => api.get('/api/admin/clients/connected'),
  stats: () => api.get('/api/admin/clients/stats'),
  getDetails: (sessionId: string) => api.get(`/api/admin/clients/session/${sessionId}`),
  disconnect: (sessionId: string) => api.delete(`/api/admin/clients/session/${sessionId}`),
};

// 会话配置管理API
export const sessionConfigApi = {
  getCurrent: () => api.get('/api/admin/session-config/current'),
  update: (configData: any) => api.put('/api/admin/session-config/update', configData),
  resetDefaults: () => api.post('/api/admin/session-config/reset-defaults'),
  validate: (configData: any) => api.post('/api/admin/session-config/validate', configData),
};