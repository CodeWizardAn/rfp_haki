import api from './api';
import type { AuthTokens, User, ApiResponse } from '@/types';

export interface RegisterPayload {
  username: string;
  password: string;
  email: string;
  full_name?: string;
  role?: 'admin' | 'manager' | 'analyst' | 'viewer';
}

export const authService = {
  login: async (username: string, password: string): Promise<AuthTokens> => {
    const { data } = await api.post<AuthTokens | ApiResponse<AuthTokens>>('/auth/login', { username, password });
    // Backend returns TokenResponse directly (not wrapped in ApiResponse)
    if ('access_token' in data) return data as AuthTokens;
    return (data as ApiResponse<AuthTokens>).data;
  },

  register: async (payload: RegisterPayload): Promise<{ user_id: string; username: string }> => {
    const { data } = await api.post<ApiResponse<{ user_id: string; username: string }>>('/auth/register', payload);
    return data.data ?? data as any;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
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
    const { data } = await api.get<ApiResponse<Record<string, unknown>>>('/auth/me');
    const raw = (data.data ?? data) as Record<string, unknown>;
    // Map backend user shape to frontend User type
    return {
      id: 0,
      username: raw.username as string,
      email: (raw.email as string) ?? '',
      full_name: (raw.full_name as string) || (raw.username as string),
      role: (raw.role as string) ?? 'viewer',
      permissions: [],
      is_active: true,
    } as User;
  },
};
