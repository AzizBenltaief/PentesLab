import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication APIs
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me'),
};

// Project APIs
export const projectAPI = {
  create: (data) => api.post('/projects', data),
  list: () => api.get('/projects'),
  get: (id) => api.get(`/projects/${id}`),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

// Scan APIs
export const scanAPI = {
  start: (data) => api.post('/scan', data),
  getStatus: (scanId) => api.get(`/status/${scanId}`),
  chat: (scanId, data) => api.post(`/scan/${scanId}/chat`, data),
  getChatHistory: (scanId) => api.get(`/scan/${scanId}/chat/history`),
  getAnalysis: (scanId, force = false) => api.get(`/scan/${scanId}/analysis`, { params: { force } }),
};

// Metrics APIs
export const metricsAPI = {
  getDashboard: () => api.get('/metrics/dashboard'),
};

// Audit APIs
export const auditAPI = {
  getLogs: (limit = 100) => api.get(`/audit/logs?limit=${limit}`),
};

// Health check
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
