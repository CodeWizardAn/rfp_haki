import api from './api';
import type { AuthTokens, User, ApiResponse } from '@/types';

export interface RegisterPayload {
  username: string;
  password: string;
  email: string;
  full_name?: string;
  role?: 'admin' | 'manager' | 'analyst' | 'viewer';
}

const DEMO_ACCOUNTS: Record<string, { role: 'admin' | 'manager' | 'analyst' | 'viewer'; name: string }> = {
  admin: { role: 'admin', name: 'Haki Administrator' },
  user: { role: 'manager', name: 'Procurement Manager' },
  manager: { role: 'manager', name: 'Operations Manager' },
  analyst: { role: 'analyst', name: 'Tender Analyst' },
  viewer: { role: 'viewer', name: 'Auditor Viewer' },
};

function createDemoSession(username: string): { tokens: AuthTokens; user: User } {
  const account = DEMO_ACCOUNTS[username.toLowerCase()] || {
    role: 'admin' as const,
    name: username.charAt(0).toUpperCase() + username.slice(1),
  };

  const tokens: AuthTokens = {
    access_token: `demo-token-${username}-${Date.now()}`,
    refresh_token: `demo-refresh-${username}-${Date.now()}`,
    token_type: 'bearer',
    expires_in: 86400,
  };

  const user: User = {
    id: 1,
    username,
    email: `${username.toLowerCase()}@hakiprocure.ai`,
    full_name: account.name,
    role: account.role,
    permissions: ['*'],
    is_active: true,
  };

  try {
    sessionStorage.setItem('haki_demo_user', JSON.stringify(user));
  } catch {
    // ignore storage quota errors
  }

  return { tokens, user };
}

export const authService = {
  login: async (username: string, password: string): Promise<AuthTokens> => {
    try {
      const { data } = await api.post<AuthTokens | ApiResponse<AuthTokens>>('/auth/login', { username, password });
      // Backend returns TokenResponse directly (not wrapped in ApiResponse)
      if ('access_token' in data) return data as AuthTokens;
      return (data as ApiResponse<AuthTokens>).data;
    } catch (err: any) {
      const status = err.response?.status;
      const isStaticOrOffline =
        status === 405 ||
        status === 404 ||
        status === 502 ||
        status === 503 ||
        status === 504 ||
        err.code === 'ERR_NETWORK' ||
        !err.response;

      // If backend is not available (e.g. static hosting on Vercel, offline, or 405 Method Not Allowed),
      // allow instant login with demo credentials
      if (isStaticOrOffline) {
        const cleanUser = username.trim().toLowerCase();
        // Allow standard demo logins (admin/admin123, user/user1234, or any demo username)
        const isDemoUser = cleanUser in DEMO_ACCOUNTS || cleanUser === 'admin';
        const isDemoPass =
          password === 'admin123' ||
          password === 'user1234' ||
          password === 'viewer123' ||
          password.length >= 4;

        if (isDemoUser && isDemoPass) {
          console.info('ℹ️ Running in demo mode fallback for static hosting/offline backend');
          const { tokens } = createDemoSession(username);
          return tokens;
        }

        throw new Error(
          status === 405
            ? 'Backend not connected on this preview deployment. Use demo credentials (admin / admin123 or user / user1234) or click Quick Demo below.'
            : 'Unable to connect to backend server. Use demo credentials (admin / admin123) to continue.'
        );
      }

      // If the backend actually responded with an auth error (e.g. 401 Invalid Credentials), bubble up the detail
      const detail = err.response?.data?.detail;
      if (detail && typeof detail === 'string') {
        throw new Error(detail);
      }
      throw err;
    }
  },

  register: async (payload: RegisterPayload): Promise<{ user_id: string; username: string }> => {
    try {
      const { data } = await api.post<ApiResponse<{ user_id: string; username: string }>>('/auth/register', payload);
      return data.data ?? (data as any);
    } catch (err: any) {
      const status = err.response?.status;
      if (status === 405 || status === 404 || !err.response) {
        // Fallback for demo on static hosting
        const { user } = createDemoSession(payload.username);
        user.email = payload.email;
        user.full_name = payload.full_name || payload.username;
        sessionStorage.setItem('haki_demo_user', JSON.stringify(user));
        return { user_id: `USR_${Date.now()}`, username: payload.username };
      }
      throw err;
    }
  },

  logout: async (): Promise<void> => {
    const token = localStorage.getItem('access_token');
    if (!token?.startsWith('demo-token')) {
      try {
        await api.post('/auth/logout');
      } catch {
        // Ignore logout errors
      }
    }
    sessionStorage.removeItem('haki_demo_user');
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    if (refreshToken.startsWith('demo-refresh')) {
      return {
        access_token: `demo-token-${Date.now()}`,
        refresh_token: `demo-refresh-${Date.now()}`,
        token_type: 'bearer',
        expires_in: 86400,
      };
    }

    try {
      const { data } = await api.post<AuthTokens | ApiResponse<AuthTokens>>('/auth/refresh', {
        refresh_token: refreshToken,
      });
      if ('access_token' in data) return data as AuthTokens;
      return (data as ApiResponse<AuthTokens>).data;
    } catch (error: any) {
      console.error('Refresh token failed:', error.response?.status, error.response?.data);
      throw error;
    }
  },

  getProfile: async (): Promise<User> => {
    const token = localStorage.getItem('access_token');
    if (token?.startsWith('demo-token')) {
      const cached = sessionStorage.getItem('haki_demo_user');
      if (cached) {
        try {
          return JSON.parse(cached) as User;
        } catch {
          // fallback below
        }
      }
      return {
        id: 1,
        username: 'admin',
        email: 'admin@hakiprocure.ai',
        full_name: 'Haki Administrator',
        role: 'admin',
        permissions: ['*'],
        is_active: true,
      };
    }

    try {
      const { data } = await api.get<ApiResponse<Record<string, unknown>>>('/auth/me');
      const raw = (data.data ?? data) as Record<string, unknown>;
      return {
        id: 0,
        username: raw.username as string,
        email: (raw.email as string) ?? '',
        full_name: (raw.full_name as string) || (raw.username as string),
        role: (raw.role as string) ?? 'viewer',
        permissions: [],
        is_active: true,
      } as User;
    } catch (err: any) {
      // In offline/static mode, fallback to demo user
      const cached = sessionStorage.getItem('haki_demo_user');
      if (cached) {
        return JSON.parse(cached) as User;
      }
      return {
        id: 1,
        username: 'admin',
        email: 'admin@hakiprocure.ai',
        full_name: 'Haki Administrator',
        role: 'admin',
        permissions: ['*'],
        is_active: true,
      };
    }
  },
};

