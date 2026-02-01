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
  getEmbedding: () => api.get('/api/admin/config/embedding/raw'),
  updateEmbedding: (data: Record<string, unknown>) => api.put('/api/admin/config/embedding', data),
  getServer: () => api.get('/api/admin/config/server'),
  validateLLM: (data: { base_url: string; api_key: string; model: string }) =>
    api.post('/api/admin/config/llm/validate', data),
  testEmbedding: (data: { base_url: string; api_key: string; model: string; test_text?: string }) =>
    api.post('/api/admin/config/embedding/test', data),
};

export const embeddingApi = {
  vectorize: (data: { text: string; artifact_id?: string }) => api.post('/api/admin/embedding/vectorize', data),
  store: (data: { artifact_id: string; text_content: string; artifact_name?: string }) =>
    api.post('/api/admin/embedding/store', data),
  search: (data: { query_text: string; top_k?: number; artifact_id?: string }) =>
    api.post('/api/admin/embedding/search', data),
  stats: () => api.get('/api/admin/embedding/stats'),
  getArtifact: (artifactId: string) => api.get(`/api/admin/embedding/artifact/${artifactId}`),
  clear: () => api.delete('/api/admin/embedding/clear'),
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