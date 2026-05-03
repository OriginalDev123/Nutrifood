import axios from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const AI_SERVICE_URL = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8001';

interface RetryableAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const createClient = (baseURL: string, timeout: number) => axios.create({
  baseURL,
  timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = createClient(API_URL, 60000);
export const aiServiceClient = createClient(AI_SERVICE_URL, 30000);

export const getAuthToken = (): string | null => {
  return localStorage.getItem('access_token');
};

const attachAuthInterceptors = (client: AxiosInstance) => {
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config as RetryableAxiosRequestConfig | undefined;

      if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
        const refreshToken = localStorage.getItem('refresh_token');

        if (refreshToken && !originalRequest.url?.includes('/auth/refresh')) {
          originalRequest._retry = true;

          try {
            const response = await axios.post(`${API_URL}/auth/refresh`, {
              refresh_token: refreshToken,
            });

            const { access_token, refresh_token } = response.data;
            localStorage.setItem('access_token', access_token);
            localStorage.setItem('refresh_token', refresh_token);

            if (!originalRequest.headers) {
              originalRequest.headers = {} as InternalAxiosRequestConfig['headers'];
            }
            (originalRequest.headers as Record<string, string>).Authorization = `Bearer ${access_token}`;
            return client(originalRequest);
          } catch {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
        } else {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }

      return Promise.reject(error);
    }
  );
};

attachAuthInterceptors(apiClient);
attachAuthInterceptors(aiServiceClient);
