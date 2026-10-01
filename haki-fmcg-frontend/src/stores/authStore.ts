import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { authService } from '@/services/auth.service';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isHydrated: boolean;
  error: string | null;

  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  clearError: () => void;
  hasPermission: (permission: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: !!localStorage.getItem('access_token'),
      isLoading: false,
      isHydrated: true,
      error: null,

      login: async (username, password) => {
        set({ isLoading: true, error: null });
        const cleanUser = username.trim().toLowerCase();

        // 1. Instant Hardcoded Demo Credentials (works offline & on static Vercel hosting)
        if (
          cleanUser === 'admin' ||
          cleanUser === 'user' ||
          cleanUser === 'manager' ||
          cleanUser === 'analyst' ||
          cleanUser === 'viewer'
        ) {
          const role = cleanUser === 'admin' ? 'admin' : cleanUser === 'viewer' ? 'viewer' : 'manager';
          const demoUser: User = {
            id: cleanUser === 'admin' ? 1 : 2,
            username: cleanUser,
            email: `${cleanUser}@hakiprocure.ai`,
            full_name: cleanUser === 'admin' ? 'Haki Administrator' : cleanUser === 'user' ? 'Procurement Manager' : cleanUser,
            role,
            permissions: ['*'],
            is_active: true,
          };
          const mockToken = `demo-token-${cleanUser}-${Date.now()}`;
          localStorage.setItem('access_token', mockToken);
          localStorage.setItem('refresh_token', `demo-refresh-${cleanUser}-${Date.now()}`);
          try {
            sessionStorage.setItem('haki_demo_user', JSON.stringify(demoUser));
          } catch {
            // ignore
          }
          set({ user: demoUser, isAuthenticated: true, isLoading: false, error: null });
          return;
        }

        // 2. Custom account backend authentication
        try {
          const tokens = await authService.login(username, password);
          localStorage.setItem('access_token', tokens.access_token);
          if (tokens.refresh_token) {
            localStorage.setItem('refresh_token', tokens.refresh_token);
          }
          let user: User | null = null;
          try {
            user = await authService.getProfile();
          } catch {
            user = {
              id: 0,
              username,
              email: '',
              full_name: username,
              role: 'admin',
              permissions: [],
              is_active: true,
            } as User;
          }
          set({ user, isAuthenticated: true, isLoading: false, error: null });
        } catch (err: any) {
          let message = 'Login failed';
          if (err?.response?.data?.detail) {
            message = typeof err.response.data.detail === 'string'
              ? err.response.data.detail
              : JSON.stringify(err.response.data.detail);
          } else if (err?.message) {
            message = err.message;
          }
          set({ error: message, isLoading: false, isAuthenticated: false });
          throw err;
        }
      },

      logout: async () => {
        try {
          await authService.logout();
        } catch {
          // ignore logout API errors
        } finally {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          set({ user: null, isAuthenticated: false });
        }
      },

      fetchProfile: async () => {
        set({ isLoading: true });
        try {
          const user = await authService.getProfile();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          set({ isLoading: false, isAuthenticated: false, user: null });
        }
      },

      clearError: () => set({ error: null }),

      hasPermission: (permission: string) => {
        const { user } = get();
        if (!user) return false;
        if (user.role === 'admin') return true;
        return user.permissions.includes(permission);
      },
    }),
    {
      name: 'haki-auth',
      partialize: (state) => ({ isAuthenticated: state.isAuthenticated, user: state.user }),
      onRehydrateStorage: () => (state) => {
        // If token is missing, force logged-out state
        if (!localStorage.getItem('access_token') && state) {
          state.isAuthenticated = false;
          state.user = null;
        }
        // Mark hydration as complete
        if (state) {
          state.isHydrated = true;
        }
      },
    },
  ),
);

// Listen for token expiry events from the Axios interceptor
if (typeof window !== 'undefined') {
  window.addEventListener('auth:expired', () => {
    useAuthStore.setState({ isAuthenticated: false, user: null });
  });
}
