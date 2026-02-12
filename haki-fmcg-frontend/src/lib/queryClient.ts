import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { STALE_TIME_SHORT } from '@/utils/constants';
import axios from 'axios';

/** Don't retry on auth errors — the interceptor already handled refresh */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
    return false;
  }
  return failureCount < 2;
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: STALE_TIME_SHORT,
      retry: shouldRetry,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 15000),
      refetchOnWindowFocus: false,
    },
    mutations: {
      onError: (error) => {
        if (axios.isAxiosError(error) && error.response?.status === 401) return; // handled by interceptor
        const message = error instanceof Error ? error.message : 'Something went wrong';
        toast.error(message);
      },
    },
  },
});

export { QueryClientProvider };
