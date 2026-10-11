import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  // Don't set default Content-Type — Axios auto-detects:
  //   JSON for plain objects, multipart/form-data (with boundary) for FormData
});

// Separate axios instance for auth refresh — no interceptors to avoid loops
const refreshClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag to prevent multiple concurrent refresh attempts
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

// Request interceptor — inject JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — handle 401/429
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 401 → try refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Skip refresh for auth endpoints themselves
      if (originalRequest.url?.includes('/auth/')) {
        return Promise.reject(error);
      }

      const currentToken = localStorage.getItem('access_token');
      // If running on demo/mock token, don't clear session or dispatch auth:expired on 401
      // This allows service fallback handlers (e.g. client-side RFP analysis) to run smoothly
      if (currentToken?.startsWith('demo-') || currentToken?.startsWith('mock-')) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken || refreshToken === 'null' || refreshToken === 'undefined' || refreshToken.startsWith('demo-')) {
        return Promise.reject(error);
      }

      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve) => {
          addRefreshSubscriber((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }

      isRefreshing = true;

      try {
        // Use separate client (no interceptors) to avoid infinite loop
        const { data } = await refreshClient.post('/auth/refresh', {
          refresh_token: refreshToken,
        });

        const newAccessToken = data.access_token;
        localStorage.setItem('access_token', newAccessToken);
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }

        isRefreshing = false;
        onTokenRefreshed(newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch {
        isRefreshing = false;
        refreshSubscribers = [];
        // Only clear token if we are strictly in online-only mode
        const isOfflineAllowed = import.meta.env.VITE_ENABLE_OFFLINE_DEMO === 'true' || window.location.hostname === 'localhost';
        if (!isOfflineAllowed) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          // Notify the app that auth has expired (store listens for this)
          window.dispatchEvent(new Event('auth:expired'));
        }
        return Promise.reject(error);
      }
    }

    // 429 → retry with backoff
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'] || 2;
      await new Promise((resolve) => setTimeout(resolve, Number(retryAfter) * 1000));
      return api(originalRequest);
    }

    return Promise.reject(error);
  },
);

export default api;
