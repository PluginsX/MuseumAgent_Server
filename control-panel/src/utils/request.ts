import { message } from 'antd';
import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import type { ApiResponse } from '../types';

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // 统一处理响应格式
    const { data } = response;
    
    // 如果响应包含code字段，检查是否成功
    if (data && typeof data.code !== 'undefined') {
      if (data.code === 200 || data.code === 0) {
        // 成功响应，返回data字段或整个响应
        return response;
      } else {
        // 业务错误
        const errorMsg = data.msg || data.message || '请求失败';
        message.error(errorMsg);
        return Promise.reject(new Error(errorMsg));
      }
    }
    
    // 没有code字段，直接返回
    return response;
  },
  (error: AxiosError<ApiResponse>) => {
    console.error('响应错误:', error);
    
    // 处理HTTP错误
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          localStorage.removeItem('token');
          const base = import.meta.env.BASE_URL || '';
          window.location.href = `${base}login`;
          message.error('登录已过期，请重新登录');
          break;
        case 403:
          message.error('没有权限访问该资源');
          break;
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error('服务器内部错误');
          break;
        default:
          const errorMsg = data?.msg || data?.message || data?.detail || '请求失败';
          message.error(errorMsg);
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      message.error('网络连接失败，请检查网络');
    } else {
      // 请求配置出错
      message.error(error.message || '请求配置错误');
    }
    
    return Promise.reject(error);
  }
);

// 封装请求方法
export const http = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) => 
    request.get<ApiResponse<T>>(url, config),
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => 
    request.post<ApiResponse<T>>(url, data, config),
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => 
    request.put<ApiResponse<T>>(url, data, config),
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig) => 
    request.delete<ApiResponse<T>>(url, config),
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => 
    request.patch<ApiResponse<T>>(url, data, config),
};

export default request;

