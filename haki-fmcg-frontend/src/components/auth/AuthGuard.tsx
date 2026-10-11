import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores';

/**
 * Auth check — token presence is the gate for route access.
 * The Zustand store is the source of truth for "user" and "role".
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasToken = !!localStorage.getItem('access_token');

  if (hasToken || isAuthenticated) {
    return <>{children}</>;
  }

  const redirectPath = encodeURIComponent(location.pathname + location.search);
  return <Navigate to={`/login?redirect=${redirectPath}`} replace />;
}

/** Redirects already-authenticated users away from login */
export function GuestGuard({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasToken = !!localStorage.getItem('access_token');

  if (hasToken && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
