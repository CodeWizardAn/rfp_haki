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
            // Profile fetch is optional — use a fallback
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
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
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
